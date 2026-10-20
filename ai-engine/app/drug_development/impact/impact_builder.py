"""
CureVerseAI — Drug Development
Impact Builder.

Assembles the per-layer outputs of the Disease ->
Biological Impact workflow into a single
BiologicalImpactResult.

Input layers (in spec order)
----------------------------

    disease node (emitted here)
    systems      (Phase 03)
    tissues      (Phase 03)
    cells        (Phase 04)
    molecular    (Phase 05)
    pathways     (Phase 06)
    reasoning    (Phase 07)

Output
------

    BiologicalImpactResult  (Phase 01 schema)

Design decisions (locked)
-------------------------

IB-A(a) The disease node is emitted here, from the
        DiseaseIdentity, with node_type = NodeType.DISEASE.

IB-B(b) Graph integrity is validated and anomalies are
        recorded in metadata.integrity. The builder does
        not raise on broken references; it records them.

IB-C(c) Top-level metadata carries a summary and the
        per-layer metadata under `layers`.

IB-D(a) BiologicalImpactResult.query is the raw user
        query, as returned by the resolver.

IB-E(a) If any layer returned found=False, the result
        resolution_status becomes "partial" and
        failure_reason names the failing layer(s).

IB-F(a) Merge order: disease, systems, tissues, cells,
        molecular, pathways.

IB-G(a) Nodes deduplicated by node_id; relationships by
        (source_id, target_id, relationship_type);
        evidence by evidence_id. First occurrence preserved.

IB-H(b) This file lives at
        app/drug_development/impact/impact_builder.py.

What this module does NOT do
----------------------------

- It does not fetch anything from a remote source.
- It does not modify any per-layer result.
- It does not run evidence reasoning (Phase 07 does that).
- It does not call ChEMBL, Reactome, Ensembl, etc.

Conventions
-----------

- Dataclasses from Phase 01 schemas are used directly.
- Layer inputs are dicts with `nodes`, `relationships`,
  `evidence`, `found`, `metadata` keys — exactly what
  each mapper returns.
- No new external libraries.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from app.drug_development.schemas.disease import (
    DiseaseIdentity,
)
from app.drug_development.schemas.evidence import (
    EvidenceCollection,
    EvidenceReference,
    ImpactEvidence,
)
from app.drug_development.schemas.impact import (
    BiologicalImpactResult,
    ImpactNode,
    ImpactNodeSet,
    ImpactReasoning,
    NodeType,
)
from app.drug_development.schemas.relationships import (
    Relationship,
    RelationshipSet,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Layer keys in the exact order required by the spec.
LAYER_ORDER: Tuple[str, ...] = (
    "systems",
    "tissues",
    "cells",
    "molecular",
    "pathways",
)

#: Fixed schema version tag recorded in metadata.
SCHEMA_VERSION = "1.0"


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------


class ImpactBuilder:
    """
    Assembles BiologicalImpactResult from per-layer outputs.
    """

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build(
        self,
        disease: DiseaseIdentity,
        raw_query: str,
        resolution_status: str,
        systems_result: Optional[Dict[str, Any]] = None,
        tissues_result: Optional[Dict[str, Any]] = None,
        cells_result: Optional[Dict[str, Any]] = None,
        molecular_result: Optional[Dict[str, Any]] = None,
        pathways_result: Optional[Dict[str, Any]] = None,
        reasoning: Optional[Dict[str, Any]] = None,
    ) -> BiologicalImpactResult:
        """
        Build the merged result.

        Every layer input is optional; missing layers are
        recorded as not-run in the integrity report.
        """

        layer_inputs: Dict[str, Optional[Dict[str, Any]]] = {
            "systems": systems_result,
            "tissues": tissues_result,
            "cells": cells_result,
            "molecular": molecular_result,
            "pathways": pathways_result,
        }

        # ---- 1) Assemblers -------------------------------------
        node_set = ImpactNodeSet()
        relationship_set = RelationshipSet()
        evidence_collection = EvidenceCollection()

        node_duplicates: List[str] = []
        rel_duplicates: List[str] = []
        ev_duplicates: List[str] = []

        seen_node_ids: set = set()
        seen_rel_keys: set = set()
        seen_ev_ids: set = set()

        # ---- 1a) Disease node (IB-A) ---------------------------
        disease_node = self._make_disease_node(disease)

        if disease_node is not None:
            node_set.add(disease_node)
            seen_node_ids.add(disease_node.node_id)

        # ---- 1b) Layers in spec order (IB-F) -------------------
        for layer_name in LAYER_ORDER:
            layer = layer_inputs.get(layer_name)

            if not layer:
                continue

            if not layer.get("found"):
                continue

            for raw_node in layer.get("nodes") or []:
                node = self._deserialize_node(raw_node)
                if node is None:
                    continue
                if node.node_id in seen_node_ids:
                    node_duplicates.append(node.node_id)
                    continue
                seen_node_ids.add(node.node_id)
                node_set.add(node)

            for raw_rel in layer.get("relationships") or []:
                rel = self._deserialize_relationship(raw_rel)
                if rel is None:
                    continue
                key = (
                    rel.source_id,
                    rel.target_id,
                    rel.relationship_type,
                )
                if key in seen_rel_keys:
                    rel_duplicates.append(
                        f"{rel.source_id}->{rel.target_id}"
                        f":{rel.relationship_type}"
                    )
                    continue
                seen_rel_keys.add(key)
                relationship_set.add(rel)

            for raw_ev in layer.get("evidence") or []:
                ev = self._deserialize_evidence(raw_ev)
                if ev is None:
                    continue
                if ev.evidence_id in seen_ev_ids:
                    ev_duplicates.append(ev.evidence_id)
                    continue
                seen_ev_ids.add(ev.evidence_id)
                evidence_collection.add(ev)

        # ---- 2) Build indexes ---------------------------------
        relationship_set.build_indexes()

        # ---- 3) Integrity check (IB-B) ------------------------
        integrity = self._validate_integrity(
            node_set=node_set,
            relationship_set=relationship_set,
            evidence_collection=evidence_collection,
            layer_inputs=layer_inputs,
            node_duplicates=node_duplicates,
            rel_duplicates=rel_duplicates,
            ev_duplicates=ev_duplicates,
        )

        # ---- 4) Reasoning -------------------------------------
        impact_reasoning = self._deserialize_reasoning(reasoning)

        # ---- 5) Resolution status (IB-E) ----------------------
        final_status, failure_reason = self._resolve_status(
            resolution_status=resolution_status,
            layer_inputs=layer_inputs,
        )

        # ---- 6) Metadata (IB-C) -------------------------------
        metadata = self._build_metadata(
            layer_inputs=layer_inputs,
            integrity=integrity,
            final_status=final_status,
        )

        # ---- 7) Assemble --------------------------------------
        return BiologicalImpactResult(
            query=raw_query,                # IB-D
            disease=disease,
            resolution_status=final_status,
            nodes=node_set,
            relationships=relationship_set,
            evidence=evidence_collection,
            reasoning=impact_reasoning,
            failure_reason=failure_reason,
            metadata=metadata,
        )

    # ------------------------------------------------------------------
    # Disease node (IB-A)
    # ------------------------------------------------------------------

    @staticmethod
    def _make_disease_node(
        disease: DiseaseIdentity,
    ) -> Optional[ImpactNode]:
        """
        Create the root disease node.

        Its node_id must match the ID the layers used in
        their relationships: derived from the resolver's
        first identifier, sanitized (colons -> underscores),
        prefixed with "disease:".
        """

        if not disease.identifiers:
            return None

        primary = disease.identifiers[0]
        ident = (primary.identifier or "").strip()

        if not ident:
            return None

        sanitized = ident.replace(":", "_")
        node_id = f"disease:{sanitized}"

        display = (
            disease.canonical_name
            or disease.query
            or ident
        )

        return ImpactNode(
            node_id=node_id,
            node_type=NodeType.DISEASE,
            name=display,
            identifier=ident,
            description=disease.description,
            evidence_ids=[],
            metadata={
                "canonical_name": disease.canonical_name,
                "query": disease.query,
                "identifiers": [
                    {
                        "source": i.source,
                        "identifier": i.identifier,
                    }
                    for i in disease.identifiers
                ],
                "sources": list(disease.sources),
                "category": disease.category,
                "is_root": True,
            },
        )

    # ------------------------------------------------------------------
    # Deserializers
    # ------------------------------------------------------------------

    @staticmethod
    def _deserialize_node(
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
            node_id=node_id,
            node_type=node_type,
            name=name,
            identifier=raw.get("identifier"),
            description=raw.get("description"),
            evidence_ids=list(raw.get("evidence_ids") or []),
            metadata=dict(raw.get("metadata") or {}),
        )

    @staticmethod
    def _deserialize_relationship(
        raw: Any,
    ) -> Optional[Relationship]:
        if not isinstance(raw, dict):
            return None

        source_id = raw.get("source_id")
        target_id = raw.get("target_id")
        rel_type = raw.get("relationship_type")

        if not source_id or not target_id or not rel_type:
            return None

        return Relationship(
            source_id=source_id,
            target_id=target_id,
            relationship_type=rel_type,
            evidence_ids=list(raw.get("evidence_ids") or []),
            evidence_level=raw.get("evidence_level"),
            description=raw.get("description"),
            metadata=dict(raw.get("metadata") or {}),
        )

    @staticmethod
    def _deserialize_evidence(
        raw: Any,
    ) -> Optional[ImpactEvidence]:
        if not isinstance(raw, dict):
            return None

        evidence_id = raw.get("evidence_id")
        source = raw.get("source")
        description = raw.get("relationship_description")

        if not evidence_id or not source or description is None:
            return None

        reference = None
        raw_ref = raw.get("reference")
        if isinstance(raw_ref, dict):
            reference = EvidenceReference(
                source=raw_ref.get("source", ""),
                source_id=raw_ref.get("source_id"),
                source_type=raw_ref.get("source_type"),
                url=raw_ref.get("url"),
                metadata=dict(raw_ref.get("metadata") or {}),
            )

        return ImpactEvidence(
            evidence_id=evidence_id,
            source=source,
            relationship_description=description,
            evidence_level=raw.get(
                "evidence_level", "insufficient"
            ),
            reference=reference,
            identifiers=dict(raw.get("identifiers") or {}),
            metadata=dict(raw.get("metadata") or {}),
        )

    @staticmethod
    def _deserialize_reasoning(
        raw: Optional[Dict[str, Any]],
    ) -> ImpactReasoning:
        if not isinstance(raw, dict):
            return ImpactReasoning()

        return ImpactReasoning(
            summary=raw.get("summary"),
            findings=list(raw.get("findings") or []),
            limitations=list(raw.get("limitations") or []),
            sources=dict(raw.get("sources") or {}),
            metadata=dict(raw.get("metadata") or {}),
        )

    # ------------------------------------------------------------------
    # Integrity (IB-B)
    # ------------------------------------------------------------------

    @staticmethod
    def _validate_integrity(
        node_set: ImpactNodeSet,
        relationship_set: RelationshipSet,
        evidence_collection: EvidenceCollection,
        layer_inputs: Dict[str, Optional[Dict[str, Any]]],
        node_duplicates: List[str],
        rel_duplicates: List[str],
        ev_duplicates: List[str],
    ) -> Dict[str, Any]:
        known_node_ids = set(node_set.by_id.keys())
        known_ev_ids = set(evidence_collection.by_id.keys())

        dangling_relationship_sources: List[str] = []
        dangling_relationship_targets: List[str] = []
        relationships_with_missing_evidence: List[str] = []
        nodes_with_missing_evidence: List[str] = []

        for rel in relationship_set.relationships:
            if rel.source_id not in known_node_ids:
                dangling_relationship_sources.append(
                    f"{rel.source_id}->{rel.target_id}"
                    f":{rel.relationship_type}"
                )
            if rel.target_id not in known_node_ids:
                dangling_relationship_targets.append(
                    f"{rel.source_id}->{rel.target_id}"
                    f":{rel.relationship_type}"
                )
            for ev_id in rel.evidence_ids:
                if ev_id not in known_ev_ids:
                    relationships_with_missing_evidence.append(
                        f"{rel.source_id}->{rel.target_id}"
                        f":{rel.relationship_type}"
                        f" (missing {ev_id})"
                    )

        for node in node_set.nodes:
            for ev_id in node.evidence_ids:
                if ev_id not in known_ev_ids:
                    nodes_with_missing_evidence.append(
                        f"{node.node_id} (missing {ev_id})"
                    )

        layers_run: List[str] = []
        layers_missing: List[str] = []
        for name in LAYER_ORDER:
            layer = layer_inputs.get(name)
            if layer and layer.get("found"):
                layers_run.append(name)
            elif layer is None:
                layers_missing.append(name)

        return {
            "ok": (
                not dangling_relationship_sources
                and not dangling_relationship_targets
                and not relationships_with_missing_evidence
            ),
            "node_count": len(node_set.nodes),
            "relationship_count": len(relationship_set.relationships),
            "evidence_count": len(evidence_collection.records),
            "dangling_relationship_sources": (
                dangling_relationship_sources
            ),
            "dangling_relationship_targets": (
                dangling_relationship_targets
            ),
            "relationships_with_missing_evidence": (
                relationships_with_missing_evidence
            ),
            "nodes_with_missing_evidence": (
                nodes_with_missing_evidence
            ),
            "duplicate_node_ids": node_duplicates,
            "duplicate_relationship_keys": rel_duplicates,
            "duplicate_evidence_ids": ev_duplicates,
            "layers_run": layers_run,
            "layers_missing": layers_missing,
        }

    # ------------------------------------------------------------------
    # Resolution status (IB-E)
    # ------------------------------------------------------------------

    @staticmethod
    def _resolve_status(
        resolution_status: str,
        layer_inputs: Dict[str, Optional[Dict[str, Any]]],
    ) -> Tuple[str, Optional[str]]:
        failed_layers: List[str] = []

        for name in LAYER_ORDER:
            layer = layer_inputs.get(name)
            if layer is None:
                continue
            if not layer.get("found"):
                failed_layers.append(name)

        if not failed_layers:
            return resolution_status, None

        reason = (
            "Partial result: layers without data - "
            + ", ".join(failed_layers)
        )

        if resolution_status == "resolved":
            return "partial", reason

        return resolution_status, reason

    # ------------------------------------------------------------------
    # Metadata (IB-C)
    # ------------------------------------------------------------------

    @staticmethod
    def _build_metadata(
        layer_inputs: Dict[str, Optional[Dict[str, Any]]],
        integrity: Dict[str, Any],
        final_status: str,
    ) -> Dict[str, Any]:
        summary = {
            "node_count": integrity["node_count"],
            "relationship_count": integrity["relationship_count"],
            "evidence_count": integrity["evidence_count"],
            "layers_run": integrity["layers_run"],
            "layers_missing": integrity["layers_missing"],
            "resolution_status": final_status,
            "schema_version": SCHEMA_VERSION,
        }

        layers_meta: Dict[str, Any] = {}
        for name in LAYER_ORDER:
            layer = layer_inputs.get(name)

            if layer is None:
                layers_meta[name] = None
                continue

            layers_meta[name] = {
                "found": bool(layer.get("found")),
                "sources": list(layer.get("sources") or []),
                "metadata": dict(layer.get("metadata") or {}),
                "reason": layer.get("reason"),
            }

        return {
            "summary": summary,
            "integrity": integrity,
            "layers": layers_meta,
        }


# ---------------------------------------------------------------------------
# Convenience
# ---------------------------------------------------------------------------


def build_impact_result(
    disease: DiseaseIdentity,
    raw_query: str,
    resolution_status: str,
    systems_result: Optional[Dict[str, Any]] = None,
    tissues_result: Optional[Dict[str, Any]] = None,
    cells_result: Optional[Dict[str, Any]] = None,
    molecular_result: Optional[Dict[str, Any]] = None,
    pathways_result: Optional[Dict[str, Any]] = None,
    reasoning: Optional[Dict[str, Any]] = None,
) -> BiologicalImpactResult:
    """
    One-shot builder for the common case.
    """
    return ImpactBuilder().build(
        disease=disease,
        raw_query=raw_query,
        resolution_status=resolution_status,
        systems_result=systems_result,
        tissues_result=tissues_result,
        cells_result=cells_result,
        molecular_result=molecular_result,
        pathways_result=pathways_result,
        reasoning=reasoning,
    )
