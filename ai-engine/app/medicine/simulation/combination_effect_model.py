"""
CureVerseAI — Medicine domain
Combination effect model.

Extends medicine_effect_model to two interventions applied
together. For every function the disease perturbs, computes:

    A alone       — via medicine_effect_model
    B alone       — via medicine_effect_model
    A + B combined — via the combination rules below

The combination rule combines the two single-medicine states
into a combined state, per function:

    restored + restored, same pathway      -> overlapping
    restored + restored, different paths   -> restored
    restored + worsened (or vice versa)    -> conflicting
    restored + unchanged                   -> restored
    worsened + unchanged                   -> worsened
    unchanged + unchanged                  -> unchanged
    any unknown on either side             -> unknown

The ranking across scenarios (baseline, A, B, A+B) is derived
from the counts of restored, conflicting, worsened functions.

Nothing is fabricated. Every combined state carries the
underlying chains from both medicines.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Tuple

from app.medicine.simulation import schemas as s
from app.medicine.simulation import medicine_effect_model as mem


COMBINATION_MODEL_VERSION = "med-combo-v1"


# ---------------------------------------------------------------------------
# Combined state rule
# ---------------------------------------------------------------------------


def _combine_states(
    a_state: str,
    b_state: str,
    a_pathways: Set[str],
    b_pathways: Set[str],
) -> Tuple[str, str]:
    """
    Return (combined_state, reason) from the two per-medicine
    states and their intersecting pathways.

    Rule as documented in the module docstring.
    """
    # Unknown handling.
    #
    # A directional state (restored / worsened) on one side
    # survives an unknown state on the other side. Only when
    # both sides are unknown, or one side is unknown and the
    # other is unchanged, is the combination unknown.
    a_unknown = a_state == "unknown"
    b_unknown = b_state == "unknown"

    if a_unknown and b_unknown:
        return "unknown", (
            "Neither medicine's direction on this function "
            "could be established."
        )

    # directional side wins over unknown
    if a_unknown and b_state in ("restored", "worsened"):
        return b_state, (
            "One medicine's direction on this function could "
            "not be established; the other medicine's state "
            "is carried forward."
        )
    if b_unknown and a_state in ("restored", "worsened"):
        return a_state, (
            "One medicine's direction on this function could "
            "not be established; the other medicine's state "
            "is carried forward."
        )

    # unknown + unchanged -> unknown
    if a_unknown or b_unknown:
        return "unknown", (
            "At least one medicine's direction on this function "
            "could not be established, and the other medicine "
            "does not touch it."
        )

    # Both unchanged.
    if a_state == "unchanged" and b_state == "unchanged":
        return "unchanged", (
            "Neither medicine's mechanism touches this function's "
            "pathways."
        )

    # Both restore.
    if a_state == "restored" and b_state == "restored":
        if a_pathways and b_pathways and a_pathways == b_pathways:
            return "overlapping", (
                "Both medicines restore this function via the "
                "same pathway. The combined effect is not additive."
            )
        return "restored", (
            "Both medicines restore this function via different "
            "pathways. The combined effect is additive."
        )

    # Both worsen.
    if a_state == "worsened" and b_state == "worsened":
        return "worsened", (
            "Both medicines worsen this function."
        )

    # Conflicting.
    if (a_state == "restored" and b_state == "worsened") or (
        a_state == "worsened" and b_state == "restored"
    ):
        return "conflicting", (
            "One medicine restores this function while the other "
            "worsens it. The combined effect is ambiguous."
        )

    # One restores, one unchanged.
    if a_state == "restored" and b_state == "unchanged":
        return "restored", (
            "One medicine restores this function; the other does "
            "not touch it."
        )
    if a_state == "unchanged" and b_state == "restored":
        return "restored", (
            "One medicine restores this function; the other does "
            "not touch it."
        )

    # One worsens, one unchanged.
    if a_state == "worsened" and b_state == "unchanged":
        return "worsened", (
            "One medicine worsens this function; the other does "
            "not touch it."
        )
    if a_state == "unchanged" and b_state == "worsened":
        return "worsened", (
            "One medicine worsens this function; the other does "
            "not touch it."
        )

    # Fallback — should not happen with the current state set.
    return "unknown", (
        f"Combination of states '{a_state}' and '{b_state}' is "
        "not covered by the current rule set."
    )


# ---------------------------------------------------------------------------
# Ranking across scenarios
# ---------------------------------------------------------------------------


def _rank_scenarios(
    scenario_summaries: Dict[str, Dict[str, int]],
) -> Dict[str, Any]:
    """
    Given a dict of {scenario_id: summary_dict}, return the
    ranking and the overall interpretation.

    Ranking key: (restored_count, -conflicting_count,
                  -worsened_count) — larger is better.

    Overall interpretation:
        any conflicting > 0   -> potentially_adverse
        all restored == 0     -> no_defensible_winner
        otherwise             -> best_supported for the top
                                 scenario, promising_uncertain
                                 for the others.
    """
    ranked = []
    for sid, summ in scenario_summaries.items():
        restored = summ.get("restored_count", 0)
        conflicting = summ.get("conflicting_count", 0)
        worsened = summ.get("worsened_count", 0)
        ranked.append({
            "scenario_id": sid,
            "restored_count": restored,
            "conflicting_count": conflicting,
            "worsened_count": worsened,
            "unchanged_count": summ.get("unchanged_count", 0),
            "unknown_count": summ.get("unknown_count", 0),
            "total_functions": summ.get("total_functions", 0),
            "key": (restored, -conflicting, -worsened),
        })

    ranked.sort(key=lambda x: x["key"], reverse=True)
    for r in ranked:
        r.pop("key", None)

    any_conflicting = any(r["conflicting_count"] > 0 for r in ranked)
    no_restored = all(r["restored_count"] == 0 for r in ranked)

    if any_conflicting:
        overall = "potentially_adverse"
    elif no_restored:
        overall = "no_defensible_winner"
    else:
        overall = "promising_uncertain"

    return {
        "ranking": ranked,
        "overall_interpretation": overall,
    }


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def compute_combination_effect(
    result: s.SimulationResult,
    intervention_a: s.InterventionRef,
    intervention_b: s.InterventionRef,
) -> Dict[str, Any]:
    """
    Compute the four-scenario effect of applying both
    interventions to the disease.

    Returns a structured dict:

        version                  — model version
        intervention_a_id/name
        intervention_b_id/name
        per_function             — one entry per indicator with
                                   a_state, b_state, combined_state,
                                   and both medicine chains
        summaries                — {A, B, A+B} counts
        ranking                  — ordered list of scenarios
        overall_interpretation   — best_supported | promising_uncertain
                                   | no_defensible_winner
                                   | potentially_adverse

    Never raises.
    """
    effect_a = mem.compute_medicine_effect(result, intervention_a)
    effect_b = mem.compute_medicine_effect(result, intervention_b)

    # Index per-function results.
    a_by_fn: Dict[str, Dict[str, Any]] = {
        f["indicator_id"]: f for f in effect_a["per_function"]
    }
    b_by_fn: Dict[str, Dict[str, Any]] = {
        f["indicator_id"]: f for f in effect_b["per_function"]
    }

    per_function: List[Dict[str, Any]] = []

    for ind in result.indicators or []:
        a_fn = a_by_fn.get(ind.id) or {
            "state": "unchanged", "medicine_chain": [],
            "intersecting_pathways": [],
        }
        b_fn = b_by_fn.get(ind.id) or {
            "state": "unchanged", "medicine_chain": [],
            "intersecting_pathways": [],
        }

        a_state = a_fn.get("state", "unchanged")
        b_state = b_fn.get("state", "unchanged")
        a_pathways = set(a_fn.get("intersecting_pathways") or [])
        b_pathways = set(b_fn.get("intersecting_pathways") or [])

        combined_state, combined_reason = _combine_states(
            a_state=a_state,
            b_state=b_state,
            a_pathways=a_pathways,
            b_pathways=b_pathways,
        )

        per_function.append({
            "indicator_id": ind.id,
            "indicator_name": ind.name,
            "a_state": a_state,
            "b_state": b_state,
            "combined_state": combined_state,
            "combined_reason": combined_reason,
            "a_chain": a_fn.get("medicine_chain", []),
            "b_chain": b_fn.get("medicine_chain", []),
        })

    def _summary_for(states: List[str]) -> Dict[str, int]:
        return {
            "restored_count": sum(1 for s_ in states if s_ == "restored"),
            "overlapping_count": sum(1 for s_ in states if s_ == "overlapping"),
            "conflicting_count": sum(1 for s_ in states if s_ == "conflicting"),
            "worsened_count": sum(1 for s_ in states if s_ == "worsened"),
            "unchanged_count": sum(1 for s_ in states if s_ == "unchanged"),
            "unknown_count": sum(1 for s_ in states if s_ == "unknown"),
            "total_functions": len(states),
        }

    summary_a = _summary_for([f["a_state"] for f in per_function])
    summary_b = _summary_for([f["b_state"] for f in per_function])
    summary_ab = _summary_for([f["combined_state"] for f in per_function])

    scenario_summaries = {
        "A_alone": summary_a,
        "B_alone": summary_b,
        "A_plus_B": summary_ab,
    }

    ranking_result = _rank_scenarios(scenario_summaries)

    return {
        "version": COMBINATION_MODEL_VERSION,
        "intervention_a_id": intervention_a.id,
        "intervention_a_name": intervention_a.name,
        "intervention_b_id": intervention_b.id,
        "intervention_b_name": intervention_b.name,
        "per_function": per_function,
        "summaries": {
            "A_alone": summary_a,
            "B_alone": summary_b,
            "A_plus_B": summary_ab,
        },
        "ranking": ranking_result["ranking"],
        "overall_interpretation": ranking_result["overall_interpretation"],
    }
