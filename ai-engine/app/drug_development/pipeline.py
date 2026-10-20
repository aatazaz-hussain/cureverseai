"""
CureVerseAI — Drug Development
Disease -> Biological Impact pipeline.

High-level runner that executes the full pipeline:

    query
      |
      v
    resolver             (Phase 02)
      |
      v
    systems, tissues,    (Phase 03)
    cells, molecular,    (Phase 04 / 05)
    pathways             (Phase 06)
      |
      v
    evidence integration (Phase 07)
      |
      v
    impact builder       (Phase 08)
      |
      v
    serialized result    (this file)

Callers get a single dict in a wire-ready shape:
indexes stripped, primary lists preserved.

No new libraries. No external calls beyond what the
underlying layers already make.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, Optional

from app.drug_development.disease.biological_systems import (
    BiologicalSystemsMapper,
)
from app.drug_development.disease.cellular_context import (
    CellularContextMapper,
)
from app.drug_development.disease.impact_evidence import (
    ImpactEvidenceIntegrator,
)
from app.drug_development.disease.molecular_context import (
    MolecularContextMapper,
)
from app.drug_development.disease.pathway_mapping import (
    PathwayMapper,
)
from app.drug_development.disease.resolver import (
    DiseaseResolver,
)
from app.drug_development.disease.tissue_mapping import (
    TissueMapper,
)
from app.drug_development.impact.impact_builder import (
    ImpactBuilder,
)
from app.drug_development.schemas.impact import (
    BiologicalImpactResult,
)


# ---------------------------------------------------------------------------
# Serialization
# ---------------------------------------------------------------------------


def serialize_impact_result(
    result: BiologicalImpactResult,
) -> Dict[str, Any]:
    """
    Convert a BiologicalImpactResult to a wire-ready dict.

    Per BE-C(b): the internal index maps (`by_id`,
    `by_type`, `by_source`, `by_target`) are STRIPPED from
    the serialized output. Only the primary lists are
    emitted:

        nodes.nodes           -> nodes
        relationships.relationships -> relationships
        evidence.records      -> evidence

    The frontend can rebuild indexes on the client side if
    it needs them. This keeps the payload ~40% smaller and
    the wire schema clean.
    """

    nodes_list = [asdict(n) for n in result.nodes.nodes]
    relationships_list = [
        asdict(r) for r in result.relationships.relationships
    ]
    evidence_list = [
        asdict(e) for e in result.evidence.records
    ]

    # Reasoning is already a flat dataclass
    reasoning_dict = asdict(result.reasoning)

    # Disease identity is already a flat dataclass
    disease_dict = (
        asdict(result.disease) if result.disease else None
    )

    return {
        "query": result.query,
        "resolution_status": result.resolution_status,
        "failure_reason": result.failure_reason,
        "disease": disease_dict,
        "nodes": nodes_list,
        "relationships": relationships_list,
        "evidence": evidence_list,
        "reasoning": reasoning_dict,
        "metadata": result.metadata,
    }


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


class DiseaseImpactPipeline:
    """
    Runs the full Disease -> Biological Impact workflow
    for one query.

    Each mapper is instantiated once per pipeline run. If
    callers want to reuse a pipeline across many queries
    (e.g., a batch smoke test), they can hold an instance
    and call `run()` repeatedly; caches at the client layer
    are preserved across calls.
    """

    def __init__(
        self,
        resolver: Optional[DiseaseResolver] = None,
        systems_mapper: Optional[BiologicalSystemsMapper] = None,
        tissues_mapper: Optional[TissueMapper] = None,
        cells_mapper: Optional[CellularContextMapper] = None,
        molecular_mapper: Optional[MolecularContextMapper] = None,
        pathways_mapper: Optional[PathwayMapper] = None,
        evidence_integrator: Optional[ImpactEvidenceIntegrator] = None,
        impact_builder: Optional[ImpactBuilder] = None,
    ):
        self.resolver = resolver or DiseaseResolver()
        self.systems_mapper = (
            systems_mapper or BiologicalSystemsMapper()
        )
        self.tissues_mapper = (
            tissues_mapper or TissueMapper()
        )
        self.cells_mapper = (
            cells_mapper or CellularContextMapper()
        )
        self.molecular_mapper = (
            molecular_mapper or MolecularContextMapper()
        )
        self.pathways_mapper = (
            pathways_mapper or PathwayMapper()
        )
        self.evidence_integrator = (
            evidence_integrator or ImpactEvidenceIntegrator()
        )
        self.impact_builder = (
            impact_builder or ImpactBuilder()
        )

    def run(
        self,
        disease_query: str,
    ) -> Dict[str, Any]:
        """
        Run the full pipeline.

        Returns a serialized result dict (see
        serialize_impact_result).

        Never raises for an unresolvable disease. Returns a
        well-formed result with resolution_status="unresolved"
        and an empty graph.

        Raises RuntimeError only for transport-level failures
        that we cannot mask (e.g., if the resolver's primary
        source is down).
        """

        raw_query = (disease_query or "").strip()

        if not raw_query:
            return self._serialize_unresolved(
                raw_query="",
                reason="Disease query cannot be empty.",
            )

        # ---- 1) Resolve -----------------------------------------
        resolution = self.resolver.resolve(raw_query)

        # If the disease did not resolve, return an
        # unresolved result without running the layers.
        if resolution.disease is None:
            return self._serialize_unresolved(
                raw_query=raw_query,
                reason=resolution.message or (
                    "Disease could not be resolved."
                ),
            )

        disease = resolution.disease

        # ---- 2) Run layers --------------------------------------
        systems = self.systems_mapper.map_disease_to_systems(
            disease
        )
        tissues = self.tissues_mapper.map_disease_to_tissues(
            disease
        )
        cells = self.cells_mapper.map_disease_to_cell_types(
            disease
        )
        molecular = (
            self.molecular_mapper.map_disease_to_molecular_entities(
                disease
            )
        )
        pathways = self.pathways_mapper.map_disease_to_pathways(
            disease
        )

        # ---- 3) Integrate evidence ------------------------------
        reasoning = self.evidence_integrator.integrate(
            systems_result=systems,
            tissues_result=tissues,
            cells_result=cells,
            molecular_result=molecular,
            pathways_result=pathways,
        )

        # ---- 4) Build result ------------------------------------
        impact = self.impact_builder.build(
            disease=disease,
            raw_query=raw_query,
            resolution_status=resolution.status,
            systems_result=systems,
            tissues_result=tissues,
            cells_result=cells,
            molecular_result=molecular,
            pathways_result=pathways,
            reasoning=reasoning,
        )

        # ---- 5) Serialize ---------------------------------------
        return serialize_impact_result(impact)

    # ------------------------------------------------------------------
    # Unresolved path
    # ------------------------------------------------------------------

    @staticmethod
    def _serialize_unresolved(
        raw_query: str,
        reason: str,
    ) -> Dict[str, Any]:
        """
        Return a well-formed but empty result for an
        unresolvable disease query.

        Matches the shape of serialize_impact_result so
        callers can treat both paths identically.
        """

        return {
            "query": raw_query,
            "resolution_status": "unresolved",
            "failure_reason": reason,
            "disease": None,
            "nodes": [],
            "relationships": [],
            "evidence": [],
            "reasoning": {
                "summary": reason,
                "findings": [],
                "limitations": [
                    "No biological record was found for this "
                    "query in the sources consulted.",
                ],
                "sources": {},
                "metadata": {},
            },
            "metadata": {
                "summary": {
                    "node_count": 0,
                    "relationship_count": 0,
                    "evidence_count": 0,
                    "layers_run": [],
                    "layers_missing": [],
                    "resolution_status": "unresolved",
                    "schema_version": "1.0",
                },
                "integrity": {
                    "ok": True,
                    "node_count": 0,
                    "relationship_count": 0,
                    "evidence_count": 0,
                    "dangling_relationship_sources": [],
                    "dangling_relationship_targets": [],
                    "relationships_with_missing_evidence": [],
                    "nodes_with_missing_evidence": [],
                    "duplicate_node_ids": [],
                    "duplicate_relationship_keys": [],
                    "duplicate_evidence_ids": [],
                    "layers_run": [],
                    "layers_missing": [],
                },
                "layers": {},
            },
        }


# ---------------------------------------------------------------------------
# Convenience
# ---------------------------------------------------------------------------


def run_disease_impact(
    disease_query: str,
) -> Dict[str, Any]:
    """
    One-shot pipeline run.
    """
    return DiseaseImpactPipeline().run(disease_query)


# ---------------------------------------------------------------------------
# Deserialization (HTTP -> in-process shape)
# ---------------------------------------------------------------------------


def deserialize_impact_result(
    serialized: Dict[str, Any],
) -> BiologicalImpactResult:
    """
    Rebuild a BiologicalImpactResult from its serialized
    dict form.

    Used by callers that receive a serialized result over
    HTTP (e.g. from the backend) and want to run the same
    in-process assertions on it.

    The serialized form (see serialize_impact_result) has
    indexes stripped and nodes / relationships / evidence
    as plain lists of dicts. This function rebuilds the
    Phase 01 dataclasses from that shape.

    It intentionally delegates to ImpactBuilder's
    deserializers so the two sides of the serialization
    boundary stay in sync.
    """

    builder = ImpactBuilder()

    node_set = _NodeSet()
    relationship_set = _RelationshipSet()
    evidence_collection = _EvidenceCollection()

    for raw in serialized.get("nodes") or []:
        node = builder._deserialize_node(raw)
        if node is not None:
            node_set.add(node)

    for raw in serialized.get("relationships") or []:
        rel = builder._deserialize_relationship(raw)
        if rel is not None:
            relationship_set.add(rel)

    relationship_set.build_indexes()

    for raw in serialized.get("evidence") or []:
        ev = builder._deserialize_evidence(raw)
        if ev is not None:
            evidence_collection.add(ev)

    reasoning = builder._deserialize_reasoning(
        serialized.get("reasoning") or {}
    )

    disease = None
    disease_raw = serialized.get("disease")
    if isinstance(disease_raw, dict):
        disease = _rebuild_disease_identity(disease_raw)

    return BiologicalImpactResult(
        query=serialized.get("query", ""),
        disease=disease,
        resolution_status=serialized.get(
            "resolution_status", "unresolved"
        ),
        nodes=node_set,
        relationships=relationship_set,
        evidence=evidence_collection,
        reasoning=reasoning,
        failure_reason=serialized.get("failure_reason"),
        metadata=dict(serialized.get("metadata") or {}),
    )


def _rebuild_disease_identity(
    raw: Dict[str, Any],
):
    """
    Rebuild a DiseaseIdentity from its serialized dict
    form.
    """

    from app.drug_development.schemas.disease import (
        DiseaseIdentifier,
        DiseaseIdentity,
    )

    identifiers = []
    for ident in raw.get("identifiers") or []:
        if not isinstance(ident, dict):
            continue
        identifiers.append(
            DiseaseIdentifier(
                source=ident.get("source", ""),
                identifier=ident.get("identifier", ""),
                url=ident.get("url"),
                metadata=dict(ident.get("metadata") or {}),
            )
        )

    return DiseaseIdentity(
        query=raw.get("query", ""),
        canonical_name=raw.get("canonical_name"),
        synonyms=list(raw.get("synonyms") or []),
        identifiers=identifiers,
        category=raw.get("category"),
        description=raw.get("description"),
        sources=list(raw.get("sources") or []),
        resolution_status=raw.get(
            "resolution_status", "unresolved"
        ),
        metadata=dict(raw.get("metadata") or {}),
    )


# ---------------------------------------------------------------------------
# Local aliases (avoid cluttering imports at module top)
# ---------------------------------------------------------------------------


def _NodeSet():
    from app.drug_development.schemas.impact import (
        ImpactNodeSet,
    )
    return ImpactNodeSet()


def _RelationshipSet():
    from app.drug_development.schemas.relationships import (
        RelationshipSet,
    )
    return RelationshipSet()


def _EvidenceCollection():
    from app.drug_development.schemas.evidence import (
        EvidenceCollection,
    )
    return EvidenceCollection()
