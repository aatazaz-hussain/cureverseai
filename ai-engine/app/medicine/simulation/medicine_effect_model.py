"""
CureVerseAI — Medicine domain
Medicine effect model.

Given a disease SimulationResult and a resolved intervention,
compute how the medicine's documented mechanism affects each
function the disease perturbs.

The model produces a per-function state:

    restored           — the medicine's mechanism opposes the
                         disease's perturbation of this
                         function along documented pathways.
    partially_restored — the medicine touches an upstream
                         pathway but the direct link to the
                         function is indirect.
    unchanged          — the medicine's mechanism does not
                         touch this function's pathways.
    worsened           — the medicine's mechanism reinforces
                         the disease's perturbation.
    unknown            — the medicine touches this function's
                         pathway but the direction cannot be
                         established from the available
                         evidence.

Every state carries the full chain:

    function -> disease pathways -> medicine pathways
             -> medicine target -> action type

Nothing is fabricated. Every state derives from an
intersection of real Reactome pathways with real ChEMBL
mechanism records.

No numeric score. No composite health number. The state is
the answer.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Tuple

from app.medicine.simulation import schemas as s


# ---------------------------------------------------------------------------
# Version
# ---------------------------------------------------------------------------


EFFECT_MODEL_VERSION = "med-effect-v1"


# ---------------------------------------------------------------------------
# Direction mapping
# ---------------------------------------------------------------------------


#: ChEMBL action types that decrease the target's activity.
_BLOCKING_ACTIONS = frozenset({
    "ANTAGONIST",
    "INHIBITOR",
    "BLOCKER",
    "NEGATIVE ALLOSTERIC MODULATOR",
    "INVERSE AGONIST",
    "DEGRADER",
})

#: ChEMBL action types that increase the target's activity.
_ACTIVATING_ACTIONS = frozenset({
    "AGONIST",
    "ACTIVATOR",
    "POSITIVE ALLOSTERIC MODULATOR",
    "OPENER",
    "STABILISER",
})


# ---------------------------------------------------------------------------
# Reactome pathway fetch per target
# ---------------------------------------------------------------------------


def _top_level_for_pathway(
    reactome_st_id: str,
) -> Optional[str]:
    """
    Return the top-level Reactome event that contains this
    pathway. Uses get_event_ancestors and reads the last entry
    of the returned chain.

    Returns None on any failure or if the chain is empty.
    Never raises.
    """
    if not reactome_st_id:
        return None
    try:
        from app.data.sources.reactome import ReactomeClient
        rc = ReactomeClient()
        chain = rc.get_event_ancestors(reactome_st_id)
    except Exception:
        return None
    if not chain:
        return None
    top = chain[-1]
    if isinstance(top, dict):
        return top.get("display_name")
    return None


def _fetch_pathways_for_target(
    target: s.TargetRef,
) -> Tuple[str, List[str]]:
    """
    Return (target_id, [reactome_st_id, ...]) for a single
    mechanism target.

    Uses the target's UniProt accession to ask Reactome which
    pathways the protein participates in. Never raises.
    """
    acc = (target.metadata or {}).get("uniprot_accession")
    if not acc:
        return target.id, []

    try:
        from app.data.sources.reactome import ReactomeClient
        rc = ReactomeClient()
        r = rc.get_pathways_for_protein(acc)
    except Exception:
        return target.id, []

    if not isinstance(r, dict) or not r.get("found"):
        return target.id, []

    st_ids: List[str] = []
    for pw in r.get("pathways") or []:
        if isinstance(pw, dict):
            st = pw.get("st_id")
            if st:
                st_ids.append(str(st))
    return target.id, st_ids


# ---------------------------------------------------------------------------
# Function state determination
# ---------------------------------------------------------------------------


def _state_for_function(
    disease_direction: str,
    action_types: List[str],
    has_intersection: bool,
) -> Tuple[str, str]:
    """
    Return (state, reason) for a single function.

    The rule:

      If the medicine does not touch this function's pathways:
          unchanged.

      If the medicine touches the function and any of its
      mechanism targets has a documented blocking action:
          if the disease direction is increase -> restored
          if the disease direction is decrease -> worsened
          if direction is unknown              -> unknown

      If the medicine touches the function and any of its
      mechanism targets has a documented activating action:
          reverse of the above.

      Otherwise:
          unknown.
    """
    if not has_intersection:
        return "unchanged", (
            "The medicine's mechanism targets do not participate "
            "in this function's Reactome pathways."
        )

    if not action_types:
        return "unknown", (
            "The medicine touches this function's pathways but "
            "no documented action type is available."
        )

    has_blocking = any(a in _BLOCKING_ACTIONS for a in action_types)
    has_activating = any(a in _ACTIVATING_ACTIONS for a in action_types)

    if has_blocking and not has_activating:
        if disease_direction == s.ResponseDirection.INCREASE:
            return "restored", (
                "The medicine blocks a target on this function's "
                "pathway, and the disease elevates this function. "
                "The blocking action opposes the disease's "
                "perturbation."
            )
        if disease_direction == s.ResponseDirection.DECREASE:
            return "worsened", (
                "The medicine blocks a target on this function's "
                "pathway, and the disease suppresses this "
                "function. The blocking action reinforces the "
                "disease's perturbation."
            )
        return "unknown", (
            "The medicine blocks a target on this function's "
            "pathway, but the disease's direction on this "
            "function is not established."
        )

    if has_activating and not has_blocking:
        if disease_direction == s.ResponseDirection.DECREASE:
            return "restored", (
                "The medicine activates a target on this "
                "function's pathway, and the disease suppresses "
                "this function. The activating action opposes "
                "the disease's perturbation."
            )
        if disease_direction == s.ResponseDirection.INCREASE:
            return "worsened", (
                "The medicine activates a target on this "
                "function's pathway, and the disease elevates "
                "this function. The activating action reinforces "
                "the disease's perturbation."
            )
        return "unknown", (
            "The medicine activates a target on this function's "
            "pathway, but the disease's direction on this "
            "function is not established."
        )

    return "unknown", (
        "The medicine has both blocking and activating "
        "documented actions on this function's pathways."
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def compute_medicine_effect(
    result: s.SimulationResult,
    intervention: s.InterventionRef,
) -> Dict[str, Any]:
    """
    Compute the per-function effect of an intervention on a
    disease SimulationResult.

    Returns a structured dict with:

        intervention_id      — "chembl:CHEMBL1234"
        intervention_name    — "MONTELUKAST SODIUM"
        mechanism_targets    — list of pharmacological targets
        per_function         — list of {indicator, state, chain}
        summary              — counts of each state
        version              — EFFECT_MODEL_VERSION

    Never raises. If the intervention has no mechanism targets
    or no pathway data is available, every function is
    "unchanged" with a note explaining why.
    """
    disease_state = next(
        (st for st in result.states if st.kind == s.StateKind.DISEASE),
        None,
    )

    # Which targets drive pharmacology?
    mech_targets = [
        t for t in (intervention.targets or [])
        if (t.metadata or {}).get("via") == "mechanism"
    ]

    mech_target_summary: List[Dict[str, Any]] = [
        {
            "target_id": t.id,
            "name": t.name,
            "action_type": (t.metadata or {}).get("action_type"),
            "uniprot_accession": (t.metadata or {}).get("uniprot_accession"),
        }
        for t in mech_targets
    ]

    # Fetch pathways per mechanism target in parallel.
    target_pathways: Dict[str, List[str]] = {}
    if mech_targets:
        with ThreadPoolExecutor(max_workers=6) as pool:
            futures = {
                pool.submit(_fetch_pathways_for_target, t): t
                for t in mech_targets
            }
            for fut in as_completed(futures):
                try:
                    tid, pws = fut.result()
                except Exception:
                    continue
                target_pathways[tid] = pws

    # Union of all medicine pathways (leaf ids).
    medicine_pathway_set = set()
    for pws in target_pathways.values():
        for p in pws:
            medicine_pathway_set.add(p)

    # Resolve the top-level Reactome event for every leaf
    # pathway involved on either side. Two pathways are
    # considered intersecting when they share a top-level
    # event. This is the Option B interpretation.

    def _top_levels_for(leaves):
        out = set()
        for leaf in leaves:
            top = _top_level_for_pathway(leaf)
            if top:
                out.add(top)
        return out

    medicine_top_levels = _top_levels_for(medicine_pathway_set)

    per_function: List[Dict[str, Any]] = []

    for ind in result.indicators or []:
        disease_pathways = set(
            (ind.metadata or {}).get("pathway_links") or []
        )
        disease_top_levels = _top_levels_for(disease_pathways)
        shared_top_levels = disease_top_levels & medicine_top_levels
        intersection = sorted(
            disease_pathways & medicine_pathway_set
        ) or sorted(shared_top_levels)

        iv = None
        if disease_state is not None:
            iv = disease_state.indicator_values.get(ind.id)

        disease_direction = (
            iv.direction if iv else s.ResponseDirection.UNKNOWN
        )

        # Which mechanism targets sit on any of the intersecting
        # pathways, and what do they do?
        action_types: List[str] = []
        medicine_chain: List[Dict[str, Any]] = []

        for t in mech_targets:
            t_pw = set(target_pathways.get(t.id, []))
            hit = disease_pathways & t_pw
            if not hit:
                continue
            action = (t.metadata or {}).get("action_type")
            if action:
                action_types.append(action)
            for pw in sorted(hit):
                medicine_chain.append({
                    "target_id": t.id,
                    "target_name": t.name,
                    "action_type": action,
                    "pathway": pw,
                    "uniprot_accession": (t.metadata or {}).get("uniprot_accession"),
                })

        has_intersection = bool(intersection) or bool(shared_top_levels)

        state, reason = _state_for_function(
            disease_direction=disease_direction,
            action_types=action_types,
            has_intersection=has_intersection,
        )

        per_function.append({
            "indicator_id": ind.id,
            "indicator_name": ind.name,
            "disease_direction": disease_direction,
            "state": state,
            "reason": reason,
            "intersecting_pathways": intersection,
            "shared_top_levels": sorted(shared_top_levels),
            "medicine_chain": medicine_chain,
        })

    summary = {
        "restored_count": sum(1 for f in per_function if f["state"] == "restored"),
        "partially_restored_count": sum(1 for f in per_function if f["state"] == "partially_restored"),
        "worsened_count": sum(1 for f in per_function if f["state"] == "worsened"),
        "unchanged_count": sum(1 for f in per_function if f["state"] == "unchanged"),
        "unknown_count": sum(1 for f in per_function if f["state"] == "unknown"),
        "total_functions": len(per_function),
    }

    return {
        "version": EFFECT_MODEL_VERSION,
        "intervention_id": intervention.id,
        "intervention_name": intervention.name,
        "mechanism_targets": mech_target_summary,
        "per_function": per_function,
        "summary": summary,
    }
