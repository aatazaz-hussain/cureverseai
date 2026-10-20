"use client";

/**
 * CureVerseAI — Medicine domain
 * Graph edge.
 *
 * Renders one bezier edge between two nodes. Edge kind is
 * styled distinctly so observed, inferred and insufficient
 * relationships are visually separable.
 */

import type {
  MedicineGraphEdge,
  MedicineGraphLayout,
} from "./graphLayout";
import { NODE_WIDTH, NODE_HEIGHT, nodeById } from "./graphLayout";

interface Props {
  edge: MedicineGraphEdge;
  layout: MedicineGraphLayout;
}

export default function GraphEdge({ edge, layout }: Props) {
  const from = nodeById(layout, edge.fromId);
  const to = nodeById(layout, edge.toId);

  if (!from || !to) return null;

  const x1 = from.x + NODE_WIDTH;
  const y1 = from.y + NODE_HEIGHT / 2;
  const x2 = to.x;
  const y2 = to.y + NODE_HEIGHT / 2;

  const midX = (x1 + x2) / 2;
  const path = `M ${x1} ${y1} C ${midX} ${y1}, ${midX} ${y2}, ${x2} ${y2}`;

  return (
    <path
      d={path}
      className={
        "cv-medicine-wf-gedge cv-medicine-wf-gedge--" + edge.kind
      }
      fill="none"
      markerEnd="url(#cv-medicine-wf-arrow)"
    />
  );
}
