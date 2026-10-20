"""
CureVerseAI — Medicine domain
Response model.

Builds the Response records and the ScenarioComparison that
W01 and W02 return.

Responsibilities:

    W01 — healthy reference vs disease state.

    W02 — disease state vs single-intervention state.

This module does NOT:

    - compute a numeric magnitude
    - compute an overall score
    - subtract two indicator values
    - add two treatment effects
    - rank scenarios by any composite

Every direction of change is derived from the actual
IndicatorValue records on the two states being compared. A
change is never asserted unless the scenario state carries a
directional IndicatorValue and its method is at least
``mechanistic_inference``.

Design constraints (locked from Phase 3 decisions 6b and 8c):

    - W01 is a comparison, not a ranking. Its overall
      interpretation is always ``no_defensible_winner``.

    - W02's overall interpretation is chosen from the
      specification's four permitted outcomes:

          best_supported         — not used in v1; we do not
                                    have a validated scoring
                                    method to justify it
          promising_uncertain    — at least one directional
                                    mechanistic inference is
                                    present and the
                                    intervention's targets link
                                    to the disease context
          no_defensible_winner   — default
          potentially_adverse    — reserved; only when a
                                    source explicitly supports
                                    an adverse effect

    - A target interaction alone does not establish efficacy.
      If the intervention's targets do not link to the
      disease context, no response is claimed, and the
      interpretation is ``no_defensible_winner`` with a
      reason recorded in the comparison notes.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.medicine.simulation import schemas as s


# ---------------------------------------------------------------------------
# Response construction
# ---------------------------------------------------------------------------


def _response_from_values(
    indicator_id: str,
    baseline_state_id: str,
    scenario_state_id: str,
    baseline_value: Optional[s.IndicatorValue],
    scenario_value: Optional[s.IndicatorValue],
) -> s.Response:
    """
    Build a single Response from two IndicatorValue records.

    Rules:

        - If the scenario value is missing or its method is
          ``insufficient``, the response is unknown /
          insufficient. No direction is asserted.
        - If the baseline is unknown and the scenario is
          directional, the direction of change is taken from
          the scenario. The change is present in the modelled
          state; the baseline is simply silent.
        - No magnitude is ever computed.

    The returned Response always carries:
        magnitude      = None
        evidence_ids   = scenario_value.evidence_ids
        uncertainty    = mirror of scenario_value.uncertainty,
                         with the baseline absence added as a
                         reason when applicable
    """
    if scenario_value is None or scenario_value.method == s.ResponseMethod.INSUFFICIENT:
        return s.Response(
            indicator_id=indicator_id,
            baseline_state_id=baseline_state_id,
            scenario_state_id=scenario_state_id,
            direction_change=s.ResponseDirection.UNKNOWN,
            method=s.ResponseMethod.INSUFFICIENT,
            magnitude=None,
            evidence_ids=[],
            uncertainty=s.Uncertainty(
                level="unknown",
                reasons=[
                    "No directional value was produced for this "
                    "indicator in the scenario state."
                ],
                sources=[],
            ),
            notes=[],
        )

    # Scenario carries a directional value.
    direction = scenario_value.direction
    method = scenario_value.method
    evidence_ids = list(scenario_value.evidence_ids or [])

    # Build uncertainty for the change.
    reasons: List[str] = []
    sources: List[str] = []

    if scenario_value.uncertainty is not None:
        reasons.extend(scenario_value.uncertainty.reasons or [])
        sources.extend(scenario_value.uncertainty.sources or [])

    if baseline_value is None or baseline_value.method == s.ResponseMethod.INSUFFICIENT:
        reasons.append(
            "Baseline reference value is not available for this "
            "indicator; the change is reported relative to an "
            "unknown reference."
        )
        level = "medium" if method == s.ResponseMethod.MECHANISTIC_INFERENCE else "unknown"
    else:
        level = (
            scenario_value.uncertainty.level
            if scenario_value.uncertainty
            else "medium"
        )

    return s.Response(
        indicator_id=indicator_id,
        baseline_state_id=baseline_state_id,
        scenario_state_id=scenario_state_id,
        direction_change=direction,
        method=method,
        magnitude=None,
        evidence_ids=evidence_ids,
        uncertainty=s.Uncertainty(
            level=level,
            reasons=reasons or [
                "Response derived from the scenario indicator "
                "value; no magnitude is available."
            ],
            sources=sources,
        ),
        notes=[],
    )


# ---------------------------------------------------------------------------
# W01 — healthy reference vs disease
# ---------------------------------------------------------------------------


def build_w01_comparison(
    pair: Dict[str, Any],
    healthy_state: s.BiologicalState,
    disease_state: s.BiologicalState,
) -> s.ScenarioComparison:
    """
    Compare the healthy reference state to the disease state.

    Baseline is the healthy state; the single scenario is the
    disease state.

    The overall interpretation is always
    ``no_defensible_winner``: W01 is a description of what the
    disease state looks like relative to a reference whose
    reference values are currently unknown. There is nothing
    to rank.
    """
    responses: List[s.Response] = []

    if pair:
        for entry in pair.get("indicators", []):
            ind_id = entry.get("id")
            if not ind_id:
                continue

            baseline = healthy_state.indicator_values.get(ind_id)
            scenario = disease_state.indicator_values.get(ind_id)

            responses.append(
                _response_from_values(
                    indicator_id=ind_id,
                    baseline_state_id=healthy_state.state_id,
                    scenario_state_id=disease_state.state_id,
                    baseline_value=baseline,
                    scenario_value=scenario,
                )
            )

    return s.ScenarioComparison(
        baseline_state_id=healthy_state.state_id,
        scenarios=[healthy_state, disease_state],
        responses=responses,
        overall_interpretation=s.OverallInterpretation.NO_DEFENSIBLE_WINNER,
        interaction_class=None,
        interaction_evidence_ids=[],
        reasoning=(
            "Comparison of the healthy reference state and the "
            "disease-associated state on the same indicator set. "
            "Directions are reported as mechanistic inferences "
            "where a curated pathway resolved; the reference "
            "values are not available in the current source "
            "stack."
        ),
        notes=[],
        metadata={
            "workflow": "virtual_disease_simulation",
        },
    )


# ---------------------------------------------------------------------------
# W02 — disease vs single intervention
# ---------------------------------------------------------------------------


def build_w02_comparison(
    pair: Dict[str, Any],
    disease_state: s.BiologicalState,
    treatment_state: s.BiologicalState,
    target_disease_link_supported: bool,
) -> s.ScenarioComparison:
    """
    Compare the disease state to the single-intervention state.

    ``target_disease_link_supported`` is decided by the caller
    (the service), because the target-to-disease linkage check
    is a service-level concern:

        - If False, no response is claimed to be beneficial.
          Every Response is still emitted (so the frontend can
          show the indicator set and its sources), but the
          overall interpretation is ``no_defensible_winner``
          and a note explains the missing link.

        - If True, and at least one response carries a
          directional mechanistic inference, the overall
          interpretation is ``promising_uncertain``.

        - Otherwise, ``no_defensible_winner``.
    """
    responses: List[s.Response] = []

    if pair:
        for entry in pair.get("indicators", []):
            ind_id = entry.get("id")
            if not ind_id:
                continue

            baseline = disease_state.indicator_values.get(ind_id)
            scenario = treatment_state.indicator_values.get(ind_id)

            responses.append(
                _response_from_values(
                    indicator_id=ind_id,
                    baseline_state_id=disease_state.state_id,
                    scenario_state_id=treatment_state.state_id,
                    baseline_value=baseline,
                    scenario_value=scenario,
                )
            )

    # Overall interpretation.
    notes: List[str] = []

    if not target_disease_link_supported:
        interpretation = s.OverallInterpretation.NO_DEFENSIBLE_WINNER
        notes.append(
            "The intervention's targets are not linked to the "
            "selected disease context by the available sources. "
            "No beneficial response is claimed."
        )
    else:
        any_directional = any(
            r.method == s.ResponseMethod.MECHANISTIC_INFERENCE
            and r.direction_change in (
                s.ResponseDirection.INCREASE,
                s.ResponseDirection.DECREASE,
            )
            for r in responses
        )

        if any_directional:
            interpretation = s.OverallInterpretation.PROMISING_UNCERTAIN
            notes.append(
                "At least one indicator has a directional "
                "mechanistic inference, and the intervention's "
                "targets link to the disease context. A "
                "validated response model is not available, so "
                "this is a promising but uncertain outcome."
            )
        else:
            interpretation = s.OverallInterpretation.NO_DEFENSIBLE_WINNER
            notes.append(
                "No directional response could be established "
                "for any indicator with the current evidence."
            )

    return s.ScenarioComparison(
        baseline_state_id=disease_state.state_id,
        scenarios=[disease_state, treatment_state],
        responses=responses,
        overall_interpretation=interpretation,
        interaction_class=None,
        interaction_evidence_ids=[],
        reasoning=(
            "Comparison of the disease state and the "
            "single-intervention state on the same indicator "
            "set. Directions are mechanistic inferences from "
            "curated pathway links; no numeric magnitude is "
            "reported."
        ),
        notes=notes,
        metadata={
            "workflow": "treatment_simulation",
            "target_disease_link_supported": bool(
                target_disease_link_supported
            ),
        },
    )
