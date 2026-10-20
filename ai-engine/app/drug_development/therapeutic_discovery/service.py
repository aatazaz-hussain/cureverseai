"""
CureVerseAI — Drug Development
Workflow 03 — Therapeutic Discovery
Top-level service.

Single public entry point for Workflow 03's AI Engine side.
The orchestrator calls run_therapeutic_discovery() for the
task `therapeutic_discovery`.

Pipeline
--------

    1. resolve disease context      (disease_context)
    2. resolve or discover mechanism (mechanism_resolver)
    3. discover targets              (target_discovery)
    4. discover compounds            (compound_discovery)
    5. interpret activities          (activity_interpreter)
    6. build MoA chains              (mechanism_of_action)
    7. evaluate candidates           (candidate_evaluation)
    8. integrate evidence            (evidence_integrator)
    9. build graph                   (therapeutic_graph)
   10. build narration               (explanation_builder)
   11. serialize                     (this file)

Design decisions
----------------

- `run()` returns a SERIALIZED dict, matching W01's
  run_disease_impact() and W02's run_reverse_disease().

- Ambiguity handling matches W02:
    unresolved disease    -> empty result with reason
    partial resolution    -> empty result with candidates
  W03 does not auto-select a candidate disease.

- Never raises for an unresolvable disease, an empty
  candidate list, or a missing source. Only genuine
  transport RuntimeErrors propagate.

Serialization contract
----------------------

Matches the W03 spec's response shape, extended with:

    graph             full node/edge/evidence lists
    summary           one-paragraph plain-language summary
    limitations       fixed scientific limitations
    metadata          schema_version, counts, timing
    integrity         graph integrity report
"""

from __future__ import annotations

import time
from dataclasses import asdict
from typing import Any, Dict, List, Optional

from app.drug_development.therapeutic_discovery.activity_interpreter import (
    ActivityInterpreter,
)
from app.drug_development.therapeutic_discovery.candidate_evaluation import (
    CandidateEvaluator,
)
from app.drug_development.therapeutic_discovery.compound_discovery import (
    CompoundDiscovery,
)
from app.drug_development.therapeutic_discovery.disease_context import (
    DiseaseContextResolver,
)
from app.drug_development.therapeutic_discovery.evidence_integrator import (
    EvidenceIntegrator,
)
from app.drug_development.therapeutic_discovery.explanation_builder import (
    ExplanationBuilder,
)
from app.drug_development.therapeutic_discovery.mechanism_of_action import (
    MechanismOfActionBuilder,
)
from app.drug_development.therapeutic_discovery.mechanism_resolver import (
    MechanismResolver,
)
from app.drug_development.therapeutic_discovery.schemas import (
    CandidateComparison,
    CandidateCompound,
    MechanismOfActionChain,
    NarrationSegment,
    ProvenanceBlock,
    ReasoningBlock,
    SelectedMechanism,
    TargetSummary,
    TherapeuticDiscoveryResult,
)
from app.drug_development.therapeutic_discovery.target_discovery import (
    TargetDiscovery,
)
from app.drug_development.therapeutic_discovery.therapeutic_graph import (
    TherapeuticGraphBuilder,
)
from app.drug_development.schemas.disease import (
    DiseaseIdentity,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


SCHEMA_VERSION = "w03-1.0"


# ---------------------------------------------------------------------------
# Service
# ---------------------------------------------------------------------------


class TherapeuticDiscoveryService:
    """
    Runs the complete Workflow 03 AI Engine pipeline for one
    query.
    """

    def __init__(
        self,
        disease_context: Optional[
            DiseaseContextResolver
        ] = None,
        mechanism_resolver: Optional[
            MechanismResolver
        ] = None,
        target_discovery: Optional[TargetDiscovery] = None,
        compound_discovery: Optional[
            CompoundDiscovery
        ] = None,
        activity_interpreter: Optional[
            ActivityInterpreter
        ] = None,
        moa_builder: Optional[
            MechanismOfActionBuilder
        ] = None,
        candidate_evaluator: Optional[
            CandidateEvaluator
        ] = None,
        evidence_integrator: Optional[
            EvidenceIntegrator
        ] = None,
        graph_builder: Optional[
            TherapeuticGraphBuilder
        ] = None,
        explanation_builder: Optional[
            ExplanationBuilder
        ] = None,
    ):
        self.disease_context = (
            disease_context or DiseaseContextResolver()
        )
        self.mechanism_resolver = (
            mechanism_resolver or MechanismResolver()
        )
        self.target_discovery = (
            target_discovery or TargetDiscovery()
        )
        self.compound_discovery = (
            compound_discovery or CompoundDiscovery()
        )
        self.activity_interpreter = (
            activity_interpreter or ActivityInterpreter()
        )
        self.moa_builder = (
            moa_builder or MechanismOfActionBuilder()
        )
        self.candidate_evaluator = (
            candidate_evaluator or CandidateEvaluator()
        )
        self.evidence_integrator = (
            evidence_integrator or EvidenceIntegrator()
        )
        self.graph_builder = (
            graph_builder or TherapeuticGraphBuilder()
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
        mechanism_id: Optional[str] = None,
        target_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Run the complete W03 pipeline.

        Never raises for unresolvable input or empty results.
        """

        started = time.time()
        raw_query = (disease_query or "").strip()

        # ---- 1. Disease context ------------------------------
        context = self.disease_context.resolve(
            disease_query=raw_query,
            mechanism_id=mechanism_id,
            target_id=target_id,
        )

        if not context["found"] or context["disease"] is None:
            return self._serialize_unresolved(
                raw_query=raw_query,
                reason=(
                    context.get("failure_reason")
                    or "Disease could not be resolved."
                ),
                status=context.get(
                    "resolution_status", "unresolved"
                ),
                candidates=context.get("candidates") or [],
                sources_queried=(
                    context.get("sources_queried") or []
                ),
                mechanism_id=mechanism_id,
                started=started,
            )

        disease: DiseaseIdentity = context["disease"]

        # ---- 2. Mechanism resolution/discovery ---------------
        mechanism_result = self.mechanism_resolver.resolve(
            disease, context
        )

        if not mechanism_result["found"]:
            return self._serialize_unresolved(
                raw_query=raw_query,
                reason=(
                    mechanism_result.get("reason")
                    or "No mechanism could be resolved or "
                    "discovered."
                ),
                status="resolved",
                disease=disease,
                sources_queried=(
                    context.get("sources_queried") or []
                ),
                mechanism_id=mechanism_id,
                started=started,
            )

        mechanism: SelectedMechanism = mechanism_result[
            "mechanism"
        ]

        # ---- 3. Target discovery -----------------------------
        targets_result = self.target_discovery.discover(
            disease=disease,
            mechanism=mechanism,
            mechanism_context=mechanism_result,
        )

        targets: List[TargetSummary] = targets_result.get(
            "targets", []
        )

        # ---- 4. Compound discovery ---------------------------
        # Only query targets that have a gene symbol or a
        # resolvable identifier. Cap to the top 10 targets to
        # keep the runtime bounded.
        queryable = [
            t
            for t in targets
            if t.gene_symbol or t.uniprot_id
        ][:10]

        compounds_result = self.compound_discovery.discover(
            queryable
        )

        candidates: List[CandidateCompound] = (
            compounds_result.get("candidates", [])
        )
        activities = compounds_result.get("activities", [])

        # ---- 5. Activity interpretation ----------------------
        interpretation = self.activity_interpreter.interpret(
            activities
        )

        # ---- 6. Mechanism of action --------------------------
        # Compute the disease node id first, so each chain can
        # carry the full compound -> target -> pathway -> disease
        # path. Without this, _link_strength in candidate
        # evaluation always reports two_hop.
        disease_node_id = self._disease_node_id(disease)

        moa_result = self.moa_builder.build(
            candidates=candidates,
            targets=targets,
            activities=activities,
            mechanism=mechanism,
            mechanism_context=mechanism_result,
            disease_node_id=disease_node_id,
        )

        chains: List[MechanismOfActionChain] = (
            moa_result.get("chains", [])
        )

        # ---- 7. Candidate evaluation -------------------------
        evaluation = self.candidate_evaluator.evaluate(
            candidates=candidates,
            activities=activities,
            chains=chains,
        )

        comparisons_all: List[CandidateComparison] = (
            evaluation.get("all_comparisons", [])
        )
        comparisons_top: List[CandidateComparison] = (
            evaluation.get("comparisons", [])
        )

        # ---- 8. Evidence integration -------------------------
        reasoning = self.evidence_integrator.integrate(
            disease_label=(
                disease.canonical_name or disease.query
            ),
            mechanism=mechanism,
            targets=targets,
            candidates=candidates,
            activities=activities,
            chains=chains,
            comparisons=comparisons_all,
            sources_queried=self._collect_sources(
                context=context,
                mechanism_result=mechanism_result,
                targets_result=targets_result,
                compounds_result=compounds_result,
            ),
            source_failures=[],
        )

        # ---- 9. Therapeutic graph ----------------------------
        graph = self.graph_builder.build(
            disease=disease,
            mechanism=mechanism,
            targets=targets,
            candidates=candidates,
            activities=activities,
            chains=chains,
        )

        # ---- 10. Explanation builder -------------------------
        narration_dicts = self.explanation_builder.build(
            graph=graph,
            mechanism=mechanism,
            targets=targets,
            candidates=candidates,
            activities=activities,
            chains=chains,
            comparisons=comparisons_top,
        )

        # ---- 11. Serialize -----------------------------------
        elapsed = time.time() - started

        return self._serialize_resolved(
            disease=disease,
            mechanism=mechanism,
            mechanism_result=mechanism_result,
            targets=targets,
            candidates=candidates,
            activities_count=len(activities),
            chains=chains,
            comparisons=comparisons_top,
            reasoning=reasoning,
            graph=graph,
            narration_dicts=narration_dicts,
            elapsed=elapsed,
        )

    # ------------------------------------------------------------------
    # Serialization — resolved path
    # ------------------------------------------------------------------

    def _serialize_resolved(
        self,
        disease: DiseaseIdentity,
        mechanism: SelectedMechanism,
        mechanism_result: Dict[str, Any],
        targets: List[TargetSummary],
        candidates: List[CandidateCompound],
        activities_count: int,
        chains: List[MechanismOfActionChain],
        comparisons: List[CandidateComparison],
        reasoning: Dict[str, Any],
        graph: Dict[str, Any],
        narration_dicts: List[Dict[str, Any]],
        elapsed: float,
    ) -> Dict[str, Any]:
        disease_block = {
            "query": disease.query,
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

        mechanism_block = {
            "mechanism_id": mechanism.mechanism_id,
            "label": mechanism.label,
            "source": mechanism.source,
            "identifier": mechanism.identifier,
            "description": mechanism.description,
            "candidate_mechanisms": [
                {
                    "mechanism_id": m.mechanism_id,
                    "label": m.label,
                    "source": m.source,
                    "identifier": m.identifier,
                    "metadata": dict(m.metadata or {}),
                }
                for m in (
                    mechanism_result.get(
                        "candidate_mechanisms"
                    )
                    or []
                )
            ],
            "metadata": dict(mechanism_result.get("metadata") or {}),
        }

        targets_block = [
            {
                "target_id": t.target_id,
                "label": t.label,
                "gene_symbol": t.gene_symbol,
                "uniprot_id": t.uniprot_id,
                "ensembl_id": t.ensembl_id,
                "chembl_target_id": t.chembl_target_id,
                "mechanism_membership": t.mechanism_membership,
                "open_targets_score": t.open_targets_score,
                "metadata": dict(t.metadata or {}),
            }
            for t in targets
        ]

        candidates_block = [
            {
                "compound_id": c.compound_id,
                "source": c.source,
                "name": c.name,
                "parent_chembl_id": c.parent_chembl_id,
                "canonical_smiles": c.canonical_smiles,
                "identifiers": dict(c.identifiers or {}),
                "metadata": dict(c.metadata or {}),
            }
            for c in candidates
        ]

        comparisons_block = [asdict(c) for c in comparisons]

        moa_block = {
            "nodes": list(graph.get("nodes") or []),
            "edges": list(graph.get("edges") or []),
        }

        reasoning_dict = {
            "supported_findings": list(
                reasoning["reasoning"].supported_findings
            ),
            "hypotheses": list(
                reasoning["reasoning"].hypotheses
            ),
            "conflicts": list(
                reasoning["reasoning"].conflicts
            ),
            "evidence_gaps": list(
                reasoning["reasoning"].evidence_gaps
            ),
        }

        provenance_block = asdict(reasoning["provenance"])

        return {
            "query": disease.query,
            "resolution_status": disease.resolution_status,
            "failure_reason": None,
            "disease": disease_block,
            "selected_mechanism": mechanism_block,
            "targets": targets_block,
            "candidates": candidates_block,
            "mechanism_of_action": moa_block,
            "candidate_comparisons": comparisons_block,
            "evidence": list(graph.get("evidence") or []),
            "reasoning": reasoning_dict,
            "provenance": provenance_block,
            "narration": {"segments": narration_dicts},
            # W03 extensions:
            "summary": reasoning.get("summary"),
            "limitations": list(
                reasoning.get("limitations") or []
            ),
            "integrity": dict(graph.get("integrity") or {}),
            "metadata": {
                "schema_version": SCHEMA_VERSION,
                "elapsed_seconds": round(elapsed, 2),
                "target_count": len(targets),
                "candidate_count": len(candidates),
                "activity_count": activities_count,
                "chain_count": len(chains),
                "narration_segment_count": len(
                    narration_dicts
                ),
            },
        }

    # ------------------------------------------------------------------
    # Serialization — unresolved / partial path
    # ------------------------------------------------------------------

    @staticmethod
    def _serialize_unresolved(
        raw_query: str,
        reason: str,
        status: str = "unresolved",
        disease: Optional[DiseaseIdentity] = None,
        candidates: Optional[List[DiseaseIdentity]] = None,
        sources_queried: Optional[List[str]] = None,
        mechanism_id: Optional[str] = None,
        started: float = 0.0,
    ) -> Dict[str, Any]:
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

        disease_block = (
            {
                "query": disease.query,
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
            if disease is not None
            else {
                "query": raw_query,
                "resolved_name": None,
                "identifiers": [],
                "resolution_status": status,
                "candidates": candidate_dicts,
            }
        )

        elapsed = time.time() - started if started else 0.0

        return {
            "query": raw_query,
            "resolution_status": status,
            "failure_reason": reason,
            "disease": disease_block,
            "selected_mechanism": (
                {"mechanism_id": mechanism_id}
                if mechanism_id
                else None
            ),
            "targets": [],
            "candidates": [],
            "mechanism_of_action": {
                "nodes": [],
                "edges": [],
            },
            "candidate_comparisons": [],
            "evidence": [],
            "reasoning": {
                "supported_findings": [],
                "hypotheses": [],
                "conflicts": [],
                "evidence_gaps": [
                    {
                        "type": "unresolved_query",
                        "statement": reason,
                    }
                ],
            },
            "provenance": {
                "sources_queried": sources_queried,
                "source_failures": [],
                "records_retrieved": 0,
                "metadata": {},
            },
            "narration": {"segments": []},
            "summary": reason,
            "limitations": [],
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
            },
            "metadata": {
                "schema_version": SCHEMA_VERSION,
                "elapsed_seconds": round(elapsed, 2),
                "target_count": 0,
                "candidate_count": 0,
                "activity_count": 0,
                "chain_count": 0,
                "narration_segment_count": 0,
            },
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _disease_node_id(disease: DiseaseIdentity) -> Optional[str]:
        """
        Same convention as therapeutic_graph.py.
        Colons in the identifier are sanitized to
        underscores so the disease node id is stable.
        """
        if not disease.identifiers:
            return None

        primary = disease.identifiers[0]
        ident = (primary.identifier or "").strip()
        if not ident:
            return None

        sanitized = ident.replace(":", "_")
        return f"disease:{sanitized}"

    @staticmethod
    def _collect_sources(
        context: Dict[str, Any],
        mechanism_result: Dict[str, Any],
        targets_result: Dict[str, Any],
        compounds_result: Dict[str, Any],
    ) -> List[str]:
        all_sources: List[str] = []

        def push(items: Any) -> None:
            if not isinstance(items, list):
                return
            for s in items:
                if isinstance(s, str) and s not in all_sources:
                    all_sources.append(s)

        push(context.get("sources_queried"))
        push(mechanism_result.get("sources_queried"))
        push(targets_result.get("sources_queried"))
        push(compounds_result.get("sources_queried"))

        return all_sources


# ---------------------------------------------------------------------------
# Convenience
# ---------------------------------------------------------------------------


def run_therapeutic_discovery(
    disease_query: str,
    mechanism_id: Optional[str] = None,
    target_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    One-shot entry point. Used by the orchestrator.
    """
    return TherapeuticDiscoveryService().run(
        disease_query=disease_query,
        mechanism_id=mechanism_id,
        target_id=target_id,
    )
