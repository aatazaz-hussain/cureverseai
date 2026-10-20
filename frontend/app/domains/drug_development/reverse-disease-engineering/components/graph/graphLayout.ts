/**
 * CureVerseAI — Drug Development
 * Workflow 02 — Reverse Disease Engineering
 * Graph layout.
 *
 * Pure function. No React. Maps a set of W02 graph nodes
 * and edges to 2D coordinates and precomputed SVG bezier
 * paths.
 *
 * Column model
 * ------------
 *
 * Five columns, left to right, matching the W02
 * investigation direction:
 *
 *   disease -> phenotype -> mechanism -> gene -> pathway
 *
 * Each column stacks its nodes vertically, centered on the
 * SVG's vertical midpoint. Edges connect from the right
 * side of the source node to the left side of the target
 * node.
 *
 * Determinism
 * -----------
 *
 * Same input always produces the same layout. Nodes are
 * laid out in input order within each column. No
 * randomness, no time-dependence.
 *
 * What this module does NOT do
 * ----------------------------
 *
 * - It does not filter nodes or edges. Callers pass the
 *   full graph; filtering is a render-time concern.
 * - It does not measure text. Node heights are computed
 *   from a simple name-length heuristic.
 * - It does not throw on malformed input. Edges that
 *   reference missing nodes are dropped silently.
 */

import type {
  ImpactNode,
  Relationship,
} from "../../types";

import type {
  GraphColumn,
  GraphEdgePath,
  GraphLayout,
  GraphNodePosition,
} from "../types";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

/** The five columns, in order. */
const COLUMNS: GraphColumn[] = [
  "disease",
  "phenotype",
  "mechanism",
  "gene",
  "pathway",
];

/** Fixed node width. */
const NODE_WIDTH = 280;

/**
 * Characters per line the graph renderer can fit at 13px
 * font size inside a 280px node. Kept in sync with
 * GraphNode.splitLabel's default.
 */
const CHARS_PER_LINE = 28;

/** Maximum lines the renderer will produce. */
const MAX_LINES = 4;

/** Vertical padding above and below the label block. */
const NODE_PADDING_Y = 20;

/** Line height for a wrapped label. */
const LINE_HEIGHT = 20;

/** Vertical gap between nodes in the same column. */
const NODE_GAP_Y = 22;

/** Horizontal gap between columns. */
const COLUMN_GAP_X = 120;

/** Outer padding around the whole layout. */
const PADDING_X = 40;
const PADDING_Y = 60;

// ---------------------------------------------------------------------------
// Column assignment
// ---------------------------------------------------------------------------

/**
 * The column a node belongs to, based on its node_type.
 *
 * Falls back to "mechanism" for unrecognized types. W02
 * does not emit unrecognized types in practice, but a
 * fallback keeps the layout from dropping nodes.
 */
function columnFor(node_type: string): GraphColumn {
  switch (node_type) {
    case "disease":
      return "disease";
    case "phenotype":
    case "manifestation":
      return "phenotype";
    case "mechanism":
    case "factor":
      return "mechanism";
    case "gene":
    case "variant":
    case "protein":
    case "molecule":
      return "gene";
    case "pathway":
      return "pathway";
    default:
      return "mechanism";
  }
}

// ---------------------------------------------------------------------------
// Node sizing
// ---------------------------------------------------------------------------

/**
 * Estimate how many display lines a name will occupy given
 * the CHARS_PER_LINE budget. Matches GraphNode.splitLabel's
 * word-wrap algorithm.
 */
function estimateLineCount(name: string): number {
  const trimmed = (name || "").trim();
  if (!trimmed) return 1;

  const words = trimmed.split(/\s+/);
  let lines = 1;
  let current = 0;

  for (const word of words) {
    if (word.length > CHARS_PER_LINE) {
      if (current > 0) {
        lines += 1;
        current = 0;
      }
      lines += 1;
      continue;
    }
    const candidateLen =
      current === 0 ? word.length : current + 1 + word.length;
    if (candidateLen <= CHARS_PER_LINE) {
      current = candidateLen;
    } else {
      lines += 1;
      current = word.length;
    }
  }

  return Math.min(lines, MAX_LINES);
}

function nodeHeight(name: string): number {
  const lines = estimateLineCount(name);
  return NODE_PADDING_Y * 2 + lines * LINE_HEIGHT;
}

// ---------------------------------------------------------------------------
// Edge key
// ---------------------------------------------------------------------------

/**
 * Canonical edge key, matching edgeKey() in ../../types.ts.
 * Kept local so this module does not depend on the top-
 * level types file at runtime.
 */
function makeEdgeKey(edge: Relationship): string {
  return `${edge.source_id}|${edge.relationship_type}|${edge.target_id}`;
}

// ---------------------------------------------------------------------------
// Bezier path builder
// ---------------------------------------------------------------------------

/**
 * A cubic bezier curve between two anchor points.
 *
 * `sourceX` is the right edge of the source node.
 * `sourceY` is the vertical center of the source node.
 * `targetX` is the left edge of the target node.
 * `targetY` is the vertical center of the target node.
 *
 * The control points push outward horizontally so the
 * curve reads as a smooth S-shape in the left-to-right
 * direction.
 */
function buildBezierPath(
  sourceX: number,
  sourceY: number,
  targetX: number,
  targetY: number,
): string {
  const dx = Math.abs(targetX - sourceX);
  const offset = Math.max(40, dx * 0.4);

  const c1x = sourceX + offset;
  const c1y = sourceY;
  const c2x = targetX - offset;
  const c2y = targetY;

  return [
    `M ${sourceX} ${sourceY}`,
    `C ${c1x} ${c1y}`,
    `${c2x} ${c2y}`,
    `${targetX} ${targetY}`,
  ].join(" ");
}

// ---------------------------------------------------------------------------
// Main layout
// ---------------------------------------------------------------------------

/**
 * Compute a GraphLayout from a set of nodes and edges.
 *
 * See the module docstring for the column model and
 * determinism guarantees.
 */
export function computeGraphLayout(
  nodes: ImpactNode[],
  edges: Relationship[],
): GraphLayout {
  // ---- Empty graph -----------------------------------------
  if (!nodes.length) {
    return {
      width: 0,
      height: 0,
      nodes: [],
      edges: [],
      by_id: {},
    };
  }

  // ---- Group nodes by column ------------------------------
  const byColumn: Record<GraphColumn, ImpactNode[]> = {
    disease: [],
    phenotype: [],
    mechanism: [],
    gene: [],
    pathway: [],
  };

  for (const node of nodes) {
    const col = columnFor(node.node_type);
    byColumn[col].push(node);
  }

  // ---- Compute each column's stack height -----------------
  const columnStackHeights: Record<GraphColumn, number> = {
    disease: 0,
    phenotype: 0,
    mechanism: 0,
    gene: 0,
    pathway: 0,
  };

  for (const col of COLUMNS) {
    const colNodes = byColumn[col];
    if (!colNodes.length) {
      columnStackHeights[col] = 0;
      continue;
    }

    let h = 0;
    for (const node of colNodes) {
      h += nodeHeight(node.name);
    }
    h += (colNodes.length - 1) * NODE_GAP_Y;
    columnStackHeights[col] = h;
  }

  // ---- Total SVG dimensions -------------------------------
  // Total width: every column gets NODE_WIDTH, plus gaps
  // between them, plus outer padding.
  const activeColumns = COLUMNS.filter(
    (c) => byColumn[c].length > 0,
  );

  const columnCount = activeColumns.length;

  const width =
    PADDING_X * 2 +
    columnCount * NODE_WIDTH +
    Math.max(0, columnCount - 1) * COLUMN_GAP_X;

  // Total height: tallest column stack + top/bottom padding.
  const tallestStack = Math.max(
    ...COLUMNS.map((c) => columnStackHeights[c]),
    0,
  );

  const height = PADDING_Y * 2 + tallestStack;

  // Vertical midpoint — every column centers around this.
  const centerY = height / 2;

  // ---- Assign positions -----------------------------------
  const positions: GraphNodePosition[] = [];
  const by_id: Record<string, GraphNodePosition> = {};

  // Column x: leftmost active column starts at PADDING_X.
  // Inactive columns do not consume horizontal space, so
  // the layout compresses when a layer is empty.
  const columnX: Partial<Record<GraphColumn, number>> = {};

  activeColumns.forEach((col, i) => {
    columnX[col] =
      PADDING_X + i * (NODE_WIDTH + COLUMN_GAP_X);
  });

  for (const col of COLUMNS) {
    const colNodes = byColumn[col];
    if (!colNodes.length) continue;

    const stackHeight = columnStackHeights[col];
    let y = centerY - stackHeight / 2;
    const x = columnX[col] as number;

    for (const node of colNodes) {
      const h = nodeHeight(node.name);

      const position: GraphNodePosition = {
        node_id: node.node_id,
        column: col,
        x,
        y,
        width: NODE_WIDTH,
        height: h,
      };

      positions.push(position);
      by_id[node.node_id] = position;

      y += h + NODE_GAP_Y;
    }
  }

  // ---- Precompute edge paths ------------------------------
  const edgePaths: GraphEdgePath[] = [];

  for (const edge of edges) {
    // Self-loops are meaningless in this layout.
    if (edge.source_id === edge.target_id) continue;

    const sourcePos = by_id[edge.source_id];
    const targetPos = by_id[edge.target_id];

    // Drop edges that reference missing nodes. This keeps
    // the layout robust against upstream data errors and
    // mirrors the AI Engine's own integrity checks.
    if (!sourcePos || !targetPos) continue;

    const sx = sourcePos.x + sourcePos.width;
    const sy = sourcePos.y + sourcePos.height / 2;

    const tx = targetPos.x;
    const ty = targetPos.y + targetPos.height / 2;

    const path = buildBezierPath(sx, sy, tx, ty);

    edgePaths.push({
      edge_key: makeEdgeKey(edge),
      source_id: edge.source_id,
      target_id: edge.target_id,
      path,
      label_x: (sx + tx) / 2,
      label_y: (sy + ty) / 2 - 6,
    });
  }

  return {
    width,
    height,
    nodes: positions,
    edges: edgePaths,
    by_id,
  };
}

// ---------------------------------------------------------------------------
// Column header positions
// ---------------------------------------------------------------------------

export interface ColumnHeader {
  column: GraphColumn;
  label: string;
  x: number;
  y: number;
}

/**
 * Compute the header position for each active column.
 * Called by MechanismGraph to render column labels at the
 * top of the SVG.
 *
 * `y` is a fixed offset below the top of the SVG.
 */
export function computeColumnHeaders(
  layout: GraphLayout,
): ColumnHeader[] {
  const byColumn = new Map<GraphColumn, number>();

  for (const pos of layout.nodes) {
    if (!byColumn.has(pos.column)) {
      byColumn.set(pos.column, pos.x);
    }
  }

  const headers: ColumnHeader[] = [];

  COLUMNS.forEach((col) => {
    const x = byColumn.get(col);
    if (x === undefined) return;

    headers.push({
      column: col,
      label: COLUMN_LABELS[col],
      x,
      y: 24,
    });
  });

  return headers;
}

const COLUMN_LABELS: Record<GraphColumn, string> = {
  disease: "DISEASE",
  phenotype: "SYMPTOMS",
  mechanism: "EVIDENCE TYPE",
  gene: "GENES",
  pathway: "BIOLOGICAL PROCESSES",
};

// ---------------------------------------------------------------------------
// Exports for tests / callers
// ---------------------------------------------------------------------------

export const GRAPH_LAYOUT_CONSTANTS = {
  COLUMNS,
  NODE_WIDTH,
  CHARS_PER_LINE,
  MAX_LINES,
  NODE_PADDING_Y,
  LINE_HEIGHT,
  NODE_GAP_Y,
  COLUMN_GAP_X,
  PADDING_X,
  PADDING_Y,
  COLUMN_LABELS,
} as const;
