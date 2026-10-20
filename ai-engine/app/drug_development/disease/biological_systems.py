"""
CureVerseAI — Drug Development
Biological System mapper.

Given a resolved DiseaseIdentity, produce the first
anatomical layer of the Biological Impact Graph:

    Disease  --affects-->  Biological System

Data source
-----------

Monarch Initiative (see sources/monarch.py) provides the
disease -> system mapping as counts of HPO phenotype
annotations aggregated by anatomical system.

Every system reported by Monarch with a positive count
becomes an ImpactNode of node_type BIOLOGICAL_SYSTEM, and a
single AFFECTS relationship is emitted from the disease node
to that system node.

Zero-count systems are dropped, per the workflow rule:

    "If evidence is unavailable, do not invent the entity."

Monarch still returns those entries; the mapper simply does
not promote them into the graph. They remain visible in the
returned metadata as evaluated-but-empty, so a caller can
distinguish "not affected" from "not evaluated".

What this module does NOT do
----------------------------

- It does not call Open Targets. Target-level evidence
  belongs to the molecular layer (Phase 05) and is added
  there, not here.

- It does not interpret Monarch's `count` as a probability,
  confidence, or clinical score. The count is preserved in
  the node's metadata verbatim, for downstream ranking
  only. It is NEVER placed on the Relationship as a
  numeric strength.

- It does not fabricate a disease node ID. If the
  DiseaseIdentity has no identifiers at all, the mapper
  returns no graph elements and flags the reason.

- It does not re-rank or re-sort Monarch's output. Systems
  appear in the order Monarch returned them (sorted by
  count descending on the server side).

Conventions
-----------

- Dataclasses from app.drug_development.schemas.* are used
  directly. No new schema types are introduced.
- No new external libraries.
- All returned structures are serializable plain dicts, so
  the impact builder (Phase 09) can consume them without
  conversion.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, List, Optional

from app.drug_development.disease.sources.monarch import (
    MonarchClient,
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


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SOURCE_NAME = "Monarch Initiative"

DISEASE_NODE_PREFIX = "disease:"
SYSTEM_NODE_PREFIX = "system:"


# ---------------------------------------------------------------------------
# Mapper
# ---------------------------------------------------------------------------


class BiologicalSystemsMapper:
    """
    Maps a DiseaseIdentity to system-level ImpactNodes and
    Relationships using Monarch Initiative data.
    """

    def __init__(
        self,
        monarch_client: Optional[MonarchClient] = None,
    ):
        self.monarch = monarch_client or MonarchClient()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def map_disease_to_systems(
        self,
        disease: DiseaseIdentity,
    ) -> Dict[str, Any]:
        """
        Build the system layer for one disease.

        Returns:

            {
                "disease_node_id": <str or None>,
                "nodes":          [<serialized ImpactNode>, ...],
                "relationships":  [<serialized Relationship>, ...],
                "evidence":       [<serialized ImpactEvidence>, ...],
                "sources":        ["Monarch Initiative"],
                "found":          <bool>,
                "metadata": {
                    "monarch_disease_id":   <str>,
                    "systems_evaluated":    <int>,
                    "systems_kept":         <int>,
                    "systems_dropped_zero": <int>,
                    "annotated_count":      <int>,
                },
                "reason": <str or None>,
            }
        """

        # ---- Resolve the disease node ID --------------------------
        disease_node_id = self._disease_node_id(disease)

        if disease_node_id is None:
            return self._empty_result(
                reason=(
                    "Disease has no identifiers; cannot build "
                    "a disease node."
                )
            )

        # ---- Resolve the Monarch disease ID -----------------------
        monarch_disease_id = self._pick_monarch_disease_id(
            disease
        )

        if monarch_disease_id is None:
            return self._empty_result(
                disease_node_id=disease_node_id,
                reason=(
                    "No MONDO identifier available for Monarch "
                    "lookup."
                ),
            )

        # ---- Query Monarch ----------------------------------------
        histopheno = self.monarch.get_histopheno(
            monarch_disease_id
        )

        if not histopheno.get("found"):
            return self._empty_result(
                disease_node_id=disease_node_id,
                reason=(
                    "Monarch has no phenotype annotations for "
                    f"{monarch_disease_id}."
                ),
            )

        systems_all = histopheno.get("systems") or []
        annotated_count = histopheno.get(
            "annotated_count", 0
        )

        # ---- Filter to positive-count systems ---------------------
        systems_kept = [
            s for s in systems_all if s.get("count", 0) > 0
        ]
        systems_dropped = len(systems_all) - len(systems_kept)

        if not systems_kept:
            return self._empty_result(
                disease_node_id=disease_node_id,
                reason=(
                    "Monarch returned no positively-annotated "
                    "systems."
                ),
                extra_metadata={
                    "monarch_disease_id": monarch_disease_id,
                    "systems_evaluated": len(systems_all),
                    "annotated_count": annotated_count,
                },
            )

        # ---- Build nodes, relationships, evidence -----------------
        nodes: List[ImpactNode] = []
        relationships: List[Relationship] = []
        evidence_records: List[ImpactEvidence] = []

        for system in systems_kept:
            system_id = system.get("id")
            raw_label = str(system.get("label") or "")
            count = int(system.get("count") or 0)

            if not system_id or not raw_label:
                # Skip malformed entries rather than guess.
                continue

            node_id = f"{SYSTEM_NODE_PREFIX}{system_id}"
            display_name = self._display_name(raw_label)

            node = ImpactNode(
                node_id=node_id,
                node_type=NodeType.BIOLOGICAL_SYSTEM,
                name=raw_label,
                identifier=system_id,
                description=None,
                evidence_ids=[],
                metadata={
                    "display_name": display_name,
                    "monarch_label": raw_label,
                    "monarch_id": system_id,
                    "hpo_annotation_count": count,
                    "source": SOURCE_NAME,
                },
            )
            nodes.append(node)

            # ---- Evidence record for the relationship ------------
            evidence_id = (
                f"ev:monarch:system:{system_id}"
            )

            evidence = ImpactEvidence(
                evidence_id=evidence_id,
                source=SOURCE_NAME,
                relationship_description=(
                    f"{disease.canonical_name or disease.query} "
                    f"has {count} HPO phenotype annotation(s) "
                    f"mapped to {raw_label}."
                ),
                evidence_level=EvidenceLevel.ASSOCIATION,
                reference=EvidenceReference(
                    source=SOURCE_NAME,
                    source_id=monarch_disease_id,
                    source_type="database",
                    url=None,
                    metadata={
                        "system_id": system_id,
                        "system_label": raw_label,
                    },
                ),
                identifiers={
                    "monarch_disease_id": monarch_disease_id,
                    "system_id": system_id,
                },
                metadata={
                    "hpo_annotation_count": count,
                    "monarch_label": raw_label,
                },
            )
            evidence_records.append(evidence)

            # ---- Relationship disease -> system ------------------
            relationship = Relationship(
                source_id=disease_node_id,
                target_id=node_id,
                relationship_type=RelationshipType.AFFECTS,
                evidence_ids=[evidence_id],
                evidence_level=EvidenceLevel.ASSOCIATION,
                description=(
                    f"{disease.canonical_name or disease.query} "
                    f"affects {raw_label} "
                    f"(HPO annotation count: {count})."
                ),
                metadata={
                    "monarch_label": raw_label,
                    "hpo_annotation_count": count,
                    "source": SOURCE_NAME,
                },
            )
            relationships.append(relationship)

        # ---- Assemble result -------------------------------------
        return {
            "disease_node_id": disease_node_id,
            "nodes": [asdict(n) for n in nodes],
            "relationships": [asdict(r) for r in relationships],
            "evidence": [asdict(e) for e in evidence_records],
            "sources": [SOURCE_NAME],
            "found": True,
            "metadata": {
                "monarch_disease_id": monarch_disease_id,
                "systems_evaluated": len(systems_all),
                "systems_kept": len(systems_kept),
                "systems_dropped_zero": systems_dropped,
                "annotated_count": annotated_count,
            },
            "reason": None,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _disease_node_id(
        disease: DiseaseIdentity,
    ) -> Optional[str]:
        """
        Deterministic disease node ID.

        Uses the FIRST identifier in the resolver-returned
        list. Phase 02 orders identifiers with the primary
        source first, so this picks the primary ID without
        re-ranking.
        """

        if not disease.identifiers:
            return None

        primary = disease.identifiers[0]
        ident = (primary.identifier or "").strip()

        if not ident:
            return None

        # Sanitize colons inside the ID to keep node IDs
        # visually clean. "MONDO:0004975" -> "MONDO_0004975".
        # Downstream code can recover the original from the
        # node's `identifier` field.
        sanitized = ident.replace(":", "_")

        return f"{DISEASE_NODE_PREFIX}{sanitized}"

    @staticmethod
    def _pick_monarch_disease_id(
        disease: DiseaseIdentity,
    ) -> Optional[str]:
        """
        Pick the best identifier for a Monarch lookup.

        Monarch accepts MONDO, OMIM, and Orphanet IDs.
        Preference order:

            1. First MONDO identifier
            2. First OMIM identifier
            3. First Orphanet identifier

        Returns None if none is available.
        """

        identifiers = disease.identifiers or []

        for prefix in ("MONDO:", "OMIM:", "Orphanet:"):
            for ident in identifiers:
                value = (ident.identifier or "").strip()
                if value.startswith(prefix):
                    return value

        return None

    @staticmethod
    def _display_name(raw_label: str) -> str:
        """
        Convert Monarch's underscored labels to a
        human-readable form.

            "nervous_system"      -> "Nervous system"
            "metabolism_homeostasis" -> "Metabolism homeostasis"
            "head_neck"           -> "Head neck"
        """

        if not raw_label:
            return ""

        words = raw_label.replace("_", " ").split()
        if not words:
            return ""

        # Capitalize first word only; keep the rest lowercased
        # so it reads like an anatomical noun phrase.
        return " ".join(
            [words[0].capitalize()] + [w.lower() for w in words[1:]]
        )

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
