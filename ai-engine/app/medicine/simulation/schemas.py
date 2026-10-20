"""
CureVerseAI — Medicine domain
Shared simulation contract.

This module defines the ONE consistent internal representation
used by all three Medicine workflows:

    virtual_disease_simulation
        healthy reference vs disease-associated state

    treatment_simulation
        disease state vs single-intervention scenario

    combination_treatment_simulation
        disease state vs intervention A, B, and A+B

Design constraints (from the Medicine specification, locked):

1. No composite health score, no numeric certainty score, and
   no arbitrary magnitude. There is deliberately NO field named
   ``overall_score``, ``health_score``, or ``composite_score``
   anywhere in this module. If a future validated model emits
   a numeric prediction, it lives inside a :class:`Measurement`
   with its method and source attached. This is an
   architectural guarantee, not a convention.

2. Numeric values only exist inside :class:`Measurement`. A
   :class:`IndicatorValue` cannot carry a bare number: it either
   has a Measurement (with source + method + unit) or it is
   qualitative (direction + optional label), or it is unknown.

3. The three evidence levels required by the specification stay
   distinct end to end:

       observed            — experimentally measured / source reported
       model_predicted     — produced by a specified computational model
       mechanistic_inference — supported hypothesis, not a measured result

   They are represented by :class:`ResponseMethod` and are
   surfaced on every :class:`Response` and every
   :class:`IndicatorValue`.

4. A missing biological record, an unavailable predictive model,
   and an upstream source failure are three distinct conditions.
   They are represented by :class:`SimulationStatus` and
   :class:`SourceStatus`, never collapsed into a single
   "insufficient evidence" outcome.

5. Simulation run identity is deterministic. ``run_id`` is a
   content-derived hash over the canonical inputs plus the
   versions of the function mapper and pipeline. The same
   inputs always produce the same id, so a baseline can be
   reproduced by re-running rather than by trusting a stored
   pointer.

6. Serialization is hand-rolled. The project does not depend on
   dataclasses-json, pydantic, or any other converter for
   internal models. :func:`to_dict` and :func:`to_wire` are the
   canonical serializers.

Vocabulary note
---------------
Medicine-local enums live here. The shared drug_development
vocabularies (``NodeType``, ``RelationshipType``,
``SupportClass``, ``EvidenceLevel``) are NOT mutated by this
module. Medicine only references them by string value, when a
Medicine module chooses to attach a support class or an
evidence level to something. That choice belongs to the module
that produces the value, not to this schema file.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ===========================================================================
# GROUP A — Vocabulary
# ===========================================================================


class SimulationTask:
    """Canonical task identifiers, matching the orchestration router."""

    VIRTUAL_DISEASE_SIMULATION = "virtual_disease_simulation"
    TREATMENT_SIMULATION = "treatment_simulation"
    COMBINATION_TREATMENT_SIMULATION = "combination_treatment_simulation"

    ALL = (
        VIRTUAL_DISEASE_SIMULATION,
        TREATMENT_SIMULATION,
        COMBINATION_TREATMENT_SIMULATION,
    )


class SimulationStatus:
    """
    Top-level scientific state of a workflow result.

    These are honest states, not errors. A non-success status is
    still a valid HTTP 200 response and must be rendered by the
    frontend as information, not as a failure.

    success      — the requested task produced a valid result
                   within its stated capabilities.
    partial      — a useful result was produced, but important
                   data or capabilities are missing.
    not_found    — no matching biological record could be
                   resolved for one of the inputs.
    unsupported  — the requested prediction cannot be supported
                   by the available model or evidence.
    error        — an execution or service failure prevented the
                   task from completing.
    """

    SUCCESS = "success"
    PARTIAL = "partial"
    NOT_FOUND = "not_found"
    UNSUPPORTED = "unsupported"
    ERROR = "error"

    ALL = (SUCCESS, PARTIAL, NOT_FOUND, UNSUPPORTED, ERROR)


class StateKind:
    """
    What a :class:`BiologicalState` represents.

    healthy_reference         — the reference baseline for the
                                chosen cell context.
    disease                   — the disease-associated state on
                                the same cell context.
    intervention_single       — a single intervention applied
                                on top of the disease state.
    intervention_combination  — two interventions applied
                                together on top of the disease
                                state.
    """

    HEALTHY_REFERENCE = "healthy_reference"
    DISEASE = "disease"
    INTERVENTION_SINGLE = "intervention_single"
    INTERVENTION_COMBINATION = "intervention_combination"

    ALL = (
        HEALTHY_REFERENCE,
        DISEASE,
        INTERVENTION_SINGLE,
        INTERVENTION_COMBINATION,
    )


class DirectionOfBenefit:
    """
    For a functional indicator, which direction is considered
    biologically favorable in the stated context.

    This is a property of the indicator, not of a scenario. It
    is decided by the function mapper from the sources, not by
    the workflow, so W02 and W03 can never disagree about it.

    qualitative_only is used when the source establishes a
    documented change without establishing an optimum (e.g.
    "dysregulated" without a direction of benefit).
    """

    HIGHER_BETTER = "higher_better"
    LOWER_BETTER = "lower_better"
    OPTIMAL_RANGE = "optimal_range"
    QUALITATIVE_ONLY = "qualitative_only"

    ALL = (
        HIGHER_BETTER,
        LOWER_BETTER,
        OPTIMAL_RANGE,
        QUALITATIVE_ONLY,
    )


class ResponseDirection:
    """
    Direction of change between two biological states.

    unknown is a first-class value. It means the source or model
    did not establish a direction. It must never be replaced by
    "unchanged" to fill a table cell: unchanged is an assertion,
    unknown is an absence of information. They are different.
    """

    INCREASE = "increase"
    DECREASE = "decrease"
    UNCHANGED = "unchanged"
    UNKNOWN = "unknown"

    ALL = (INCREASE, DECREASE, UNCHANGED, UNKNOWN)


class ResponseMethod:
    """
    How a response was obtained. Mirrors the specification's
    three permitted evidence levels plus an explicit
    insufficient-evidence state.

    observed               — a source reports the change as a
                             measured or experimentally observed
                             result under a specified context.
    model_predicted        — a specified computational model
                             produced the change, with its own
                             assumptions and validation status.
    mechanistic_inference  — available evidence supports a
                             possible relationship but the
                             downstream effect is not established.
    insufficient           — no defensible response could be
                             produced for this indicator.
    """

    OBSERVED = "observed"
    MODEL_PREDICTED = "model_predicted"
    MECHANISTIC_INFERENCE = "mechanistic_inference"
    INSUFFICIENT = "insufficient"

    ALL = (
        OBSERVED,
        MODEL_PREDICTED,
        MECHANISTIC_INFERENCE,
        INSUFFICIENT,
    )


class OverallInterpretation:
    """
    Workflow-level interpretation, used by W03 (and optionally
    by W02 in its summary). Matches the specification's four
    permitted outcomes for a comparison, plus a not-modelled
    state for combinations whose interaction could not be
    evaluated.

    The frontend must render these verbatim. It must not
    translate them into "best" or "winner" language.
    """

    BEST_SUPPORTED = "best_supported"
    PROMISING_UNCERTAIN = "promising_uncertain"
    NO_DEFENSIBLE_WINNER = "no_defensible_winner"
    POTENTIALLY_ADVERSE = "potentially_adverse"
    NOT_MODELLED = "not_modelled"

    ALL = (
        BEST_SUPPORTED,
        PROMISING_UNCERTAIN,
        NO_DEFENSIBLE_WINNER,
        POTENTIALLY_ADVERSE,
        NOT_MODELLED,
    )


class InteractionClass:
    """
    W03 only. How two interventions interact.

    The specification is explicit: synergy must not be declared
    merely because the combination looks larger than either
    intervention alone. A value may only be assigned when a
    source explicitly supports it, or when a validated
    combination model exists.

    unknown and insufficient_evidence are the default states.
    unknown means the interaction was not classified.
    insufficient_evidence means classification was attempted
    and the evidence did not support any of the specific
    interaction classes.
    """

    ADDITIVE = "additive"
    SYNERGISTIC = "synergistic"
    ANTAGONISTIC = "antagonistic"
    OVERLAPPING = "overlapping"
    ADVERSE = "adverse"
    UNKNOWN = "unknown"
    INSUFFICIENT_EVIDENCE = "insufficient_evidence"

    ALL = (
        ADDITIVE,
        SYNERGISTIC,
        ANTAGONISTIC,
        OVERLAPPING,
        ADVERSE,
        UNKNOWN,
        INSUFFICIENT_EVIDENCE,
    )


# ===========================================================================
# GROUP B — Entity Identity
# ===========================================================================


@dataclass
class CellContext:
    """
    The specific cell type and biological context the simulation
    is modelling.

    A disease does not affect every cell identically. The chosen
    context must be stated explicitly on every state so that
    two states are only ever compared when they share the same
    context.

    ``source`` is mandatory: the context is a claim, and every
    claim carries its origin. ``ontology_id`` is optional in
    general but must be populated whenever the source provides
    one (Cell Ontology, UBERON, etc.). Downstream code that
    needs a stable key should prefer ``ontology_id`` when
    present and fall back to ``id``.
    """

    id: str
    name: str
    source: str
    ontology_id: Optional[str] = None
    confidence: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DiseaseRef:
    """
    A resolved disease reference.

    This is Medicine-local and deliberately does not import
    ``DiseaseIdentity`` from ``drug_development``: the two
    domains should be decoupled, and the shape here is smaller
    and shaped around simulation needs rather than graph needs.

    ``resolution_status`` uses the same vocabulary as the rest
    of CureVerseAI (``resolved``, ``partial``, ``unresolved``,
    ``no_candidates``, ``invalid_input``) so the frontend does
    not need a second vocabulary for Medicine.
    """

    id: Optional[str]
    name: str
    query: str
    source: str
    resolution_status: str
    identifiers: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TargetRef:
    """
    A biological target that an intervention acts on.

    Populated by the intervention resolver from a source
    (ChEMBL, Open Targets, etc.). ``source`` and ``source_id``
    are mandatory together: a target without provenance is not
    admissible.
    """

    id: str
    name: str
    source: str
    source_id: str
    target_type: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class InterventionRef:
    """
    A resolved intervention (compound, biologic, or other
    defined intervention).

    ``id`` is the canonical, namespaced identifier used
    throughout Medicine, e.g. ``chembl:CHEMBL1234``. It is
    the key that states, responses, and comparisons refer to.
    """

    id: str
    name: str
    source: str
    source_id: str
    intervention_type: Optional[str] = None
    targets: List[TargetRef] = field(default_factory=list)
    resolution_status: str = "resolved"
    metadata: Dict[str, Any] = field(default_factory=dict)


# ===========================================================================
# GROUP C — Functional indicators and measurements
# ===========================================================================


@dataclass
class Measurement:
    """
    A numeric value with its method and source.

    This is the ONLY place a numeric biological value may
    live. A Measurement without ``source`` or without
    ``method`` is not admissible: those two fields are
    mandatory so that a number can never be presented to the
    user without provenance and method.

    ``value_type`` mirrors the specification's three evidence
    levels:

        measured        — reported by a source
        model_predicted — produced by a named computational model
        qualitative     — the source establishes a direction but
                          no numeric value; ``value`` is None

    ``value`` is Optional because a qualitative measurement
    carries no number. It is None in that case, NOT zero.
    """

    value: Optional[float]
    unit: str
    value_type: str
    method: str
    source: str
    uncertainty: Optional[Dict[str, Any]] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FunctionalIndicator:
    """
    A biological function or measurable quantity that the
    simulation tracks across states.

    One :class:`FunctionalIndicator` describes the function
    itself, independent of any state. State-specific values
    live in :class:`IndicatorValue`, keyed by ``id``.

    ``direction_of_benefit`` is mandatory and belongs to the
    indicator, not to any state. It is populated once, by the
    function mapper, from the sources, and reused unchanged by
    W01, W02, and W03.

    ``measurement`` is optional and, when present, carries the
    REFERENCE measurement for this indicator if the source
    supplies one (for example a healthy reference value). It
    is not the disease value and not any scenario value: those
    live on :class:`IndicatorValue`.

    There is deliberately NO ``overall_score`` field here or
    anywhere else in this module.
    """

    id: str
    name: str
    direction_of_benefit: str
    unit: Optional[str] = None
    description: Optional[str] = None
    evidence_level: Optional[str] = None
    measurement: Optional[Measurement] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class IndicatorValue:
    """
    The value of one functional indicator within one
    biological state.

    A value is expressed as a direction (mandatory) plus,
    optionally, a Measurement. A Measurement is present only
    when a source or model produced a number. When it is
    absent, ``qualitative_label`` may carry a source-provided
    label such as ``"impaired"`` or ``"dysregulated"``.

    ``method`` states how the direction was obtained, using
    :class:`ResponseMethod`. This prevents a model prediction
    from being silently shown as an observation downstream.

    An IndicatorValue with method=INSUFFICIENT and direction=
    UNKNOWN is a first-class, honest result. It is not a
    placeholder: it is the answer, and the frontend must render
    it as "not established".
    """

    indicator_id: str
    direction: str = ResponseDirection.UNKNOWN
    method: str = ResponseMethod.INSUFFICIENT
    qualitative_label: Optional[str] = None
    measurement: Optional[Measurement] = None
    evidence_ids: List[str] = field(default_factory=list)
    uncertainty: Optional[Uncertainty] = None
    notes: List[str] = field(default_factory=list)


# ===========================================================================
# GROUP D — Biological states
# ===========================================================================


@dataclass
class BiologicalState:
    """
    One state of the modelled biological system.

    States are named, keyed, and comparable. The same
    ``indicator_id`` set must appear on every state that will
    be compared, so that a comparison is an alignment, not a
    guess.

    ``state_id`` is a flat string of the form::

        <run_id>::<kind>
        <run_id>::intervention::<intervention_id>
        <run_id>::combination::<intervention_a>::<intervention_b>

    The flat shape is deliberate: it serializes to JSON
    cleanly, and the frontend can switch on a single string
    without understanding a nested schema.

    ``intervention_ref`` is set only for intervention states
    and is None otherwise. ``intervention_b_ref`` is set only
    for combination states.
    """

    state_id: str
    kind: str
    run_id: str
    indicator_values: Dict[str, IndicatorValue] = field(default_factory=dict)
    intervention_ref: Optional[InterventionRef] = None
    intervention_b_ref: Optional[InterventionRef] = None
    evidence_ids: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Uncertainty:
    """
    Structured uncertainty attached to a Response or an
    IndicatorValue.

    ``level`` is one of:

        low      — retrieved evidence is direct and specific
                   to the modelled disease + cell context.
        medium   — evidence is present but drawn from a
                   different context, or from a source that
                   does not directly state the change.
        high     — evidence is sparse, heterogeneous, or the
                   mapping from source to indicator is
                   indirect.
        unknown  — the workflow could not evaluate the
                   evidence well enough to assign a level.
                   This is a first-class state and must not
                   be rendered as "low".

    ``reasons`` is a list of short, human-readable strings
    explaining why the level was assigned. It must be
    non-empty whenever the level is not ``low``.

    ``sources`` lists the source identifiers whose records
    contributed to the uncertainty assessment. It is empty
    only when no source could be reached.

    Uncertainty is not a score and is never aggregated into
    a single number. Two responses with the same level may
    have completely different underlying reasons; the reasons
    are authoritative, the level is a summary.
    """

    level: str
    reasons: List[str] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)


# ===========================================================================
# GROUP E — Response and scenario comparison
# ===========================================================================


@dataclass
class Response:
    """
    The change in one functional indicator between two states.

    ``direction_change`` is mandatory and uses
    :class:`ResponseDirection`. ``magnitude`` is optional and
    is populated ONLY when a source provides a numeric change
    with a unit, method, and source. It is never computed by
    subtracting two arbitrary scores.

    ``method`` uses :class:`ResponseMethod` and is the single
    most important field on this record: it is what prevents a
    model prediction from being read as an observation.
    """

    indicator_id: str
    baseline_state_id: str
    scenario_state_id: str
    direction_change: str = ResponseDirection.UNKNOWN
    method: str = ResponseMethod.INSUFFICIENT
    magnitude: Optional[Measurement] = None
    evidence_ids: List[str] = field(default_factory=list)
    uncertainty: Optional[Uncertainty] = None
    notes: List[str] = field(default_factory=list)


@dataclass
class ScenarioComparison:
    """
    The side-by-side comparison across all states in a
    simulation.

    Every scenario in ``scenarios`` uses the same indicator
    set as the baseline, so the comparison is defined as an
    alignment.

    ``interaction_class`` is populated only by W03 and only
    when a source or a validated model supports the
    classification. It is None for W01 and W02.

    ``overall_interpretation`` uses
    :class:`OverallInterpretation` and is mandatory: when no
    defensible ranking exists, its value is
    ``no_defensible_winner``, which is itself the honest
    answer.

    ``reasoning`` is a short, human-readable explanation that
    is DERIVED from the structured records below it. It is not
    an independent claim and it must not introduce facts that
    are absent from the evidence set.
    """

    baseline_state_id: str
    scenarios: List[BiologicalState] = field(default_factory=list)
    responses: List[Response] = field(default_factory=list)
    overall_interpretation: str = OverallInterpretation.NO_DEFENSIBLE_WINNER
    interaction_class: Optional[str] = None
    interaction_evidence_ids: List[str] = field(default_factory=list)
    reasoning: Optional[str] = None
    notes: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ===========================================================================
# GROUP F — Evidence, provenance, source status
# ===========================================================================


@dataclass
class ProvenanceRecord:
    """
    Provenance for any retrieved item.

    ``source`` and ``source_id`` are mandatory. ``source_id``
    may be an empty string only if the source genuinely does
    not expose a stable identifier for the item; in that case
    ``metadata`` should carry enough context to reconstruct
    the lookup.

    ``retrieved_at`` is an ISO-8601 string in UTC.
    """

    source: str
    source_id: str
    source_type: Optional[str] = None
    url: Optional[str] = None
    retrieved_at: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SourceStatus:
    """
    Diagnostic status of one external source for one workflow
    run.

    This exists so the response can distinguish three
    different situations that would otherwise be conflated:

        reachable=True,  returned_records=0   -> source answered, no match
        reachable=True,  returned_records>0   -> source answered with data
        reachable=False, error is set         -> source failed

    A frontend must not render these as the same biological
    conclusion. The workflow status (in :class:`SimulationRun`)
    is the scientific state; SourceStatus is the operational
    detail behind it.
    """

    source: str
    reachable: bool
    returned_records: int = 0
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MedicineEvidence:
    """
    One evidence record produced or retrieved during a
    Medicine simulation.

    ``evidence_level`` and ``support_class`` use the SHARED
    vocabularies from drug_development (``EvidenceLevel`` and
    ``SupportClass``). Medicine does not define its own copies
    and does not mutate the shared enums.

    ``description`` is a short, non-causal statement of what
    the record supports. It must not be paraphrased into
    stronger language downstream.
    """

    evidence_id: str
    source: str
    description: str
    evidence_level: Optional[str] = None
    support_class: Optional[str] = None
    provenance: Optional[ProvenanceRecord] = None
    identifiers: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ===========================================================================
# GROUP G — Simulation run and top-level result
# ===========================================================================


@dataclass
class SimulationRun:
    """
    Identity and context of one simulation run.

    ``run_id`` is deterministic. It is derived from the
    canonical disease id, the cell context id, the function
    mapper version, and the pipeline version. The same inputs
    always produce the same run_id, so a baseline can be
    reproduced by re-running rather than by trusting a stored
    pointer. The human-readable prefix is documentation; the
    hash is the identity.

    ``function_mapper_version`` and ``pipeline_version`` are
    mandatory because the meaning of a run depends on which
    function definitions and which pipeline produced it. A
    change to either invalidates previous baselines by design.

    ``status`` uses :class:`SimulationStatus` and carries the
    scientific state of the run. It is orthogonal to the
    HTTP status of the response.
    """

    run_id: str
    task: str
    disease: DiseaseRef
    cell_context: CellContext
    function_mapper_version: str
    pipeline_version: str
    created_at: str
    status: str = SimulationStatus.SUCCESS
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SimulationResult:
    """
    The top-level result returned by every Medicine workflow.

    This is the contract between the AI Engine, the backend,
    and the frontend. It is serialized via :func:`to_wire`.

    ``states`` contains the healthy reference and disease
    states at minimum; W02 adds single-intervention states;
    W03 adds combination states. Every state uses the same
    ``indicators`` set.

    ``evidence``, ``source_status``, ``limitations``, and
    ``warnings`` are mandatory structural fields. They may be
    empty lists, but their absence in the serialized output
    is a bug: the frontend expects them to exist so it can
    render empty states without branching on key presence.
    """

    run: SimulationRun
    indicators: List[FunctionalIndicator] = field(default_factory=list)
    states: List[BiologicalState] = field(default_factory=list)
    comparison: Optional[ScenarioComparison] = None
    evidence: List[MedicineEvidence] = field(default_factory=list)
    source_status: List[SourceStatus] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ===========================================================================
# GROUP H — Serialization
# ===========================================================================


def to_dict(obj: Any) -> Any:
    """
    Recursively convert dataclass instances, lists, and dicts
    into JSON-serializable primitives.

    Rules:

        - dataclass instance      -> dict of fields
        - list / tuple            -> list of converted items
        - dict                    -> dict with converted values
        - primitives              -> returned as-is
        - anything else           -> ``repr(obj)`` as a last
                                     resort, to avoid silent
                                     data loss

    This function does not consult any external converter. It
    is deliberately small so it can be reasoned about in full.
    """

    if obj is None:
        return None

    if isinstance(obj, (str, int, float, bool)):
        return obj

    if isinstance(obj, (list, tuple)):
        return [to_dict(item) for item in obj]

    if isinstance(obj, dict):
        return {str(k): to_dict(v) for k, v in obj.items()}

    if hasattr(obj, "__dataclass_fields__"):
        return {
            name: to_dict(getattr(obj, name))
            for name in obj.__dataclass_fields__.keys()
        }

    return repr(obj)


def to_wire(result: SimulationResult) -> Dict[str, Any]:
    """
    Serialize a :class:`SimulationResult` for the HTTP wire.

    The wire shape mirrors the dataclass exactly. There is no
    transformation, no computed field, and no summary added
    here: any summary is either present in the structured
    fields or it does not exist.

    The caller (the workflow handler) is responsible for
    placing this dict inside the standard CureVerseAI
    response envelope:

        {
          "domain": "medicine",
          "task": <task>,
          "engine": <engine>,
          "result": <this dict>,
        }
    """

    return to_dict(result)
