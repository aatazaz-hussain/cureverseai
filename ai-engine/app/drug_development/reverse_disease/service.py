"""
CureVerseAI — Drug Development
Workflow 02 — Reverse Disease Engineering
Top-level service.

This module is the single public entry point for
Workflow 02's AI Engine side. It:

    1. resolves the disease query
    2. fetches the four layers
       (phenotypes, mechanisms, genes, pathways)
    3. merges them into one graph via CausalGraphBuilder
    4. integrates evidence via EvidenceIntegrator
    5. ranks mechanisms and pathways via MechanismRanker
    6. builds narration segments via ExplanationBuilder
    7. serializes the result into the W02 wire contract

The orchestrator (see ai-engine/app/orchestrator/engine.py)
calls run_reverse_disease() for the task
`reverse_disease_engineering`.

Design decisions
----------------

- `run()` returns a SERIALIZED dict, matching W01's
  run_disease_impact() contract. The in-process dataclass
  (ReverseDiseaseResult) is built for testability and can
  be reconstructed via deserialize_reverse_disease_result.

- Layers are executed SEQUENTIALLY. Parallel execution
  would add thread-pool complexity for a bounded runtime
  (the slow parts — Reactome and ChEMBL — are cached).

- ChEMBL enrichment is opt-out via `fetch_chembl=False`.
  Ensembl and UniProt resolution always run because gene
  identity should not depend on an opt-in flag.

- Ambiguity handling: when the resolver returns
  status="partial" (multiple matches) or "unresolved"
  (no match), the service emits a well-formed result with
  an EMPTY graph, the disease block carrying the query and
  candidates, and a clear failure_reason. It does NOT
  auto-select a candidate. This matches the W02 spec's
  rule against arbitrary selection.

- Layer transport failures propagate as RuntimeError.
  The service does not swallow them; the backend handles
  them as upstream errors.

Serialization contract
----------------------

The result matches the W02 spec's response shape:

    {
        "query": "...",
        "resolution_status": "resolved" | "partial" | "unresolved",
        "failure_reason": <str or None>,
        "disease": { ... } | None,
        "mechanistic_investigation": {
            "phenotypes": [...],
            "contributing_factors": [...],
            "mechanisms": [...],
            "genes": [...],
            "variants": [],
            "pathways": [...],
            "manifestations": [],
        },
        "graph": {
            "nodes": [...],
            "edges": [...],
        },
        "evidence": [...],
        "explanations": [...],
        "uncertainties": [...],
        "provenance": {
            "sources_queried": [...],
            "source_failures": [...],
            "records_retrieved": <int>,
        },
        # Extensions (not in the minimum spec, retained for
        # debugging and frontend use):
        "reasoning": {
            "summary": <str>,
            "findings": [...],
            "limitations": [...],
            "sources": {...},
        },
        "ranking": {
            "ranked_mechanism_categories": [...],
            "ranked_pathways": [...],
            "metadata": {...},
        },
        "integrity": { ... },
        "metadata": {
            "schema_version": "w02-1.0",
            "layers_run": [...],
            "layers_missing": [...],
            ...
        },
    }
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, List, Optional

from app.drug_development.reverse_disease.causal_graph_builder import (
    CausalGraphBuilder,
)
from app.drug_development.reverse_disease.disease_resolver import (
    W02DiseaseResolver,
)
from app.drug_development.reverse_disease.evidence_integrator import (
    EvidenceIntegrator,
)
from app.drug_development.reverse_disease.explanation_builder import (
    ExplanationBuilder,
)
from app.drug_development.reverse_disease.gene_variant_mapper import (
    GeneVariantMapper,
)
from app.drug_development.reverse_disease.mechanism_ranker import (
    MechanismRanker,
)
from app.drug_development.reverse_disease.mechanism_retriever import (
    MechanismRetriever,
)
from app.drug_development.reverse_disease.pathway_mapper import (
    PathwayMapper,
)
from app.drug_development.reverse_disease.phenotype_retriever import (
    PhenotypeRetriever,
)
from app.drug_development.reverse_disease.schemas import (
    Explanation,
    ProvenanceRecord,
    ReverseDiseaseResult,
)
from app.drug_development.schemas.disease import (
    DiseaseIdentity,
)
from app.drug_development.schemas.evidence import (
    EvidenceCollection,
)
from app.drug_development.schemas.impact import (
    ImpactNodeSet,
)
from app.drug_development.schemas.relationships import (
    RelationshipSet,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


SCHEMA_VERSION = "w02-1.0"

#: Canonical layer order. Also the order the layers are run.
LAYER_ORDER: List[str] = [
    "phenotypes",
    "mechanisms",
    "genes",
    "pathways",
]


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class ReverseDiseaseService:
    """
    Runs the complete Workflow 02 AI Engine pipeline for one
    disease query.
    """

    def __init__(
        self,
        resolver: Optional[W02DiseaseResolver] = None,
        phenotype_retriever: Optional[
            PhenotypeRetriever
        ] = None,
        mechanism_retriever: Optional[
            MechanismRetriever
        ] = None,
        gene_variant_mapper: Optional[
            GeneVariantMapper
        ] = None,
        pathway_mapper: Optional[PathwayMapper] = None,
        graph_builder: Optional[CausalGraphBuilder] = None,
        evidence_integrator: Optional[
            EvidenceIntegrator
        ] = None,
        mechanism_ranker: Optional[MechanismRanker] = None,
        explanation_builder: Optional[
            ExplanationBuilder
        ] = None,
        fetch_chembl: bool = True,
    ):
        self.resolver = resolver or W02DiseaseResolver()

        self.phenotype_retriever = (
            phenotype_retriever or PhenotypeRetriever()
        )
        self.mechanism_retriever = (
            mechanism_retriever or MechanismRetriever()
        )
        self.gene_variant_mapper = (
            gene_variant_mapper
            or GeneVariantMapper(fetch_chembl=fetch_chembl)
        )
        self.pathway_mapper = (
            pathway_mapper or PathwayMapper()
        )

        self.graph_builder = (
            graph_builder or CausalGraphBuilder()
        )
        self.evidence_integrator = (
            evidence_integrator or EvidenceIntegrator()
        )
        self.mechanism_ranker = (
            mechanism_ranker or MechanismRanker()
        )
        self.explanation_builder = (
            explanation_builder or ExplanationBuilder()
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def run(
        self,
        disease_query: str,
    ) -> Dict[str, Any]:
        """
        Run the complete W02 pipeline.

        Returns a serialized result dict. Never raises for an
        unresolvable or ambiguous disease. Raises RuntimeError
        only on transport-level failures from a source.
        """

        raw_query = (disease_query or "").strip()

        if not raw_query:
            return self._serialize_unresolved(
                raw_query="",
                reason=(
                    "Disease query cannot be empty."
                ),
            )

        # ---- 1. Resolve --------------------------------------
        resolution = self.resolver.resolve(raw_query)

        if resolution.disease is None:
            return self._serialize_unresolved(
                raw_query=raw_query,
                reason=(
                    resolution.message
                    or "Disease could not be resolved."
                ),
                status=resolution.status,
                candidates=resolution.candidates,
                sources_queried=W02DiseaseResolver.to_layer_dict(
                    resolution
                ).get("sources_queried", []),
            )

        disease = resolution.disease

        # ---- 2. Fetch layers ---------------------------------
        layers: Dict[str, Dict[str, Any]] = {}

        layers["phenotypes"] = (
            self.phenotype_retriever.retrieve(disease)
        )
        layers["mechanisms"] = (
            self.mechanism_retriever.retrieve(disease)
        )
        layers["genes"] = (
            self.gene_variant_mapper.retrieve(disease)
        )
        layers["pathways"] = (
            self.pathway_mapper.retrieve(disease)
        )

        # ---- 3. Merge ----------------------------------------
        merged = self.graph_builder.build(disease, layers)

        # ---- 4. Integrate evidence ---------------------------
        reasoning = self.evidence_integrator.integrate(
            disease=disease,
            merged_graph=merged,
            layers=layers,
        )

        # ---- 5. Rank -----------------------------------------
        ranking = self.mechanism_ranker.rank(merged)

        # ---- 6. Explanations ---------------------------------
        explanations = self.explanation_builder.build(
            merged_graph=merged,
            ranking=ranking,
        )

        # ---- 7. Serialize ------------------------------------
        return self._serialize_resolved(
            resolution=resolution,
            merged=merged,
            layers=layers,
            reasoning=reasoning,
            ranking=ranking,
            explanations=explanations,
        )

    # ------------------------------------------------------------------
    # Serialization — resolved path
    # ------------------------------------------------------------------

    def _serialize_resolved(
        self,
        resolution: Any,
        merged: Dict[str, Any],
        layers: Dict[str, Dict[str, Any]],
        reasoning: Dict[str, Any],
        ranking: Dict[str, Any],
        explanations: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        disease: DiseaseIdentity = resolution.disease
        graph = merged.get("graph") or {}
        integrity = merged.get("integrity") or {}

        # ---- mechanistic_investigation ----------------------
        variants_block: List[Dict[str, Any]] = []
        variants_reason = ""
        genes_layer = layers.get("genes") or {}
        variants_meta = genes_layer.get("metadata") or {}
        if "variants_unavailable_reason" in variants_meta:
            variants_reason = (
                variants_meta["variants_unavailable_reason"]
            )

        mechanistic_investigation = {
            "phenotypes": self._nodes_of_type(
                graph, "phenotype"
            ),
            "contributing_factors": (
                self._build_contributing_factors(
                    layers=layers
                )
            ),
            "mechanisms": self._nodes_of_type(
                graph, "mechanism"
            ),
            "genes": self._nodes_of_type(graph, "gene"),
            "variants": variants_block,
            "pathways": self._nodes_of_type(
                graph, "pathway"
            ),
            "manifestations": [],
        }

        # ---- disease block ----------------------------------
        disease_block = {
            "query": resolution.query,
            "resolved_name": disease.canonical_name,
            "identifiers": [
                {
                    "source": i.source,
                    "identifier": i.identifier,
                    "url": i.url,
                }
                for i in (disease.identifiers or [])
            ],
            "resolution_status": disease.resolution_status,
            "synonyms": list(disease.synonyms or []),
            "description": disease.description,
            "sources": list(disease.sources or []),
        }

        # ---- explanation block ------------------------------
        # Serialize Explanation dataclasses to dicts.
        explanation_dicts: List[Dict[str, Any]] = []
        for exp in explanations or []:
            if isinstance(exp, Explanation):
                explanation_dicts.append(asdict(exp))
            elif isinstance(exp, dict):
                explanation_dicts.append(exp)

        # ---- uncertainties ----------------------------------
        uncertainties = list(
            reasoning.get("uncertainties") or []
        )

        # Dedupe uncertainties by `type`. The
        # EvidenceIntegrator already emits generic notes for
        # some categories; the service adds richer notes on
        # top. Only add a service note when the type is not
        # already present.
        existing_types = {
            u.get("type")
            for u in uncertainties
            if isinstance(u, dict)
        }

        if (
            variants_reason
            and "missing_variant_layer" not in existing_types
        ):
            uncertainties.append(
                {
                    "type": "missing_variant_layer",
                    "statement": variants_reason,
                    "related_ids": [],
                    "severity": "info",
                }
            )
            existing_types.add("missing_variant_layer")

        if "missing_manifestations_layer" not in existing_types:
            uncertainties.append(
                {
                    "type": "missing_manifestations_layer",
                    "statement": (
                        "Manifestations are not separately "
                        "sourced from phenotypes in Phase 1. "
                        "The `manifestations` key is empty "
                        "by design."
                    ),
                    "related_ids": [],
                    "severity": "info",
                }
            )

        # ---- provenance -------------------------------------
        provenance = dict(
            reasoning.get("provenance") or {}
        )

        # ---- metadata ---------------------------------------
        layers_run: List[str] = []
        layers_missing: List[str] = []
        for name in LAYER_ORDER:
            layer = layers.get(name) or {}
            if layer.get("found"):
                layers_run.append(name)
            else:
                layers_missing.append(name)

        metadata = {
            "schema_version": SCHEMA_VERSION,
            "layers_run": layers_run,
            "layers_missing": layers_missing,
            "node_count": len(graph.get("nodes") or []),
            "edge_count": len(graph.get("edges") or []),
            "evidence_count": len(
                graph.get("evidence") or []
            ),
            "layer_counts": (
                (merged.get("integrity") or {}).get(
                    "layer_entity_counts"
                )
                or {}
            ),
        }

        # ---- assemble ---------------------------------------
        return {
            "query": resolution.query,
            "resolution_status": disease.resolution_status,
            "failure_reason": None,
            "disease": disease_block,
            "mechanistic_investigation": (
                mechanistic_investigation
            ),
            "graph": {
                "nodes": list(graph.get("nodes") or []),
                "edges": list(graph.get("edges") or []),
            },
            "evidence": list(
                graph.get("evidence") or []
            ),
            "explanations": explanation_dicts,
            "uncertainties": uncertainties,
            "provenance": provenance,
            "reasoning": {
                "summary": reasoning.get("summary"),
                "findings": list(
                    reasoning.get("findings") or []
                ),
                "limitations": list(
                    reasoning.get("limitations") or []
                ),
                "sources": dict(
                    reasoning.get("sources") or {}
                ),
            },
            "ranking": ranking,
            "integrity": integrity,
            "metadata": metadata,
        }

    # ------------------------------------------------------------------
    # Serialization — unresolved / partial path
    # ------------------------------------------------------------------

    @staticmethod
    def _serialize_unresolved(
        raw_query: str,
        reason: str,
        status: str = "unresolved",
        candidates: Optional[List[DiseaseIdentity]] = None,
        sources_queried: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Return a well-formed but empty result for an
        unresolved or partial query.
        """

        candidates = candidates or []
        sources_queried = sources_queried or []

        candidate_dicts = [
            {
                "canonical_name": c.canonical_name,
                "identifiers": [
                    {
                        "source": i.source,
                        "identifier": i.identifier,
                        "url": i.url,
                    }
                    for i in (c.identifiers or [])
                ],
                "description": c.description,
                "sources": list(c.sources or []),
            }
            for c in candidates
        ]

        disease_block = {
            "query": raw_query,
            "resolved_name": None,
            "identifiers": [],
            "resolution_status": status,
            "candidates": candidate_dicts,
        }

        return {
            "query": raw_query,
            "resolution_status": status,
            "failure_reason": reason,
            "disease": disease_block,
            "mechanistic_investigation": {
                "phenotypes": [],
                "contributing_factors": [],
                "mechanisms": [],
                "genes": [],
                "variants": [],
                "pathways": [],
                "manifestations": [],
            },
            "graph": {"nodes": [], "edges": []},
            "evidence": [],
            "explanations": [],
            "uncertainties": [
                {
                    "type": "unresolved_disease",
                    "statement": reason,
                    "related_ids": [],
                    "severity": "warning",
                }
            ],
            "provenance": {
                "sources_queried": sources_queried,
                "source_failures": [],
                "records_retrieved": 0,
            },
            "reasoning": {
                "summary": reason,
                "findings": [],
                "limitations": [
                    (
                        "No biological graph was produced "
                        "because the disease did not resolve."
                    ),
                ],
                "sources": {},
            },
            "ranking": {
                "ranked_mechanism_categories": [],
                "ranked_pathways": [],
                "metadata": {
                    "mechanism_categories_ranked": 0,
                    "pathways_ranked": 0,
                    "note": (
                        "No graph was produced, so no "
                        "ranking was computed."
                    ),
                },
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
                "layers_merged": [],
                "layer_entity_counts": {},
            },
            "metadata": {
                "schema_version": SCHEMA_VERSION,
                "layers_run": [],
                "layers_missing": list(LAYER_ORDER),
                "node_count": 0,
                "edge_count": 0,
                "evidence_count": 0,
                "layer_counts": {},
            },
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _nodes_of_type(
        graph: Dict[str, Any],
        node_type: str,
    ) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []
        for node in graph.get("nodes") or []:
            if not isinstance(node, dict):
                continue
            if node.get("node_type") == node_type:
                out.append(node)
        return out

    @staticmethod
    def _build_contributing_factors(
        layers: Dict[str, Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Synthesize a contributing-factors list from the gene
        layer's aggregated datasource counts.

        Each entry:
            {
                "type": "datasource",
                "id": <datasource_id>,
                "count": <targets_with_this_source>,
                "label": <human-readable>,
            }
        """
        genes_layer = layers.get("genes") or {}
        nodes = genes_layer.get("nodes") or []

        datasource_counts: Dict[str, int] = {}

        for node in nodes:
            if not isinstance(node, dict):
                continue
            meta = node.get("metadata") or {}
            for ds in meta.get("datasource_scores") or []:
                if not isinstance(ds, dict):
                    continue
                ds_id = ds.get("id")
                if not ds_id:
                    continue
                datasource_counts[ds_id] = (
                    datasource_counts.get(ds_id, 0) + 1
                )

        out: List[Dict[str, Any]] = []
        for ds_id, count in sorted(
            datasource_counts.items(),
            key=lambda kv: -kv[1],
        ):
            out.append(
                {
                    "type": "datasource",
                    "id": ds_id,
                    "count": count,
                    "label": ds_id.replace("_", " ").title(),
                }
            )

        return out


# ---------------------------------------------------------------------------
# Convenience
# ---------------------------------------------------------------------------


def run_reverse_disease(
    disease_query: str,
    fetch_chembl: bool = True,
) -> Dict[str, Any]:
    """
    One-shot entry point. Used by the orchestrator.
    """
    return ReverseDiseaseService(
        fetch_chembl=fetch_chembl
    ).run(disease_query)
