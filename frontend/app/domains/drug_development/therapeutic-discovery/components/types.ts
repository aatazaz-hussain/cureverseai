/**
 * CureVerseAI — Drug Development
 * Workflow 03 — Therapeutic Discovery
 * Component-level types and metadata.
 *
 * UI contract boundary. Nothing here talks about the AI
 * Engine response shape (that lives in ../types.ts).
 */

import type {
  ActivityQuality,
  CandidateBlock,
  CandidateComparisonBlock,
  ImpactNode,
  MechanismLinkStrength,
  Relationship,
  TargetBlock,
} from "../types";

// ---------------------------------------------------------------------------
// Graph layout — five columns
// ---------------------------------------------------------------------------

/**
 * The five columns of the W03 graph, left to right:
 *
 *   disease -> mechanism -> pathway -> target -> compound
 */
export type GraphColumn =
  | "disease"
  | "mechanism"
  | "pathway"
  | "target"
  | "compound";

export interface GraphNodePosition {
  node_id: string;
  column: GraphColumn;
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface GraphEdgePath {
  edge_key: string;
  source_id: string;
  target_id: string;
  path: string;
  label_x: number;
  label_y: number;
}

export interface GraphLayout {
  width: number;
  height: number;
  nodes: GraphNodePosition[];
  edges: GraphEdgePath[];
  by_id: Record<string, GraphNodePosition>;
}

// ---------------------------------------------------------------------------
// Node visual identity
// ---------------------------------------------------------------------------

export interface NodeTypeMeta {
  label: string;
  accent: string;
  glyph: string;
  description: string;
}

export const NODE_TYPE_META: Record<string, NodeTypeMeta> = {
  disease: {
    label: "Disease",
    accent: "#e0525a",
    glyph: "◉",
    description: "The disease anchor.",
  },
  mechanism: {
    label: "Mechanism",
    accent: "#6ee7f2",
    glyph: "◇",
    description:
      "The biological process under investigation.",
  },
  pathway: {
    label: "Pathway",
    accent: "#7bcab5",
    glyph: "⬡",
    description: "The Reactome pathway that carries the mechanism.",
  },
  gene: {
    label: "Target",
    accent: "#b9b5d4",
    glyph: "▣",
    description: "A candidate biological target.",
  },
  target: {
    label: "Target",
    accent: "#b9b5d4",
    glyph: "▣",
    description: "A candidate biological target.",
  },
  compound: {
    label: "Compound",
    accent: "#e9c58c",
    glyph: "◆",
    description:
      "A candidate compound retrieved from ChEMBL.",
  },
  molecular_action: {
    label: "Action",
    accent: "#f0666e",
    glyph: "✶",
    description:
      "A specific molecular interaction (binds, inhibits).",
  },
  biological_response: {
    label: "Response",
    accent: "#a4e0c8",
    glyph: "◌",
    description: "A downstream biological effect.",
  },
  phenotype: {
    label: "Symptom",
    accent: "#e9c58c",
    glyph: "◐",
    description: "Not used by W03; kept for compatibility.",
  },
  variant: {
    label: "Variant",
    accent: "#c8a4e0",
    glyph: "◈",
    description: "Not used by W03.",
  },
  protein: {
    label: "Protein",
    accent: "#a4c8e0",
    glyph: "◈",
    description: "A protein entity.",
  },
  molecule: {
    label: "Molecule",
    accent: "#e0c8a4",
    glyph: "○",
    description: "Not used by W03.",
  },
};

export const UNKNOWN_NODE_TYPE_META: NodeTypeMeta = {
  label: "Entity",
  accent: "#888e90",
  glyph: "◯",
  description: "An entity of an unrecognized type.",
};

export function getNodeTypeMeta(node_type: string): NodeTypeMeta {
  return (
    NODE_TYPE_META[node_type] ?? UNKNOWN_NODE_TYPE_META
  );
}

// ---------------------------------------------------------------------------
// Support class visual identity — seven classes
// ---------------------------------------------------------------------------

export interface SupportClassMeta {
  label: string;
  accent: string;
  description: string;
  strokeWidth: number;
}

export const SUPPORT_CLASS_META: Record<
  string,
  SupportClassMeta
> = {
  retrieved_fact: {
    label: "Recorded fact",
    accent: "#6ee7f2",
    description:
      "Directly recorded in a scientific database.",
    strokeWidth: 2,
  },
  supported_association: {
    label: "Research link",
    accent: "#e0525a",
    description:
      "Backed by published research or DNA studies.",
    strokeWidth: 1.5,
  },
  mechanistic_inference: {
    label: "Inferred link",
    accent: "#e9c58c",
    description:
      "Derived by combining several other supported links.",
    strokeWidth: 1.25,
  },
  experimentally_measured: {
    label: "Experimental",
    accent: "#7bcab5",
    description:
      "Backed by an actual assay record against the target.",
    strokeWidth: 2.5,
  },
  predicted: {
    label: "Predicted",
    accent: "#c8a4e0",
    description:
      "Produced by a computational method, not observed.",
    strokeWidth: 1.25,
  },
  unknown: {
    label: "Not classified",
    accent: "#5f5b55",
    description: "No evidence category assigned.",
    strokeWidth: 1,
  },
  unresolved: {
    label: "Unresolved",
    accent: "#888e90",
    description:
      "The workflow tried and could not establish the link.",
    strokeWidth: 1,
  },
};

export const UNKNOWN_SUPPORT_CLASS_META: SupportClassMeta = {
  label: "Unclassified",
  accent: "#5f5b55",
  description: "Relationship without a support classification.",
  strokeWidth: 1,
};

export function getSupportClassMeta(
  support_class: string | null,
): SupportClassMeta {
  if (!support_class) return UNKNOWN_SUPPORT_CLASS_META;
  return (
    SUPPORT_CLASS_META[support_class] ??
    UNKNOWN_SUPPORT_CLASS_META
  );
}

// ---------------------------------------------------------------------------
// Per-render style contracts
// ---------------------------------------------------------------------------

export interface GraphNodeStyle {
  node: ImpactNode;
  position: GraphNodePosition;
  meta: NodeTypeMeta;
  selected: boolean;
  hovered: boolean;
  dimmed: boolean;
  connected_to_selected: boolean;
}

export interface GraphEdgeStyle {
  edge: Relationship;
  edge_key: string;
  path: GraphEdgePath;
  meta: SupportClassMeta;
  selected: boolean;
  dimmed: boolean;
  connected_to_selected: boolean;
}

// ---------------------------------------------------------------------------
// Layer keys — W03 sections
// ---------------------------------------------------------------------------

export type LayerKey =
  | "targets"
  | "candidates"
  | "mechanism_of_action"
  | "candidate_comparisons";

export const LAYER_ORDER: LayerKey[] = [
  "targets",
  "candidates",
  "mechanism_of_action",
  "candidate_comparisons",
];

export const LAYER_LABELS: Record<LayerKey, string> = {
  targets: "Targets",
  candidates: "Candidates",
  mechanism_of_action: "Mechanism of action",
  candidate_comparisons: "Comparisons",
};

// ---------------------------------------------------------------------------
// Selection kind — extends W02 with "candidate"
// ---------------------------------------------------------------------------

export type DrawerKind =
  | { kind: "none" }
  | { kind: "node"; node: ImpactNode }
  | { kind: "edge"; edge: Relationship; edge_key: string }
  | { kind: "candidate"; candidate: CandidateBlock };

// ---------------------------------------------------------------------------
// Candidate filter/sort helpers
// ---------------------------------------------------------------------------

export type CandidateSortKey =
  | "activity_quality"
  | "mechanism_link_strength"
  | "evidence_diversity"
  | "data_gaps"
  | "compound_id";

export const ACTIVITY_QUALITY_LABELS: Record<
  ActivityQuality,
  string
> = {
  measured: "Measured",
  qualitative: "Qualitative",
  none: "No activity",
};

export const MECHANISM_LINK_LABELS: Record<
  MechanismLinkStrength,
  string
> = {
  direct: "Direct",
  two_hop: "Two-hop",
  indirect: "Indirect",
};

// ---------------------------------------------------------------------------
// Panel props
// ---------------------------------------------------------------------------

export interface PanelProps {
  target?: TargetBlock;
  candidate?: CandidateBlock;
  comparison?: CandidateComparisonBlock;
}
