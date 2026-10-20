"""
CureVerseAI — Drug Development
Workflow 02 — Reverse Disease Engineering
Mechanism Retriever (layer module).

Emits the second W02 graph layer:

    disease  --involves-->  mechanism

What "mechanism" means in this workflow
---------------------------------------

Open Targets does NOT expose a named "mechanism" per disease.
What it exposes, for each disease-associated target, is a
structured attribution of what KIND of evidence supports the
association:

    datatypeScores:   literature, clinical, genetic_association,
                      rna_expression, animal_model
    datasourceScores: europepmc, clinical_precedence,
                      gwas_credible_sets, expression_atlas,
                      gene_burden, impc

Workflow 02 elevates those evidence categories to first-class
mechanism nodes. Each node represents a mode of causal
support the disease has in Open Targets:

    mechanism:evidence:literature
    mechanism:evidence:clinical
    mechanism:evidence:genetic_association
    mechanism:evidence:rna_expression
    mechanism:evidence:animal_model

Each node's metadata carries:

    - how many disease-associated targets exhibit this
      evidence type
    - the mean datatype score across those targets
    - the contributing datasources with their own counts

This is deliberately NOT a named biological mechanism. Named
biological mechanisms (Reactome pathways such as
"Interleukin-4 and Interleukin-13 signaling") belong to the
W02 pathways layer, which is a separate graph layer. The
mechanisms layer answers "what kinds of evidence explain the
disease" rather than "which named process drives it."

Provenance
----------

Every mechanism node and every disease -> mechanism
relationship carries an ImpactEvidence record sourced from
Open Targets. No numeric score is stored as a probability;
counts and mean scores retain their source meaning.

What this module does NOT do
----------------------------

- It does not invent a mechanism name that Open Targets
  did not return.
- It does not conflate genes with mechanisms. Genes are
  a separate layer produced by gene_variant_mapper.py.
- It does not rank mechanisms. Ordering is preserved as
  Open Targets returned the targets; aggregations are
  sorted by target count descending, which is a count,
  not a score.

Output shape
------------

Mirrors the phenotype layer exactly:

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
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import asdict
from typing import Any, Dict, List, Optional

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
from app.drug_development.sources.open_targets import (
    OpenTargetsClient,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


SOURCE_NAME = "Open Targets"

DISEASE_NODE_PREFIX = "disease:"
MECHANISM_NODE_PREFIX = "mechanism:evidence:"

#: How many top-ranked disease-associated targets to scan
#: when aggregating evidence types. 20 is enough to capture
#: every datatype that Open Targets plausibly attaches to a
#: disease without paying for a full pagination.
_TOP_TARGETS = 20

#: A datatype must appear in at least this many targets to
#: become a mechanism node. One-off datatypes are dropped as
#: noise; they remain visible in the layer metadata.
_MIN_TARGETS_FOR_NODE = 2

#: Descriptive labels for the datatype ids Open Targets
#: currently uses. If Open Targets adds a new datatype, the
#: retriever still emits a node for it using the raw id as
#: the label fallback. The dict is a display convenience,
#: not an allowlist.
_DATATYPE_LABELS: Dict[str, str] = {
    "literature": "Literature-supported associations",
    "clinical": "Clinical precedence evidence",
    "genetic_association": "Genetic association evidence",
    "rna_expression": "RNA expression evidence",
    "animal_model": "Animal model evidence",
    "somatic_mutation": "Somatic mutation evidence",
    "affected_pathway": "Affected pathway evidence",
}


# ---------------------------------------------------------------------------
# Retriever
# ---------------------------------------------------------------------------


class MechanismRetriever:
    """
    Aggregates Open Targets evidence-type attribution across
    disease-associated targets into W02 mechanism nodes.
    """

    def __init__(
        self,
        open_targets_client: Optional[OpenTargetsClient] = None,
    ):
        self.open_targets = (
            open_targets_client or OpenTargetsClient()
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def retrieve(
        self,
        disease: DiseaseIdentity,
    ) -> Dict[str, Any]:
        """
        Build the mechanism layer for one disease.

        Never raises for a disease with no retrievable
        evidence types. RuntimeError from Open Targets
        propagates.
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
                    "identifier available for mechanism "
                    "lookup."
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

        aggregation = self._aggregate_evidence(rows)

        if not aggregation["datatypes"]:
            return self._empty_result(
                disease_node_id=disease_node_id,
                reason=(
                    "Open Targets returned associated targets "
                    "for this disease but none carried "
                    "datatypeScores."
                ),
                extra_metadata={
                    "open_targets_disease_id": ot_disease_id,
                    "rows_returned": len(rows),
                },
            )

        # ---- Build nodes / relationships / evidence --------
        nodes: List[ImpactNode] = []
        relationships: List[Relationship] = []
        evidence_records: List[ImpactEvidence] = []

        kept_datatypes = 0
        dropped_datatypes = 0

        for datatype_id, stats in aggregation["datatypes"].items():
            target_count = stats["target_count"]

            if target_count < _MIN_TARGETS_FOR_NODE:
                dropped_datatypes += 1
                continue

            kept_datatypes += 1

            node_id = self._mechanism_node_id(datatype_id)
            label = self._mechanism_label(datatype_id)

            mean_score = (
                stats["score_sum"] / target_count
                if target_count
                else 0.0
            )

            description = (
                f"{label} supports the link between this "
                f"disease and {target_count} of its "
                f"associated genes. "
                f"Average evidence strength: "
                f"{mean_score:.2f} of 1.0."
            )

            node = ImpactNode(
                node_id=node_id,
                node_type=NodeType.MECHANISM,
                name=label,
                identifier=datatype_id,
                description=description,
                evidence_ids=[],
                metadata={
                    "datatype_id": datatype_id,
                    "targets_supporting": target_count,
                    "mean_score": round(mean_score, 4),
                    "score_sum": round(stats["score_sum"], 4),
                    "datasources": dict(
                        stats["datasources"]
                    ),
                    "source": SOURCE_NAME,
                },
            )
            nodes.append(node)

            # ---- Evidence record -----------------------------
            evidence_id = (
                f"ev:ot:mechanism:{datatype_id}"
            )

            evidence = ImpactEvidence(
                evidence_id=evidence_id,
                source=SOURCE_NAME,
                relationship_description=(
                    f"{disease.canonical_name or disease.query} "
                    f"has {target_count} associated target(s) "
                    f"supported by '{datatype_id}' evidence "
                    f"in Open Targets."
                ),
                evidence_level=EvidenceLevel.ASSOCIATION,
                reference=EvidenceReference(
                    source=SOURCE_NAME,
                    source_id=ot_disease_id,
                    source_type="database",
                    url=None,
                    metadata={
                        "datatype_id": datatype_id,
                        "targets_supporting": target_count,
                        "mean_score": round(mean_score, 4),
                    },
                ),
                identifiers={
                    "open_targets_disease_id": ot_disease_id,
                    "datatype_id": datatype_id,
                },
                metadata={
                    "targets_supporting": target_count,
                    "datasources": dict(
                        stats["datasources"]
                    ),
                },
            )
            evidence_records.append(evidence)

            # ---- Relationship ---------------------------------
            relationship = Relationship(
                source_id=disease_node_id,
                target_id=node_id,
                relationship_type=RelationshipType.INVOLVES,
                evidence_ids=[evidence_id],
                evidence_level=EvidenceLevel.ASSOCIATION,
                support_class=SupportClass.SUPPORTED_ASSOCIATION,
                description=(
                    f"{disease.canonical_name or disease.query} "
                    f"involves {label.lower()} "
                    f"({target_count} associated targets)."
                ),
                metadata={
                    "datatype_id": datatype_id,
                    "targets_supporting": target_count,
                    "source": SOURCE_NAME,
                },
            )
            relationships.append(relationship)

        if not nodes:
            return self._empty_result(
                disease_node_id=disease_node_id,
                reason=(
                    "No datatype appeared in at least "
                    f"{_MIN_TARGETS_FOR_NODE} associated "
                    "targets; mechanism layer is empty."
                ),
                extra_metadata={
                    "open_targets_disease_id": ot_disease_id,
                    "rows_returned": len(rows),
                    "datatypes_seen": list(
                        aggregation["datatypes"].keys()
                    ),
                },
            )

        # ---- Assemble result ------------------------------
        return {
            "disease_node_id": disease_node_id,
            "nodes": [asdict(n) for n in nodes],
            "relationships": [asdict(r) for r in relationships],
            "evidence": [asdict(e) for e in evidence_records],
            "sources": [SOURCE_NAME],
            "found": True,
            "metadata": {
                "open_targets_disease_id": ot_disease_id,
                "rows_returned": len(rows),
                "datatypes_kept": kept_datatypes,
                "datatypes_dropped_below_threshold": (
                    dropped_datatypes
                ),
                "min_targets_for_node": _MIN_TARGETS_FOR_NODE,
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
        """
        Query disease.associatedTargets with the score
        breakdown, and return the raw rows list.
        """

        graphql_query = """
        query W02MechanismRows($efoId: String!, $size: Int!) {
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
            {"efoId": ot_disease_id, "size": _TOP_TARGETS},
        )

        if data is None:
            raise RuntimeError(
                "Open Targets returned no data for "
                f"mechanism query on {ot_disease_id}."
            )

        disease = data.get("disease")

        if disease is None:
            raise RuntimeError(
                "Open Targets returned no disease object for "
                f"mechanism query on {ot_disease_id}. "
                "This usually indicates a rejected GraphQL "
                "sub-selection."
            )

        associated = disease.get("associatedTargets")

        if associated is None:
            # Disease exists but has no associatedTargets
            # block. Legitimate empty result.
            return []

        rows = associated.get("rows") or []

        if not isinstance(rows, list):
            return []

        return rows

    # ------------------------------------------------------------------
    # Aggregation
    # ------------------------------------------------------------------

    @staticmethod
    def _aggregate_evidence(
        rows: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Aggregate datatype and datasource presence across
        the rows.

        Returns:

            {
                "datatypes": {
                    <datatype_id>: {
                        "target_count": <int>,
                        "score_sum":     <float>,
                        "datasources":   {<ds_id>: <count>, ...},
                    },
                    ...
                }
            }

        Only rows with a valid target and datatypeScores are
        considered. No row contributes more than once per
        datatype id.
        """

        datatypes: Dict[str, Dict[str, Any]] = {}

        for row in rows:
            if not isinstance(row, dict):
                continue

            target = row.get("target")
            if not isinstance(target, dict):
                continue

            seen_for_row: set[str] = set()

            for dt in row.get("datatypeScores") or []:
                if not isinstance(dt, dict):
                    continue

                dt_id = dt.get("id")
                if not dt_id or dt_id in seen_for_row:
                    continue

                seen_for_row.add(dt_id)

                entry = datatypes.setdefault(
                    dt_id,
                    {
                        "target_count": 0,
                        "score_sum": 0.0,
                        "datasources": defaultdict(int),
                    },
                )

                try:
                    score_value = float(dt.get("score") or 0.0)
                except (TypeError, ValueError):
                    score_value = 0.0

                entry["target_count"] += 1
                entry["score_sum"] += score_value

            for ds in row.get("datasourceScores") or []:
                if not isinstance(ds, dict):
                    continue

                ds_id = ds.get("id")
                if not ds_id:
                    continue

                # Attach datasource counts to every datatype
                # present in this row. Datasources are not
                # independent evidence types; they are the
                # specific sources feeding the datatype.
                for dt_id in seen_for_row:
                    datatypes[dt_id]["datasources"][ds_id] += 1

        # Materialize defaultdicts into plain dicts for
        # serializability.
        for dt_id, entry in datatypes.items():
            entry["datasources"] = dict(entry["datasources"])

        return {"datatypes": datatypes}

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
    def _mechanism_node_id(datatype_id: str) -> str:
        return f"{MECHANISM_NODE_PREFIX}{datatype_id}"

    @staticmethod
    def _mechanism_label(datatype_id: str) -> str:
        return _DATATYPE_LABELS.get(
            datatype_id,
            datatype_id.replace("_", " ").capitalize(),
        )

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
    def _empty_result(
        disease_node_id: Optional[str] = None,
        reason: Optional[str] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return {
            "disease_node_id": disease_node_id,
            "nodes": [],
            "relationships": [],
            "evidence": [],
            "sources": [SOURCE_NAME],
            "found": False,
            "metadata": extra_metadata or {},
            "reason": reason,
        }
