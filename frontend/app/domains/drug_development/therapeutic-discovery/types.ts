/**
 * CureVerseAI — Drug Development
 * Workflow 03 — Therapeutic Discovery
 * TypeScript mirrors of the AI Engine response.
 *
 * These types describe the serialized
 * TherapeuticDiscoveryResult returned by:
 *
 *   POST /api/v1/analyze
 *   {
 *     "domain": "drug_development",
 *     "task": "therapeutic_discovery",
 *     "input": {
 *       "disease": "<query>",
 *       "mechanism_id": <str | null>,
 *       "target_id": <str | null>
 *     }
 *   }
 *
 * The response envelope is nested:
 *
 *   {
 *     "success": true,
 *     "domain":  "drug_development",
 *     "task":    "therapeutic_discovery",
 *     "data": {
 *       "domain": "drug_development",
 *       "task":   "therapeutic_discovery",
 *       "engine": "therapeutic_discovery_pipeline",
 *       "result": <TherapeuticDiscoveryResult>
 *     }
 *   }
 *
 * Shape defined by W03's service.py serializer.
 */

// ---------------------------------------------------------------------------
// Node / relationship / evidence primitives
// ---------------------------------------------------------------------------

/**
 * Node type vocabulary. Extends W01's with W03 additions
 * (compound, molecular_action, biological_response).
 */
export type NodeType =
  | "disease"
  | "phenotype"
  | "mechanism"
  | "gene"
  | "variant"
  | "pathway"
  | "protein"
  | "molecule"
  | "manifestation"
  | "factor"
  | "compound"
  | "molecular_action"
  | "biological_response";

export interface ImpactNode {
  node_id: string;
  node_type: NodeType | string;
  name: string;
  identifier: string | null;
  description: string | null;
  evidence_ids: string[];
  metadata: Record<string, unknown>;
}

/**
 * Support class vocabulary used across W01, W02, W03.
 *
 * W03 additions:
 *   experimentally_measured — backed by an assay record
 *   predicted               — computational only
 *   unresolved              — the workflow tried and failed
 */
export type SupportClass =
  | "retrieved_fact"
  | "supported_association"
  | "mechanistic_inference"
  | "unknown"
  | "experimentally_measured"
  | "predicted"
  | "unresolved";

export interface Relationship {
  source_id: string;
  target_id: string;
  relationship_type: string;
  evidence_ids: string[];
  evidence_level: string | null;
  support_class: SupportClass | string | null;
  description: string | null;
  metadata: Record<string, unknown>;
}

export interface EvidenceReference {
  source: string;
  source_id: string | null;
  source_type: string | null;
  url: string | null;
  metadata: Record<string, unknown>;
}

export interface ImpactEvidence {
  evidence_id: string;
  source: string;
  relationship_description: string;
  evidence_level: string;
  reference: EvidenceReference | null;
  identifiers: Record<string, string>;
  metadata: Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// Disease identity
// ---------------------------------------------------------------------------

export interface DiseaseIdentifier {
  source: string;
  identifier: string;
  url: string | null;
}

export interface DiseaseCandidate {
  canonical_name: string | null;
  identifiers: DiseaseIdentifier[];
  description: string | null;
  sources: string[];
}

export interface DiseaseBlock {
  query: string;
  resolved_name: string | null;
  identifiers: DiseaseIdentifier[];
  resolution_status: "resolved" | "partial" | "unresolved";
  candidates?: DiseaseCandidate[];
  synonyms?: string[];
  description?: string | null;
  sources?: string[];
}

// ---------------------------------------------------------------------------
// Selected mechanism
// ---------------------------------------------------------------------------

export interface CandidateMechanism {
  mechanism_id: string;
  label: string | null;
  source: string;
  identifier: string | null;
  metadata: Record<string, unknown>;
}

export interface SelectedMechanismBlock {
  mechanism_id: string;
  label: string | null;
  source: string;
  identifier: string | null;
  description: string | null;
  candidate_mechanisms: CandidateMechanism[];
  metadata: Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// Targets
// ---------------------------------------------------------------------------

export interface TargetBlock {
  target_id: string;
  label: string;
  gene_symbol: string | null;
  uniprot_id: string | null;
  ensembl_id: string | null;
  chembl_target_id: string | null;
  mechanism_membership: boolean;
  open_targets_score: number | null;
  metadata: Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// Candidates
// ---------------------------------------------------------------------------

export interface CandidateBlock {
  compound_id: string;
  source: string;
  name: string | null;
  parent_chembl_id: string | null;
  canonical_smiles: string | null;
  identifiers: Record<string, string>;
  metadata: Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// Activity record
// ---------------------------------------------------------------------------

/**
 * One assay measurement attached to a compound-target
 * relationship. Mirrors W03's ActivityRecord dataclass
 * from the AI Engine.
 *
 * `evidence_level` values:
 *   "quantitative"   a numeric standard_value exists
 *   "qualitative"    only standard_text_value exists
 *   "observational"  neither is present
 *
 * `assay_type` is ChEMBL's single-letter code:
 *   "B" binding   "F" functional
 *   "A" ADME      "T" toxicity     "P" physicochemical
 *
 * `classification` is added by W03's activity_interpreter:
 *   "measured_potency" | "out_of_range" |
 *   "qualitative_activity" | "observational"
 */
export interface ActivityRecord {
  activity_id: string;
  target_chembl_id: string;
  compound_chembl_id: string;
  evidence_level: string;
  standard_type: string | null;
  standard_value: string | null;
  standard_units: string | null;
  standard_relation: string | null;
  standard_text_value: string | null;
  pchembl_value: string | null;
  assay_id: string | null;
  assay_type: string | null;
  assay_description: string | null;
  publication_year: number | null;
  publication_journal: string | null;
  source: string;
  source_record_id: string | null;
  metadata: Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// Candidate comparison (4 dimensions, no composite score)
// ---------------------------------------------------------------------------

export type ActivityQuality =
  | "measured"
  | "qualitative"
  | "none";

export type MechanismLinkStrength =
  | "direct"
  | "two_hop"
  | "indirect";

export interface CandidateComparisonBlock {
  candidate_id: string;
  activity_quality: ActivityQuality;
  mechanism_link_strength: MechanismLinkStrength;
  evidence_diversity: number;
  data_gaps: number;
  notes: string[];
  metadata: Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// Mechanism of action
// ---------------------------------------------------------------------------

export interface MechanismOfActionBlock {
  nodes: ImpactNode[];
  edges: Relationship[];
}

// ---------------------------------------------------------------------------
// Reasoning
// ---------------------------------------------------------------------------

export interface ReasoningFinding {
  type?: string;
  statement?: string;
  [key: string]: unknown;
}

export interface ReasoningBlock {
  supported_findings: ReasoningFinding[];
  hypotheses: ReasoningFinding[];
  conflicts: ReasoningFinding[];
  evidence_gaps: ReasoningFinding[];
}

// ---------------------------------------------------------------------------
// Provenance
// ---------------------------------------------------------------------------

export interface SourceFailure {
  source: string;
  reason: string;
  metadata?: Record<string, unknown>;
}

export interface ProvenanceBlock {
  sources_queried: string[];
  source_failures: SourceFailure[];
  records_retrieved: number;
  metadata?: Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// Narration segments
// ---------------------------------------------------------------------------

export interface NarrationSegment {
  explanation_id: string;
  target_kind: "node" | "edge";
  target_id: string;
  text: string;
  support_class: SupportClass | string | null;
  evidence_ids: string[];
  metadata: Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// Integrity
// ---------------------------------------------------------------------------

export interface IntegrityReport {
  ok: boolean;
  node_count: number;
  relationship_count: number;
  evidence_count: number;
  dangling_relationship_sources: string[];
  dangling_relationship_targets: string[];
  relationships_with_missing_evidence: string[];
  nodes_with_missing_evidence: string[];
  duplicate_node_ids: string[];
  duplicate_relationship_keys: string[];
  duplicate_evidence_ids: string[];
  layers_merged: string[];
}

// ---------------------------------------------------------------------------
// Metadata
// ---------------------------------------------------------------------------

export interface ResultMetadata {
  schema_version: string;
  elapsed_seconds: number;
  target_count: number;
  candidate_count: number;
  activity_count: number;
  chain_count: number;
  narration_segment_count: number;
}

// ---------------------------------------------------------------------------
// Top-level result
// ---------------------------------------------------------------------------

export interface TherapeuticDiscoveryResult {
  query: string;
  resolution_status:
    | "resolved"
    | "no_candidates"
    | "partial"
    | "unresolved"
    | "invalid_input";
  failure_reason: string | null;

  disease: DiseaseBlock | null;
  selected_mechanism: SelectedMechanismBlock | null;

  targets: TargetBlock[];
  candidates: CandidateBlock[];

  mechanism_of_action: MechanismOfActionBlock;
  candidate_comparisons: CandidateComparisonBlock[];

  evidence: ImpactEvidence[];
  reasoning: ReasoningBlock;
  provenance: ProvenanceBlock;
  narration: { segments: NarrationSegment[] };

  // W03 extensions
  summary: string | null;
  limitations: string[];
  integrity: IntegrityReport;
  metadata: ResultMetadata;
}

// ---------------------------------------------------------------------------
// Backend envelope
// ---------------------------------------------------------------------------

export interface AnalyzeResponseEnvelope {
  success: boolean;
  domain: string;
  task: string;
  data: {
    domain: string;
    task: string;
    engine: string;
    result: TherapeuticDiscoveryResult;
  };
}

// ---------------------------------------------------------------------------
// UI helpers
// ---------------------------------------------------------------------------

/**
 * The currently selected element. Used by the graph and
 * panels. `null` means nothing is selected.
 */
export type SelectionTarget =
  | { kind: "node"; node_id: string }
  | { kind: "edge"; edge_key: string }
  | { kind: "candidate"; compound_id: string }
  | null;

/**
 * Canonical edge key. Matches W02's format so segments and
 * edges address the same way.
 */
export function edgeKey(edge: Relationship): string {
  return `${edge.source_id}|${edge.relationship_type}|${edge.target_id}`;
}

/**
 * A candidate paired with its comparison record, so panels
 * do not have to index repeatedly.
 */
export interface CandidateWithComparison {
  candidate: CandidateBlock;
  comparison: CandidateComparisonBlock | null;
}

/**
 * A target paired with its assigned chembl id when
 * resolved.
 */
export interface TargetWithChembl extends TargetBlock {
  chembl_target_id: string | null;
}
