/**
 * CureVerseAI — Medicine domain
 * Shared TypeScript types.
 *
 * These types mirror the wire shape returned by the backend
 * for the three Medicine workflows. They are hand-written to
 * match the Python dataclasses in
 * `ai-engine/app/medicine/simulation/schemas.py` and the
 * serialization performed by `to_wire`.
 *
 * Rules:
 *   - No field is optional unless the backend serializes it as
 *     missing. Where the backend always emits a key, the type
 *     requires it.
 *   - No numeric magnitude is typed as required, because the
 *     backend never populates it in Phase 3.
 *   - String enums mirror the vocabulary in schemas.py exactly.
 */

// ---------------------------------------------------------------------------
// Enums (string literals, matching schemas.py)
// ---------------------------------------------------------------------------

export type SimulationTask =
  | "virtual_disease_simulation"
  | "treatment_simulation"
  | "combination_treatment_simulation";

export type SimulationStatus =
  | "success"
  | "partial"
  | "not_found"
  | "unsupported"
  | "error";

export type StateKind =
  | "healthy_reference"
  | "disease"
  | "intervention_single"
  | "intervention_combination";

export type DirectionOfBenefit =
  | "higher_better"
  | "lower_better"
  | "optimal_range"
  | "qualitative_only";

export type ResponseDirection =
  | "increase"
  | "decrease"
  | "unchanged"
  | "unknown";

export type ResponseMethod =
  | "observed"
  | "model_predicted"
  | "mechanistic_inference"
  | "insufficient";

export type OverallInterpretation =
  | "best_supported"
  | "promising_uncertain"
  | "no_defensible_winner"
  | "potentially_adverse"
  | "not_modelled";

export type InteractionClass =
  | "additive"
  | "synergistic"
  | "antagonistic"
  | "overlapping"
  | "adverse"
  | "unknown"
  | "insufficient_evidence";

export type UncertaintyLevel =
  | "low"
  | "medium"
  | "high"
  | "unknown";

// ---------------------------------------------------------------------------
// Identity
// ---------------------------------------------------------------------------

export interface CellContext {
  id: string;
  name: string;
  source: string;
  ontology_id: string | null;
  confidence: string | null;
  metadata: Record<string, unknown>;
}

export interface DiseaseRef {
  id: string | null;
  name: string;
  query: string;
  source: string;
  resolution_status: string;
  identifiers: Record<string, string>;
  metadata: Record<string, unknown>;
}

export interface TargetRef {
  id: string;
  name: string;
  source: string;
  source_id: string;
  target_type: string | null;
  metadata: Record<string, unknown>;
}

export interface InterventionRef {
  id: string;
  name: string;
  source: string;
  source_id: string;
  intervention_type: string | null;
  targets: TargetRef[];
  resolution_status: string;
  metadata: Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// Indicators and states
// ---------------------------------------------------------------------------

export interface Measurement {
  value: number | null;
  unit: string;
  value_type: string;
  method: string;
  source: string;
  uncertainty: Record<string, unknown> | null;
  metadata: Record<string, unknown>;
}

export interface FunctionalIndicator {
  id: string;
  name: string;
  direction_of_benefit: DirectionOfBenefit;
  unit: string | null;
  description: string | null;
  evidence_level: string | null;
  measurement: Measurement | null;
  metadata: Record<string, unknown>;
}

export interface Uncertainty {
  level: UncertaintyLevel;
  reasons: string[];
  sources: string[];
}

export interface IndicatorValue {
  indicator_id: string;
  direction: ResponseDirection;
  method: ResponseMethod;
  qualitative_label: string | null;
  measurement: Measurement | null;
  evidence_ids: string[];
  uncertainty: Uncertainty | null;
  notes: string[];
}

export interface BiologicalState {
  state_id: string;
  kind: StateKind;
  run_id: string;
  indicator_values: Record<string, IndicatorValue>;
  intervention_ref: InterventionRef | null;
  intervention_b_ref: InterventionRef | null;
  evidence_ids: string[];
  notes: string[];
  metadata: Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// Response and comparison
// ---------------------------------------------------------------------------

export interface Response {
  indicator_id: string;
  baseline_state_id: string;
  scenario_state_id: string;
  direction_change: ResponseDirection;
  method: ResponseMethod;
  magnitude: Measurement | null;
  evidence_ids: string[];
  uncertainty: Uncertainty | null;
  notes: string[];
}

export interface ScenarioComparison {
  baseline_state_id: string;
  scenarios: BiologicalState[];
  responses: Response[];
  overall_interpretation: OverallInterpretation;
  interaction_class: InteractionClass | null;
  interaction_evidence_ids: string[];
  reasoning: string | null;
  notes: string[];
  metadata: Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// Evidence and source status
// ---------------------------------------------------------------------------

export interface ProvenanceRecord {
  source: string;
  source_id: string;
  source_type: string | null;
  url: string | null;
  retrieved_at: string | null;
  metadata: Record<string, unknown>;
}

export interface SourceStatus {
  source: string;
  reachable: boolean;
  returned_records: number;
  error: string | null;
  metadata: Record<string, unknown>;
}

export interface MedicineEvidence {
  evidence_id: string;
  source: string;
  description: string;
  evidence_level: string | null;
  support_class: string | null;
  provenance: ProvenanceRecord | null;
  identifiers: Record<string, string>;
  metadata: Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// Run and result
// ---------------------------------------------------------------------------

export interface SimulationRun {
  run_id: string;
  task: SimulationTask;
  disease: DiseaseRef;
  cell_context: CellContext;
  function_mapper_version: string;
  pipeline_version: string;
  created_at: string;
  status: SimulationStatus;
  metadata: Record<string, unknown>;
}

export interface SimulationResult {
  run: SimulationRun;
  indicators: FunctionalIndicator[];
  states: BiologicalState[];
  comparison: ScenarioComparison | null;
  evidence: MedicineEvidence[];
  source_status: SourceStatus[];
  limitations: string[];
  warnings: string[];
  metadata: Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// Backend envelope
// ---------------------------------------------------------------------------

export interface AnalyzeResponseData {
  domain: "medicine";
  task: SimulationTask;
  engine: string;
  status: SimulationStatus;
  result: SimulationResult;
}

export interface AnalyzeResponse {
  success: boolean;
  domain: "medicine";
  task: SimulationTask;
  data: AnalyzeResponseData;
}

// ---------------------------------------------------------------------------
// Curated vocabulary
// ---------------------------------------------------------------------------

export interface CuratedPair {
  disease_id: string;
  disease_name: string;
  cell_context_id: string;
  cell_context_name: string;
}

export interface CuratedResponse {
  success: boolean;
  version: string;
  count: number;
  curated: CuratedPair[];
}
