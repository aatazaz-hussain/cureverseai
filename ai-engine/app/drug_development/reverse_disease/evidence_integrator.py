"""
CureVerseAI — Drug Development
Workflow 02 — Reverse Disease Engineering
Evidence Integrator.

Takes the merged graph from CausalGraphBuilder and produces
the reasoning, uncertainty, and provenance payload that
lands in the final W02 result.

Scope
-----

This module is a PURE post-processor. It does NOT:

    - touch the network
    - call external sources
    - re-run any layer
    - rewrite graph entities

Its inputs are the merged graph and the per-layer dicts.
Its outputs are:

    - summary      : one-paragraph structured narrative
    - findings     : per-layer finding records
    - limitations  : W02-specific architectural caveats
    - sources      : deduplicated source list + per-layer breakdown
    - uncertainties: structured notes with a controlled vocabulary
    - provenance   : {sources_queried, source_failures, records_retrieved}
    - metadata     : counts, engine outputs, layer summaries

Reuse of EvidenceReasoningEngine
--------------------------------

W01's ImpactEvidenceIntegrator calls
EvidenceReasoningEngine.reason() for the molecular layer.
W02's gene layer is the direct analog, so the integrator
calls the same engine with W02-shaped inputs:

    biological_context   : first gene symbol + disease name
    target_analysis      : evidence list built from gene nodes
    open_targets_evidence: collected from gene layer evidence
    chembl_evidence      : None in Phase 1 (ChEMBL bioactivity
                           records are attached as metadata on
                           gene nodes, not as a separate bundle)

The engine's output lands in `metadata.engine_output` and
its findings are merged into the top-level `findings` list.

Fixed limitations
-----------------

W02's fixed limitations list describes what the workflow
does NOT claim:

    - "mechanism" nodes are evidence-type categories, not
      named biological mechanisms
    - disease->pathway edges are inferred from >=2 gene
      associations, not direct annotations
    - the variant layer is deferred (Phase 1)
    - ChEMBL bioactivity records indicate experimental
      investigation, not causal disease mechanism
    - evidence composition counts categories and does not
      establish clinical validity

Uncertainty vocabulary
----------------------

Each uncertainty note has:

    {
        "type": <str>,          # controlled vocabulary below
        "statement": <str>,     # human-readable
        "related_ids": [<str>], # node or edge ids
        "severity": <str>,      # "info" | "warning" | "error"
    }

Types (controlled):

    missing_source_data      a source returned nothing
    missing_variant_layer    variant layer is not wired
    inferred_edge            edge is an aggregate, not direct
    partial_layer            layer had partial results
    source_unavailable       a source errored
    evidence_gap             no evidence at all for a layer
"""

from __future__ import annotations

from collections import Counter
from typing import Any, Dict, List, Optional

from app.analysis.evidence_reasoning import (
    EvidenceReasoningEngine,
)
from app.drug_development.schemas.disease import (
    DiseaseIdentity,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


#: Fixed architectural limitations for W02. Each entry is a
#: plain string. They are always included in the output
#: regardless of what data was retrieved.
FIXED_LIMITATIONS: List[str] = [
    (
        "Mechanism nodes represent evidence-type categories "
        "(literature, genetic association, clinical "
        "precedence, etc.), not named biological mechanisms. "
        "Named mechanisms are visible through pathway names."
    ),
    (
        "Disease -> pathway edges are inferred from 2 or "
        "more disease-associated genes participating in the "
        "pathway. They are aggregate associations, not "
        "direct experimental annotations of the disease."
    ),
    (
        "The variant layer is deferred to a future phase. "
        "Open Targets' GraphQL surface does not expose a "
        "target-level variant field, and no alternative "
        "variant source is wired in Phase 1."
    ),
    (
        "ChEMBL bioactivity records (when present) indicate "
        "that a target has been experimentally investigated "
        "with a compound. They do not establish that the "
        "target causes the disease."
    ),
    (
        "Evidence composition counts categories. It does "
        "not establish clinical validity, safety, efficacy, "
        "or regulatory approval."
    ),
    (
        "Open Targets association scores are preserved "
        "verbatim. They are not converted into probabilities "
        "of causation."
    ),
]


# ---------------------------------------------------------------------------
# Integrator
# ---------------------------------------------------------------------------


class EvidenceIntegrator:
    """
    Post-processes a merged W02 graph into a reasoning
    payload.
    """

    def __init__(
        self,
        reasoning_engine: Optional[EvidenceReasoningEngine] = None,
    ):
        self.reasoning_engine = (
            reasoning_engine or EvidenceReasoningEngine()
        )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def integrate(
        self,
        disease: DiseaseIdentity,
        merged_graph: Dict[str, Any],
        layers: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Produce the W02 reasoning payload.

        `merged_graph` is the output of
        CausalGraphBuilder.build(). `layers` is the same
        per-layer dict the builder receives.
        """

        graph = merged_graph.get("graph") or {}
        nodes = graph.get("nodes") or []
        edges = graph.get("edges") or []
        evidence = graph.get("evidence") or []

        # ---- Counts ------------------------------------------
        node_type_counts = self._count_by_key(
            nodes, "node_type"
        )
        rel_type_counts = self._count_by_key(
            edges, "relationship_type"
        )
        support_class_counts = self._count_by_key(
            edges, "support_class"
        )
        evidence_level_counts = self._count_by_key(
            evidence, "evidence_level"
        )

        # ---- Per-layer findings ------------------------------
        layer_findings, layer_counts = (
            self._build_layer_findings(layers)
        )

        # ---- Evidence engine ---------------------------------
        engine_output = self._run_evidence_engine(
            disease=disease,
            nodes=nodes,
            evidence=evidence,
        )

        engine_findings = self._shape_engine_findings(
            engine_output
        )

        # ---- Sources -----------------------------------------
        sources_block = self._collect_sources(layers)

        # ---- Uncertainties -----------------------------------
        uncertainties = self._build_uncertainties(
            layers=layers,
            nodes=nodes,
            edges=edges,
            engine_output=engine_output,
        )

        # ---- Provenance --------------------------------------
        provenance = self._build_provenance(
            layers=layers,
            sources_block=sources_block,
            evidence=evidence,
        )

        # ---- Limitations -------------------------------------
        limitations = list(FIXED_LIMITATIONS)

        # Per-layer failure reasons
        for name, layer in layers.items():
            if not isinstance(layer, dict):
                continue
            if layer.get("found"):
                continue
            reason = layer.get("reason")
            if reason:
                limitations.append(
                    f"{name} layer: {reason}"
                )

        # Engine's own limitations (they do not duplicate ours)
        for item in engine_output.get("limitations") or []:
            if isinstance(item, str) and item not in limitations:
                limitations.append(item)

        # ---- Summary -----------------------------------------
        summary = self._build_summary(
            disease=disease,
            node_type_counts=node_type_counts,
            rel_type_counts=rel_type_counts,
            support_class_counts=support_class_counts,
            layer_counts=layer_counts,
        )

        # ---- Findings merge ----------------------------------
        merged_findings: List[Dict[str, Any]] = []
        for f in engine_findings:
            merged_findings.append(
                {"layer": "gene", **f}
            )
        merged_findings.extend(layer_findings)

        # ---- Assemble ----------------------------------------
        return {
            "summary": summary,
            "findings": merged_findings,
            "limitations": limitations,
            "sources": sources_block,
            "uncertainties": uncertainties,
            "provenance": provenance,
            "metadata": {
                "node_type_counts": node_type_counts,
                "relationship_type_counts": rel_type_counts,
                "support_class_counts": support_class_counts,
                "evidence_level_counts": (
                    evidence_level_counts
                ),
                "layer_counts": layer_counts,
                "engine_output": {
                    "reasoning_type": engine_output.get(
                        "reasoning_type"
                    ),
                    "evidence_summary": engine_output.get(
                        "evidence_summary"
                    ),
                    "evidence_composition": (
                        engine_output.get(
                            "evidence_composition"
                        )
                    ),
                },
            },
        }

    # ------------------------------------------------------------------
    # Counting helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _count_by_key(
        items: List[Dict[str, Any]],
        key: str,
    ) -> Dict[str, int]:
        counter: Counter = Counter()

        for item in items:
            if not isinstance(item, dict):
                continue
            value = item.get(key)
            if value is None:
                counter["<none>"] += 1
            else:
                counter[str(value)] += 1

        return dict(counter.most_common())

    # ------------------------------------------------------------------
    # Per-layer findings
    # ------------------------------------------------------------------

    @staticmethod
    def _build_layer_findings(
        layers: Dict[str, Dict[str, Any]],
    ) -> (List[Dict[str, Any]], Dict[str, Dict[str, int]]):
        findings: List[Dict[str, Any]] = []
        counts: Dict[str, Dict[str, int]] = {}

        for layer_name, layer in layers.items():
            layer_counts = {
                "nodes": 0,
                "relationships": 0,
                "evidence": 0,
                "found": 0,
            }

            if not isinstance(layer, dict):
                counts[layer_name] = layer_counts
                continue

            if not layer.get("found"):
                counts[layer_name] = layer_counts
                continue

            layer_counts["nodes"] = len(
                layer.get("nodes") or []
            )
            layer_counts["relationships"] = len(
                layer.get("relationships") or []
            )
            layer_counts["evidence"] = len(
                layer.get("evidence") or []
            )
            layer_counts["found"] = 1

            counts[layer_name] = layer_counts

            findings.append(
                {
                    "type": f"{layer_name}_layer",
                    "layer": layer_name,
                    "statement": (
                        f"{layer_name.capitalize()} layer "
                        f"contributed {layer_counts['nodes']} "
                        f"node(s), "
                        f"{layer_counts['relationships']} "
                        f"relationship(s), and "
                        f"{layer_counts['evidence']} evidence "
                        f"record(s)."
                    ),
                    "counts": layer_counts,
                }
            )

        return findings, counts

    # ------------------------------------------------------------------
    # Evidence engine wrapper
    # ------------------------------------------------------------------

    def _run_evidence_engine(
        self,
        disease: DiseaseIdentity,
        nodes: List[Dict[str, Any]],
        evidence: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        gene_symbols = [
            n.get("name")
            for n in nodes
            if isinstance(n, dict)
            and n.get("node_type") == "gene"
        ][:20]

        biological_context: Dict[str, Any] = {
            "gene": (
                {"symbol": gene_symbols[0]}
                if gene_symbols
                else None
            ),
            "disease": {
                "name": disease.canonical_name or disease.query,
                "identifiers": [
                    i.identifier
                    for i in (disease.identifiers or [])
                ],
            },
        }

        target_analysis: Dict[str, Any] = {
            "evidence": [
                {
                    "strength": "direct",
                    "source": "Open Targets",
                    "description": (
                        f"Gene {symbol} is associated with "
                        f"{disease.canonical_name or disease.query}."
                    ),
                }
                for symbol in gene_symbols
            ],
            "pathways": {"entity_count": 0},
            "variants": {"variant_count": 0},
        }

        # Group Open Targets evidence by target for the engine.
        ot_evidence_items: List[Dict[str, Any]] = []
        for ev in evidence:
            if not isinstance(ev, dict):
                continue
            if ev.get("source") != "Open Targets":
                continue
            identifiers = ev.get("identifiers") or {}
            ot_evidence_items.append(
                {
                    "target": identifiers.get(
                        "gene_symbol"
                    )
                    or identifiers.get("hpo_id"),
                    "source": "Open Targets",
                    "description": ev.get(
                        "relationship_description"
                    ),
                    "metadata": ev.get("metadata") or {},
                }
            )

        open_targets_evidence = {
            "summary": {
                "sources": (
                    ["Open Targets"]
                    if ot_evidence_items
                    else []
                ),
            },
            "evidence": ot_evidence_items[:200],
        }

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

    @staticmethod
    def _shape_engine_findings(
        engine_output: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []

        for item in engine_output.get("findings") or []:
            if isinstance(item, dict):
                out.append(item)

        return out

    # ------------------------------------------------------------------
    # Sources
    # ------------------------------------------------------------------

    @staticmethod
    def _collect_sources(
        layers: Dict[str, Dict[str, Any]],
    ) -> Dict[str, Any]:
        all_sources: List[str] = []
        by_layer: Dict[str, List[str]] = {}

        for name, layer in layers.items():
            layer_sources: List[str] = []
            if isinstance(layer, dict):
                for s in layer.get("sources") or []:
                    if not isinstance(s, str):
                        continue
                    if s not in layer_sources:
                        layer_sources.append(s)
                    if s not in all_sources:
                        all_sources.append(s)
            by_layer[name] = layer_sources

        return {
            "all": all_sources,
            "by_layer": by_layer,
        }

    # ------------------------------------------------------------------
    # Uncertainties
    # ------------------------------------------------------------------

    @staticmethod
    def _build_uncertainties(
        layers: Dict[str, Dict[str, Any]],
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
        engine_output: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []

        # 1. Missing variant layer
        out.append(
            {
                "type": "missing_variant_layer",
                "statement": (
                    "The variant layer is not populated in "
                    "Phase 1. No variant nodes or edges are "
                    "asserted."
                ),
                "related_ids": [],
                "severity": "info",
            }
        )

        # 2. Per-layer missing or partial
        for name, layer in layers.items():
            if not isinstance(layer, dict):
                continue
            if layer.get("found"):
                continue
            reason = layer.get("reason") or (
                f"{name} layer returned no results."
            )
            out.append(
                {
                    "type": "evidence_gap",
                    "statement": f"{name}: {reason}",
                    "related_ids": [],
                    "severity": "warning",
                }
            )

        # 3. Gene layer: genes without Ensembl or UniProt
        gene_layer = layers.get("genes") or {}
        gene_nodes = [
            n
            for n in (gene_layer.get("nodes") or [])
            if isinstance(n, dict)
        ]
        if gene_nodes:
            no_uniprot = [
                n.get("node_id")
                for n in gene_nodes
                if not n.get("metadata", {}).get(
                    "uniprot_resolved"
                )
            ]
            if no_uniprot:
                out.append(
                    {
                        "type": "partial_layer",
                        "statement": (
                            f"{len(no_uniprot)} gene(s) had no "
                            "reviewed UniProt accession; they "
                            "are included as nodes but lack "
                            "protein identity."
                        ),
                        "related_ids": no_uniprot,
                        "severity": "info",
                    }
                )

            chembl_errored = [
                n.get("node_id")
                for n in gene_nodes
                if n.get("metadata", {}).get(
                    "chembl_status"
                )
                == "error"
            ]
            if chembl_errored:
                out.append(
                    {
                        "type": "source_unavailable",
                        "statement": (
                            f"{len(chembl_errored)} gene(s) "
                            "failed ChEMBL lookup; the gene "
                            "nodes are intact but their "
                            "bioactivity evidence is missing."
                        ),
                        "related_ids": chembl_errored,
                        "severity": "warning",
                    }
                )

        # 4. Pathway layer: inferred disease->pathway edges
        inferred_edges = [
            e
            for e in edges
            if isinstance(e, dict)
            and e.get("support_class") == "supported_association"
            and e.get("relationship_type") == "associated_with"
            and str(e.get("source_id", "")).startswith(
                "disease:"
            )
            and str(e.get("target_id", "")).startswith(
                "pathway:"
            )
        ]
        if inferred_edges:
            out.append(
                {
                    "type": "inferred_edge",
                    "statement": (
                        f"{len(inferred_edges)} disease -> "
                        "pathway edge(s) are inferred from 2+ "
                        "disease-associated genes participating "
                        "in the pathway. They are aggregate "
                        "associations, not direct annotations."
                    ),
                    "related_ids": [
                        EvidenceIntegrator._edge_key(e)
                        for e in inferred_edges[:50]
                    ],
                    "severity": "info",
                }
            )

        # 5. Mechanism layer: categories not named mechanisms
        mechanism_nodes = [
            n
            for n in nodes
            if isinstance(n, dict)
            and n.get("node_type") == "mechanism"
        ]
        if mechanism_nodes:
            out.append(
                {
                    "type": "inferred_edge",
                    "statement": (
                        "Mechanism nodes are evidence-type "
                        "categories aggregated across "
                        "associated targets, not named "
                        "biological mechanisms."
                    ),
                    "related_ids": [
                        n.get("node_id")
                        for n in mechanism_nodes
                    ],
                    "severity": "info",
                }
            )

        return out

    @staticmethod
    def _edge_key(edge: Dict[str, Any]) -> str:
        return (
            f"{edge.get('source_id')}|"
            f"{edge.get('relationship_type')}|"
            f"{edge.get('target_id')}"
        )

    # ------------------------------------------------------------------
    # Provenance
    # ------------------------------------------------------------------

    @staticmethod
    def _build_provenance(
        layers: Dict[str, Dict[str, Any]],
        sources_block: Dict[str, Any],
        evidence: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        sources_queried = list(
            sources_block.get("all") or []
        )

        # Source failures come from layer-level and node-level
        # error markers.
        source_failures: List[Dict[str, Any]] = []

        for name, layer in layers.items():
            if not isinstance(layer, dict):
                continue

            if not layer.get("found"):
                reason = layer.get("reason")
                if reason:
                    source_failures.append(
                        {
                            "source": name,
                            "reason": reason,
                        }
                    )

            for node in layer.get("nodes") or []:
                if not isinstance(node, dict):
                    continue
                meta = node.get("metadata") or {}
                errors = meta.get("chembl_errors")
                if not errors:
                    continue

                source_failures.append(
                    {
                        "source": "ChEMBL",
                        "reason": "; ".join(
                            str(e) for e in errors[:3]
                        ),
                        "metadata": {
                            "node_id": node.get("node_id"),
                        },
                    }
                )

        # records_retrieved is the total evidence count.
        records_retrieved = len(
            [e for e in evidence if isinstance(e, dict)]
        )

        return {
            "sources_queried": sources_queried,
            "source_failures": source_failures,
            "records_retrieved": records_retrieved,
        }

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    @staticmethod
    def _build_summary(
        disease: DiseaseIdentity,
        node_type_counts: Dict[str, int],
        rel_type_counts: Dict[str, int],
        support_class_counts: Dict[str, int],
        layer_counts: Dict[str, Dict[str, int]],
    ) -> str:
        active_layers = [
            name
            for name, counts in layer_counts.items()
            if counts.get("found")
        ]

        if not active_layers:
            return (
                "No W02 graph data was produced for this "
                "query. This may be an unresolvable disease, "
                "or the sources consulted returned no "
                "records."
            )

        parts: List[str] = []

        if disease.canonical_name or disease.query:
            parts.append(
                f"Investigation of "
                f"'{disease.canonical_name or disease.query}'"
            )

        parts.append(
            f"merged {len(active_layers)} layer(s) "
            f"({', '.join(active_layers)})"
        )

        node_parts = [
            f"{count} {ntype}"
            for ntype, count in node_type_counts.items()
            if ntype != "disease"
        ]
        if node_parts:
            parts.append(
                "producing " + ", ".join(node_parts)
            )

        if support_class_counts:
            sc_parts = [
                f"{count} {sc}"
                for sc, count in support_class_counts.items()
                if sc != "<none>"
            ]
            if sc_parts:
                parts.append(
                    "with " + ", ".join(sc_parts)
                )

        return " ".join(parts) + "."
