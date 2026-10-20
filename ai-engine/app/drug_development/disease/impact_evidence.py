"""
CureVerseAI — Drug Development
Impact Evidence Integrator.

Combines the evidence produced by all impact layers
(systems, tissues, cells, molecular, pathways) into a
single ImpactReasoning payload for BiologicalImpactResult.

Design
------

The existing EvidenceReasoningEngine in
app/analysis/evidence_reasoning.py is authoritative for
evidence categorization of the molecular layer. It is
NOT modified here. This module:

    1. Wraps EvidenceReasoningEngine.reason() with the
       molecular evidence inputs the engine expects.
    2. Separately aggregates the systems / tissues /
       cells / pathways evidence produced by Phases 03
       through 06 into per-layer finding records.
    3. Merges both into a single ImpactReasoning payload.

Layer summaries are COUNTING, not scoring. No evidence
category is collapsed into a single composite number.

What this module does NOT do
----------------------------

- It does not modify EvidenceReasoningEngine.
- It does not call any external source.
- It does not synthesize evidence. It only reads what
  prior phases produced.
- It does not assign numeric confidence.

Conventions
-----------

- Dataclasses from Phase 01 schemas are used directly.
- No new external libraries.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.analysis.evidence_reasoning import (
    EvidenceReasoningEngine,
)
from app.drug_development.schemas.impact import ImpactReasoning


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Architectural limitations that always apply to the
#: Disease -> Biological Impact workflow.
FIXED_LIMITATIONS = [
    (
        "Cell types are identified, but baseline vs "
        "disease-associated cellular state is not "
        "distinguished."
    ),
    (
        "Systems and tissues are attached to the disease "
        "node independently; no system-contains-tissue "
        "relationship is asserted without supporting "
        "evidence."
    ),
    (
        "Pathways are attached per-protein from Reactome; "
        "the disease -> pathway relationship is inferred "
        "from disease-associated proteins, not from a "
        "disease-specific pathway annotation."
    ),
    (
        "No compound or drug intervention is included in "
        "this layer; bioactivity evidence belongs to a "
        "later phase."
    ),
    (
        "Evidence composition counts categories and does "
        "not establish clinical validity, safety, "
        "efficacy, or regulatory approval."
    ),
]


# ---------------------------------------------------------------------------
# Integrator
# ---------------------------------------------------------------------------


class ImpactEvidenceIntegrator:
    """
    Merges per-layer evidence outputs into one
    ImpactReasoning payload.
    """

    def __init__(
        self,
        evidence_reasoning_engine: Optional[
            EvidenceReasoningEngine
        ] = None,
    ):
        self.reasoning_engine = (
            evidence_reasoning_engine
            or EvidenceReasoningEngine()
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def integrate(
        self,
        systems_result: Optional[Dict[str, Any]] = None,
        tissues_result: Optional[Dict[str, Any]] = None,
        cells_result: Optional[Dict[str, Any]] = None,
        molecular_result: Optional[Dict[str, Any]] = None,
        pathways_result: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Build the merged reasoning payload.

        Returns a dict with the same shape as
        ImpactReasoning, plus a `metadata` bag containing
        per-layer counts.

        Every input is optional. Layers that were not run
        or returned found=False are recorded in the
        limitations list, not silently dropped.
        """

        # ---- 1) Molecular layer reasoning -----------------------
        engine_output = self._run_evidence_engine(
            molecular_result
        )

        # ---- 2) Per-layer findings -----------------------------
        layer_findings: List[Dict[str, Any]] = []

        layer_counts: Dict[str, Dict[str, int]] = {}

        for layer_name, layer_result in (
            ("systems", systems_result),
            ("tissues", tissues_result),
            ("cells", cells_result),
            ("molecular", molecular_result),
            ("pathways", pathways_result),
        ):
            finding, counts = self._build_layer_finding(
                layer_name, layer_result
            )

            if finding is not None:
                layer_findings.append(finding)

            layer_counts[layer_name] = counts

        # ---- 3) Limitations ------------------------------------
        limitations = self._collect_limitations(
            engine_output=engine_output,
            layer_results={
                "systems": systems_result,
                "tissues": tissues_result,
                "cells": cells_result,
                "molecular": molecular_result,
                "pathways": pathways_result,
            },
        )

        # ---- 4) Merge findings ---------------------------------
        merged_findings: List[Dict[str, Any]] = []

        engine_findings = engine_output.get("findings") or []
        for f in engine_findings:
            if isinstance(f, dict):
                merged_findings.append(
                    {"layer": "molecular", **f}
                )

        merged_findings.extend(layer_findings)

        # ---- 5) Summary ----------------------------------------
        summary = self._build_summary(
            engine_output=engine_output,
            layer_counts=layer_counts,
        )

        # ---- 6) Sources ----------------------------------------
        sources = self._collect_sources(
            engine_output=engine_output,
            layer_results={
                "systems": systems_result,
                "tissues": tissues_result,
                "cells": cells_result,
                "molecular": molecular_result,
                "pathways": pathways_result,
            },
        )

        return {
            "summary": summary,
            "findings": merged_findings,
            "limitations": limitations,
            "sources": sources,
            "metadata": {
                "layer_counts": layer_counts,
                "engine_reasoning_type": engine_output.get(
                    "reasoning_type"
                ),
                "engine_evidence_summary": engine_output.get(
                    "evidence_summary"
                ),
                "engine_evidence_composition": engine_output.get(
                    "evidence_composition"
                ),
            },
        }

    # ------------------------------------------------------------------
    # EvidenceReasoningEngine wrapper
    # ------------------------------------------------------------------

    def _run_evidence_engine(
        self,
        molecular_result: Optional[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Call EvidenceReasoningEngine.reason() with the
        inputs it expects, constructed from the molecular
        layer result.

        If the molecular layer is missing or empty, returns
        an empty engine output with the correct keys so
        downstream code does not need to special-case.
        """

        if not molecular_result or not molecular_result.get(
            "found"
        ):
            return self._empty_engine_output()

        biological_context = self._build_biological_context(
            molecular_result
        )

        target_analysis = self._build_target_analysis(
            molecular_result
        )

        open_targets_evidence = (
            self._build_open_targets_evidence(molecular_result)
        )

        try:
            output = self.reasoning_engine.reason(
                biological_context=biological_context,
                target_analysis=target_analysis,
                open_targets_evidence=open_targets_evidence,
                chembl_evidence=None,
            )
        except Exception:
            return self._empty_engine_output()

        if not isinstance(output, dict):
            return self._empty_engine_output()

        return output

    @staticmethod
    def _build_biological_context(
        molecular_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Minimal biological context: the gene symbols
        present in the molecular layer.

        EvidenceReasoningEngine only reads `gene` from this
        dict; we supply the first gene symbol found.
        """

        gene_symbol = None

        for node in molecular_result.get("nodes") or []:
            if not isinstance(node, dict):
                continue
            if node.get("node_type") == "gene":
                gene_symbol = node.get("name")
                break

        return {
            "gene": {"symbol": gene_symbol} if gene_symbol else None,
        }

    @staticmethod
    def _build_target_analysis(
        molecular_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Build a target_analysis dict containing the
        `evidence` list that EvidenceReasoningEngine reads
        for `strength` categorization.

        We map every gene and protein node into an
        evidence entry so the engine's categorization
        reflects the actual count.
        """

        evidence: List[Dict[str, Any]] = []

        for node in molecular_result.get("nodes") or []:
            if not isinstance(node, dict):
                continue

            node_type = node.get("node_type")

            if node_type == "gene":
                evidence.append(
                    {
                        "strength": "direct",
                        "source": "Open Targets",
                        "description": (
                            f"Gene {node.get('name')} is "
                            f"associated with the disease."
                        ),
                    }
                )
            elif node_type == "protein":
                evidence.append(
                    {
                        "strength": "direct",
                        "source": "UniProt",
                        "description": (
                            f"Protein {node.get('name')} "
                            f"resolved from a disease "
                            f"associated gene."
                        ),
                    }
                )

        return {
            "evidence": evidence,
            "pathways": {"entity_count": 0},
            "variants": {"variant_count": 0},
        }

    @staticmethod
    def _build_open_targets_evidence(
        molecular_result: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Collect Open Targets evidence entries from the
        molecular layer result so the engine can count
        them as disease_association evidence.
        """

        items: List[Dict[str, Any]] = []

        for ev in molecular_result.get("evidence") or []:
            if not isinstance(ev, dict):
                continue
            if ev.get("source") != "Open Targets":
                continue

            items.append(
                {
                    "target": (ev.get("identifiers") or {}).get(
                        "gene_symbol"
                    ),
                    "source": ev.get("source"),
                    "description": ev.get(
                        "relationship_description"
                    ),
                    "metadata": ev.get("metadata") or {},
                }
            )

        return {
            "summary": {
                "sources": ["Open Targets"] if items else [],
            },
            "evidence": items,
        }

    @staticmethod
    def _empty_engine_output() -> Dict[str, Any]:
        return {
            "reasoning_type": None,
            "gene": None,
            "evidence_summary": {},
            "evidence_composition": {},
            "findings": [],
            "sources": {},
            "limitations": [],
        }

    # ------------------------------------------------------------------
    # Per-layer findings
    # ------------------------------------------------------------------

    @staticmethod
    def _build_layer_finding(
        layer_name: str,
        layer_result: Optional[Dict[str, Any]],
    ) -> (Optional[Dict[str, Any]], Dict[str, int]):
        """
        Summarize one layer's contribution.

        Returns (finding_or_None, counts_dict).

        The counts are raw counts of nodes and evidence,
        not scores. Nothing is normalized.
        """

        counts = {
            "nodes": 0,
            "relationships": 0,
            "evidence": 0,
            "found": 0,
        }

        if not layer_result:
            return None, counts

        if not layer_result.get("found"):
            return None, counts

        nodes = layer_result.get("nodes") or []
        relationships = layer_result.get("relationships") or []
        evidence = layer_result.get("evidence") or []

        counts["nodes"] = len(nodes)
        counts["relationships"] = len(relationships)
        counts["evidence"] = len(evidence)
        counts["found"] = 1

        finding = {
            "type": f"{layer_name}_layer",
            "layer": layer_name,
            "statement": (
                f"{layer_name.capitalize()} layer contributed "
                f"{counts['nodes']} node(s), "
                f"{counts['relationships']} relationship(s), "
                f"and {counts['evidence']} evidence record(s)."
            ),
            "counts": counts,
        }

        return finding, counts

    # ------------------------------------------------------------------
    # Limitations
    # ------------------------------------------------------------------

    @staticmethod
    def _collect_limitations(
        engine_output: Dict[str, Any],
        layer_results: Dict[str, Optional[Dict[str, Any]]],
    ) -> List[str]:
        limitations: List[str] = []

        # Engine's own limitations
        for item in engine_output.get("limitations") or []:
            if isinstance(item, str):
                limitations.append(item)

        # Per-layer failure reasons
        for layer_name, layer_result in layer_results.items():
            if not layer_result:
                limitations.append(
                    f"{layer_name}: layer was not run."
                )
                continue

            if layer_result.get("found"):
                continue

            reason = layer_result.get("reason")
            if reason:
                limitations.append(
                    f"{layer_name}: {reason}"
                )
            else:
                limitations.append(
                    f"{layer_name}: returned no results."
                )

        # Fixed architectural limitations
        for item in FIXED_LIMITATIONS:
            limitations.append(item)

        # Deduplicate while preserving order
        seen = set()
        unique: List[str] = []
        for item in limitations:
            if item in seen:
                continue
            seen.add(item)
            unique.append(item)

        return unique

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    @staticmethod
    def _build_summary(
        engine_output: Dict[str, Any],
        layer_counts: Dict[str, Dict[str, int]],
    ) -> Optional[str]:
        active_layers = [
            name for name, c in layer_counts.items()
            if c.get("found")
        ]

        if not active_layers:
            return (
                "No biological impact data was found for this "
                "query. This may be a symptom or a term that "
                "is not a disease. Try a disease name — for "
                "example, 'Asthma', 'Alzheimer's disease', or "
                "'Type 2 diabetes'."
            )

        parts = []

        for name in active_layers:
            c = layer_counts[name]
            parts.append(
                f"{name}: {c['nodes']} node(s)"
            )

        engine_summary = engine_output.get("evidence_summary")
        if isinstance(engine_summary, dict):
            total = engine_summary.get("total")
            if total:
                parts.append(
                    f"molecular evidence records: {total}"
                )

        return (
            "Impact graph produced by "
            + ", ".join(parts)
            + "."
        )

    # ------------------------------------------------------------------
    # Sources
    # ------------------------------------------------------------------

    @staticmethod
    def _collect_sources(
        engine_output: Dict[str, Any],
        layer_results: Dict[str, Optional[Dict[str, Any]]],
    ) -> Dict[str, Any]:
        all_sources: List[str] = []

        # Engine sources
        engine_sources = engine_output.get("sources") or {}
        if isinstance(engine_sources, dict):
            for value in engine_sources.values():
                if isinstance(value, list):
                    for s in value:
                        if isinstance(s, str):
                            all_sources.append(s)

        # Layer sources
        for layer_result in layer_results.values():
            if not isinstance(layer_result, dict):
                continue
            for s in layer_result.get("sources") or []:
                if isinstance(s, str):
                    all_sources.append(s)

        # Deduplicate preserving order
        seen = set()
        unique: List[str] = []
        for s in all_sources:
            if s in seen:
                continue
            seen.add(s)
            unique.append(s)

        return {
            "all": unique,
            "by_layer": {
                name: (
                    layer_results.get(name, {}).get("sources", [])
                    if isinstance(
                        layer_results.get(name), dict
                    )
                    else []
                )
                for name in layer_results
            },
        }


# ---------------------------------------------------------------------------
# Convenience
# ---------------------------------------------------------------------------


def build_impact_reasoning(
    systems_result: Optional[Dict[str, Any]] = None,
    tissues_result: Optional[Dict[str, Any]] = None,
    cells_result: Optional[Dict[str, Any]] = None,
    molecular_result: Optional[Dict[str, Any]] = None,
    pathways_result: Optional[Dict[str, Any]] = None,
) -> ImpactReasoning:
    """
    Convenience function: run the integrator and convert
    the result into a Phase 01 ImpactReasoning dataclass.

    The metadata bag is preserved on ImpactReasoning.metadata.
    """

    raw = ImpactEvidenceIntegrator().integrate(
        systems_result=systems_result,
        tissues_result=tissues_result,
        cells_result=cells_result,
        molecular_result=molecular_result,
        pathways_result=pathways_result,
    )

    return ImpactReasoning(
        summary=raw.get("summary"),
        findings=raw.get("findings") or [],
        limitations=raw.get("limitations") or [],
        sources=raw.get("sources") or {},
        metadata=raw.get("metadata") or {},
    )
