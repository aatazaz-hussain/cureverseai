/**
 * CureVerseAI — Drug Development
 * Workflow 03 — Therapeutic Discovery
 * Graph layout.
 *
 * Pure function. Maps the W03 graph to a 2D layout with
 * five columns:
 *
 *   disease -> mechanism -> pathway -> target -> compound
 *
 * Deterministic. Node heights are computed from name
 * length. Edges are precomputed beziers.
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

const COLUMNS: GraphColumn[] = [
  "disease",
  "mechanism",
  "pathway",
  "target",
  "compound",
];

/** Node width. Wider than W02 to accommodate compound names. */
const NODE_WIDTH = 180;

/** Characters per line at 13px font inside 260px. */
const CHARS_PER_LINE = 18;

/** Maximum lines rendered. */
const MAX_LINES = 4;

/** Padding above and below the label block. */
const NODE_PADDING_Y = 22;

/** Line height for a wrapped label. */
const LINE_HEIGHT = 20;

/** Vertical gap between nodes. */
const NODE_GAP_Y = 22;

/** Horizontal gap between columns. */
const COLUMN_GAP_X = 40;

/** Outer padding. */
const PADDING_X = 28;
const PADDING_Y = 72;

// ---------------------------------------------------------------------------
// Column assignment
// ---------------------------------------------------------------------------

function columnFor(node_type: string): GraphColumn {
  switch (node_type) {
    case "disease":
      return "disease";
    case "mechanism":
    case "biological_response":
      return "mechanism";
    case "pathway":
      return "pathway";
    case "gene":
    case "target":
    case "protein":
    case "molecular_action":
      return "target";
    case "compound":
    case "molecule":
      return "compound";
    default:
      return "mechanism";
  }
}

// ---------------------------------------------------------------------------
// Node height (matches GraphNode.splitLabel)
// ---------------------------------------------------------------------------

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

function makeEdgeKey(edge: Relationship): string {
  return `${edge.source_id}|${edge.relationship_type}|${edge.target_id}`;
}

// ---------------------------------------------------------------------------
// Bezier
// ---------------------------------------------------------------------------

function buildBezierPath(
  sx: number,
  sy: number,
  tx: number,
  ty: number,
): string {
  const dx = Math.abs(tx - sx);
  const offset = Math.max(40, dx * 0.4);
  return [
    `M ${sx} ${sy}`,
    `C ${sx + offset} ${sy}`,
    `${tx - offset} ${ty}`,
    `${tx} ${ty}`,
  ].join(" ");
}

// ---------------------------------------------------------------------------
// Main layout
// ---------------------------------------------------------------------------

export function computeGraphLayout(
  nodes: ImpactNode[],
  edges: Relationship[],
): GraphLayout {
  if (!nodes.length) {
    return {
      width: 0,
      height: 0,
      nodes: [],
      edges: [],
      by_id: {},
    };
  }

  // Group by column.
  const byColumn: Record<GraphColumn, ImpactNode[]> = {
    disease: [],
    mechanism: [],
    pathway: [],
    target: [],
    compound: [],
  };

  for (const node of nodes) {
    const col = columnFor(node.node_type);
    byColumn[col].push(node);
  }

  // Column stack heights.
  const stackHeights: Record<GraphColumn, number> = {
    disease: 0,
    mechanism: 0,
    pathway: 0,
    target: 0,
    compound: 0,
  };

  for (const col of COLUMNS) {
    const colNodes = byColumn[col];
    if (!colNodes.length) continue;

    let h = 0;
    for (const n of colNodes) h += nodeHeight(n.name);
    h += (colNodes.length - 1) * NODE_GAP_Y;
    stackHeights[col] = h;
  }

  const activeColumns = COLUMNS.filter(
    (c) => byColumn[c].length > 0,
  );
  const columnCount = activeColumns.length;

  const width =
    PADDING_X * 2 +
    columnCount * NODE_WIDTH +
    Math.max(0, columnCount - 1) * COLUMN_GAP_X;

  const tallestStack = Math.max(
    ...COLUMNS.map((c) => stackHeights[c]),
    0,
  );
  const height = PADDING_Y * 2 + tallestStack;
  const centerY = height / 2;

  // Assign positions.
  const positions: GraphNodePosition[] = [];
  const by_id: Record<string, GraphNodePosition> = {};

  const columnX: Partial<Record<GraphColumn, number>> = {};
  activeColumns.forEach((col, i) => {
    columnX[col] =
      PADDING_X + i * (NODE_WIDTH + COLUMN_GAP_X);
  });

  for (const col of COLUMNS) {
    const colNodes = byColumn[col];
    if (!colNodes.length) continue;

    const stackHeight = stackHeights[col];
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

  // Edges.
  const edgePaths: GraphEdgePath[] = [];

  for (const edge of edges) {
    if (edge.source_id === edge.target_id) continue;

    const sourcePos = by_id[edge.source_id];
    const targetPos = by_id[edge.target_id];
    if (!sourcePos || !targetPos) continue;

    const sx = sourcePos.x + sourcePos.width;
    const sy = sourcePos.y + sourcePos.height / 2;
    const tx = targetPos.x;
    const ty = targetPos.y + targetPos.height / 2;

    edgePaths.push({
      edge_key: makeEdgeKey(edge),
      source_id: edge.source_id,
      target_id: edge.target_id,
      path: buildBezierPath(sx, sy, tx, ty),
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
// Column headers
// ---------------------------------------------------------------------------

export interface ColumnHeader {
  column: GraphColumn;
  label: string;
  x: number;
  y: number;
}

export function computeColumnHeaders(
  layout: GraphLayout,
): ColumnHeader[] {
  const seen = new Map<GraphColumn, number>();

  for (const pos of layout.nodes) {
    if (!seen.has(pos.column)) {
      seen.set(pos.column, pos.x);
    }
  }

  const out: ColumnHeader[] = [];

  COLUMNS.forEach((col) => {
    const x = seen.get(col);
    if (x === undefined) return;
    out.push({
      column: col,
      label: COLUMN_LABELS[col],
      x,
      y: 24,
    });
  });

  return out;
}

const COLUMN_LABELS: Record<GraphColumn, string> = {
  disease: "DISEASE",
  mechanism: "MECHANISM",
  pathway: "PATHWAY",
  target: "TARGETS",
  compound: "CANDIDATES",
};

// ---------------------------------------------------------------------------
// Export constants
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
