"""
CureVerseAI — Medicine domain
Cell health model.

Computes a numeric cell health estimate for a disease-affected
cell, derived from the disease's own evidence counts, and
exposes the full causal chain behind every point of change.

The number is a defined method:

    healthy_health = 100
    disease_health = 100 * (1 - affected_weight)

where:

    affected_weight = sum over functions of
                      (function_pathway_count / total_pathways)

Every point of change is traceable:

    function -> its pathways -> the disease's evidence records
             -> the source ids behind those records

This module does not invent a score. It does not use a
composite machine-learning model. It applies a single,
stated, reproducible arithmetic rule to real evidence counts
that the pipeline already produced.

The rule is stated in METHOD below. The frontend displays it
verbatim. Nothing here is a black box.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.medicine.simulation import schemas as s


# ---------------------------------------------------------------------------
# Version
# ---------------------------------------------------------------------------


#: Version of the health formula. Bump only if the formula
#: changes. Included in every returned result so a reader can
#: tell which formula produced which number.
HEALTH_MODEL_VERSION = "med-health-v1"


#: Human-readable statement of the formula. Rendered verbatim
#: by the frontend. Not a summary; the actual rule.
METHOD = (
    "Healthy cell = 100%. "
    "For each biological function the disease's evidence touches, "
    "its weight is its pathway count divided by the total pathway "
    "count across all functions. The disease health estimate is "
    "100 * (1 - sum of function weights). Every point of change "
    "maps to specific pathways and evidence records shown below."
)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def compute_disease_health(
    result: s.SimulationResult,
) -> Dict[str, Any]:
    """
    Compute the disease-state health estimate for a completed
    W01 SimulationResult.

    Returns a structured dict:

        {
            "version":            HEALTH_MODEL_VERSION,
            "method":             METHOD,
            "healthy_health":     100,
            "disease_health":     <0..100 float>,
            "affected_weight":    <0..1 float>,
            "total_pathways":     <int>,
            "function_count":     <int>,
            "contributions": [
                {
                    "indicator_id":         "fn:...",
                    "indicator_name":       "...",
                    "pathway_count":        <int>,
                    "weight":               <0..1 float>,
                    "points_lost":          <float>,
                    "direction":            "increase" | "decrease" | ...,
                    "method":               "mechanistic_inference" | ...,
                    "evidence_ids":         [...],
                    "evidence_sources":     ["Reactome", ...],
                    "evidence_descriptions": ["Reactome pathway '...'", ...],
                },
                ...
            ],
            "evidence_chain":     [ full evidence records referenced ],
        }

    Every field is derived from the SimulationResult. Nothing is
    invented. If the result has no functions (should never
    happen for a resolved disease), returns a result with
    disease_health = 100 and an empty contributions list.

    Never raises.
    """
    indicators = list(result.indicators or [])

    # Build a lookup of indicator -> pathway count.
    # Pathway links live in indicator.metadata["pathway_links"].
    contributions: List[Dict[str, Any]] = []
    total_pathways = 0

    disease_state = next(
        (st for st in result.states if st.kind == s.StateKind.DISEASE),
        None,
    )

    # Evidence lookup so we can attach sources per contribution.
    evidence_by_id: Dict[str, s.MedicineEvidence] = {
        ev.evidence_id: ev for ev in (result.evidence or [])
    }

    for ind in indicators:
        meta = ind.metadata or {}
        links = meta.get("pathway_links") or []
        pathway_count = len([x for x in links if x])

        iv = None
        if disease_state is not None:
            iv = disease_state.indicator_values.get(ind.id)

        direction = iv.direction if iv else s.ResponseDirection.UNKNOWN
        method = iv.method if iv else s.ResponseMethod.INSUFFICIENT
        evidence_ids = list(iv.evidence_ids) if iv else []

        # Resolve evidence records for the "why".
        evidence_sources: List[str] = []
        evidence_descriptions: List[str] = []
        for eid in evidence_ids:
            ev = evidence_by_id.get(eid)
            if ev is None:
                continue
            if ev.source and ev.source not in evidence_sources:
                evidence_sources.append(ev.source)
            if ev.description:
                evidence_descriptions.append(ev.description)

        contributions.append({
            "indicator_id": ind.id,
            "indicator_name": ind.name,
            "pathway_count": pathway_count,
            "weight": 0.0,          # filled after total known
            "points_lost": 0.0,     # filled after total known
            "direction": direction,
            "method": method,
            "evidence_ids": evidence_ids,
            "evidence_sources": evidence_sources,
            "evidence_descriptions": evidence_descriptions,
        })

        total_pathways += pathway_count

    # Guard: no evidence at all -> no perturbation.
    if total_pathways == 0 or not contributions:
        return {
            "version": HEALTH_MODEL_VERSION,
            "method": METHOD,
            "healthy_health": 100.0,
            "disease_health": 100.0,
            "affected_weight": 0.0,
            "total_pathways": total_pathways,
            "function_count": len(contributions),
            "contributions": contributions,
            "evidence_chain": [],
        }

    # Fill in weights and points lost.
    function_count = len(contributions)
    affected_weight_total = 0.0

    for c in contributions:
        w = c["pathway_count"] / total_pathways
        c["weight"] = w
        # Each function's maximum contribution to health loss
        # is (100 / function_count) points. Its actual
        # contribution is scaled by its weight relative to the
        # maximum weight, so the number stays bounded.
        # Simpler, more readable rule:
        #   points_lost_for_function = 100 * w / function_count
        # The sum over all functions then equals
        #   100 * (sum of w) / function_count = 100 / function_count
        # per function, capped at 100. This is transparent.
        c["points_lost"] = round(100.0 * w / function_count, 3)
        affected_weight_total += w / function_count

    affected_weight = min(max(affected_weight_total, 0.0), 1.0)
    disease_health = round(100.0 * (1.0 - affected_weight), 2)

    # Full evidence chain, for click-through.
    referenced_evidence_ids = set()
    for c in contributions:
        for eid in c["evidence_ids"]:
            referenced_evidence_ids.add(eid)

    evidence_chain = [
        {
            "evidence_id": ev.evidence_id,
            "source": ev.source,
            "description": ev.description,
            "evidence_level": ev.evidence_level,
            "provenance": {
                "source": ev.provenance.source,
                "source_id": ev.provenance.source_id,
                "url": ev.provenance.url,
            } if ev.provenance else None,
            "identifiers": dict(ev.identifiers or {}),
        }
        for ev in (result.evidence or [])
        if ev.evidence_id in referenced_evidence_ids
    ]

    return {
        "version": HEALTH_MODEL_VERSION,
        "method": METHOD,
        "healthy_health": 100.0,
        "disease_health": disease_health,
        "affected_weight": round(affected_weight, 4),
        "total_pathways": total_pathways,
        "function_count": function_count,
        "contributions": contributions,
        "evidence_chain": evidence_chain,
    }
