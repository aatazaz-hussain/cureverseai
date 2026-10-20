/**
 * CureVerseAI — Drug Development
 * Workflow 02 — Reverse Disease Engineering
 * TypeScript mirrors of the AI Engine response.
 *
 * These types describe the serialized ReverseDiseaseResult
 * returned by:
 *
 *   POST /api/v1/analyze
 *   {
 *     "domain": "drug_development",
 *     "task": "reverse_disease_engineering",
 *     "input": { "disease": "<query>", "fetch_chembl": <bool> }
 *   }
 *
 * The response envelope is nested:
 *
 *   {
 *     "success": true,
 *     "domain":  "drug_development",
 *     "task":    "reverse_disease_engineering",
 *     "data": {
 *       "domain": "drug_development",
 *       "task":   "reverse_disease_engineering",
 *       "engine": "reverse_disease_engineering_pipeline",
 *       "result": <ReverseDiseaseResult>
 *     }
 *   }
 *
 * The shape of ReverseDiseaseResult is defined by the W02
 * AI Engine service in
 * ai-engine/app/drug_development/reverse_disease/service.py.
 * It is intentionally distinct from the W01
 * BiologicalImpactResult — the two workflows share only
 * graph primitives.
 */

// ---------------------------------------------------------------------------
// Node / relationship / evidence primitives
// ---------------------------------------------------------------------------

/**
 * Node type vocabulary used by W02. Extends W01's with
 * phenotype, variant, manifestation, factor (via
 * NodeType additions in schemas/impact.py).
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
  | "factor";

/**
 * A single typed node in the W02 mechanism graph.
 */
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
 * A single directed edge in the W02 mechanism graph.
 *
 * `support_class` is W02's four-class support model:
 *   - "retrieved_fact"          — direct database record
 *   - "supported_association"   — statistical/curated
 *   - "mechanistic_inference"   — derived from several edges
 *   - "unknown"                 — evidence absent
 *
 * It is null on any edge emitted by a W01 layer (W02 does
 * not produce those, but the type is tolerant).
 */
export interface Relationship {
  source_id: string;
  target_id: string;
  relationship_type: string;
  evidence_ids: string[];
  evidence_level: string | null;
  support_class: string | null;
  description: string | null;
  metadata: Record<string, unknown>;
}

/**
 * Pointer to the source-of-truth record behind an evidence
 * entry. Same shape as W01.
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
 * Same shape as W01.
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
}

/**
 * A candidate disease when the resolver could not
 * auto-select (resolution_status === "partial").
 */
export interface DiseaseCandidate {
  canonical_name: string | null;
  identifiers: DiseaseIdentifier[];
  description: string | null;
  sources: string[];
}

/**
 * The disease block in the W02 result.
 *
 * When resolution_status is "resolved", candidates is
 * absent. When "partial", candidates is populated and
 * identifiers is empty. When "unresolved", both are absent
 * or empty.
 */
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
// mechanistic_investigation
// ---------------------------------------------------------------------------

/**
 * The seven W02 investigation layers, each a list of
 * serialized ImpactNodes.
 *
 * `variants` and `manifestations` are always empty in
 * Phase 1 (no source wired / not separately sourced), and
 * are documented as such in the `uncertainties` block.
 */
export interface MechanisticInvestigation {
  phenotypes: ImpactNode[];
  contributing_factors: ContributingFactor[];
  mechanisms: ImpactNode[];
  genes: ImpactNode[];
  variants: ImpactNode[];
  pathways: ImpactNode[];
  manifestations: ImpactNode[];
}

/**
 * A contributing factor is synthesized by the service from
 * the gene layer's aggregated datasource counts. It is not
 * a graph node.
 */
export interface ContributingFactor {
  type: "datasource" | string;
  id: string;
  count: number;
  label: string;
}

// ---------------------------------------------------------------------------
// Explanation (narration segments)
// ---------------------------------------------------------------------------

/**
 * A single narration segment returned by the W02
 * explanation_builder. Each segment references either a
 * node or an edge.
 *
 * `target_id` for a node segment is a node_id.
 * `target_id` for an edge segment is the stable key
 *   "<source_id>|<relationship_type>|<target_id>".
 */
export interface Explanation {
  explanation_id: string;
  target_kind: "node" | "edge";
  target_id: string;
  text: string;
  support_class: string | null;
  evidence_ids: string[];
  metadata: Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// Uncertainty
// ---------------------------------------------------------------------------

export type UncertaintySeverity = "info" | "warning" | "error";

/**
 * A structured uncertainty note emitted by the W02
 * evidence integrator.
 *
 * Known `type` values (this list is not exhaustive — the
 * AI Engine may add more):
 *
 *   missing_variant_layer
 *   missing_manifestations_layer
 *   partial_layer
 *   inferred_edge
 *   evidence_gap
 *   source_unavailable
 *   unresolved_disease
 */
export interface Uncertainty {
  type: string;
  statement: string;
  related_ids: string[];
  severity: UncertaintySeverity;
}

// ---------------------------------------------------------------------------
// Provenance
// ---------------------------------------------------------------------------

export interface SourceFailure {
  source: string;
  reason: string;
  metadata?: Record<string, unknown>;
}

export interface Provenance {
  sources_queried: string[];
  source_failures: SourceFailure[];
  records_retrieved: number;
}

// ---------------------------------------------------------------------------
// Ranking
// ---------------------------------------------------------------------------

export interface RankedMechanismCategory {
  rank: number;
  node_id: string;
  name: string | null;
  datatype_id: string | null;
  targets_supporting: number;
  mean_score: number;
  datasources: Record<string, number>;
}

export interface RankedPathway {
  rank: number;
  node_id: string;
  name: string | null;
  reactome_id: string | null;
  supporting_gene_count: number;
  supporting_genes: string[];
  elevated: boolean;
}

export interface RankingMetadata {
  mechanism_categories_ranked: number;
  pathways_ranked: number;
  ranking_method_categories?: string;
  ranking_method_pathways?: string;
  note?: string;
}

export interface RankingDocument {
  ranked_mechanism_categories: RankedMechanismCategory[];
  ranked_pathways: RankedPathway[];
  metadata: RankingMetadata;
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

export interface ReasoningSources {
  all?: string[];
  by_layer?: Record<string, string[]>;
}

export interface Reasoning {
  summary: string | null;
  findings: ReasoningFinding[];
  limitations: string[];
  sources: ReasoningSources | Record<string, unknown>;
}

// ---------------------------------------------------------------------------
// Integrity
// ---------------------------------------------------------------------------

export interface LayerEntityCounts {
  nodes_in: number;
  relationships_in: number;
  evidence_in: number;
  nodes_deduped: number;
  relationships_deduped: number;
  evidence_deduped: number;
}

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
  layer_entity_counts: Record<string, LayerEntityCounts>;
}

// ---------------------------------------------------------------------------
// Metadata
// ---------------------------------------------------------------------------

export interface ResultMetadata {
  schema_version: string;
  layers_run: string[];
  layers_missing: string[];
  node_count: number;
  edge_count: number;
  evidence_count: number;
  layer_counts: Record<string, LayerEntityCounts>;
}

// ---------------------------------------------------------------------------
// Top-level result
// ---------------------------------------------------------------------------

/**
 * The complete result of the W02 Reverse Disease
 * Engineering pipeline, as delivered over HTTP inside
 * `data.result`.
 */
export interface ReverseDiseaseResult {
  query: string;
  resolution_status: "resolved" | "partial" | "unresolved";
  failure_reason: string | null;
  disease: DiseaseBlock | null;

  mechanistic_investigation: MechanisticInvestigation;

  graph: {
    nodes: ImpactNode[];
    edges: Relationship[];
  };

  evidence: ImpactEvidence[];
  explanations: Explanation[];
  uncertainties: Uncertainty[];
  provenance: Provenance;
  reasoning: Reasoning;
  ranking: RankingDocument;
  integrity: IntegrityReport;
  metadata: ResultMetadata;
}

// ---------------------------------------------------------------------------
// Backend envelope
// ---------------------------------------------------------------------------

/**
 * The outer envelope returned by the backend. Matches
 * W01's envelope shape exactly — the backend wraps the
 * AI Engine's response the same way regardless of task.
 */
export interface AnalyzeResponseEnvelope {
  success: boolean;
  domain: string;
  task: string;
  data: {
    domain: string;
    task: string;
    engine: string;
    result: ReverseDiseaseResult;
  };
}

// ---------------------------------------------------------------------------
// UI-facing derived types
// ---------------------------------------------------------------------------

/**
 * Discriminated union used by the graph view to identify
 * the currently selected node or edge.
 */
export type SelectionTarget =
  | { kind: "node"; node_id: string }
  | { kind: "edge"; edge_key: string }
  | null;

/**
 * A convenience type: an edge + its computed edge_key.
 * The edge_key matches the format used by explanations:
 *   "<source_id>|<relationship_type>|<target_id>"
 */
export interface EdgeWithKey {
  edge: Relationship;
  edge_key: string;
}

/**
 * Helper that produces the canonical edge key used by
 * explanations and the selection model.
 */
export function edgeKey(edge: Relationship): string {
  return `${edge.source_id}|${edge.relationship_type}|${edge.target_id}`;
}
