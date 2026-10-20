"""
CureVerseAI — Drug Development
Tissue mapper.

Given a resolved DiseaseIdentity, produce the tissue layer
of the Biological Impact Graph:

    Disease  --affects-->  Tissue

Data flow
---------

    Disease
      |
      v
    Open Targets: disease -> top-N associated targets
      |
      v
    GTEx: per-gene median tissue expression
      |
      v
    Filter to tissues with median TPM >= MIN_TPM
      |
      v
    Keep top TOP_TISSUES_PER_GENE per gene
      |
      v
    Deduplicate across genes, aggregate evidence
      |
      v
    ImpactNodes + Relationships + Evidence

Design decisions (locked)
-------------------------

H1  Top 10 Open Targets targets by association score.
H2  TPM >= 5 threshold, then top 10 tissues per gene.
H3  Deduplicate by tissue ID; aggregate evidence across
    the genes that supported each tissue.
H4  Relationship is Disease --affects--> Tissue
    (NOT system -> tissue; we do not have evidence
    linking a specific GTEx tissue to a specific Monarch
    system, and inventing that link would violate the
    evidence principle).
H5  Reuse RelationshipType.AFFECTS.
H6  GTEx tissueSiteDetailId is the node identity.

Evidence semantics
------------------

Every tissue node's supporting evidence is a list of
(gene symbol, median TPM, GENCODE id) records. The
relationship's evidence_level is ASSOCIATION because the
link is drawn from aggregated population-level expression
data, not from a direct causal observation.

The TPM value is preserved verbatim in evidence metadata.
It is NEVER placed on the Relationship as a numeric
strength.

What this module does NOT do
----------------------------

- It does not call Monarch. Systems were mapped in
  biological_systems.py.
- It does not assign tissues to systems. That would
  require an ontology mapping we have not built.
- It does not interpret TPM as a probability, score, or
  clinical confidence. TPM is a unit of RNA abundance.

Conventions
-----------

- httpx via GTExClient and OpenTargetsClient. No new
  external libraries.
- All returned structures are serializable plain dicts.
- No modification of existing files.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, List, Optional

from app.drug_development.disease.sources.gtex import (
    GTExClient,
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
)
from app.drug_development.sources.open_targets import (
    OpenTargetsClient,
)


# ---------------------------------------------------------------------------
# Constants (from locked decisions H1, H2)
# ---------------------------------------------------------------------------

SOURCE_OT = "Open Targets"
SOURCE_GTEX = "GTEx"

TISSUE_NODE_PREFIX = "tissue:"
DISEASE_NODE_PREFIX = "disease:"

#: H1 — how many top-scoring Open Targets targets to probe.
MAX_TARGETS = 10

#: H2 — minimum median TPM for a tissue to count as
#: expressed for a gene.
MIN_TPM = 5.0

#: H2 — maximum tissues kept per gene after thresholding.
TOP_TISSUES_PER_GENE = 10


# ---------------------------------------------------------------------------
# Mapper
# ---------------------------------------------------------------------------


class TissueMapper:
    """
    Maps a DiseaseIdentity to tissue-level ImpactNodes and
    Relationships using Open Targets + GTEx.
    """

    def __init__(
        self,
        open_targets_client: Optional[OpenTargetsClient] = None,
        gtex_client: Optional[GTExClient] = None,
    ):
        self.open_targets = (
            open_targets_client or OpenTargetsClient()
        )
        self.gtex = gtex_client or GTExClient()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def map_disease_to_tissues(
        self,
        disease: DiseaseIdentity,
    ) -> Dict[str, Any]:
        """
        Build the tissue layer for one disease.

        Returns:

            {
                "disease_node_id": <str or None>,
                "nodes":          [<serialized ImpactNode>, ...],
                "relationships":  [<serialized Relationship>, ...],
                "evidence":       [<serialized ImpactEvidence>, ...],
                "sources":        ["Open Targets", "GTEx"],
                "found":          <bool>,
                "metadata": {
                    "disease_id":            <str>,
                    "targets_queried":       <int>,
                    "targets_resolved":      <int>,
                    "tissues_kept":          <int>,
                    "aggregation": {
                        "<tissue_id>": {
                            "gene_count": <int>,
                            "genes": [<symbol>, ...],
                        },
                        ...
                    },
                },
                "reason": <str or None>,
            }
        """

        disease_node_id = self._disease_node_id(disease)

        if disease_node_id is None:
            return self._empty(
                reason=(
                    "Disease has no identifiers; cannot build "
                    "a disease node."
                )
            )

        ot_disease_id = self._pick_ot_disease_id(disease)

        if ot_disease_id is None:
            return self._empty(
                disease_node_id=disease_node_id,
                reason=(
                    "No Open Targets-compatible identifier "
                    "available for this disease."
                ),
            )

        # ---- Query Open Targets for top-N targets ----------------
        try:
            ot_targets = self._fetch_top_targets(
                ot_disease_id, MAX_TARGETS
            )
        except RuntimeError as exc:
            return self._empty(
                disease_node_id=disease_node_id,
                reason=(
                    "Open Targets request failed: "
                    f"{exc}"
                ),
            )

        if not ot_targets:
            return self._empty(
                disease_node_id=disease_node_id,
                reason=(
                    f"Open Targets returned no associated "
                    f"targets for {ot_disease_id}."
                ),
                extra_metadata={
                    "disease_id": ot_disease_id,
                    "targets_queried": 0,
                },
            )

        # ---- Per-target GTEx lookup + thresholding --------------
        aggregated: Dict[str, Dict[str, Any]] = {}
        targets_resolved = 0

        for target in ot_targets:
            symbol = target.get("symbol")
            if not symbol:
                continue

            try:
                expr = self.gtex.get_gene_tissue_expression(
                    symbol
                )
            except RuntimeError:
                # Skip this gene, keep going.
                continue

            if not expr.get("found"):
                continue

            targets_resolved += 1

            # Filter + cap (H2)
            kept = [
                t
                for t in expr["tissues"]
                if t["median_tpm"] >= MIN_TPM
            ]
            kept.sort(
                key=lambda t: t["median_tpm"],
                reverse=True,
            )
            kept = kept[:TOP_TISSUES_PER_GENE]

            for t in kept:
                tissue_id = t["tissue_id"]

                entry = aggregated.setdefault(
                    tissue_id,
                    {
                        "tissue_id": tissue_id,
                        "gene_hits": [],
                    },
                )

                entry["gene_hits"].append(
                    {
                        "gene_symbol": symbol,
                        "gencode_id": expr["gencode_id"],
                        "median_tpm": t["median_tpm"],
                        "unit": t["unit"],
                        "ot_score": target.get("score"),
                    }
                )

        if not aggregated:
            return self._empty(
                disease_node_id=disease_node_id,
                reason=(
                    "No tissue passed the TPM threshold for "
                    "any of the top targets."
                ),
                extra_metadata={
                    "disease_id": ot_disease_id,
                    "targets_queried": len(ot_targets),
                    "targets_resolved": targets_resolved,
                },
            )

        # ---- Build nodes, relationships, evidence ---------------
        nodes: List[ImpactNode] = []
        relationships: List[Relationship] = []
        evidence_records: List[ImpactEvidence] = []

        for tissue_id, entry in aggregated.items():
            gene_hits = entry["gene_hits"]
            gene_count = len(gene_hits)
            gene_symbols = [
                h["gene_symbol"] for h in gene_hits
            ]

            node_id = f"{TISSUE_NODE_PREFIX}{tissue_id}"

            node = ImpactNode(
                node_id=node_id,
                node_type=NodeType.TISSUE,
                name=tissue_id,
                identifier=tissue_id,
                description=None,
                evidence_ids=[],
                metadata={
                    "display_name": self._display_name(
                        tissue_id
                    ),
                    "gtex_tissue_id": tissue_id,
                    "supporting_gene_count": gene_count,
                    "supporting_genes": gene_symbols,
                    "source": SOURCE_GTEX,
                },
            )
            nodes.append(node)

            evidence_id = (
                f"ev:gtex:tissue:{tissue_id}"
            )

            evidence = ImpactEvidence(
                evidence_id=evidence_id,
                source=SOURCE_GTEX,
                relationship_description=(
                    f"{disease.canonical_name or disease.query} "
                    f"has {gene_count} associated target(s) "
                    f"with median expression >= {MIN_TPM} TPM "
                    f"in {tissue_id}: "
                    f"{', '.join(gene_symbols)}."
                ),
                evidence_level=EvidenceLevel.ASSOCIATION,
                reference=EvidenceReference(
                    source=SOURCE_GTEX,
                    source_id=tissue_id,
                    source_type="database",
                    url=None,
                    metadata={
                        "dataset": self.gtex.DATASET_ID,
                        "min_tpm": MIN_TPM,
                    },
                ),
                identifiers={
                    "gtex_tissue_id": tissue_id,
                },
                metadata={
                    "supporting_gene_count": gene_count,
                    "supporting_genes": gene_symbols,
                    "gene_hits": gene_hits,
                },
            )
            evidence_records.append(evidence)

            relationship = Relationship(
                source_id=disease_node_id,
                target_id=node_id,
                relationship_type=RelationshipType.AFFECTS,
                evidence_ids=[evidence_id],
                evidence_level=EvidenceLevel.ASSOCIATION,
                description=(
                    f"{disease.canonical_name or disease.query} "
                    f"affects {tissue_id} via "
                    f"{gene_count} associated target(s)."
                ),
                metadata={
                    "gtex_tissue_id": tissue_id,
                    "supporting_gene_count": gene_count,
                    "source": SOURCE_GTEX,
                },
            )
            relationships.append(relationship)

        # ---- Aggregation metadata ------------------------------
        aggregation_meta = {
            tissue_id: {
                "gene_count": len(entry["gene_hits"]),
                "genes": [
                    h["gene_symbol"]
                    for h in entry["gene_hits"]
                ],
            }
            for tissue_id, entry in aggregated.items()
        }

        return {
            "disease_node_id": disease_node_id,
            "nodes": [asdict(n) for n in nodes],
            "relationships": [asdict(r) for r in relationships],
            "evidence": [asdict(e) for e in evidence_records],
            "sources": [SOURCE_OT, SOURCE_GTEX],
            "found": True,
            "metadata": {
                "disease_id": ot_disease_id,
                "targets_queried": len(ot_targets),
                "targets_resolved": targets_resolved,
                "tissues_kept": len(aggregated),
                "aggregation": aggregation_meta,
            },
            "reason": None,
        }

    # ------------------------------------------------------------------
    # Open Targets helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _pick_ot_disease_id(
        disease: DiseaseIdentity,
    ) -> Optional[str]:
        """
        Pick the identifier Open Targets expects. It accepts
        EFO, MONDO, Orphanet IDs. Preference order:

            1. MONDO (colon form)
            2. EFO   (colon form)
            3. Orphanet

        Open Targets' GraphQL accepts both colon and
        underscore form for these prefixes; we pass colon
        form since that is what our schemas store.
        """

        identifiers = disease.identifiers or []

        for prefix in ("MONDO:", "EFO:", "Orphanet:"):
            for ident in identifiers:
                value = (ident.identifier or "").strip()
                if value.startswith(prefix):
                    return value

        return None

    def _fetch_top_targets(
        self,
        ot_disease_id: str,
        size: int,
    ) -> List[Dict[str, Any]]:
        """
        Query Open Targets for the top-N associated targets
        of a disease. Returns a list of dicts with keys
        `id`, `symbol`, `score`.
        """

        graphql_query = """
        query DiseaseTargets($id: String!, $size: Int!) {
          disease(efoId: $id) {
            id
            name
            associatedTargets(
              page: {index: 0, size: $size}
            ) {
              count
              rows {
                target {
                  id
                  approvedSymbol
                }
                score
              }
            }
          }
        }
        """

        # Open Targets GraphQL uses underscore form for the
        # efoId argument. Convert colon form -> underscore
        # form for the request only.
        ot_id_arg = ot_disease_id.replace(":", "_")

        data = self.open_targets.query(
            graphql_query,
            {"id": ot_id_arg, "size": size},
        )

        disease = data.get("disease") or {}
        associations = (
            disease.get("associatedTargets") or {}
        )
        rows = associations.get("rows") or []

        targets: List[Dict[str, Any]] = []

        for row in rows:
            target = row.get("target") or {}
            symbol = target.get("approvedSymbol")
            target_id = target.get("id")

            if not symbol or not target_id:
                continue

            targets.append(
                {
                    "id": target_id,
                    "symbol": symbol,
                    "score": row.get("score"),
                }
            )

        return targets

    # ------------------------------------------------------------------
    # Node helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _disease_node_id(
        disease: DiseaseIdentity,
    ) -> Optional[str]:
        """
        Mirrors biological_systems.py's node ID derivation
        so the disease node ID is identical across the two
        layers of the same impact result.
        """

        if not disease.identifiers:
            return None

        primary = disease.identifiers[0]
        ident = (primary.identifier or "").strip()

        if not ident:
            return None

        sanitized = ident.replace(":", "_")

        return f"{DISEASE_NODE_PREFIX}{sanitized}"

    @staticmethod
    def _display_name(gtex_tissue_id: str) -> str:
        """
        Convert GTEx tissueSiteDetailId to a display form.

            "Brain_Cortex"            -> "Brain cortex"
            "Adipose_Subcutaneous"    -> "Adipose subcutaneous"
            "Artery_Aorta"            -> "Artery aorta"
            "Cells_EBV-transformed_lymphocytes"
                -> "Cells EBV-transformed lymphocytes"
        """

        if not gtex_tissue_id:
            return ""

        words = gtex_tissue_id.replace("_", " ").split()
        if not words:
            return ""

        return " ".join(
            [words[0].capitalize()]
            + [w.lower() for w in words[1:]]
        )

    @staticmethod
    def _empty(
        disease_node_id: Optional[str] = None,
        reason: Optional[str] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return {
            "disease_node_id": disease_node_id,
            "nodes": [],
            "relationships": [],
            "evidence": [],
            "sources": [SOURCE_OT, SOURCE_GTEX],
            "found": False,
            "metadata": extra_metadata or {},
            "reason": reason,
        }
