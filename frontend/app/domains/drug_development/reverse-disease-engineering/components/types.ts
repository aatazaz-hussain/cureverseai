/**
 * CureVerseAI — Drug Development
 * Workflow 02 — Reverse Disease Engineering
 * Component-level types and metadata.
 *
 * This file is the boundary between "the data we received"
 * (top-level types.ts) and "how we render it." Nothing here
 * talks about the AI Engine response shape — that lives in
 * ../types.ts. Everything here is a UI contract.
 *
 * Contents:
 *
 *   GraphColumn, GraphNodePosition, GraphEdgePath, GraphLayout
 *     — the output of graph/graphLayout.ts
 *
 *   NodeTypeMeta, SUPPORT_CLASS_META
 *     — static tables driving visual identity
 *
 *   GraphNodeStyle, GraphEdgeStyle
 *     — per-node / per-edge render contracts
 *
 *   LayerKey
 *     — the seven W02 investigation layers
 *
 *   DrawerKind
 *     — evidence inspector state
 */

import type {
  ImpactNode,
  Relationship,
} from "../types";

// ---------------------------------------------------------------------------
// Graph layout
// ---------------------------------------------------------------------------

/**
 * The five columns of the W02 graph, left to right.
 * Matches the investigation direction:
 *
 *   disease -> phenotype -> mechanism -> gene -> pathway
 */
export type GraphColumn =
  | "disease"
  | "phenotype"
  | "mechanism"
  | "gene"
  | "pathway";

/**
 * Where a single node lives in the layout.
 */
export interface GraphNodePosition {
  node_id: string;
  column: GraphColumn;
  x: number;
  y: number;
  width: number;
  height: number;
}

/**
 * Precomputed bezier geometry for a single edge. The
 * component does not need to redo the math.
 */
export interface GraphEdgePath {
  edge_key: string;
  source_id: string;
  target_id: string;
  /** SVG path "d" attribute for the curve. */
  path: string;
  /** Label anchor (midpoint) coordinates for optional markers. */
  label_x: number;
  label_y: number;
}

/**
 * The complete layout computed from a set of nodes and
 * edges. Pure data — no React.
 */
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

/**
 * Static metadata describing how each node type is
 * rendered. Accent colors are drawn from the design system
 * (see reverse-disease-engineering.css and globals.css).
 *
 * The glyph is a single character rendered inside the node
 * badge. Deliberately monochrome glyphs — differentiation
 * comes from color, not from icon complexity.
 */
export interface NodeTypeMeta {
  label: string;
  accent: string;
  glyph: string;
  description: string;
}

/**
 * The canonical mapping from a node_type value to its
 * visual identity.
 *
 * Any node_type not present here falls back to the
 * "unknown" entry — see getNodeTypeMeta() below.
 */
export const NODE_TYPE_META: Record<string, NodeTypeMeta> = {
  disease: {
    label: "Disease",
    accent: "#e0525a",
    glyph: "◉",
    description:
      "The disease you asked about, matched to an official record.",
  },
  phenotype: {
    label: "Symptom",
    accent: "#e9c58c",
    glyph: "◐",
    description:
      "An observable feature that has been recorded for this disease.",
  },
  mechanism: {
    label: "Evidence type",
    accent: "#6ee7f2",
    glyph: "◇",
    description:
      "A type of evidence linking the disease to its associated genes (e.g. published research, DNA studies). Not a named biological mechanism.",
  },
  gene: {
    label: "Gene",
    accent: "#b9b5d4",
    glyph: "▣",
    description:
      "A gene that scientific databases link to this disease.",
  },
  variant: {
    label: "Variant",
    accent: "#c8a4e0",
    glyph: "◆",
    description:
      "A genetic variant. Not populated in Phase 1.",
  },
  pathway: {
    label: "Biological process",
    accent: "#7bcab5",
    glyph: "⬡",
    description:
      "A group of genes that work together in the body. Recorded in Reactome.",
  },
  protein: {
    label: "Protein",
    accent: "#a4c8e0",
    glyph: "◈",
    description:
      "A protein. Not populated by W02 in Phase 1.",
  },
  molecule: {
    label: "Molecule",
    accent: "#e0c8a4",
    glyph: "○",
    description:
      "A molecule. Not populated by W02 in Phase 1.",
  },
  manifestation: {
    label: "Manifestation",
    accent: "#a4e0c8",
    glyph: "◌",
    description:
      "A clinical manifestation. Not separately sourced in Phase 1.",
  },
  factor: {
    label: "Contributing Factor",
    accent: "#c8a4a4",
    glyph: "◒",
    description:
      "A contributing factor synthesized from datasource counts.",
  },
};

/**
 * Fallback metadata for unrecognized node types. Ensures
 * that even an unknown node renders without crashing.
 */
export const UNKNOWN_NODE_TYPE_META: NodeTypeMeta = {
  label: "Entity",
  accent: "#888e90",
  glyph: "◯",
  description: "An entity of an unrecognized type.",
};

/**
 * Look up the visual metadata for a node.
 * Never throws — falls back to UNKNOWN_NODE_TYPE_META.
 */
export function getNodeTypeMeta(node_type: string): NodeTypeMeta {
  return (
    NODE_TYPE_META[node_type] ?? UNKNOWN_NODE_TYPE_META
  );
}

// ---------------------------------------------------------------------------
// Support class visual identity
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
      "Directly recorded in a scientific database. No inference involved.",
    strokeWidth: 2,
  },
  supported_association: {
    label: "Research link",
    accent: "#e0525a",
    description:
      "Backed by published research or DNA studies. A likely link, not proof of cause.",
    strokeWidth: 1.5,
  },
  mechanistic_inference: {
    label: "Inferred link",
    accent: "#e9c58c",
    description:
      "Inferred by combining several other supported links. Not directly recorded.",
    strokeWidth: 1.25,
  },
  unknown: {
    label: "Not classified",
    accent: "#5f5b55",
    description:
      "No evidence category assigned to this link.",
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
  if (!support_class) {
    return UNKNOWN_SUPPORT_CLASS_META;
  }
  return (
    SUPPORT_CLASS_META[support_class] ??
    UNKNOWN_SUPPORT_CLASS_META
  );
}

// ---------------------------------------------------------------------------
// Per-render style contracts
// ---------------------------------------------------------------------------

/**
 * The render state of a single node. Computed once per
 * render in MechanismGraph and passed to GraphNode.
 *
 * `dimmed` is set when the current filter or selection
 * hides this node from emphasis. `selected` and `hovered`
 * are self-explanatory.
 */
export interface GraphNodeStyle {
  node: ImpactNode;
  position: GraphNodePosition;
  meta: NodeTypeMeta;
  selected: boolean;
  hovered: boolean;
  dimmed: boolean;
  connected_to_selected: boolean;
}

/**
 * The render state of a single edge.
 */
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
// Investigation layer keys
// ---------------------------------------------------------------------------

/**
 * The seven keys inside ReverseDiseaseResult.mechanistic_investigation.
 * Used for iteration and for labelling layer panels.
 */
export type LayerKey =
  | "phenotypes"
  | "contributing_factors"
  | "mechanisms"
  | "genes"
  | "variants"
  | "pathways"
  | "manifestations";

export const LAYER_ORDER: LayerKey[] = [
  "phenotypes",
  "contributing_factors",
  "mechanisms",
  "genes",
  "variants",
  "pathways",
  "manifestations",
];

export const LAYER_LABELS: Record<LayerKey, string> = {
  phenotypes: "Phenotypes",
  contributing_factors: "Contributing factors",
  mechanisms: "Mechanisms",
  genes: "Genes",
  variants: "Variants",
  pathways: "Pathways",
  manifestations: "Manifestations",
};

// ---------------------------------------------------------------------------
// Evidence inspector
// ---------------------------------------------------------------------------

/**
 * Which kind of graph element the inspector is showing.
 * `null` means the inspector is closed (or in its
 * placeholder state).
 */
export type DrawerKind =
  | { kind: "none" }
  | { kind: "node"; node: ImpactNode }
  | { kind: "edge"; edge: Relationship; edge_key: string };
