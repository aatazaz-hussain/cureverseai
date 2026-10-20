"""
CureVerseAI — Drug Development
Workflow 03 — Therapeutic Discovery
Explanation Builder.

Produces narration segments tied to specific graph
elements. Each segment references either a node ID or a
stable edge key so the frontend can highlight the
corresponding element.

Segment selection (40 max)
--------------------------

    disease node                   1
    mechanism node                 1
    pathway node                   1
    mechanism-member targets       5
    Open-Targets-only targets      3
    top candidates                25
    conflicts                      4
                                 ---
                                  40

Text is generated from the structured result only. No
claim in any segment references a fact that is not
directly readable from the graph, the candidates, or the
activities.

What this module does NOT do
----------------------------

    - It does not call a language model.
    - It does not infer clinical effects.
    - It does not upgrade an association into a causal
      claim.
    - It does not invent missing values.

Every segment is a template rendering of source data.

Edge key format
---------------

An edge segment's `target_id` is the canonical key

    "<source_id>|<relationship_type>|<target_id>"

matching the W02 convention. Node segments use the node's
own ID.

Pure module, no I/O.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, List, Optional, Tuple

from app.drug_development.therapeutic_discovery.schemas import (
    ActivityRecord,
    CandidateComparison,
    CandidateCompound,
    MechanismOfActionChain,
    NarrationSegment,
    SelectedMechanism,
    TargetSummary,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


_MAX_MEMBER_TARGETS = 5
_MAX_OT_ONLY_TARGETS = 3
_MAX_CANDIDATES = 25
_MAX_CONFLICTS = 4
_MAX_SEGMENTS = 40


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------


class ExplanationBuilder:
    """
    Produce narration segments from a W03 result.
    """

    def __init__(self) -> None:
        pass

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build(
        self,
        graph: Dict[str, Any],
        mechanism: SelectedMechanism,
        targets: List[TargetSummary],
        candidates: List[CandidateCompound],
        activities: List[ActivityRecord],
        chains: List[MechanismOfActionChain],
        comparisons: List[CandidateComparison],
    ) -> List[Dict[str, Any]]:
        """
        Return a list of serialized NarrationSegment dicts.
        """

        segments: List[NarrationSegment] = []

        # ---- 1) Disease segment -----------------------------
        disease_node = self._find_node(
            graph, lambda n: n.get("node_type") == "disease"
        )
        if disease_node:
            segments.append(
                self._disease_segment(disease_node)
            )

        # ---- 2) Mechanism segment ---------------------------
        mechanism_node = self._find_node(
            graph, lambda n: n.get("node_type") == "mechanism"
        )
        if mechanism_node:
            segments.append(
                self._mechanism_segment(
                    mechanism_node, mechanism, targets
                )
            )

        # ---- 3) Pathway segment -----------------------------
        pathway_node = self._find_node(
            graph, lambda n: n.get("node_type") == "pathway"
        )
        if pathway_node:
            segments.append(
                self._pathway_segment(
                    pathway_node, mechanism, targets
                )
            )

        # ---- 4) Member-target segments ----------------------
        member_targets = [
            t for t in targets if t.mechanism_membership
        ][:_MAX_MEMBER_TARGETS]

        for target in member_targets:
            segments.append(
                self._member_target_segment(
                    target, mechanism
                )
            )

        # ---- 5) Open-Targets-only target segments -----------
        ot_only = [
            t
            for t in targets
            if not t.mechanism_membership
            and t.open_targets_score is not None
        ]
        ot_only.sort(
            key=lambda t: -(t.open_targets_score or 0.0)
        )

        for target in ot_only[:_MAX_OT_ONLY_TARGETS]:
            segments.append(
                self._ot_only_target_segment(
                    target, mechanism
                )
            )

        # ---- 6) Candidate segments --------------------------
        # `comparisons` is already sorted best-first.
        activities_by_cid: Dict[
            str, List[ActivityRecord]
        ] = {}
        for r in activities:
            activities_by_cid.setdefault(
                r.compound_chembl_id, []
            ).append(r)

        candidates_by_id: Dict[
            str, CandidateCompound
        ] = {c.compound_id: c for c in candidates}

        chains_by_cid: Dict[
            str, MechanismOfActionChain
        ] = {c.candidate_id: c for c in chains}

        candidate_count = 0
        for comparison in comparisons:
            if candidate_count >= _MAX_CANDIDATES:
                break

            candidate = candidates_by_id.get(
                comparison.candidate_id
            )
            if candidate is None:
                continue

            chain = chains_by_cid.get(
                comparison.candidate_id
            )

            segments.append(
                self._candidate_segment(
                    candidate=candidate,
                    comparison=comparison,
                    activities=activities_by_cid.get(
                        candidate.compound_id, []
                    ),
                    chain=chain,
                    targets=targets,
                )
            )
            candidate_count += 1

        # ---- 7) Conflict segments ---------------------------
        conflict_count = 0
        for seg in self._build_conflict_segments(activities):
            if conflict_count >= _MAX_CONFLICTS:
                break
            segments.append(seg)
            conflict_count += 1

        # ---- 8) Cap ----------------------------------------
        segments = segments[:_MAX_SEGMENTS]

        return [asdict(s) for s in segments]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _find_node(
        graph: Dict[str, Any],
        predicate,
    ) -> Optional[Dict[str, Any]]:
        for node in graph.get("nodes") or []:
            if not isinstance(node, dict):
                continue
            if predicate(node):
                return node
        return None

    # ------------------------------------------------------------------
    # Segment constructors — nodes
    # ------------------------------------------------------------------

    @staticmethod
    def _disease_segment(
        node: Dict[str, Any],
    ) -> NarrationSegment:
        name = node.get("name") or "The disease"
        identifier = node.get("identifier")
        description = node.get("description") or ""

        # First sentence of the description only.
        first = _first_sentence(description)

        text_parts = []
        if identifier:
            text_parts.append(f"{name} ({identifier}).")
        else:
            text_parts.append(f"{name}.")

        if first:
            text_parts.append(first.rstrip(". ") + ".")

        text_parts.append(
            "This investigation looks at which compounds could "
            "modify a biological mechanism associated with this "
            "disease."
        )

        return NarrationSegment(
            explanation_id=f"exp:node:{node.get('node_id')}",
            target_kind="node",
            target_id=str(node.get("node_id")),
            text=" ".join(text_parts),
            support_class=None,
            evidence_ids=[],
            metadata={"node_type": "disease"},
        )

    @staticmethod
    def _mechanism_segment(
        node: Dict[str, Any],
        mechanism: SelectedMechanism,
        targets: List[TargetSummary],
    ) -> NarrationSegment:
        label = node.get("name") or mechanism.label or (
            mechanism.mechanism_id
        )
        member_count = len(
            [t for t in targets if t.mechanism_membership]
        )

        source_text = (
            "selected as a starting point from Workflow 02"
            if mechanism.source == "w02_handoff"
            else "discovered from the disease's associated "
            "targets"
        )

        text = (
            f"The mechanism under investigation is "
            f"'{label}'. It was {source_text}. "
            f"{member_count} of the disease's candidate "
            f"targets participate in this biological "
            f"process."
        )

        return NarrationSegment(
            explanation_id=f"exp:node:{node.get('node_id')}",
            target_kind="node",
            target_id=str(node.get("node_id")),
            text=text,
            support_class=None,
            evidence_ids=[],
            metadata={"node_type": "mechanism"},
        )

    @staticmethod
    def _pathway_segment(
        node: Dict[str, Any],
        mechanism: SelectedMechanism,
        targets: List[TargetSummary],
    ) -> NarrationSegment:
        label = node.get("name") or mechanism.label
        identifier = node.get("identifier") or (
            mechanism.identifier or ""
        )
        member_count = len(
            [t for t in targets if t.mechanism_membership]
        )

        text = (
            f"'{label}' ({identifier}) is a biological "
            f"process recorded in Reactome. {member_count} of "
            f"the disease's candidate targets are members of "
            f"this pathway."
        )

        return NarrationSegment(
            explanation_id=f"exp:node:{node.get('node_id')}",
            target_kind="node",
            target_id=str(node.get("node_id")),
            text=text,
            support_class=None,
            evidence_ids=[],
            metadata={"node_type": "pathway"},
        )

    @staticmethod
    def _member_target_segment(
        target: TargetSummary,
        mechanism: SelectedMechanism,
    ) -> NarrationSegment:
        symbol = target.gene_symbol or target.label
        mech_label = mechanism.label or mechanism.mechanism_id

        text = (
            f"'{symbol}' is a member of the '{mech_label}' "
            f"pathway and also appears in Open Targets "
            f"associations for the disease."
        )

        return NarrationSegment(
            explanation_id=f"exp:node:{target.target_id}",
            target_kind="node",
            target_id=target.target_id,
            text=text,
            support_class="retrieved_fact",
            evidence_ids=[],
            metadata={
                "node_type": "gene",
                "role": "mechanism_member",
            },
        )

    @staticmethod
    def _ot_only_target_segment(
        target: TargetSummary,
        mechanism: SelectedMechanism,
    ) -> NarrationSegment:
        symbol = target.gene_symbol or target.label
        score = target.open_targets_score

        if score is not None:
            text = (
                f"'{symbol}' is associated with the disease "
                f"in Open Targets with a score of "
                f"{score:.2f}. It is not a member of the "
                f"selected mechanism's pathway."
            )
        else:
            text = (
                f"'{symbol}' is a candidate target from "
                f"Open Targets associations. It is not a "
                f"member of the selected mechanism's pathway."
            )

        return NarrationSegment(
            explanation_id=f"exp:node:{target.target_id}",
            target_kind="node",
            target_id=target.target_id,
            text=text,
            support_class="supported_association",
            evidence_ids=[],
            metadata={
                "node_type": "gene",
                "role": "open_targets_only",
            },
        )

    @staticmethod
    def _candidate_segment(
        candidate: CandidateCompound,
        comparison: CandidateComparison,
        activities: List[ActivityRecord],
        chain: Optional[MechanismOfActionChain],
        targets: List[TargetSummary],
    ) -> NarrationSegment:
        label = candidate.name or candidate.compound_id

        # Find the target from the chain.
        target_label = "its target"
        if chain and chain.target_id:
            for t in targets:
                if t.target_id == chain.target_id:
                    target_label = t.label
                    break

        # Find a sample measured value.
        sample = None
        for r in activities:
            if (r.metadata or {}).get(
                "classification"
            ) == "measured_potency":
                sample = r
                break

        parts: List[str] = []
        parts.append(f"'{label}' ({candidate.compound_id})")

        if sample is not None and sample.standard_value:
            unit = sample.standard_units or ""
            parts.append(
                f"has a measured "
                f"{sample.standard_type or 'activity'} of "
                f"{sample.standard_value} {unit} against "
                f"{target_label}."
            )
        elif activities:
            parts.append(
                f"has {len(activities)} activity record(s) "
                f"against {target_label}, but no numeric "
                f"measurement."
            )
        else:
            parts.append(
                f"has no recorded activity against "
                f"{target_label}."
            )

        # Link strength note.
        if comparison.mechanism_link_strength == "direct":
            parts.append(
                "Its chain connects the compound to the "
                "target, the mechanism's pathway, and the "
                "disease."
            )
        elif comparison.mechanism_link_strength == "two_hop":
            parts.append(
                "Its chain reaches the pathway or the "
                "disease but not both."
            )
        else:
            parts.append(
                "Its chain reaches only the target."
            )

        parts.append(
            "This is a mechanism hypothesis. Measured "
            "activity is not clinical efficacy."
        )

        support_class = (
            "experimentally_measured"
            if sample is not None
            else "supported_association"
        )

        return NarrationSegment(
            explanation_id=(
                f"exp:node:compound:{candidate.compound_id}"
            ),
            target_kind="node",
            target_id=(
                f"compound:{candidate.compound_id}"
            ),
            text=" ".join(parts),
            support_class=support_class,
            evidence_ids=[],
            metadata={"node_type": "compound"},
        )

    # ------------------------------------------------------------------
    # Conflict segments
    # ------------------------------------------------------------------

    @staticmethod
    def _build_conflict_segments(
        activities: List[ActivityRecord],
    ) -> List[NarrationSegment]:
        # Group measured values by (compound, target).
        grouped: Dict[
            Tuple[str, str], List[ActivityRecord]
        ] = {}
        for r in activities:
            classification = (r.metadata or {}).get(
                "classification"
            )
            if classification != "measured_potency":
                continue
            key = (r.compound_chembl_id, r.target_chembl_id)
            grouped.setdefault(key, []).append(r)

        out: List[NarrationSegment] = []

        for (cid, tid), records in grouped.items():
            if len(records) < 2:
                continue

            values: List[float] = []
            unit = ""
            for r in records:
                v = _to_float(r.standard_value)
                if v is None or v <= 0:
                    continue
                if (r.standard_units or "").lower() not in (
                    "nm",
                    "nanomolar",
                ):
                    continue
                values.append(v)
                if not unit:
                    unit = r.standard_units or ""

            if len(values) < 2:
                continue

            lo = min(values)
            hi = max(values)
            if lo <= 0:
                continue

            ratio = hi / lo
            if ratio < 100:
                continue

            text = (
                f"'{cid}' has multiple assay measurements "
                f"against '{tid}' spanning {lo:.1f} to "
                f"{hi:.1f} {unit}, a roughly {ratio:.0f}-fold "
                f"spread. Both are preserved; neither is "
                f"discarded."
            )

            out.append(
                NarrationSegment(
                    explanation_id=(
                        f"exp:conflict:{cid}:{tid}"
                    ),
                    target_kind="node",
                    target_id=f"compound:{cid}",
                    text=text,
                    support_class="experimentally_measured",
                    evidence_ids=[],
                    metadata={
                        "type": "conflict",
                        "compound_chembl_id": cid,
                        "target_chembl_id": tid,
                    },
                )
            )

        # Sort by ratio descending — most striking first.
        out.sort(
            key=lambda s: -(
                (s.metadata or {}).get("ratio", 1.0)
            )
        )

        return out


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _first_sentence(text: str) -> str:
    if not text:
        return ""
    trimmed = text.strip()
    match = trimmed and trimmed.find(". ")
    if match and match > 0:
        return trimmed[: match + 1]
    if trimmed.endswith("."):
        return trimmed
    if len(trimmed) > 220:
        return trimmed[:220].strip() + "…"
    return trimmed


def _to_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Convenience
# ---------------------------------------------------------------------------


def build_explanations(
    graph: Dict[str, Any],
    mechanism: SelectedMechanism,
    targets: List[TargetSummary],
    candidates: List[CandidateCompound],
    activities: List[ActivityRecord],
    chains: List[MechanismOfActionChain],
    comparisons: List[CandidateComparison],
) -> List[Dict[str, Any]]:
    """
    One-shot entry point.
    """
    return ExplanationBuilder().build(
        graph=graph,
        mechanism=mechanism,
        targets=targets,
        candidates=candidates,
        activities=activities,
        chains=chains,
        comparisons=comparisons,
    )
