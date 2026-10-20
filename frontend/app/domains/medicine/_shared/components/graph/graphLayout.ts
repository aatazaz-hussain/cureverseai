/**
 * CureVerseAI — Medicine domain
 * Graph layout helper.
 *
 * Column-based layout for the Medicine mechanism graph:
 *
 *     col 0: intervention
 *     col 1: targets
 *     col 2: pathways
 *     col 3: indicators
 *
 * The layout is deterministic — same inputs produce the same
 * positions — so the graph does not jump on re-render.
 *
 * This module only computes positions. It never invents
 * relationships; edges come from the caller.
 */

import type {
  FunctionalIndicator,
  InterventionRef,
} from "../../types";

export const NODE_WIDTH = 180;
export const NODE_HEIGHT = 52;
export const COLUMN_GAP = 64;
export const ROW_GAP = 14;

export type MedicineNodeKind =
  | "intervention"
  | "target"
  | "pathway"
  | "indicator";

export interface MedicineGraphNode {
  id: string;
  kind: MedicineNodeKind;
  label: string;
  sublabel?: string | null;
  column: number;
  row: number;
  x: number;
  y: number;
}

export interface MedicineGraphEdge {
  id: string;
  fromId: string;
  toId: string;
  kind: "observed" | "inferred" | "insufficient";
  label?: string | null;
}

export interface MedicineGraphLayout {
  nodes: MedicineGraphNode[];
  edges: MedicineGraphEdge[];
  width: number;
  height: number;
}

function computeColumnX(column: number): number {
  return column * (NODE_WIDTH + COLUMN_GAP);
}

function computeRowY(row: number): number {
  return row * (NODE_HEIGHT + ROW_GAP);
}

export interface BuildLayoutInput {
  intervention: InterventionRef | null;
  pathways: { id: string; name: string }[];
  indicators: FunctionalIndicator[];
  edges: MedicineGraphEdge[];
}

export function buildGraphLayout(input: BuildLayoutInput): MedicineGraphLayout {
  const nodes: MedicineGraphNode[] = [];

  // Column 0 — intervention.
  if (input.intervention) {
    nodes.push({
      id: input.intervention.id,
      kind: "intervention",
      label: input.intervention.name,
      sublabel: input.intervention.source,
      column: 0,
      row: 0,
      x: computeColumnX(0),
      y: computeRowY(0),
    });
  }

  // Column 1 — targets.
  const targets = input.intervention?.targets ?? [];
  targets.forEach((t, i) => {
    nodes.push({
      id: t.id,
      kind: "target",
      label: t.name,
      sublabel: t.source_id,
      column: 1,
      row: i,
      x: computeColumnX(1),
      y: computeRowY(i),
    });
  });

  // Column 2 — pathways.
  input.pathways.forEach((p, i) => {
    nodes.push({
      id: p.id,
      kind: "pathway",
      label: p.name,
      sublabel: p.id,
      column: 2,
      row: i,
      x: computeColumnX(2),
      y: computeRowY(i),
    });
  });

  // Column 3 — indicators.
  input.indicators.forEach((ind, i) => {
    nodes.push({
      id: ind.id,
      kind: "indicator",
      label: ind.name,
      sublabel: ind.direction_of_benefit,
      column: 3,
      row: i,
      x: computeColumnX(3),
      y: computeRowY(i),
    });
  });

  const maxCol = nodes.reduce((m, n) => Math.max(m, n.column), 0);
  const maxRow = nodes.reduce((m, n) => Math.max(m, n.row), 0);
  const width = computeColumnX(maxCol) + NODE_WIDTH;
  const height = computeRowY(maxRow) + NODE_HEIGHT;

  return {
    nodes,
    edges: input.edges,
    width,
    height,
  };
}

export function nodeById(
  layout: MedicineGraphLayout,
  id: string,
): MedicineGraphNode | undefined {
  return layout.nodes.find((n) => n.id === id);
}
