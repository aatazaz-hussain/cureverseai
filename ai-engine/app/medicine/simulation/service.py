"""
CureVerseAI — Medicine domain
Simulation service.

Top-level entry points for the three Medicine workflows:

    run_virtual_disease_simulation(disease, cell_type, context)
    run_treatment_simulation(disease, intervention_id, baseline_id)
    run_combination_treatment_simulation(
        disease, intervention_a_id, intervention_b_id, baseline_id
    )

Each function assembles a SimulationResult by orchestrating the
modules built for this domain:

    disease_resolver       — resolve the disease
    function_vocabulary    — look up the curated pair
    evidence_integrator    — fetch Open Targets + Reactome evidence
    cell_state_builder     — build the healthy reference and the
                             disease state
    intervention_resolver  — resolve interventions and targets
    response_model         — build W01 and W02 comparisons
    combination_model      — build the W03 four-scenario comparison
    uncertainty            — build consistent Uncertainty records

Baseline handling
-----------------

``baseline_id`` is honoured as an ASSERTION, not a stored
pointer:

    - The service recomputes the run_id from the current inputs
      and the current function_mapper_version and
      pipeline_version.
    - If the computed run_id matches the supplied baseline_id,
      the request proceeds.
    - If it does not match, the service returns a partial
      result whose limitation explains the mismatch. It does
      NOT silently fall back to a different baseline.

No persistent store of baselines exists in this phase. The
deterministic id is the reproducibility contract.

Target–disease linkage (W02 only)
---------------------------------

The specification requires W02 to check whether an
intervention's targets are relevant to the selected disease
context. ChEMBL targets and Open Targets targets use
different namespaces:

    ChEMBL target : CHEMBL1798, name "Cysteinyl leukotriene
                    receptor 1"
    Open Targets  : ENSG00000150201, approved symbol CYSLTR1

Without a cross-reference, the honest check we can perform
today is a NAME MATCH: does the ChEMBL target's name appear
(as a substring, case-insensitively) in any Open Targets
approved_symbol or approved_name for this disease?

This check is best-effort. When no match is found, the flag is
False, and W02 records the absence rather than claiming a
benefit.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from app.medicine.simulation import cell_state_builder as csb
from app.medicine.simulation import combination_model as cmb
from app.medicine.simulation import disease_resolver as dr
from app.medicine.simulation import disease_direction_resolver as ddr
from app.medicine.simulation import medicine_effect_model as mem
from app.medicine.simulation import combination_effect_model as cemb
from app.medicine.simulation import evidence_integrator as ei
from app.medicine.simulation import function_vocabulary as fv
from app.medicine.simulation import function_mapper as fm
from app.medicine.simulation import intervention_resolver as ir
from app.medicine.simulation import response_model as rm
from app.medicine.simulation import schemas as s
from app.medicine.simulation import uncertainty as unc


# ---------------------------------------------------------------------------
# Version constants
# ---------------------------------------------------------------------------


#: Pipeline version. Bump when the orchestration changes in a
#: way that changes the meaning of a result.
PIPELINE_VERSION = "med-pipe-v1"


# ---------------------------------------------------------------------------
# Run-id computation
# ---------------------------------------------------------------------------


def _compute_run_id(
    disease_id: Optional[str],
    cell_context_id: Optional[str],
) -> str:
    """
    Deterministic run_id.

    Identity = sha256 of the canonical inputs + versions.
    The human-readable prefix makes the id legible in logs.

    Same inputs + same function mapper version + same pipeline
    version → same id. That is the reproducibility contract.
    """
    disease_part = disease_id or "unknown_disease"
    cell_part = cell_context_id or "unknown_cell"

    payload = "|".join([
        disease_part,
        cell_part,
        fv.FUNCTION_MAPPER_VERSION,
        PIPELINE_VERSION,
    ])

    digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:16]

    short_disease = disease_part.split(":")[-1][:16]
    short_cell = cell_part.split(":")[-1][:16]

    return f"med:{short_disease}:{short_cell}:{digest}"


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


# ---------------------------------------------------------------------------
# Disease-class direction derivation
# ---------------------------------------------------------------------------


def _fetch_disease_ancestors(disease_ref: s.DiseaseRef) -> set:
    """
    Fetch the MONDO ancestor ids for a resolved disease from
    Open Targets. Returns an empty set on any failure.

    Used only to classify the disease into a mechanistic class
    for direction derivation. Never raises.
    """
    if not disease_ref or not disease_ref.id:
        return set()

    try:
        from app.drug_development.sources.open_targets import (
            OpenTargetsClient,
        )
        from app.drug_development.reverse_disease.utils import (
            to_opentargets_id,
        )
    except Exception:
        return set()

    query = """
    query A($efoId: String!) {
      disease(efoId: $efoId) { id ancestors }
    }
    """

    try:
        ot = OpenTargetsClient()
        r = ot.query(query, {"efoId": to_opentargets_id(disease_ref.id)})
    except Exception:
        return set()

    d = (r or {}).get("disease") or {}
    return set(d.get("ancestors") or [])


def _compute_class_directions(
    disease_ref: s.DiseaseRef,
    pair: Dict[str, Any],
) -> Dict[str, Dict[str, Any]]:
    """
    Return {function_name: {direction, provenance}} for every
    function in the pair, based on the disease's MONDO class.

    Empty dict when the disease has no class or the pair has no
    indicators. Never raises.
    """
    if not pair or not isinstance(pair, dict):
        return {}

    ancestors = _fetch_disease_ancestors(disease_ref)
    if not ancestors:
        return {}

    function_names: list = []
    for ind in pair.get("indicators") or []:
        name = ind.get("name")
        if name:
            function_names.append(name)

    if not function_names:
        return {}

    try:
        return ddr.resolve_directions(ancestors, function_names)
    except Exception:
        return {}


# ---------------------------------------------------------------------------
# Shared preparation steps
# ---------------------------------------------------------------------------


def _resolve_and_pair(
    disease: str,
    cell_type: Optional[str],
) -> Tuple[s.DiseaseRef, Optional[Dict[str, Any]], s.SourceStatus]:
    """
    Resolve the disease, look up the curated pair, and return
    the source status for the resolver call.
    """
    disease_ref, source_status = dr.resolve_disease_with_status(disease)

    pair = None
    if disease_ref.id:
        pair = fv.get_pair(disease_ref.id, cell_type)

    return disease_ref, pair, source_status


def _gather_evidence(
    pair: Dict[str, Any],
    disease_ref: s.DiseaseRef,
    target_size: int = 20,
) -> Tuple[Dict[str, Any], Dict[str, Dict[str, Any]], List[s.SourceStatus]]:
    """
    Fetch Open Targets disease-target payload and Reactome
    pathway metadata for every pathway the curated vocabulary
    attaches to any indicator of the pair.

    Returns (ot_payload, pathway_metadata, source_status_list).
    """
    ot_payload, ot_status = ei.fetch_disease_targets(
        disease_ref, size=target_size
    )

    pathway_ids: List[str] = []
    for entry in pair.get("indicators", []):
        pathway_ids.extend(entry.get("pathway_links") or [])

    pw_payload, pw_status = ei.fetch_pathway_metadata(pathway_ids)

    return ot_payload, pw_payload, [ot_status, pw_status]


def _empty_result(
    task: str,
    disease_ref: s.DiseaseRef,
    cell_context: s.CellContext,
    run_id: str,
    status: str,
    limitations: List[str],
    warnings: List[str],
    source_status: List[s.SourceStatus],
) -> s.SimulationResult:
    """
    Build a minimal SimulationResult for the case where we
    cannot proceed (missing pair, unresolved disease, etc.).

    The result is honest: it carries whatever was resolved and
    lists the reasons it could not proceed.
    """
    run = s.SimulationRun(
        run_id=run_id,
        task=task,
        disease=disease_ref,
        cell_context=cell_context,
        function_mapper_version=fv.FUNCTION_MAPPER_VERSION,
        pipeline_version=PIPELINE_VERSION,
        created_at=_now_iso(),
        status=status,
        metadata={},
    )

    return s.SimulationResult(
        run=run,
        indicators=[],
        states=[],
        comparison=None,
        evidence=[],
        source_status=source_status,
        limitations=limitations,
        warnings=warnings,
        metadata={},
    )


def _cell_context_from_pair(
    pair: Optional[Dict[str, Any]],
    override_id: Optional[str] = None,
) -> s.CellContext:
    """
    Build the CellContext from the curated pair, or a minimal
    placeholder when the pair is absent.
    """
    if pair:
        return s.CellContext(
            id=pair.get("cell_context_id") or "",
            name=pair.get("cell_context_name") or "",
            source=pair.get("cell_context_source") or "",
            ontology_id=pair.get("cell_context_id"),
            confidence=None,
            metadata={
                "ontology": pair.get("cell_context_ontology"),
                "context_notes": pair.get("context_notes"),
            },
        )

    return s.CellContext(
        id=override_id or "",
        name=override_id or "",
        source="",
        ontology_id=override_id,
        confidence=None,
        metadata={},
    )


# ---------------------------------------------------------------------------
# W01 — virtual disease simulation
# ---------------------------------------------------------------------------


def run_virtual_disease_simulation(
    disease: str,
    cell_type: Optional[str] = None,
    context: Optional[str] = None,
) -> s.SimulationResult:
    """
    W01 entry point.

    Inputs:
        disease    — free-text disease query (required)
        cell_type  — optional cell-context hint
        context    — optional additional context (currently unused
                     beyond being recorded in metadata)

    Returns a SimulationResult. Never raises for an unknown
    disease or an uncurated pair; those become partial or
    not_found statuses with explicit limitations.
    """
    if not disease or not str(disease).strip():
        raise ValueError(
            "A disease query is required for the virtual disease "
            "simulation."
        )

    disease_ref, pair, resolver_status = _resolve_and_pair(
        disease, cell_type
    )

    cell_context = _cell_context_from_pair(pair, override_id=cell_type)
    run_id = _compute_run_id(
        disease_ref.id, cell_context.id or cell_type
    )

    limitations: List[str] = []
    warnings: List[str] = []
    source_statuses: List[s.SourceStatus] = [resolver_status]

    # Disease could not be resolved at all.
    if not disease_ref.id:
        limitations.append(
            "The disease query could not be resolved to a "
            "canonical identifier. No simulation is possible "
            "without a resolved disease."
        )
        return _empty_result(
            task=s.SimulationTask.VIRTUAL_DISEASE_SIMULATION,
            disease_ref=disease_ref,
            cell_context=cell_context,
            run_id=run_id,
            status=s.SimulationStatus.NOT_FOUND,
            limitations=limitations,
            warnings=warnings,
            source_status=source_statuses,
        )

    # Disease resolved but no curated pair: derive one from the
    # disease's own Open Targets associations + Reactome pathways.
    if pair is None:
        pair, mapper_statuses = fm.derive_pair(
            disease_ref, cell_type
        )
        source_statuses.extend(mapper_statuses)

    if pair is None:
        limitations.append(
            f"Disease '{disease_ref.name}' resolved to "
            f"{disease_ref.id}, but no biological evidence could "
            "be derived for it from Open Targets or Reactome. No "
            "defensible function set is available."
        )
        return _empty_result(
            task=s.SimulationTask.VIRTUAL_DISEASE_SIMULATION,
            disease_ref=disease_ref,
            cell_context=cell_context,
            run_id=run_id,
            status=s.SimulationStatus.PARTIAL,
            limitations=limitations,
            warnings=warnings,
            source_status=source_statuses,
        )

    # --- Full pipeline ---
    ot_payload, pw_payload, extra_statuses = _gather_evidence(
        pair, disease_ref
    )
    source_statuses.extend(extra_statuses)

    indicators = csb.build_indicators(pair)
    healthy = csb.build_healthy_reference_state(run_id, pair)
    class_directions = _compute_class_directions(disease_ref, pair)
    disease_state, disease_evidence = csb.build_disease_state(
        run_id, pair, disease_ref, ot_payload, pw_payload,
        disease_class_directions=class_directions,
    )

    comparison = rm.build_w01_comparison(pair, healthy, disease_state)

    limitations.extend([
        "Reference (healthy) values are not available from the "
        "current source stack; every healthy-state indicator is "
        "reported as unknown.",
        "Disease-state directions are reported as mechanistic "
        "inferences from curated pathway links, not as "
        "experimentally measured values for this specific "
        "disease context.",
    ])

    for st in extra_statuses:
        if not st.reachable:
            warnings.append(
                f"{st.source} unreachable during this run: "
                f"{st.error}"
            )

    run = s.SimulationRun(
        run_id=run_id,
        task=s.SimulationTask.VIRTUAL_DISEASE_SIMULATION,
        disease=disease_ref,
        cell_context=cell_context,
        function_mapper_version=fv.FUNCTION_MAPPER_VERSION,
        pipeline_version=PIPELINE_VERSION,
        created_at=_now_iso(),
        status=s.SimulationStatus.SUCCESS,
        metadata={
            "requested_cell_type": cell_type,
            "requested_context": context,
        },
    )

    return s.SimulationResult(
        run=run,
        indicators=indicators,
        states=[healthy, disease_state],
        comparison=comparison,
        evidence=disease_evidence,
        source_status=source_statuses,
        limitations=limitations,
        warnings=warnings,
        metadata={
            "workflow": "virtual_disease_simulation",
            "indicator_count": len(indicators),
        },
    )


# ---------------------------------------------------------------------------
# Target–disease linkage check (W02)
# ---------------------------------------------------------------------------


def _target_disease_link_supported(
    intervention: s.InterventionRef,
    ot_payload: Dict[str, Any],
) -> bool:
    """
    Best-effort check: does any of the intervention's ChEMBL
    targets appear (by name) in the disease's Open Targets
    target list?

    Returns False by default when no match is found. This is
    the conservative choice: under-claim rather than
    over-claim.
    """
    if not intervention.targets:
        return False

    ot_rows = (ot_payload or {}).get("rows") or []
    if not ot_rows:
        return False

    haystack: List[str] = []
    for row in ot_rows:
        symbol = (row.get("approved_symbol") or "").lower()
        name = (row.get("approved_name") or "").lower()
        if symbol:
            haystack.append(symbol)
        if name:
            haystack.append(name)

    if not haystack:
        return False

    for target in intervention.targets:
        target_name = (target.name or "").lower().strip()
        if not target_name:
            continue
        # Skip obvious non-biological target placeholders that
        # ChEMBL records but that are not real biology.
        if target_name in {"unchecked", "admet", "hepatotoxicity"}:
            continue
        for entry in haystack:
            if target_name in entry or entry in target_name:
                return True

    return False


# ---------------------------------------------------------------------------
# Treatment state construction (W02 and W03)
# ---------------------------------------------------------------------------


def _build_treatment_state(
    run_id: str,
    kind: str,
    pair: Dict[str, Any],
    disease_state: s.BiologicalState,
    intervention: s.InterventionRef,
    intervention_b: Optional[s.InterventionRef] = None,
) -> s.BiologicalState:
    """
    Build a treatment state (single or combination).

    The treatment state uses the SAME indicator set as the
    disease state. Its direction values mirror the disease
    state's direction values where a curated pathway resolved,
    because the mechanistic inference is the same in the
    presence of the intervention as in the disease state:
    we do not have a validated model of the intervention's
    effect.

    The intervention reference is attached to the state so the
    frontend and downstream reasoning can display it. The
    state's notes and metadata record explicitly that the
    treatment state is NOT a simulated response, because no
    validated response model exists in this phase.

    This is the honest position and matches Phase 0's gap
    flag: without a validated model, we do not fabricate a
    treatment effect.
    """
    from copy import deepcopy

    state = deepcopy(disease_state)

    if kind == s.StateKind.INTERVENTION_COMBINATION:
        if intervention_b is None:
            raise ValueError(
                "combination state requires two interventions"
            )
        state.state_id = csb.build_state_id(
            run_id, kind, intervention.id, intervention_b.id
        )
    else:
        state.state_id = csb.build_state_id(
            run_id, kind, intervention.id
        )

    state.kind = kind
    state.intervention_ref = intervention
    state.intervention_b_ref = intervention_b

    state.notes = list(state.notes) + [
        "The treatment state currently mirrors the disease "
        "state because no validated response model is "
        "available in this phase. The intervention's resolved "
        "identity and targets are attached for reference.",
    ]
    state.metadata = dict(state.metadata)
    state.metadata["intervention_id"] = intervention.id
    if intervention_b is not None:
        state.metadata["intervention_b_id"] = intervention_b.id

    return state


# ---------------------------------------------------------------------------
# W02 — treatment simulation
# ---------------------------------------------------------------------------


def run_treatment_simulation(
    disease: str,
    intervention_id: str,
    baseline_id: Optional[str] = None,
) -> s.SimulationResult:
    """
    W02 entry point.
    """
    if not disease or not str(disease).strip():
        raise ValueError("A disease query is required.")
    if not intervention_id or not str(intervention_id).strip():
        raise ValueError("An intervention id or query is required.")

    disease_ref, pair, resolver_status = _resolve_and_pair(
        disease, None
    )

    cell_context = _cell_context_from_pair(pair)
    run_id = _compute_run_id(disease_ref.id, cell_context.id)

    # Baseline assertion.
    if baseline_id and baseline_id != run_id:
        return _baseline_mismatch_result(
            task=s.SimulationTask.TREATMENT_SIMULATION,
            disease_ref=disease_ref,
            cell_context=cell_context,
            run_id=run_id,
            requested_baseline=baseline_id,
        )

    limitations: List[str] = []
    warnings: List[str] = []
    source_statuses: List[s.SourceStatus] = [resolver_status]

    if not disease_ref.id:
        limitations.append(
            "The disease query could not be resolved to a "
            "canonical identifier."
        )
        return _empty_result(
            task=s.SimulationTask.TREATMENT_SIMULATION,
            disease_ref=disease_ref,
            cell_context=cell_context,
            run_id=run_id,
            status=s.SimulationStatus.NOT_FOUND,
            limitations=limitations,
            warnings=warnings,
            source_status=source_statuses,
        )

    if pair is None:
        pair, mapper_statuses = fm.derive_pair(
            disease_ref, None
        )
        source_statuses.extend(mapper_statuses)

    if pair is None:
        limitations.append(
            f"Disease '{disease_ref.name}' resolved to "
            f"{disease_ref.id}, but no biological evidence could "
            "be derived for it from Open Targets or Reactome."
        )
        return _empty_result(
            task=s.SimulationTask.TREATMENT_SIMULATION,
            disease_ref=disease_ref,
            cell_context=cell_context,
            run_id=run_id,
            status=s.SimulationStatus.PARTIAL,
            limitations=limitations,
            warnings=warnings,
            source_status=source_statuses,
        )

    # Resolve intervention.
    intervention, int_status = ir.resolve_intervention_with_status(
        intervention_id
    )
    source_statuses.append(int_status)

    if intervention.resolution_status != "resolved":
        limitations.append(
            f"The intervention '{intervention_id}' could not be "
            "resolved to a ChEMBL molecule."
        )
        return _empty_result(
            task=s.SimulationTask.TREATMENT_SIMULATION,
            disease_ref=disease_ref,
            cell_context=cell_context,
            run_id=run_id,
            status=s.SimulationStatus.NOT_FOUND,
            limitations=limitations,
            warnings=warnings,
            source_status=source_statuses,
        )

    # Evidence pipeline for the baseline + disease state.
    ot_payload, pw_payload, extra_statuses = _gather_evidence(
        pair, disease_ref
    )
    source_statuses.extend(extra_statuses)

    indicators = csb.build_indicators(pair)
    healthy = csb.build_healthy_reference_state(run_id, pair)
    class_directions = _compute_class_directions(disease_ref, pair)
    disease_state, disease_evidence = csb.build_disease_state(
        run_id, pair, disease_ref, ot_payload, pw_payload,
        disease_class_directions=class_directions,
    )

    # Target-disease linkage check.
    link_supported = _target_disease_link_supported(
        intervention, ot_payload
    )

    # Build the treatment state.
    treatment_state = _build_treatment_state(
        run_id=run_id,
        kind=s.StateKind.INTERVENTION_SINGLE,
        pair=pair,
        disease_state=disease_state,
        intervention=intervention,
    )

    # Build the W02 comparison.
    comparison = rm.build_w02_comparison(
        pair, disease_state, treatment_state, link_supported
    )

    limitations.extend([
        "Reference (healthy) values are not available from the "
        "current source stack.",
        "No validated response model is available; treatment "
        "state mirrors the disease state's mechanistic "
        "inferences. A beneficial response is not claimed "
        "unless the intervention's targets link to the "
        "disease context AND a directional inference exists.",
        "The target-disease link check is a best-effort name "
        "match; a missing link does not by itself prove the "
        "intervention is irrelevant.",
    ])

    for st in extra_statuses + [int_status]:
        if not st.reachable:
            warnings.append(
                f"{st.source} unreachable: {st.error}"
            )

    # Compute the per-function medicine effect using real
    # ChEMBL mechanism targets and Reactome pathway overlap.
    # Every state carries the full medicine -> target -> pathway
    # chain. Never raises; failures degrade to an empty dict.
    medicine_effect: Dict[str, Any] = {}
    try:
        medicine_effect = mem.compute_medicine_effect(
            s.SimulationResult(
                run=s.SimulationRun(
                    run_id=run_id,
                    task=s.SimulationTask.VIRTUAL_DISEASE_SIMULATION,
                    disease=disease_ref,
                    cell_context=cell_context,
                    function_mapper_version=fv.FUNCTION_MAPPER_VERSION,
                    pipeline_version=PIPELINE_VERSION,
                    created_at=_now_iso(),
                    status=s.SimulationStatus.SUCCESS,
                    metadata={},
                ),
                indicators=indicators,
                states=[healthy, disease_state],
                comparison=None,
                evidence=disease_evidence,
                source_status=source_statuses,
                limitations=[],
                warnings=[],
                metadata={},
            ),
            intervention,
        )
    except Exception as exc:
        warnings.append(
            f"Medicine effect model failed: {exc}"
        )

    run = s.SimulationRun(
        run_id=run_id,
        task=s.SimulationTask.TREATMENT_SIMULATION,
        disease=disease_ref,
        cell_context=cell_context,
        function_mapper_version=fv.FUNCTION_MAPPER_VERSION,
        pipeline_version=PIPELINE_VERSION,
        created_at=_now_iso(),
        status=s.SimulationStatus.SUCCESS,
        metadata={
            "intervention_id": intervention.id,
            "intervention_name": intervention.name,
            "link_supported": link_supported,
            "requested_baseline_id": baseline_id,
        },
    )

    return s.SimulationResult(
        run=run,
        indicators=indicators,
        states=[healthy, disease_state, treatment_state],
        comparison=comparison,
        evidence=disease_evidence,
        source_status=source_statuses,
        limitations=limitations,
        warnings=warnings,
        metadata={
            "workflow": "treatment_simulation",
            "intervention": s.to_dict(intervention),
            "medicine_effect": medicine_effect,
        },
    )


# ---------------------------------------------------------------------------
# W03 — combination treatment simulation
# ---------------------------------------------------------------------------


def run_combination_treatment_simulation(
    disease: str,
    intervention_a_id: str,
    intervention_b_id: str,
    baseline_id: Optional[str] = None,
) -> s.SimulationResult:
    """
    W03 entry point.
    """
    if not disease or not str(disease).strip():
        raise ValueError("A disease query is required.")
    if not intervention_a_id or not str(intervention_a_id).strip():
        raise ValueError("Intervention A id or query is required.")
    if not intervention_b_id or not str(intervention_b_id).strip():
        raise ValueError("Intervention B id or query is required.")

    disease_ref, pair, resolver_status = _resolve_and_pair(disease, None)
    cell_context = _cell_context_from_pair(pair)
    run_id = _compute_run_id(disease_ref.id, cell_context.id)

    if baseline_id and baseline_id != run_id:
        return _baseline_mismatch_result(
            task=s.SimulationTask.COMBINATION_TREATMENT_SIMULATION,
            disease_ref=disease_ref,
            cell_context=cell_context,
            run_id=run_id,
            requested_baseline=baseline_id,
        )

    limitations: List[str] = []
    warnings: List[str] = []
    source_statuses: List[s.SourceStatus] = [resolver_status]

    if not disease_ref.id:
        limitations.append(
            "The disease query could not be resolved to a "
            "canonical identifier."
        )
        return _empty_result(
            task=s.SimulationTask.COMBINATION_TREATMENT_SIMULATION,
            disease_ref=disease_ref,
            cell_context=cell_context,
            run_id=run_id,
            status=s.SimulationStatus.NOT_FOUND,
            limitations=limitations,
            warnings=warnings,
            source_status=source_statuses,
        )

    if pair is None:
        pair, mapper_statuses = fm.derive_pair(
            disease_ref, None
        )
        source_statuses.extend(mapper_statuses)

    if pair is None:
        limitations.append(
            f"Disease '{disease_ref.name}' resolved to "
            f"{disease_ref.id}, but no biological evidence could "
            "be derived for it from Open Targets or Reactome."
        )
        return _empty_result(
            task=s.SimulationTask.COMBINATION_TREATMENT_SIMULATION,
            disease_ref=disease_ref,
            cell_context=cell_context,
            run_id=run_id,
            status=s.SimulationStatus.PARTIAL,
            limitations=limitations,
            warnings=warnings,
            source_status=source_statuses,
        )

    # Resolve both interventions.
    intervention_a, status_a = ir.resolve_intervention_with_status(
        intervention_a_id
    )
    intervention_b, status_b = ir.resolve_intervention_with_status(
        intervention_b_id
    )
    source_statuses.extend([status_a, status_b])

    if (
        intervention_a.resolution_status != "resolved"
        or intervention_b.resolution_status != "resolved"
    ):
        unresolved = []
        if intervention_a.resolution_status != "resolved":
            unresolved.append(intervention_a_id)
        if intervention_b.resolution_status != "resolved":
            unresolved.append(intervention_b_id)
        limitations.append(
            f"One or both interventions could not be resolved: "
            f"{', '.join(unresolved)}."
        )
        return _empty_result(
            task=s.SimulationTask.COMBINATION_TREATMENT_SIMULATION,
            disease_ref=disease_ref,
            cell_context=cell_context,
            run_id=run_id,
            status=s.SimulationStatus.NOT_FOUND,
            limitations=limitations,
            warnings=warnings,
            source_status=source_statuses,
        )

    # Evidence.
    ot_payload, pw_payload, extra_statuses = _gather_evidence(
        pair, disease_ref
    )
    source_statuses.extend(extra_statuses)

    indicators = csb.build_indicators(pair)
    healthy = csb.build_healthy_reference_state(run_id, pair)
    class_directions = _compute_class_directions(disease_ref, pair)
    disease_state, disease_evidence = csb.build_disease_state(
        run_id, pair, disease_ref, ot_payload, pw_payload,
        disease_class_directions=class_directions,
    )

    state_a = _build_treatment_state(
        run_id=run_id,
        kind=s.StateKind.INTERVENTION_SINGLE,
        pair=pair,
        disease_state=disease_state,
        intervention=intervention_a,
    )
    state_b = _build_treatment_state(
        run_id=run_id,
        kind=s.StateKind.INTERVENTION_SINGLE,
        pair=pair,
        disease_state=disease_state,
        intervention=intervention_b,
    )
    state_ab = _build_treatment_state(
        run_id=run_id,
        kind=s.StateKind.INTERVENTION_COMBINATION,
        pair=pair,
        disease_state=disease_state,
        intervention=intervention_a,
        intervention_b=intervention_b,
    )

    # Curated combination rule, if any.
    rule = fv.get_combination_rule(
        intervention_a.id, intervention_b.id
    )

    comparison = cmb.build_w03_comparison(
        pair=pair,
        baseline_state=disease_state,
        state_a=state_a,
        state_b=state_b,
        state_ab=state_ab,
        intervention_a=intervention_a,
        intervention_b=intervention_b,
        combination_rule=rule,
    )

    limitations.extend([
        "Reference (healthy) values are not available from the "
        "current source stack.",
        "No validated combination model is available in this "
        "phase. The A+B scenario mirrors the disease state's "
        "mechanistic inferences and is NOT computed by summing "
        "individual effects.",
        "Interaction classification is reported only when a "
        "documented combination rule exists for the pair.",
    ])

    for st in extra_statuses + [status_a, status_b]:
        if not st.reachable:
            warnings.append(
                f"{st.source} unreachable: {st.error}"
            )

    # Compute the four-scenario combination effect using real
    # mechanism targets and Reactome pathway overlap on both
    # sides. Every combined state carries both medicine chains.
    combination_effect: Dict[str, Any] = {}
    try:
        combination_effect = cemb.compute_combination_effect(
            s.SimulationResult(
                run=s.SimulationRun(
                    run_id=run_id,
                    task=s.SimulationTask.VIRTUAL_DISEASE_SIMULATION,
                    disease=disease_ref,
                    cell_context=cell_context,
                    function_mapper_version=fv.FUNCTION_MAPPER_VERSION,
                    pipeline_version=PIPELINE_VERSION,
                    created_at=_now_iso(),
                    status=s.SimulationStatus.SUCCESS,
                    metadata={},
                ),
                indicators=indicators,
                states=[healthy, disease_state],
                comparison=None,
                evidence=disease_evidence,
                source_status=source_statuses,
                limitations=[],
                warnings=[],
                metadata={},
            ),
            intervention_a,
            intervention_b,
        )
    except Exception as exc:
        warnings.append(
            f"Combination effect model failed: {exc}"
        )

    run = s.SimulationRun(
        run_id=run_id,
        task=s.SimulationTask.COMBINATION_TREATMENT_SIMULATION,
        disease=disease_ref,
        cell_context=cell_context,
        function_mapper_version=fv.FUNCTION_MAPPER_VERSION,
        pipeline_version=PIPELINE_VERSION,
        created_at=_now_iso(),
        status=s.SimulationStatus.SUCCESS,
        metadata={
            "intervention_a_id": intervention_a.id,
            "intervention_b_id": intervention_b.id,
            "rule_present": rule is not None,
            "requested_baseline_id": baseline_id,
        },
    )

    return s.SimulationResult(
        run=run,
        indicators=indicators,
        states=[healthy, disease_state, state_a, state_b, state_ab],
        comparison=comparison,
        evidence=disease_evidence,
        source_status=source_statuses,
        limitations=limitations,
        warnings=warnings,
        metadata={
            "workflow": "combination_treatment_simulation",
            "interventions": [
                s.to_dict(intervention_a),
                s.to_dict(intervention_b),
            ],
            "combination_effect": combination_effect,
        },
    )


# ---------------------------------------------------------------------------
# Baseline mismatch helper
# ---------------------------------------------------------------------------


def _baseline_mismatch_result(
    task: str,
    disease_ref: s.DiseaseRef,
    cell_context: s.CellContext,
    run_id: str,
    requested_baseline: str,
) -> s.SimulationResult:
    """
    Return a partial result when a supplied baseline_id does
    not match the deterministic run_id computed from the
    current inputs.

    No stored baseline is looked up; the mismatch is reported
    rather than silently resolved.
    """
    limitations = [
        f"The supplied baseline_id '{requested_baseline}' does "
        f"not match the current run_id '{run_id}'. This can "
        "happen if the disease, cell context, function mapper "
        "version, or pipeline version has changed. No stored "
        "baseline is loaded in this phase."
    ]

    return _empty_result(
        task=task,
        disease_ref=disease_ref,
        cell_context=cell_context,
        run_id=run_id,
        status=s.SimulationStatus.PARTIAL,
        limitations=limitations,
        warnings=[],
        source_status=[],
    )
