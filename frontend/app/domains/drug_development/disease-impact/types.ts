/**
 * CureVerseAI — Disease → Biological Impact
 * TypeScript types mirroring the backend response.
 *
 * These types describe the serialized BiologicalImpactResult
 * returned by:
 *
 *   POST /api/v1/analyze
 *   {
 *     "domain": "drug_development",
 *     "task": "disease_biological_impact",
 *     "input": { "disease": "<query>" }
 *   }
 *
 * The backend serializes the AI Engine's impact result with
 * internal indexes stripped. Node / relationship / evidence
 * lists are plain arrays, not indexed containers.
 */

// ---------------------------------------------------------------------------
// Node / relationship / evidence primitives
// ---------------------------------------------------------------------------

/**
 * Node type vocabulary, matching the AI Engine's
 * `NodeType.ALL`.
 */
export type NodeType =
  | "disease"
  | "system"
  | "organ"
  | "tissue"
  | "cell"
  | "gene"
  | "protein"
  | "molecule"
  | "pathway"
  | "mechanism"
  | "effect";

/**
 * A single typed entity in the impact graph.
 */
export interface ImpactNode {
  node_id: string;
  node_type: NodeType;
  name: string;
  identifier: string | null;
  description: string | null;
  evidence_ids: string[];
  metadata: Record<string, unknown>;
}

/**
 * A single directed edge in the impact graph.
 */
export interface Relationship {
  source_id: string;
  target_id: string;
  relationship_type: string;
  evidence_ids: string[];
  evidence_level: string | null;
  description: string | null;
  metadata: Record<string, unknown>;
}

/**
 * Pointer to the source-of-truth record behind an evidence
 * entry.
 */
export interface EvidenceReference {
  source: string;
  source_id: string | null;
  source_type: string | null;
  url: string | null;
  metadata: Record<string, unknown>;
}

/**
 * A single evidence record attached to a relationship.
 */
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
  metadata: Record<string, unknown>;
}

export interface DiseaseIdentity {
  query: string;
  canonical_name: string | null;
  synonyms: string[];
  identifiers: DiseaseIdentifier[];
  category: string | null;
  description: string | null;
  sources: string[];
  resolution_status: "resolved" | "partial" | "unresolved";
  metadata: Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// Reasoning
// ---------------------------------------------------------------------------

export interface ReasoningFinding {
  type?: string;
  layer?: string;
  statement?: string;
  counts?: Record<string, number>;
  [key: string]: unknown;
}

export interface ImpactReasoning {
  summary: string | null;
  findings: ReasoningFinding[];
  limitations: string[];
  sources: Record<string, unknown>;
  metadata: Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// Metadata
// ---------------------------------------------------------------------------

export interface LayerMetadata {
  found: boolean;
  sources: string[];
  metadata: Record<string, unknown>;
  reason: string | null;
}

export interface ImpactMetadataSummary {
  node_count: number;
  relationship_count: number;
  evidence_count: number;
  layers_run: string[];
  layers_missing: string[];
  resolution_status: string;
  schema_version: string;
}

export interface ImpactIntegrity {
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
  layers_run: string[];
  layers_missing: string[];
}

export interface ImpactMetadata {
  summary: ImpactMetadataSummary;
  integrity: ImpactIntegrity;
  layers: Record<string, LayerMetadata | null>;
}

// ---------------------------------------------------------------------------
// Top-level result
// ---------------------------------------------------------------------------

/**
 * The complete result of the Disease → Biological Impact
 * pipeline, as delivered over HTTP.
 */
export interface BiologicalImpactResult {
  query: string;
  resolution_status: "resolved" | "partial" | "unresolved";
  failure_reason: string | null;
  disease: DiseaseIdentity | null;
  nodes: ImpactNode[];
  relationships: Relationship[];
  evidence: ImpactEvidence[];
  reasoning: ImpactReasoning;
  metadata: ImpactMetadata;
}

// ---------------------------------------------------------------------------
// Backend envelope
// ---------------------------------------------------------------------------

/**
 * The outer envelope returned by the backend.
 */
export interface AnalyzeResponseEnvelope {
  success: boolean;
  domain: string;
  task: string;
  data: {
    domain: string;
    task: string;
    engine: string;
    result: BiologicalImpactResult;
  };
}
