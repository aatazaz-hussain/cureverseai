"""
CureVerseAI — Drug Development
Workflow 03 — Therapeutic Discovery
Activity Interpreter.

Classifies already-fetched ChEMBL activity records and
produces a per-compound summary. This is the module that
must not invent potency, must not compute a composite
score, and must not treat a bound as a point estimate.

Classification vocabulary
-------------------------

    measured_potency       numeric standard_value with a
                           recognized standard_type
                           (IC50, EC50, Ki, Kd, AC50) and a
                           standard_relation of "="

    out_of_range           numeric standard_value but the
                           standard_relation is one of
                           "<", "<=", ">", ">=". The value is
                           a bound, not a point estimate.

    qualitative_activity   no numeric standard_value, but a
                           standard_text_value exists (e.g.
                           "active", "inactive",
                           "weakly active").

    observational          neither a numeric value nor a
                           text value. The record exists but
                           reports no result.

Per-compound summary
--------------------

The summary is a transparent count of records. It is NOT a
score. Specifically:

    measured_potency_count
    out_of_range_count
    qualitative_count
    observational_count
    distinct_assays
    distinct_targets
    activity_types_present
    pchembl_values_present   (boolean; ChEMBL's normalization)
    has_any_measured         (boolean)

No composite number is produced. The frontend may sort
compounds by any single count, but no combined metric
exists in this output.

pchembl_value
-------------

When ChEMBL supplies a `pchembl_value`, it is ChEMBL's own
normalization, not ours. It is passed through unchanged.
We never compute it. The record's metadata records that
the value came from ChEMBL.

Records are never dropped
-------------------------

Every input ActivityRecord produces an output ActivityRecord
in the same list. The classification only attaches a label;
it does not filter. Filtering (by assay type) happened in
compound_discovery.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.drug_development.therapeutic_discovery.schemas import (
    ActivityRecord,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


_RECOGNIZED_POTENCY_TYPES = {
    "IC50",
    "EC50",
    "Ki",
    "Kd",
    "AC50",
}

_OUT_OF_RANGE_RELATIONS = {
    "<",
    "<=",
    ">",
    ">=",
    "≤",
    "≥",
    "≤",
    "≥",
}


# ---------------------------------------------------------------------------
# Single-record classifier
# ---------------------------------------------------------------------------


def classify_record(
    record: ActivityRecord,
) -> str:
    """
    Return one of:
        "measured_potency"
        "out_of_range"
        "qualitative_activity"
        "observational"
    """

    value = record.standard_value
    text_value = record.standard_text_value
    standard_type = record.standard_type
    relation = record.standard_relation

    # Numeric?
    numeric = _is_numeric(value)

    if numeric and standard_type in _RECOGNIZED_POTENCY_TYPES:
        if relation and relation.strip() in _OUT_OF_RANGE_RELATIONS:
            return "out_of_range"
        return "measured_potency"

    if text_value:
        return "qualitative_activity"

    return "observational"


def _is_numeric(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, (int, float)):
        return True
    try:
        float(str(value).strip())
        return True
    except (TypeError, ValueError):
        return False


# ---------------------------------------------------------------------------
# Interpreter
# ---------------------------------------------------------------------------


class ActivityInterpreter:
    """
    Classify activities and produce per-compound summaries.
    """

    def __init__(self) -> None:
        pass

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def interpret(
        self,
        activities: List[ActivityRecord],
    ) -> Dict[str, Any]:
        """
        Classify records and summarize per compound.

        `activities` is the list returned by
        compound_discovery.discover()["activities"].
        """

        if not activities:
            return self._empty(
                reason="No activity records were supplied."
            )

        # ---- 1) Classify each record in place -------------
        # ActivityRecord has a metadata dict; we add the
        # classification there so the record remains intact.
        for record in activities:
            classification = classify_record(record)
            record.metadata["classification"] = classification

            # Mark pchembl provenance explicitly.
            if record.pchembl_value:
                record.metadata[
                    "pchembl_source"
                ] = "ChEMBL"

        # ---- 2) Group by compound ------------------------
        records_by_compound: Dict[
            str, List[ActivityRecord]
        ] = {}
        for record in activities:
            cid = record.compound_chembl_id
            records_by_compound.setdefault(cid, []).append(
                record
            )

        # ---- 3) Summarize --------------------------------
        summaries: Dict[str, Dict[str, Any]] = {}
        for cid, records in records_by_compound.items():
            summaries[cid] = self._summarize(cid, records)

        # ---- 4) Global counts ----------------------------
        counts = {
            "total_records": len(activities),
            "measured_potency": 0,
            "out_of_range": 0,
            "qualitative": 0,
            "observational": 0,
        }
        activity_types_seen: set[str] = set()

        for record in activities:
            classification = record.metadata.get(
                "classification", "observational"
            )
            if classification == "measured_potency":
                counts["measured_potency"] += 1
            elif classification == "out_of_range":
                counts["out_of_range"] += 1
            elif classification == "qualitative_activity":
                counts["qualitative"] += 1
            else:
                counts["observational"] += 1

            if record.standard_type:
                activity_types_seen.add(record.standard_type)

        return {
            "found": True,
            "records_by_compound": records_by_compound,
            "summaries_by_compound": summaries,
            "counts": counts,
            "reason": None,
            "metadata": {
                "compounds_summarized": len(summaries),
                "activity_types_seen": sorted(
                    activity_types_seen
                ),
            },
        }

    # ------------------------------------------------------------------
    # Per-compound summary
    # ------------------------------------------------------------------

    @staticmethod
    def _summarize(
        compound_id: str,
        records: List[ActivityRecord],
    ) -> Dict[str, Any]:
        measured = 0
        out_of_range = 0
        qualitative = 0
        observational = 0

        assays: set[str] = set()
        targets: set[str] = set()
        activity_types: set[str] = set()

        has_pchembl = False

        for r in records:
            classification = r.metadata.get(
                "classification", "observational"
            )

            if classification == "measured_potency":
                measured += 1
            elif classification == "out_of_range":
                out_of_range += 1
            elif classification == "qualitative_activity":
                qualitative += 1
            else:
                observational += 1

            if r.assay_id:
                assays.add(r.assay_id)
            if r.target_chembl_id:
                targets.add(r.target_chembl_id)
            if r.standard_type:
                activity_types.add(r.standard_type)
            if r.pchembl_value:
                has_pchembl = True

        notes: List[str] = []

        if (
            measured == 0
            and out_of_range == 0
            and qualitative == 0
        ):
            notes.append(
                "No quantitative or qualitative activity "
                "was reported for this compound against the "
                "target."
            )

        if out_of_range > 0 and measured == 0:
            notes.append(
                "Only bounds were reported (e.g. IC50 < X). "
                "No point estimate is available."
            )

        if qualitative > 0 and measured == 0:
            notes.append(
                "Only qualitative activity was reported. No "
                "numeric potency is available."
            )

        return {
            "compound_id": compound_id,
            "measured_potency_count": measured,
            "out_of_range_count": out_of_range,
            "qualitative_count": qualitative,
            "observational_count": observational,
            "distinct_assays": len(assays),
            "distinct_targets": len(targets),
            "activity_types_present": sorted(activity_types),
            "pchembl_values_present": has_pchembl,
            "has_any_measured": (
                measured > 0 or out_of_range > 0
            ),
            "notes": notes,
        }

    # ------------------------------------------------------------------
    # Empty path
    # ------------------------------------------------------------------

    @staticmethod
    def _empty(reason: str) -> Dict[str, Any]:
        return {
            "found": False,
            "records_by_compound": {},
            "summaries_by_compound": {},
            "counts": {
                "total_records": 0,
                "measured_potency": 0,
                "out_of_range": 0,
                "qualitative": 0,
                "observational": 0,
            },
            "reason": reason,
            "metadata": {
                "compounds_summarized": 0,
                "activity_types_seen": [],
            },
        }


# ---------------------------------------------------------------------------
# Convenience
# ---------------------------------------------------------------------------


def interpret_activities(
    activities: List[ActivityRecord],
) -> Dict[str, Any]:
    """
    One-shot entry point.
    """
    return ActivityInterpreter().interpret(activities)
