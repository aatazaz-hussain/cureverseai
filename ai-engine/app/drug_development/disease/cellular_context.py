"""
CureVerseAI — Drug Development
Cellular Context mapper.

Given a resolved DiseaseIdentity, produce the cell-type
layer of the Biological Impact Graph:

    Disease  --affects-->  Cell type

Data flow
---------

    Disease
      |
      v
    Open Targets: disease -> top-N associated targets
      |
      v
    HPA: per-gene single-cell RNA expression by cell type
      |
      v
    Filter to cell types with nCPM >= MIN_NCPM
      |
      v
    Keep top TOP_CELL_TYPES_PER_GENE per gene
      |
      v
    Deduplicate across genes, aggregate evidence
      |
      v
    ImpactNodes + Relationships + Evidence

Design decisions (locked)
-------------------------

I1(a)  Single-cell columns only.
I2(a)  nCPM >= 1.0 threshold, then top 10 cell types
       per gene.
I3(a)  Request the full verified column list from the
       client and filter client-side.

Cellular state limitation
-------------------------

This mapper identifies CELL TYPES only. It does NOT
distinguish baseline from disease-associated cellular
states. Doing so requires single-cell case-vs-control
comparisons, which is a research-grade analysis, not an
API call. The cell type layer is therefore honest about
what it can and cannot claim.

Evidence semantics
------------------

Every cell-type node's supporting evidence is a list of
(gene symbol, nCPM, Ensembl ID) records. The relationship
evidence_level is ASSOCIATION because the link is drawn
from aggregated single-cell expression, not from a
direct causal observation.

nCPM values are preserved verbatim in evidence metadata
and are NEVER placed on the Relationship as a numeric
strength.

What this module does NOT do
----------------------------

- It does not call GTEx or Monarch. Those sources serve
  other layers of the impact graph.
- It does not assign cell types to tissues or systems.
  That would require an ontology mapping we have not
  built.
- It does not interpret nCPM as a probability, score, or
  clinical confidence. nCPM is a unit of RNA abundance.

Conventions
-----------

- httpx via HPAClient and OpenTargetsClient. No new
  external libraries.
- All returned structures are serializable plain dicts.
- No modification of existing files.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, List, Optional

from app.drug_development.disease.sources.hpa import (
    HPAClient,
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
# Constants (from locked decisions I1-I3)
# ---------------------------------------------------------------------------

SOURCE_OT = "Open Targets"
SOURCE_HPA = "Human Protein Atlas"

CELL_TYPE_NODE_PREFIX = "celltype:"
DISEASE_NODE_PREFIX = "disease:"

#: Same cap as Phase 03 tissue mapping (I1(a) of Phase 03).
MAX_TARGETS = 10

#: Minimum nCPM for a cell type to count as expressed
#: for a gene (I2(a)).
MIN_NCPM = 1.0

#: Maximum cell types kept per gene after thresholding
#: (I2(a)).
TOP_CELL_TYPES_PER_GENE = 10


# ---------------------------------------------------------------------------
# Mapper
# ---------------------------------------------------------------------------


class CellularContextMapper:
    """
    Maps a DiseaseIdentity to cell-type-level ImpactNodes
    and Relationships using Open Targets + HPA.
    """

    def __init__(
        self,
        open_targets_client: Optional[OpenTargetsClient] = None,
        hpa_client: Optional[HPAClient] = None,
    ):
        self.open_targets = (
            open_targets_client or OpenTargetsClient()
        )
        self.hpa = hpa_client or HPAClient()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def map_disease_to_cell_types(
        self,
        disease: DiseaseIdentity,
    ) -> Dict[str, Any]:
        """
        Build the cell-type layer for one disease.

        Returns:

            {
                "disease_node_id": <str or None>,
                "nodes":          [<serialized ImpactNode>, ...],
                "relationships":  [<serialized Relationship>, ...],
                "evidence":       [<serialized ImpactEvidence>, ...],
                "sources":        ["Open Targets",
                                   "Human Protein Atlas"],
                "found":          <bool>,
                "metadata": {
                    "disease_id":          <str>,
                    "targets_queried":     <int>,
                    "targets_resolved":    <int>,
                    "cell_types_kept":     <int>,
                    "aggregation": {
                        "<cell_type>": {
                            "gene_count": <int>,
                            "genes": [<symbol>, ...],
                        },
                        ...
                    },
                    "limitation": (
                        "Cell types only; baseline vs "
                        "disease-associated state not "
                        "distinguished."
                    ),
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

        # ---- Per-target HPA lookup + thresholding ----------------
        aggregated: Dict[str, Dict[str, Any]] = {}
        targets_resolved = 0

        for target in ot_targets:
            symbol = target.get("symbol")
            if not symbol:
                continue

            try:
                expr = self.hpa.get_gene_cell_type_expression(
                    symbol
                )
            except RuntimeError:
                continue

            if not expr.get("found"):
                continue

            targets_resolved += 1

            kept = [
                ct
                for ct in expr["cell_types"]
                if ct["ncpm"] >= MIN_NCPM
            ]
            kept.sort(
                key=lambda ct: ct["ncpm"],
                reverse=True,
            )
            kept = kept[:TOP_CELL_TYPES_PER_GENE]

            for ct in kept:
                cell_type = ct["cell_type"]

                entry = aggregated.setdefault(
                    cell_type,
                    {
                        "cell_type": cell_type,
                        "display": ct["display"],
                        "gene_hits": [],
                    },
                )

                entry["gene_hits"].append(
                    {
                        "gene_symbol": symbol,
                        "ensembl_id": expr["ensembl_id"],
                        "ncpm": ct["ncpm"],
                        "ot_score": target.get("score"),
                    }
                )

        if not aggregated:
            return self._empty(
                disease_node_id=disease_node_id,
                reason=(
                    "No cell type passed the nCPM threshold "
                    "for any of the top targets."
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

        for cell_type, entry in aggregated.items():
            gene_hits = entry["gene_hits"]
            gene_count = len(gene_hits)
            gene_symbols = [
                h["gene_symbol"] for h in gene_hits
            ]
            display = entry["display"]

            node_id = (
                f"{CELL_TYPE_NODE_PREFIX}{cell_type}"
            )

            node = ImpactNode(
                node_id=node_id,
                node_type=NodeType.CELL_TYPE,
                name=cell_type,
                identifier=cell_type,
                description=None,
                evidence_ids=[],
                metadata={
                    "display_name": display,
                    "hpa_cell_type_code": cell_type,
                    "supporting_gene_count": gene_count,
                    "supporting_genes": gene_symbols,
                    "source": SOURCE_HPA,
                },
            )
            nodes.append(node)

            evidence_id = (
                f"ev:hpa:celltype:{cell_type}"
            )

            evidence = ImpactEvidence(
                evidence_id=evidence_id,
                source=SOURCE_HPA,
                relationship_description=(
                    f"{disease.canonical_name or disease.query} "
                    f"has {gene_count} associated target(s) "
                    f"with single-cell expression >= "
                    f"{MIN_NCPM} nCPM in {display}: "
                    f"{', '.join(gene_symbols)}."
                ),
                evidence_level=EvidenceLevel.ASSOCIATION,
                reference=EvidenceReference(
                    source=SOURCE_HPA,
                    source_id=cell_type,
                    source_type="database",
                    url=None,
                    metadata={
                        "min_ncpm": MIN_NCPM,
                    },
                ),
                identifiers={
                    "hpa_cell_type": cell_type,
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
                    f"affects {display} via "
                    f"{gene_count} associated target(s)."
                ),
                metadata={
                    "hpa_cell_type": cell_type,
                    "supporting_gene_count": gene_count,
                    "source": SOURCE_HPA,
                },
            )
            relationships.append(relationship)

        # ---- Aggregation metadata ------------------------------
        aggregation_meta = {
            cell_type: {
                "gene_count": len(entry["gene_hits"]),
                "genes": [
                    h["gene_symbol"]
                    for h in entry["gene_hits"]
                ],
            }
            for cell_type, entry in aggregated.items()
        }

        return {
            "disease_node_id": disease_node_id,
            "nodes": [asdict(n) for n in nodes],
            "relationships": [asdict(r) for r in relationships],
            "evidence": [asdict(e) for e in evidence_records],
            "sources": [SOURCE_OT, SOURCE_HPA],
            "found": True,
            "metadata": {
                "disease_id": ot_disease_id,
                "targets_queried": len(ot_targets),
                "targets_resolved": targets_resolved,
                "cell_types_kept": len(aggregated),
                "aggregation": aggregation_meta,
                "limitation": (
                    "Cell types only; baseline vs "
                    "disease-associated state not "
                    "distinguished."
                ),
            },
            "reason": None,
        }

    # ------------------------------------------------------------------
    # Open Targets helpers (mirrors Phase 03 tissue_mapping.py)
    # ------------------------------------------------------------------

    @staticmethod
    def _pick_ot_disease_id(
        disease: DiseaseIdentity,
    ) -> Optional[str]:
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
        Mirrors biological_systems.py and tissue_mapping.py's
        node ID derivation so all layers of the same impact
        result share the same disease node ID.
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
            "sources": [SOURCE_OT, SOURCE_HPA],
            "found": False,
            "metadata": extra_metadata or {},
            "reason": reason,
        }
