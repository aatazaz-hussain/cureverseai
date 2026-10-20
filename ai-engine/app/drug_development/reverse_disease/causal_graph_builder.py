"""
CureVerseAI — Drug Development
Workflow 02 — Reverse Disease Engineering
Causal Graph Builder.

Merges the four W02 layer outputs (phenotypes, mechanisms,
genes, pathways) into a single in-process graph:

    - one ImpactNodeSet   (deduped by node_id)
    - one RelationshipSet (deduped by source|type|target)
    - one EvidenceCollection (deduped by evidence_id)

And creates the disease node itself, which none of the
layer modules emit. The disease node is the anchor every
layer's edges point back to.

Responsibility boundary
-----------------------

This module is a PURE merger and validator. It does NOT:

    - touch the network
    - call any external source
    - infer new relationships between layers
    - rank or filter
    - rewrite a layer's output

Every layer produces its own nodes, relationships, and
evidence, tagged with the layer name. The graph builder
simply concatenates them, deduplicates, validates
integrity, and returns the merged graph plus the
per-layer dicts for downstream consumption.

Integrity validation
--------------------

Per W01's established pattern (see serialize_impact_result
in drug_development/pipeline.py), integrity issues are
RECORDED but do NOT raise. The frontend and service layer
see what went wrong and can report it.

The integrity report contains:

    - dangling_relationship_sources:  relationship source_ids
                                       with no matching node
    - dangling_relationship_targets:  relationship target_ids
                                       with no matching node
    - relationships_with_missing_evidence: relationship
                                       evidence_ids with no
                                       matching evidence record
    - nodes_with_missing_evidence:    same, for nodes
    - duplicate_node_ids:             node_ids appearing
                                       more than once after dedup
                                       (should be empty — dedup
                                       removes duplicates by design;
                                       if a duplicate slips through
                                       it indicates a bug upstream)
    - duplicate_relationship_keys:    same, for relationships
    - duplicate_evidence_ids:         same, for evidence

A duplicate appearing in this report is a real bug, not a
warning. Dedup runs first; anything reported is what
survived dedup.

Layer merge order
-----------------

Layers are merged in the order given by the caller's `layers`
dict insertion order. Downstream code should supply them in
the canonical W02 order:

    phenotypes, mechanisms, genes, pathways

This preserves the "investigation direction" the spec
describes (phenotype -> mechanism -> gene -> pathway) in
node and edge ordering. The frontend renders in that order.

Output shape
------------

    {
        "disease_node": <ImpactNode as dict>,
        "graph": {
            "nodes":    [<all nodes, deduped, disease first>],
            "edges":    [<all relationships, deduped>],
            "evidence": [<all evidence, deduped>],
        },
        "integrity": {
            "ok": <bool>,
            "node_count": <int>,
            "relationship_count": <int>,
            "evidence_count": <int>,
            "dangling_relationship_sources": [...],
            "dangling_relationship_targets": [...],
            "relationships_with_missing_evidence": [...],
            "nodes_with_missing_evidence": [...],
            "duplicate_node_ids": [...],
            "duplicate_relationship_keys": [...],
            "duplicate_evidence_ids": [...],
            "layers_merged": [<str>, ...],
        },
        "layers": {
            "phenotypes": <layer dict>,
            "mechanisms": <layer dict>,
            "genes":      <layer dict>,
            "pathways":   <layer dict>,
        },
    }
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, List, Optional, Tuple

from app.drug_development.schemas.disease import (
    DiseaseIdentity,
)
from app.drug_development.schemas.evidence import (
    EvidenceCollection,
    ImpactEvidence,
)
from app.drug_development.schemas.impact import (
    ImpactNode,
    ImpactNodeSet,
    NodeType,
)
from app.drug_development.schemas.relationships import (
    Relationship,
    RelationshipSet,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


DISEASE_NODE_PREFIX = "disease:"

#: Canonical layer order used by downstream code. The graph
#: builder does not enforce this on the caller, but the
#: recommended order matches the W02 investigation direction.
CANONICAL_LAYER_ORDER: Tuple[str, ...] = (
    "phenotypes",
    "mechanisms",
    "genes",
    "pathways",
)


# ---------------------------------------------------------------------------
# Graph builder
# ---------------------------------------------------------------------------


class CausalGraphBuilder:
    """
    Merges W02 layer outputs into one graph and validates
    its integrity.
    """

    def __init__(self) -> None:
        pass

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build(
        self,
        disease: DiseaseIdentity,
        layers: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Merge layer outputs.

        `layers` maps a layer name (e.g. "phenotypes") to the
        dict returned by the corresponding layer module. Order
        is preserved from `layers` insertion order.
        """

        disease_node = self._build_disease_node(disease)

        nodes = ImpactNodeSet()
        relationships = RelationshipSet()
        evidence = EvidenceCollection()

        # The disease node goes first so it renders first.
        if disease_node is not None:
            nodes.add(disease_node)

        # Track which layer each entity came from, for metadata.
        layer_entity_counts: Dict[str, Dict[str, int]] = {}

        for layer_name, layer_result in layers.items():
            counts = self._merge_layer(
                layer_name=layer_name,
                layer_result=layer_result,
                nodes=nodes,
                relationships=relationships,
                evidence=evidence,
            )
            layer_entity_counts[layer_name] = counts

        # Build indexes on the relationship set for fast lookup
        # downstream (by source, by target, by type).
        relationships.build_indexes()

        integrity = self._check_integrity(
            nodes=nodes,
            relationships=relationships,
            evidence=evidence,
            layers_merged=list(layers.keys()),
            layer_entity_counts=layer_entity_counts,
        )

        return {
            "disease_node": (
                asdict(disease_node)
                if disease_node is not None
                else None
            ),
            "graph": {
                "nodes": [asdict(n) for n in nodes.nodes],
                "edges": [
                    asdict(r)
                    for r in relationships.relationships
                ],
                "evidence": [
                    asdict(e) for e in evidence.records
                ],
            },
            "integrity": integrity,
            "layers": {
                name: dict(result)
                for name, result in layers.items()
            },
        }

    # ------------------------------------------------------------------
    # Disease node
    # ------------------------------------------------------------------

    @staticmethod
    def _build_disease_node(
        disease: DiseaseIdentity,
    ) -> Optional[ImpactNode]:
        """
        Create the anchor disease node.

        The node_id mirrors the layer modules' convention:
        colons in the primary identifier are replaced with
        underscores.

        Returns None if the disease has no identifiers, in
        which case every layer would have produced zero
        relationships anyway (they all use the same
        convention and check).
        """

        if not disease.identifiers:
            return None

        primary = disease.identifiers[0]
        ident = (primary.identifier or "").strip()

        if not ident:
            return None

        sanitized = ident.replace(":", "_")
        node_id = f"{DISEASE_NODE_PREFIX}{sanitized}"

        return ImpactNode(
            node_id=node_id,
            node_type=NodeType.DISEASE,
            name=disease.canonical_name or disease.query,
            identifier=ident,
            description=disease.description,
            evidence_ids=[],
            metadata={
                "canonical_name": disease.canonical_name,
                "query": disease.query,
                "synonyms": list(disease.synonyms or []),
                "sources": list(disease.sources or []),
                "resolution_status": disease.resolution_status,
                "category": disease.category,
            },
        )

    # ------------------------------------------------------------------
    # Layer merge
    # ------------------------------------------------------------------

    @staticmethod
    def _merge_layer(
        layer_name: str,
        layer_result: Dict[str, Any],
        nodes: ImpactNodeSet,
        relationships: RelationshipSet,
        evidence: EvidenceCollection,
    ) -> Dict[str, int]:
        """
        Merge one layer into the shared containers.

        Dedup policy:

            nodes:         by node_id
            relationships: by (source_id, relationship_type, target_id)
            evidence:      by evidence_id

        Dedup is silent and intentional: two layers may
        legitimately emit the same node (e.g. a gene node
        from the gene layer and the same gene appearing via
        the pathway layer's gene reference). The first
        emission wins.

        Returns per-layer counts for metadata.
        """

        counts = {
            "nodes_in": 0,
            "relationships_in": 0,
            "evidence_in": 0,
            "nodes_deduped": 0,
            "relationships_deduped": 0,
            "evidence_deduped": 0,
        }

        if not isinstance(layer_result, dict):
            return counts

        # ---- Evidence first (relationships reference it) ----
        for raw in layer_result.get("evidence") or []:
            counts["evidence_in"] += 1
            ev = CausalGraphBuilder._dict_to_evidence(raw)
            if ev is None:
                continue
            if ev.evidence_id in evidence.by_id:
                counts["evidence_deduped"] += 1
                continue
            evidence.add(ev)

        # ---- Nodes ---------------------------------------
        for raw in layer_result.get("nodes") or []:
            counts["nodes_in"] += 1
            node = CausalGraphBuilder._dict_to_node(raw)
            if node is None:
                continue
            if node.node_id in nodes.by_id:
                counts["nodes_deduped"] += 1
                continue
            nodes.add(node)

        # ---- Relationships -------------------------------
        for raw in layer_result.get("relationships") or []:
            counts["relationships_in"] += 1
            rel = CausalGraphBuilder._dict_to_relationship(raw)
            if rel is None:
                continue

            key = CausalGraphBuilder._relationship_key(rel)
            if CausalGraphBuilder._relationship_exists(
                relationships, rel
            ):
                counts["relationships_deduped"] += 1
                continue

            relationships.add(rel)

        return counts

    # ------------------------------------------------------------------
    # Dict → dataclass helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _dict_to_node(
        raw: Any,
    ) -> Optional[ImpactNode]:
        if not isinstance(raw, dict):
            return None

        node_id = raw.get("node_id")
        node_type = raw.get("node_type")
        name = raw.get("name")

        if not node_id or not node_type or not name:
            return None

        return ImpactNode(
            node_id=str(node_id),
            node_type=str(node_type),
            name=str(name),
            identifier=raw.get("identifier"),
            description=raw.get("description"),
            evidence_ids=list(raw.get("evidence_ids") or []),
            metadata=dict(raw.get("metadata") or {}),
        )

    @staticmethod
    def _dict_to_relationship(
        raw: Any,
    ) -> Optional[Relationship]:
        if not isinstance(raw, dict):
            return None

        source_id = raw.get("source_id")
        target_id = raw.get("target_id")
        relationship_type = raw.get("relationship_type")

        if not source_id or not target_id or not relationship_type:
            return None

        return Relationship(
            source_id=str(source_id),
            target_id=str(target_id),
            relationship_type=str(relationship_type),
            evidence_ids=list(raw.get("evidence_ids") or []),
            evidence_level=raw.get("evidence_level"),
            support_class=raw.get("support_class"),
            description=raw.get("description"),
            metadata=dict(raw.get("metadata") or {}),
        )

    @staticmethod
    def _dict_to_evidence(
        raw: Any,
    ) -> Optional[ImpactEvidence]:
        if not isinstance(raw, dict):
            return None

        evidence_id = raw.get("evidence_id")
        source = raw.get("source")
        relationship_description = raw.get(
            "relationship_description"
        )

        if not evidence_id or not source:
            return None

        # Reconstruct the reference from its serialized form
        # if present.
        from app.drug_development.schemas.evidence import (
            EvidenceReference,
        )

        reference_raw = raw.get("reference")
        reference: Optional[EvidenceReference] = None

        if isinstance(reference_raw, dict):
            reference = EvidenceReference(
                source=reference_raw.get("source") or source,
                source_id=reference_raw.get("source_id"),
                source_type=reference_raw.get("source_type"),
                url=reference_raw.get("url"),
                metadata=dict(
                    reference_raw.get("metadata") or {}
                ),
            )

        return ImpactEvidence(
            evidence_id=str(evidence_id),
            source=str(source),
            relationship_description=(
                str(relationship_description)
                if relationship_description
                else ""
            ),
            evidence_level=raw.get(
                "evidence_level", "insufficient"
            ),
            reference=reference,
            identifiers=dict(raw.get("identifiers") or {}),
            metadata=dict(raw.get("metadata") or {}),
        )

    # ------------------------------------------------------------------
    # Relationship key helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _relationship_key(
        rel: Relationship,
    ) -> str:
        return (
            f"{rel.source_id}|{rel.relationship_type}|"
            f"{rel.target_id}"
        )

    @staticmethod
    def _relationship_exists(
        relationships: RelationshipSet,
        rel: Relationship,
    ) -> bool:
        """
        Check whether an equivalent relationship already
        exists. Uses the by_source index for a fast scan.
        """

        indexes = relationships.by_source.get(rel.source_id)

        # If indexes were never built, fall back to a linear
        # scan. The graph builder always rebuilds indexes
        # before returning, but callers may pass partial sets.
        if indexes is None:
            for existing in relationships.relationships:
                if (
                    existing.source_id == rel.source_id
                    and existing.target_id == rel.target_id
                    and existing.relationship_type
                    == rel.relationship_type
                ):
                    return True
            return False

        for idx in indexes:
            existing = relationships.relationships[idx]
            if (
                existing.target_id == rel.target_id
                and existing.relationship_type
                == rel.relationship_type
            ):
                return True

        return False

    # ------------------------------------------------------------------
    # Integrity
    # ------------------------------------------------------------------

    @staticmethod
    def _check_integrity(
        nodes: ImpactNodeSet,
        relationships: RelationshipSet,
        evidence: EvidenceCollection,
        layers_merged: List[str],
        layer_entity_counts: Dict[str, Dict[str, int]],
    ) -> Dict[str, Any]:
        node_ids = set(nodes.by_id.keys())
        evidence_ids = set(evidence.by_id.keys())

        dangling_sources: List[str] = []
        dangling_targets: List[str] = []
        rels_missing_evidence: List[str] = []

        for rel in relationships.relationships:
            if rel.source_id not in node_ids:
                key = (
                    f"{rel.source_id}|"
                    f"{rel.relationship_type}|"
                    f"{rel.target_id}"
                )
                if key not in dangling_sources:
                    dangling_sources.append(key)

            if rel.target_id not in node_ids:
                key = (
                    f"{rel.source_id}|"
                    f"{rel.relationship_type}|"
                    f"{rel.target_id}"
                )
                if key not in dangling_targets:
                    dangling_targets.append(key)

            for ev_id in rel.evidence_ids or []:
                if ev_id not in evidence_ids:
                    key = (
                        f"{rel.source_id}|"
                        f"{rel.relationship_type}|"
                        f"{rel.target_id}->{ev_id}"
                    )
                    if key not in rels_missing_evidence:
                        rels_missing_evidence.append(key)

        nodes_missing_evidence: List[str] = []
        for node in nodes.nodes:
            for ev_id in node.evidence_ids or []:
                if ev_id not in evidence_ids:
                    key = f"{node.node_id}->{ev_id}"
                    if key not in nodes_missing_evidence:
                        nodes_missing_evidence.append(key)

        # Duplicates surviving dedup should be zero. If any
        # are reported, the caller sees an upstream bug.
        duplicate_node_ids = CausalGraphBuilder._find_duplicates(
            [n.node_id for n in nodes.nodes]
        )
        duplicate_relationship_keys = (
            CausalGraphBuilder._find_duplicates(
                [
                    CausalGraphBuilder._relationship_key(r)
                    for r in relationships.relationships
                ]
            )
        )
        duplicate_evidence_ids = (
            CausalGraphBuilder._find_duplicates(
                [e.evidence_id for e in evidence.records]
            )
        )

        ok = (
            not dangling_sources
            and not dangling_targets
            and not rels_missing_evidence
            and not nodes_missing_evidence
            and not duplicate_node_ids
            and not duplicate_relationship_keys
            and not duplicate_evidence_ids
        )

        return {
            "ok": ok,
            "node_count": len(nodes.nodes),
            "relationship_count": len(
                relationships.relationships
            ),
            "evidence_count": len(evidence.records),
            "dangling_relationship_sources": dangling_sources,
            "dangling_relationship_targets": dangling_targets,
            "relationships_with_missing_evidence": (
                rels_missing_evidence
            ),
            "nodes_with_missing_evidence": (
                nodes_missing_evidence
            ),
            "duplicate_node_ids": duplicate_node_ids,
            "duplicate_relationship_keys": (
                duplicate_relationship_keys
            ),
            "duplicate_evidence_ids": duplicate_evidence_ids,
            "layers_merged": list(layers_merged),
            "layer_entity_counts": dict(layer_entity_counts),
        }

    @staticmethod
    def _find_duplicates(
        values: List[str],
    ) -> List[str]:
        seen: set[str] = set()
        dupes: List[str] = []

        for value in values:
            if value in seen:
                if value not in dupes:
                    dupes.append(value)
            else:
                seen.add(value)

        return dupes
