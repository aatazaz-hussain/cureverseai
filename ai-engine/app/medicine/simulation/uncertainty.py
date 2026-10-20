"""
CureVerseAI — Medicine domain
Uncertainty helpers.

Small pure functions for building and combining
``schemas.Uncertainty`` records consistently.

Design constraints:

    - Uncertainty is a CATEGORY, not a score. There is no
      numeric aggregation anywhere in this module.

    - Levels are the four documented in schemas.Uncertainty:
      ``low``, ``medium``, ``high``, ``unknown``.

    - ``combine`` merges by taking the highest-severity level
      present, never by averaging, weighting, or summing.

    - Reasons and sources are preserved verbatim; combining
      deduplicates but never paraphrases.

    - No fabricated values. An uncertainty built from a
      SourceStatus whose only information is "reachable=False"
      says exactly that, with the underlying error string
      included as a reason.
"""

from __future__ import annotations

from typing import Iterable, List, Optional

from app.medicine.simulation import schemas as s


#: Severity ordering. Higher number = more severe.
#: ``unknown`` sits between ``low`` and ``medium`` because
#: "we could not evaluate" is worse than a positive low
#: confidence but milder than a concrete medium caveat.
_SEVERITY = {
    "low": 1,
    "unknown": 2,
    "medium": 3,
    "high": 4,
}


def _max_level(levels: Iterable[str]) -> str:
    """
    Return the highest-severity level from an iterable.
    Defaults to ``unknown`` when the iterable is empty or
    contains only unrecognised strings.
    """
    best = "unknown"
    best_rank = _SEVERITY[best]

    for level in levels:
        rank = _SEVERITY.get(level)
        if rank is not None and rank > best_rank:
            best = level
            best_rank = rank

    return best


def _dedupe_preserving_order(items: Iterable[str]) -> List[str]:
    """
    Deduplicate a list of strings, preserving first-seen
    order. Empty strings and None are dropped.
    """
    seen = set()
    out: List[str] = []

    for item in items or []:
        if not item:
            continue
        text = str(item)
        if text in seen:
            continue
        seen.add(text)
        out.append(text)

    return out


# ---------------------------------------------------------------------------
# From SourceStatus
# ---------------------------------------------------------------------------


def from_source_status(
    status: s.SourceStatus,
    default_reasons: Optional[List[str]] = None,
) -> s.Uncertainty:
    """
    Build an Uncertainty from a single SourceStatus.

    Mapping:

        reachable=False                       -> high
        reachable=True, returned_records=0    -> unknown
        reachable=True, returned_records>0    -> low

    ``default_reasons`` are prepended to the reasons list
    when provided; they let a caller contextualise the
    uncertainty ("this indicator relies on this source") while
    keeping the source-derived reasons intact.
    """
    reasons: List[str] = list(default_reasons or [])
    sources: List[str] = [status.source] if status.source else []

    if not status.reachable:
        level = "high"
        if status.error:
            reasons.append(
                f"Source unreachable: {status.error}"
            )
        else:
            reasons.append("Source unreachable.")
    elif status.returned_records == 0:
        level = "unknown"
        reasons.append(
            "Source answered with no matching records."
        )
    else:
        level = "low"
        reasons.append(
            f"Source returned {status.returned_records} "
            f"record(s)."
        )

    return s.Uncertainty(
        level=level,
        reasons=_dedupe_preserving_order(reasons),
        sources=_dedupe_preserving_order(sources),
    )


# ---------------------------------------------------------------------------
# Combine
# ---------------------------------------------------------------------------


def combine(
    uncertainties: Iterable[Optional[s.Uncertainty]],
) -> s.Uncertainty:
    """
    Merge a list of Uncertainties into one.

    Level = highest severity present.
    Reasons and sources = union, deduplicated, order preserved.

    ``None`` entries are skipped. An empty or all-None input
    returns an ``unknown`` level with no reasons, which is the
    honest answer ("we did not evaluate this").
    """
    level_inputs: List[str] = []
    all_reasons: List[str] = []
    all_sources: List[str] = []

    for u in uncertainties or []:
        if u is None:
            continue
        level_inputs.append(u.level)
        all_reasons.extend(u.reasons or [])
        all_sources.extend(u.sources or [])

    if not level_inputs:
        return s.Uncertainty(
            level="unknown",
            reasons=[],
            sources=[],
        )

    return s.Uncertainty(
        level=_max_level(level_inputs),
        reasons=_dedupe_preserving_order(all_reasons),
        sources=_dedupe_preserving_order(all_sources),
    )


# ---------------------------------------------------------------------------
# From evidence method
# ---------------------------------------------------------------------------


def from_evidence_method(
    method: str,
    evidence_ids: Optional[List[str]] = None,
    sources: Optional[List[str]] = None,
    extra_reasons: Optional[List[str]] = None,
) -> s.Uncertainty:
    """
    Return the default Uncertainty for a given ResponseMethod.

    Mapping:

        OBSERVED                -> low
        MODEL_PREDICTED         -> medium
        MECHANISTIC_INFERENCE   -> medium
        INSUFFICIENT            -> unknown

    ``extra_reasons`` are appended to the default reason so a
    caller can add method-specific caveats (model name,
    pathway provenance, etc.) without losing the default
    explanation.

    ``evidence_ids`` are counted, not inspected. The count is
    turned into a short reason when positive; the ids
    themselves are not repeated here because they already
    live on the Response or IndicatorValue.
    """
    reasons: List[str] = list(extra_reasons or [])

    if method == s.ResponseMethod.OBSERVED:
        level = "low"
        reasons.append(
            "Response is reported by an identified source."
        )
    elif method == s.ResponseMethod.MODEL_PREDICTED:
        level = "medium"
        reasons.append(
            "Response is model-predicted; its assumptions and "
            "validation status should be consulted."
        )
    elif method == s.ResponseMethod.MECHANISTIC_INFERENCE:
        level = "medium"
        reasons.append(
            "Response is inferred from a curated mechanistic "
            "link, not measured for this disease context."
        )
    else:
        level = "unknown"
        reasons.append(
            "No defensible response method was available for "
            "this indicator."
        )

    if evidence_ids:
        reasons.append(
            f"Grounded in {len(evidence_ids)} evidence "
            f"record(s)."
        )

    return s.Uncertainty(
        level=level,
        reasons=_dedupe_preserving_order(reasons),
        sources=_dedupe_preserving_order(sources or []),
    )
