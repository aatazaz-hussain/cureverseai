"""
CureVerseAI — Drug Development
Workflow 02 — Reverse Disease Engineering
Gene / Variant Mapper (layer module).

Emits the third W02 graph layer:

    disease  --associated_with-->  gene

And, when a variant source becomes available, a variant
sub-layer:

    gene  --alters-->  variant

In the current W02 Phase 1 build, no variant source is wired
(Open Targets' GraphQL surface does not expose a
target-level variant field — verified by introspection in
Phase 1 File 1b). The variant layer therefore returns an
honest empty list with a provenance entry in metadata. No
variants are fabricated.

What this layer produces
------------------------

For each of the top N disease-associated targets returned
by Open Targets' disease.associatedTargets:

    - one ImpactNode of node_type = GENE
    - one ImpactEvidence record describing the association
    - one Relationship  disease --associated_with--> gene
      with support_class = SUPPORTED_ASSOCIATION

Each gene is enriched, on a best-effort basis, with:

    - Ensembl gene lookup           (already cached, W01 client)
    - reviewed UniProt accession    (already cached, W01 client)
    - ChEMBL target + bioactivity   (only when UniProt resolves;
                                     opt-out via constructor flag)

Enrichment failures are recorded in node metadata. A gene
without Ensembl or UniProt resolution remains a valid gene
node with the Open Targets data alone. Nothing is fabricated.

Enrichment contract
-------------------

The Ensembl + ChEMBL enrichment is heavy (up to 3 network
round-trips per gene, ~20 genes, all cached after first run).
For callers that need a fast path, pass
`fetch_chembl=False` to skip ChEMBL entirely. Ensembl and
UniProt lookups are not skipped because gene identity should
not depend on an opt-in flag.

ChEMBL is deliberately non-blocking:

    - A LookupError from ChEMBL (target not found) records
      a `chembl_status="not_found"` entry on the node and
      moves on.
    - A gene with 0 ChEMBL activities is not an error. It
      records `chembl_status="no_activities"`.
    - Any transport-level RuntimeError from ChEMBL is
      recorded as `chembl_status="error"` with the message,
      and the gene node is still emitted.

The layer never fails because ChEMBL was unavailable.

Runtime
-------

First run:   ~40-90s for 20 genes (cold Ensembl + ChEMBL caches)
Subsequent:  <5s (all cached)

Output shape
------------

Mirrors the phenotype and mechanism layers:

    {
        "disease_node_id": <str or None>,
        "nodes":           [<ImpactNode as dict>, ...],
        "relationships":   [<Relationship as dict>, ...],
        "evidence":        [<ImpactEvidence as dict>, ...],
        "sources":         [<str>, ...],
        "found":           <bool>,
        "metadata":        {...},
        "reason":          <str or None>,
    }

Plus two W02-specific keys inside `metadata`:

    "variants":                 []  (always, in Phase 1)
    "variants_unavailable_reason": <str>
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, List, Optional

from app.data.sources.ensembl import EnsemblClient
from app.drug_development.reverse_disease.utils import (
    to_opentargets_id,
)
from app.drug_development.schemas.disease import (
    DiseaseIdentity,
)
from app.drug_development.schemas.evidence import (
    EvidenceLevel,
    EvidenceReference,
    ImpactEvidence,
)
from app.drug_development.schemas.impact import (
    ImpactNode,
    NodeType,
)
from app.drug_development.schemas.relationships import (
    Relationship,
    RelationshipType,
    SupportClass,
)
from app.drug_development.sources.chembl_evidence import (
    ChEMBLEvidenceService,
)
from app.drug_development.sources.open_targets import (
    OpenTargetsClient,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


SOURCE_NAME = "Open Targets"
ENRICHMENT_SOURCES = ("Ensembl", "UniProt", "ChEMBL")

DISEASE_NODE_PREFIX = "disease:"
GENE_NODE_PREFIX = "gene:"

#: How many top-ranked targets become gene nodes. Aligned
#: with the mechanism layer's _TOP_TARGETS so the two
#: layers describe the same target set.
_TOP_GENES = 20

#: Standard ChEMBL activity types for bioactivity evidence.
_CHEMBL_STANDARD_TYPES = ["IC50", "EC50", "Ki", "Kd", "AC50"]

#: ChEMBL evidence fetches at most this many activities per
#: gene. Kept low because we only need presence, not a full
#: bioactivity dump in Phase 1.
_CHEMBL_ACTIVITY_LIMIT = 10


# ---------------------------------------------------------------------------
# Mapper
# ---------------------------------------------------------------------------


class GeneVariantMapper:
    """
    Maps a disease to its associated genes and enriches each
    gene with Ensembl, UniProt, and (optionally) ChEMBL
    evidence.
    """

    def __init__(
        self,
        open_targets_client: Optional[OpenTargetsClient] = None,
        ensembl_client: Optional[EnsemblClient] = None,
        chembl_service: Optional[ChEMBLEvidenceService] = None,
        fetch_chembl: bool = True,
    ):
        self.open_targets = (
            open_targets_client or OpenTargetsClient()
        )
        self.ensembl = ensembl_client or EnsemblClient()
        self._chembl_service = chembl_service
        self.fetch_chembl = fetch_chembl

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def retrieve(
        self,
        disease: DiseaseIdentity,
    ) -> Dict[str, Any]:
        """
        Build the gene layer for one disease.

        Never raises for a disease with no associated genes.
        Transport failures on Open Targets propagate;
        enrichment failures are absorbed and recorded.
        """

        disease_node_id = self._disease_node_id(disease)

        if disease_node_id is None:
            return self._empty_result(
                reason=(
                    "Disease has no identifiers; cannot build "
                    "a disease node."
                )
            )

        ot_disease_id = self._pick_open_targets_disease_id(
            disease
        )

        if ot_disease_id is None:
            return self._empty_result(
                disease_node_id=disease_node_id,
                reason=(
                    "No Open Targets-compatible disease "
                    "identifier available for gene lookup."
                ),
            )

        rows = self._fetch_open_targets_rows(ot_disease_id)

        if not rows:
            return self._empty_result(
                disease_node_id=disease_node_id,
                reason=(
                    "Open Targets returned no associated "
                    f"targets for {ot_disease_id}."
                ),
                extra_metadata={
                    "open_targets_disease_id": ot_disease_id,
                    "rows_returned": 0,
                },
            )

        # ---- Build gene nodes --------------------------------
        nodes: List[ImpactNode] = []
        relationships: List[Relationship] = []
        evidence_records: List[ImpactEvidence] = []

        dropped_malformed = 0
        ensembl_resolved = 0
        uniprot_resolved = 0
        chembl_resolved = 0
        chembl_with_activities = 0

        for row in rows:
            target = row.get("target")
            if not isinstance(target, dict):
                dropped_malformed += 1
                continue

            ensembl_id = target.get("id")
            symbol = target.get("approvedSymbol")

            if not ensembl_id or not symbol:
                dropped_malformed += 1
                continue

            node_id = self._gene_node_id(str(symbol))

            # ---- Enrichment (best-effort) --------------------
            enrichment = self._enrich_gene(
                gene_symbol=str(symbol),
                ensembl_id=str(ensembl_id),
            )

            if enrichment.get("ensembl_resolved"):
                ensembl_resolved += 1
            if enrichment.get("uniprot_resolved"):
                uniprot_resolved += 1
            if enrichment.get("chembl_resolved"):
                chembl_resolved += 1
                if enrichment.get("chembl_activity_count", 0) > 0:
                    chembl_with_activities += 1

            # ---- Node ----------------------------------------
            score = row.get("score")
            datatypes = self._collect_score_list(
                row.get("datatypeScores")
            )
            datasources = self._collect_score_list(
                row.get("datasourceScores")
            )

            metadata: Dict[str, Any] = {
                "ensembl_id": str(ensembl_id),
                "approved_symbol": str(symbol),
                "approved_name": target.get("approvedName"),
                "biotype": target.get("biotype"),
                "open_targets_score": score,
                "datatype_scores": datatypes,
                "datasource_scores": datasources,
                "source": SOURCE_NAME,
            }
            metadata.update(enrichment)

            node = ImpactNode(
                node_id=node_id,
                node_type=NodeType.GENE,
                name=str(symbol),
                identifier=str(ensembl_id),
                description=target.get("approvedName"),
                evidence_ids=[],
                metadata=metadata,
            )
            nodes.append(node)

            # ---- Evidence record -----------------------------
            evidence_id = f"ev:ot:gene:{symbol}"

            evidence = ImpactEvidence(
                evidence_id=evidence_id,
                source=SOURCE_NAME,
                relationship_description=(
                    f"{disease.canonical_name or disease.query} "
                    f"is associated with gene {symbol} "
                    f"({target.get('approvedName') or symbol})."
                ),
                evidence_level=EvidenceLevel.ASSOCIATION,
                reference=EvidenceReference(
                    source=SOURCE_NAME,
                    source_id=ot_disease_id,
                    source_type="database",
                    url=None,
                    metadata={
                        "gene_symbol": str(symbol),
                        "ensembl_id": str(ensembl_id),
                    },
                ),
                identifiers={
                    "open_targets_disease_id": ot_disease_id,
                    "ensembl_gene_id": str(ensembl_id),
                    "gene_symbol": str(symbol),
                },
                metadata={
                    "score": score,
                    "datatype_scores": datatypes,
                    "datasource_scores": datasources,
                },
            )
            evidence_records.append(evidence)

            # ---- Relationship ---------------------------------
            relationship = Relationship(
                source_id=disease_node_id,
                target_id=node_id,
                relationship_type=RelationshipType.ASSOCIATED_WITH,
                evidence_ids=[evidence_id],
                evidence_level=EvidenceLevel.ASSOCIATION,
                support_class=SupportClass.SUPPORTED_ASSOCIATION,
                description=(
                    f"{disease.canonical_name or disease.query} "
                    f"is associated with {symbol}."
                ),
                metadata={
                    "gene_symbol": str(symbol),
                    "ensembl_id": str(ensembl_id),
                    "open_targets_score": score,
                    "source": SOURCE_NAME,
                },
            )
            relationships.append(relationship)

        if not nodes:
            return self._empty_result(
                disease_node_id=disease_node_id,
                reason=(
                    "Open Targets returned target rows but none "
                    "carried a usable gene identity."
                ),
                extra_metadata={
                    "open_targets_disease_id": ot_disease_id,
                    "rows_returned": len(rows),
                    "dropped_malformed": dropped_malformed,
                },
            )

        # ---- Assemble result ---------------------------------
        return {
            "disease_node_id": disease_node_id,
            "nodes": [asdict(n) for n in nodes],
            "relationships": [asdict(r) for r in relationships],
            "evidence": [asdict(e) for e in evidence_records],
            "sources": [SOURCE_NAME] + list(ENRICHMENT_SOURCES),
            "found": True,
            "metadata": {
                "open_targets_disease_id": ot_disease_id,
                "rows_returned": len(rows),
                "genes_kept": len(nodes),
                "dropped_malformed": dropped_malformed,
                "ensembl_resolved": ensembl_resolved,
                "uniprot_resolved": uniprot_resolved,
                "chembl_resolved": chembl_resolved,
                "chembl_with_activities": chembl_with_activities,
                "fetch_chembl": self.fetch_chembl,
                "variants": [],
                "variants_unavailable_reason": (
                    "No variant source is wired in W02 Phase 1. "
                    "Open Targets' GraphQL surface does not "
                    "expose a target-level variant field "
                    "(verified by introspection). The variant "
                    "layer is deferred to a future phase."
                ),
            },
            "reason": None,
        }

    # ------------------------------------------------------------------
    # Open Targets fetch
    # ------------------------------------------------------------------

    def _fetch_open_targets_rows(
        self,
        ot_disease_id: str,
    ) -> List[Dict[str, Any]]:
        graphql_query = """
        query W02GeneRows($efoId: String!, $size: Int!) {
          disease(efoId: $efoId) {
            id
            name
            associatedTargets(page: { index: 0, size: $size }) {
              count
              rows {
                score
                target {
                  id
                  approvedSymbol
                  approvedName
                  biotype
                }
                datatypeScores {
                  id
                  score
                }
                datasourceScores {
                  id
                  score
                }
              }
            }
          }
        }
        """

        data = self.open_targets.query(
            graphql_query,
            {"efoId": ot_disease_id, "size": _TOP_GENES},
        )

        if data is None:
            raise RuntimeError(
                "Open Targets returned no data for gene query "
                f"on {ot_disease_id}."
            )

        disease = data.get("disease")

        if disease is None:
            raise RuntimeError(
                "Open Targets returned no disease object for "
                f"gene query on {ot_disease_id}. This usually "
                "indicates a rejected GraphQL sub-selection."
            )

        associated = disease.get("associatedTargets")

        if associated is None:
            return []

        rows = associated.get("rows") or []

        if not isinstance(rows, list):
            return []

        return rows

    # ------------------------------------------------------------------
    # Enrichment
    # ------------------------------------------------------------------

    def _enrich_gene(
        self,
        gene_symbol: str,
        ensembl_id: str,
    ) -> Dict[str, Any]:
        """
        Best-effort enrichment. Never raises.

        Returns a dict with at minimum:

            {
                "ensembl_resolved":   <bool>,
                "uniprot_resolved":   <bool>,
                "uniprot_id":         <str or None>,
                "uniprot_protein_name": <str or None>,
                "chembl_resolved":    <bool>,
                "chembl_status":      <str>,   # "not_queried" | "not_found" |
                                               # "no_activities" | "has_activities" |
                                               # "error"
                "chembl_activity_count": <int>,
                "chembl_target_id":   <str or None>,
                "chembl_compound_count": <int>,
                "chembl_errors":      [<str>, ...],
            }
        """
        out: Dict[str, Any] = {
            "ensembl_resolved": False,
            "uniprot_resolved": False,
            "uniprot_id": None,
            "uniprot_protein_name": None,
            "chembl_resolved": False,
            "chembl_status": "not_queried",
            "chembl_activity_count": 0,
            "chembl_target_id": None,
            "chembl_compound_count": 0,
            "chembl_errors": [],
        }

        # ---- Ensembl gene lookup (best-effort) ---------------
        try:
            gene_record = self.ensembl.lookup_gene(gene_symbol)
        except Exception as exc:
            out["chembl_errors"].append(
                f"ensembl lookup failed: {type(exc).__name__}"
            )
            gene_record = None

        if isinstance(gene_record, dict):
            out["ensembl_resolved"] = True
            out["ensembl_description"] = gene_record.get(
                "description"
            )
            out["ensembl_biotype"] = gene_record.get(
                "biotype"
            )
            out["ensembl_seq_region"] = gene_record.get(
                "seq_region_name"
            )

        # ---- UniProt resolution (best-effort) ----------------
        uniprot_id: Optional[str] = None
        uniprot_protein_name: Optional[str] = None

        try:
            uniprot_resolution = (
                self.ensembl.resolve_reviewed_uniprot_accession(
                    ensembl_id=ensembl_id,
                )
            )
        except Exception as exc:
            out["chembl_errors"].append(
                f"uniprot resolution failed: "
                f"{type(exc).__name__}"
            )
            uniprot_resolution = None

        if isinstance(uniprot_resolution, dict):
            accession = uniprot_resolution.get("accession")
            if accession:
                uniprot_id = str(accession)
                uniprot_protein_name = (
                    uniprot_resolution.get("protein_name")
                )
                out["uniprot_resolved"] = True
                out["uniprot_id"] = uniprot_id
                out["uniprot_protein_name"] = (
                    uniprot_protein_name
                )
                out["uniprot_entry_type"] = (
                    uniprot_resolution.get("entry_type")
                )
                out["uniprot_reviewed"] = bool(
                    uniprot_resolution.get("reviewed")
                )

        # ---- ChEMBL enrichment (only if UniProt resolved) ----
        if not self.fetch_chembl:
            out["chembl_status"] = "not_queried"
            return out

        if not uniprot_id:
            out["chembl_status"] = "not_queried"
            out["chembl_errors"].append(
                "chembl skipped: no resolved UniProt accession"
            )
            return out

        try:
            service = self._get_chembl_service()
            bundle = service.get_target_evidence_bundle(
                gene_symbol=gene_symbol,
                uniprot_id=uniprot_id,
                preferred_name=uniprot_protein_name
                or gene_symbol,
                limit=_CHEMBL_ACTIVITY_LIMIT,
                standard_types=_CHEMBL_STANDARD_TYPES,
            )
        except LookupError:
            out["chembl_status"] = "not_found"
            return out
        except Exception as exc:
            out["chembl_status"] = "error"
            out["chembl_errors"].append(
                f"chembl fetch failed: {type(exc).__name__}: "
                f"{str(exc)[:200]}"
            )
            return out

        # Extract a lightweight summary from the bundle.
        target_records = getattr(bundle, "targets", []) or []
        compounds = getattr(bundle, "compounds", []) or []
        relationships = getattr(bundle, "relationships", []) or []

        target_chembl_id: Optional[str] = None
        if target_records:
            first = target_records[0]
            target_chembl_id = getattr(first, "target_id", None)

        activity_count = len(relationships)
        compound_count = len(compounds)

        out["chembl_resolved"] = True
        out["chembl_target_id"] = target_chembl_id
        out["chembl_activity_count"] = activity_count
        out["chembl_compound_count"] = compound_count

        if activity_count > 0:
            out["chembl_status"] = "has_activities"
        else:
            out["chembl_status"] = "no_activities"

        return out

    def _get_chembl_service(self) -> ChEMBLEvidenceService:
        if self._chembl_service is None:
            self._chembl_service = ChEMBLEvidenceService()
        return self._chembl_service

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _disease_node_id(
        disease: DiseaseIdentity,
    ) -> Optional[str]:
        if not disease.identifiers:
            return None

        primary = disease.identifiers[0]
        ident = (primary.identifier or "").strip()

        if not ident:
            return None

        sanitized = ident.replace(":", "_")
        return f"{DISEASE_NODE_PREFIX}{sanitized}"

    @staticmethod
    def _gene_node_id(symbol: str) -> str:
        return f"{GENE_NODE_PREFIX}{symbol.strip().upper()}"

    @staticmethod
    def _pick_open_targets_disease_id(
        disease: DiseaseIdentity,
    ) -> Optional[str]:
        identifiers = disease.identifiers or []

        for prefix in ("MONDO:", "EFO:", "Orphanet:"):
            for ident in identifiers:
                value = (ident.identifier or "").strip()
                if value.startswith(prefix):
                    return to_opentargets_id(value)

        return None

    @staticmethod
    def _collect_score_list(
        raw: Any,
    ) -> List[Dict[str, Any]]:
        if not isinstance(raw, list):
            return []

        out: List[Dict[str, Any]] = []
        for item in raw:
            if not isinstance(item, dict):
                continue
            out.append(
                {
                    "id": item.get("id"),
                    "score": item.get("score"),
                }
            )
        return out

    @staticmethod
    def _empty_result(
        disease_node_id: Optional[str] = None,
        reason: Optional[str] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        meta = extra_metadata or {}
        meta.setdefault("variants", [])
        meta.setdefault(
            "variants_unavailable_reason",
            "Variant layer not available in Phase 1.",
        )

        return {
            "disease_node_id": disease_node_id,
            "nodes": [],
            "relationships": [],
            "evidence": [],
            "sources": [SOURCE_NAME] + list(ENRICHMENT_SOURCES),
            "found": False,
            "metadata": meta,
            "reason": reason,
        }
