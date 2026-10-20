"""
CureVerseAI — Medicine domain
Combination model (Workflow 03).

Builds the four-scenario comparison required by the
Combination Treatment Simulator:

    baseline (disease state)
    A alone
    B alone
    A + B together

and classifies the interaction between A and B.

Design constraints (locked in Phase 3 decision 9c):

    - The interaction class is set ONLY from a documented
      combination rule in the function vocabulary. If no
      rule exists, the interaction is
      ``insufficient_evidence`` and the overall
      interpretation is ``not_modelled``.

    - Synergy, antagonism, overlapping, additive, and
      adverse are never inferred from the numerical pattern
      of the individual responses. They are read from the
      rule, and only when the rule exists.

    - The A + B scenario state is supplied by the caller
      (the service). This module does not synthesize it from
      A and B. If the service cannot produce a defensible
      A + B state, the caller passes a state whose indicator
      values are all ``insufficient``, and the comparison
      records the honest absence.

    - No magnitude is ever computed. All Response.magnitude
      fields are None.

    - No overall score, no ranking, no winner is asserted
      unless the rule-based interaction class supports it.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.medicine.simulation import schemas as s


# ---------------------------------------------------------------------------
# Per-scenario response construction
# ---------------------------------------------------------------------------


def _build_responses_for_scenario(
    pair: Dict[str, Any],
    baseline_state: s.BiologicalState,
    scenario_state: s.BiologicalState,
) -> List[s.Response]:
    """
    Build the Response list for one scenario against the
    baseline disease state.

    Rules mirror response_model._response_from_values:

        - Missing or insufficient scenario value → unknown /
          insufficient, no direction claimed.
        - Directional scenario value → take its direction and
          method, no magnitude.
        - Baseline insufficiency is recorded as an uncertainty
          reason on the response.
    """
    responses: List[s.Response] = []

    if not pair:
        return responses

    for entry in pair.get("indicators", []):
        ind_id = entry.get("id")
        if not ind_id:
            continue

        baseline = baseline_state.indicator_values.get(ind_id)
        scenario = scenario_state.indicator_values.get(ind_id)

        if scenario is None or scenario.method == s.ResponseMethod.INSUFFICIENT:
            responses.append(
                s.Response(
                    indicator_id=ind_id,
                    baseline_state_id=baseline_state.state_id,
                    scenario_state_id=scenario_state.state_id,
                    direction_change=s.ResponseDirection.UNKNOWN,
                    method=s.ResponseMethod.INSUFFICIENT,
                    magnitude=None,
                    evidence_ids=[],
                    uncertainty=s.Uncertainty(
                        level="unknown",
                        reasons=[
                            "No directional value was produced "
                            "for this indicator in this scenario."
                        ],
                        sources=[],
                    ),
                    notes=[],
                )
            )
            continue

        reasons: List[str] = []
        sources: List[str] = []

        if scenario.uncertainty is not None:
            reasons.extend(scenario.uncertainty.reasons or [])
            sources.extend(scenario.uncertainty.sources or [])

        if baseline is None or baseline.method == s.ResponseMethod.INSUFFICIENT:
            reasons.append(
                "Baseline reference value is not available for "
                "this indicator."
            )

        level = (
            scenario.uncertainty.level
            if scenario.uncertainty
            else "medium"
        )

        responses.append(
            s.Response(
                indicator_id=ind_id,
                baseline_state_id=baseline_state.state_id,
                scenario_state_id=scenario_state.state_id,
                direction_change=scenario.direction,
                method=scenario.method,
                magnitude=None,
                evidence_ids=list(scenario.evidence_ids or []),
                uncertainty=s.Uncertainty(
                    level=level,
                    reasons=reasons or [
                        "Response derived from the scenario "
                        "indicator value; no magnitude is "
                        "available."
                    ],
                    sources=sources,
                ),
                notes=[],
            )
        )

    return responses


# ---------------------------------------------------------------------------
# Overall interpretation from the rule (if any)
# ---------------------------------------------------------------------------


def _derive_interpretation(
    combination_rule: Optional[Dict[str, Any]],
    all_responses: List[s.Response],
) -> s.OverallInterpretation:
    """
    Return the overall interpretation.

    Ordering:

        1. No rule → not_modelled.
        2. Rule exists and any response carries a rule-declared
           adverse interaction → potentially_adverse.
        3. Rule exists and any response has a directional
           mechanistic inference → promising_uncertain.
        4. Otherwise → no_defensible_winner.
    """
    if combination_rule is None:
        return s.OverallInterpretation.NOT_MODELLED

    rule_class = combination_rule.get("interaction_class")
    if rule_class == s.InteractionClass.ADVERSE:
        return s.OverallInterpretation.POTENTIALLY_ADVERSE

    any_directional = any(
        r.method == s.ResponseMethod.MECHANISTIC_INFERENCE
        and r.direction_change in (
            s.ResponseDirection.INCREASE,
            s.ResponseDirection.DECREASE,
        )
        for r in all_responses
    )

    if any_directional:
        return s.OverallInterpretation.PROMISING_UNCERTAIN

    return s.OverallInterpretation.NO_DEFENSIBLE_WINNER


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def build_w03_comparison(
    pair: Dict[str, Any],
    baseline_state: s.BiologicalState,
    state_a: s.BiologicalState,
    state_b: s.BiologicalState,
    state_ab: s.BiologicalState,
    intervention_a: s.InterventionRef,
    intervention_b: s.InterventionRef,
    combination_rule: Optional[Dict[str, Any]] = None,
) -> s.ScenarioComparison:
    """
    Build the four-scenario comparison for W03.

    The comparison contains:

        - scenarios:   [baseline, A, B, A+B]
        - responses:   A vs baseline, then B vs baseline,
                       then A+B vs baseline
        - interaction_class:    None when no rule exists,
                                otherwise the rule's class
        - overall_interpretation: derived per the rules
                                  documented above
        - notes: explicit about the combination state
        - metadata: intervention ids, rule provenance

    Never computes a magnitude. Never sums individual
    responses. Never classifies an interaction without a
    documented rule.
    """
    responses: List[s.Response] = []

    responses.extend(
        _build_responses_for_scenario(pair, baseline_state, state_a)
    )
    responses.extend(
        _build_responses_for_scenario(pair, baseline_state, state_b)
    )
    responses.extend(
        _build_responses_for_scenario(pair, baseline_state, state_ab)
    )

    interaction_class: Optional[str] = None
    interaction_evidence_ids: List[str] = []
    notes: List[str] = []

    if combination_rule is None:
        interaction_class = s.InteractionClass.INSUFFICIENT_EVIDENCE
        notes.append(
            "No documented combination rule exists for this "
            "intervention pair. The combined effect cannot be "
            "classified from the individual effects alone."
        )
    else:
        interaction_class = combination_rule.get("interaction_class")
        notes.append(
            combination_rule.get("reason")
            or "A documented combination rule exists for this pair."
        )
        # The vocabulary entry may later carry evidence ids.
        # Today it does not; the field is preserved for that
        # future case.
        interaction_evidence_ids = list(
            combination_rule.get("evidence_ids") or []
        )

    interpretation = _derive_interpretation(
        combination_rule, responses
    )

    return s.ScenarioComparison(
        baseline_state_id=baseline_state.state_id,
        scenarios=[baseline_state, state_a, state_b, state_ab],
        responses=responses,
        overall_interpretation=interpretation,
        interaction_class=interaction_class,
        interaction_evidence_ids=interaction_evidence_ids,
        reasoning=(
            "Four-scenario comparison of the disease baseline, "
            "intervention A alone, intervention B alone, and the "
            "combination. The combination classification is "
            "reported only when a documented combination rule "
            "exists for the intervention pair; the individual "
            "effects are never summed to produce a combined "
            "response."
        ),
        notes=notes,
        metadata={
            "workflow": "combination_treatment_simulation",
            "intervention_a_id": intervention_a.id,
            "intervention_b_id": intervention_b.id,
            "rule_present": combination_rule is not None,
            "rule": combination_rule or None,
        },
    )
