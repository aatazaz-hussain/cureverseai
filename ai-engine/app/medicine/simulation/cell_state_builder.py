"""
CureVerseAI — Medicine domain
Cell-state builder.

Builds the two foundational biological states of a Medicine
simulation:

    - the healthy reference state
    - the disease-associated state

Both use the SAME indicator set, drawn from the curated
function_vocabulary, so that the two states are comparable by
construction rather than by convention.

This module does not call external sources directly. It
consumes:

    - the curated vocabulary pair (function_vocabulary)
    - the Open Targets disease-target payload
      (evidence_integrator.fetch_disease_targets)
    - the Reactome pathway-metadata payload
      (evidence_integrator.fetch_pathway_metadata)

and produces the shared-contract dataclasses.

Design constraints (locked from the Medicine specification
and Phase 3 decisions):

    1. No numeric health score. No magnitude. No fabricated
       reference value. Reference values are absent because
       the current source stack does not supply validated
       reference measurements for these indicators. The
       absence is stated in the healthy state's notes.

    2. Direction of change is assigned only by
       mechanistic inference from a CURATED pathway link.
       The result is labelled:

           direction     : increase | decrease
           method        : mechanistic_inference
           uncertainty   : medium

       Every inferred direction carries the Reactome
       evidence_id for the pathway that grounds it.

    3. Indicators whose curated pathways did not resolve are
       returned with:

           direction     : unknown
           method        : insufficient

       No default direction is applied. Unknown is the
       answer, not a placeholder.

    4. Every evidence record carries a real source and (where
       available) a stable identifier and URL.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from app.medicine.simulation import schemas as s


# ---------------------------------------------------------------------------
# State-id helper
# ---------------------------------------------------------------------------


def build_state_id(
    run_id: str,
    kind: str,
    intervention_id: Optional[str] = None,
    intervention_b_id: Optional[str] = None,
) -> str:
    """
    Return the flat state_id string for a given kind of state.

    Forms:

        <run_id>::healthy_reference
        <run_id>::disease
        <run_id>::intervention::<intervention_id>
        <run_id>::combination::<intervention_a>::<intervention_b>

    The form is stable and used by every workflow so that a
    baseline in W01 and a scenario in W02 or W03 align.
    """
    if kind == s.StateKind.HEALTHY_REFERENCE:
        return f"{run_id}::healthy_reference"

    if kind == s.StateKind.DISEASE:
        return f"{run_id}::disease"

    if kind == s.StateKind.INTERVENTION_SINGLE:
        if not intervention_id:
            raise ValueError(
                "intervention_id is required for a single-"
                "intervention state."
            )
        return f"{run_id}::intervention::{intervention_id}"

    if kind == s.StateKind.INTERVENTION_COMBINATION:
        if not intervention_id or not intervention_b_id:
            raise ValueError(
                "both intervention ids are required for a "
                "combination state."
            )
        return (
            f"{run_id}::combination::"
            f"{intervention_id}::{intervention_b_id}"
        )

    raise ValueError(f"Unknown state kind: {kind}")


# ---------------------------------------------------------------------------
# Evidence construction helpers
# ---------------------------------------------------------------------------


def _pathway_evidence(
    pathway_id: str,
    pathway_meta: Dict[str, Any],
) -> s.MedicineEvidence:
    """
    Build a MedicineEvidence record for one resolved Reactome
    pathway.
    """
    display = pathway_meta.get("display_name") or pathway_id
    species = pathway_meta.get("species_name") or ""

    description = (
        f"Reactome pathway '{display}'"
        + (f" ({species})" if species else "")
        + "."
    )

    go_bp = pathway_meta.get("go_biological_process") or {}
    go_acc = go_bp.get("accession")

    url = (
        f"https://reactome.org/content/detail/{pathway_id}"
    )

    identifiers: Dict[str, str] = {"reactome": pathway_id}
    if go_acc:
        identifiers["go_biological_process"] = f"GO:{go_acc}"

    return s.MedicineEvidence(
        evidence_id=f"ev:reactome:{pathway_id}",
        source="Reactome",
        description=description,
        evidence_level="contextual",
        support_class=None,
        provenance=s.ProvenanceRecord(
            source="Reactome",
            source_id=pathway_id,
            source_type="pathway_database",
            url=url,
        ),
        identifiers=identifiers,
        metadata={
            "species": species,
            "review_status": pathway_meta.get("review_status"),
            "release_date": pathway_meta.get("release_date"),
            "literature_count": pathway_meta.get("literature_count"),
        },
    )


#: Open Targets datatype categories that we treat as
#: disease-relevant for target-level evidence. Categories not
#: listed here are still carried in the raw payload but do not
#: produce a MedicineEvidence record, to keep the evidence list
#: focused.
_DISEASE_RELEVANT_DATATYPES = {
    "genetic_association",
    "clinical",
    "animal_model",
    "somatic_mutation",
    "affected_pathway",
}


def _target_evidence(
    row: Dict[str, Any],
    disease_ref: s.DiseaseRef,
) -> Optional[s.MedicineEvidence]:
    """
    Build a MedicineEvidence record for one disease-associated
    target row from Open Targets, when the row carries at
    least one disease-relevant datatype category.

    Returns None if the row has no disease-relevant category.
    """
    symbol = row.get("approved_symbol")
    target_id = row.get("target_id")
    if not symbol or not target_id:
        return None

    dt_ids = [
        dt.get("id") for dt in row.get("datatype_scores") or []
        if dt.get("id")
    ]
    relevant = [d for d in dt_ids if d in _DISEASE_RELEVANT_DATATYPES]
    if not relevant:
        return None

    name = row.get("approved_name") or symbol
    disease_name = disease_ref.name if disease_ref else "the disease"

    description = (
        f"{name} ({symbol}) is associated with {disease_name} "
        f"via Open Targets evidence categories: "
        f"{', '.join(sorted(relevant))}."
    )

    return s.MedicineEvidence(
        evidence_id=f"ev:ot:target:{target_id}",
        source="Open Targets",
        description=description,
        evidence_level="association",
        support_class=None,
        provenance=s.ProvenanceRecord(
            source="Open Targets",
            source_id=target_id,
            source_type="target_disease_association",
            url=(
                f"https://platform.opentargets.org/target/"
                f"{target_id}"
            ),
        ),
        identifiers={
            "ensembl_gene": target_id,
            "approved_symbol": symbol,
        },
        metadata={
            "datatype_categories": sorted(relevant),
        },
    )


# ---------------------------------------------------------------------------
# Indicator construction
# ---------------------------------------------------------------------------


def build_indicators(
    pair: Dict[str, Any],
) -> List[s.FunctionalIndicator]:
    """
    Convert the curated vocabulary indicators for a pair into
    the shared-contract FunctionalIndicator dataclasses.

    Deterministic. No network. No numeric values. Every
    indicator keeps its curated direction_of_benefit and its
    source-of-truth name (the source that will substantiate
    it at runtime, if the source exists in the current stack).

    ``measurement`` is always None here: a reference
    measurement would have to come from a validated source,
    which the current stack does not provide.
    """
    if not pair:
        return []

    out: List[s.FunctionalIndicator] = []

    for entry in pair.get("indicators", []):
        ind = s.FunctionalIndicator(
            id=entry.get("id"),
            name=entry.get("name"),
            direction_of_benefit=entry.get(
                "direction_of_benefit",
                s.DirectionOfBenefit.QUALITATIVE_ONLY,
            ),
            unit=entry.get("unit"),
            description=entry.get("description"),
            evidence_level=entry.get("evidence_level"),
            measurement=None,
            metadata={
                "curated_source": entry.get("source"),
                "pathway_links": list(
                    entry.get("pathway_links") or []
                ),
            },
        )
        out.append(ind)

    return out


# ---------------------------------------------------------------------------
# State construction
# ---------------------------------------------------------------------------


def build_healthy_reference_state(
    run_id: str,
    pair: Dict[str, Any],
) -> s.BiologicalState:
    """
    Build the healthy reference state.

    Every indicator is returned with:

        direction : unknown
        method    : insufficient

    because the current source stack does not provide a
    validated numeric or directional reference for these
    indicators. The notes list states this explicitly. The
    state is not empty: it carries the SAME indicator set as
    the disease state so that the two states are directly
    comparable.

    A future phase that adds a validated reference source
    changes only this function.
    """
    state = s.BiologicalState(
        state_id=build_state_id(
            run_id, s.StateKind.HEALTHY_REFERENCE
        ),
        kind=s.StateKind.HEALTHY_REFERENCE,
        run_id=run_id,
        intervention_ref=None,
        intervention_b_ref=None,
        evidence_ids=[],
        notes=[
            "Reference (healthy) values are not provided by the "
            "current source stack. Indicator directions are "
            "reported as unknown rather than invented.",
        ],
        metadata={
            "cell_context_id": pair.get("cell_context_id") if pair else None,
            "cell_context_name": pair.get("cell_context_name") if pair else None,
        },
    )

    if not pair:
        return state

    for entry in pair.get("indicators", []):
        ind_id = entry.get("id")
        if not ind_id:
            continue

        state.indicator_values[ind_id] = s.IndicatorValue(
            indicator_id=ind_id,
            direction=s.ResponseDirection.UNKNOWN,
            method=s.ResponseMethod.INSUFFICIENT,
            qualitative_label=None,
            measurement=None,
            evidence_ids=[],
            uncertainty=s.Uncertainty(
                level="unknown",
                reasons=[
                    "No validated reference measurement is "
                    "available for this indicator in the "
                    "current source stack.",
                ],
                sources=[],
            ),
            notes=[],
        )

    return state


def build_disease_state(
    run_id: str,
    pair: Dict[str, Any],
    disease_ref: s.DiseaseRef,
    disease_targets_payload: Dict[str, Any],
    pathway_metadata: Dict[str, Dict[str, Any]],
    disease_class_directions: Optional[Dict[str, Dict[str, Any]]] = None,
) -> Tuple[s.BiologicalState, List[s.MedicineEvidence]]:
    """
    Build the disease-associated state.

    Direction of change is assigned ONLY by mechanistic
    inference from a resolved curated pathway link:

        - if at least one curated pathway for the indicator
          resolved AND its direction_of_benefit is
          lower_better → direction = increase
        - if at least one curated pathway for the indicator
          resolved AND its direction_of_benefit is
          higher_better → direction = decrease
        - optimal_range and qualitative_only indicators are
          reported as unknown even when a pathway resolved,
          because direction of benefit is context-dependent.

    Every inferred direction is labelled method =
    mechanistic_inference, uncertainty = medium, and carries
    the Reactome evidence_ids for the pathways that grounded
    it.

    The second return value is the list of MedicineEvidence
    records produced here: one per resolved pathway used, and
    one per disease-associated target from Open Targets with a
    disease-relevant evidence category.
    """
    evidence_records: List[s.MedicineEvidence] = []
    seen_evidence_ids: set = set()

    def _add_evidence(ev: Optional[s.MedicineEvidence]) -> None:
        if ev is None:
            return
        if ev.evidence_id in seen_evidence_ids:
            return
        seen_evidence_ids.add(ev.evidence_id)
        evidence_records.append(ev)

    # --- Pathway evidence, once per resolved pathway ---
    for pid, meta in (pathway_metadata or {}).items():
        _add_evidence(_pathway_evidence(pid, meta))

    # --- Target evidence, top N ---
    top_targets = (disease_targets_payload or {}).get("rows") or []
    for row in top_targets[:10]:
        _add_evidence(_target_evidence(row, disease_ref))

    state = s.BiologicalState(
        state_id=build_state_id(run_id, s.StateKind.DISEASE),
        kind=s.StateKind.DISEASE,
        run_id=run_id,
        intervention_ref=None,
        intervention_b_ref=None,
        evidence_ids=[ev.evidence_id for ev in evidence_records],
        notes=[
            "Disease-state directions are reported as "
            "mechanistic inferences from curated pathway "
            "links, not as experimentally measured values.",
        ],
        metadata={
            "cell_context_id": pair.get("cell_context_id") if pair else None,
            "cell_context_name": pair.get("cell_context_name") if pair else None,
            "resolved_pathways": sorted(
                list((pathway_metadata or {}).keys())
            ),
            "disease_target_count": int(
                (disease_targets_payload or {}).get("count") or 0
            ),
            "disease_targets_sampled": len(
                (disease_targets_payload or {}).get("rows") or []
            ),
        },
    )

    if not pair:
        return state, evidence_records

    # --- Indicator values ---
    for entry in pair.get("indicators", []):
        ind_id = entry.get("id")
        if not ind_id:
            continue

        direction_of_benefit = entry.get(
            "direction_of_benefit",
            s.DirectionOfBenefit.QUALITATIVE_ONLY,
        )
        pathway_links: List[str] = list(
            entry.get("pathway_links") or []
        )

        resolved_links = [
            pid for pid in pathway_links
            if pid in (pathway_metadata or {})
        ]

        if not resolved_links:
            state.indicator_values[ind_id] = s.IndicatorValue(
                indicator_id=ind_id,
                direction=s.ResponseDirection.UNKNOWN,
                method=s.ResponseMethod.INSUFFICIENT,
                qualitative_label=None,
                measurement=None,
                evidence_ids=[],
                uncertainty=s.Uncertainty(
                    level="unknown",
                    reasons=[
                        "No curated pathway for this indicator "
                        "resolved in Reactome.",
                    ],
                    sources=["Reactome"],
                ),
                notes=[],
            )
            continue

        # Direction inference.
        #
        # Priority:
        #   1. If the indicator has a curated direction of
        #      benefit (lower_better / higher_better), that
        #      unambiguously determines the disease direction.
        #   2. Otherwise, if a disease-class direction was
        #      derived for this indicator's name (from the
        #      resolver), use that.
        #   3. Otherwise, unknown.
        #
        # Every derived direction carries its provenance in
        # the resulting IndicatorValue's metadata so a reader
        # can see why the direction was set.

        direction_provenance: Optional[str] = None

        if direction_of_benefit == s.DirectionOfBenefit.LOWER_BETTER:
            direction = s.ResponseDirection.INCREASE
            direction_provenance = (
                "Direction derived from the indicator's curated "
                "direction_of_benefit (lower is better)."
            )
        elif direction_of_benefit == s.DirectionOfBenefit.HIGHER_BETTER:
            direction = s.ResponseDirection.DECREASE
            direction_provenance = (
                "Direction derived from the indicator's curated "
                "direction_of_benefit (higher is better)."
            )
        else:
            # Fallback: disease-class-derived direction, if any.
            class_dir = None
            if disease_class_directions:
                entry = disease_class_directions.get(
                    entry.get("name") if isinstance(entry, dict) else None
                )
                if entry:
                    class_dir = entry.get("direction")
                    direction_provenance = entry.get("provenance")

            if class_dir and class_dir != s.ResponseDirection.UNKNOWN:
                direction = class_dir
            else:
                direction = s.ResponseDirection.UNKNOWN
                direction_provenance = None

        evidence_ids = [
            f"ev:reactome:{pid}" for pid in resolved_links
        ]

        notes = []
        if direction_provenance:
            notes.append(direction_provenance)

        state.indicator_values[ind_id] = s.IndicatorValue(
            indicator_id=ind_id,
            direction=direction,
            method=s.ResponseMethod.MECHANISTIC_INFERENCE,
            qualitative_label=(
                "pathway-implied change"
                if direction != s.ResponseDirection.UNKNOWN
                else None
            ),
            measurement=None,
            evidence_ids=evidence_ids,
            uncertainty=s.Uncertainty(
                level="medium",
                reasons=[
                    "Direction inferred from a curated "
                    "pathway link; not experimentally "
                    "measured for this disease context.",
                ],
                sources=["Reactome"],
            ),
            notes=notes,
        )

    return state, evidence_records
