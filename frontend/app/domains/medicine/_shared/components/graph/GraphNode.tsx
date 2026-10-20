"use client";

/**
 * CureVerseAI — Medicine domain
 * Graph node.
 *
 * Renders one MedicineGraphNode. The wrapper is a button so
 * that every node is focusable and clickable without a mouse.
 */

import type { MedicineGraphNode } from "./graphLayout";
import { NODE_WIDTH, NODE_HEIGHT } from "./graphLayout";

interface Props {
  node: MedicineGraphNode;
  selected?: boolean;
  onClick?: (id: string) => void;
}

export default function GraphNode({ node, selected, onClick }: Props) {
  return (
    <button
      type="button"
      className={
        "cv-medicine-wf-gnode cv-medicine-wf-gnode--" +
        node.kind +
        (selected ? " cv-medicine-wf-gnode--selected" : "")
      }
      style={{
        left: node.x,
        top: node.y,
        width: NODE_WIDTH,
        height: NODE_HEIGHT,
      }}
      onClick={() => onClick?.(node.id)}
      aria-label={`${node.kind}: ${node.label}`}
    >
      <span className="cv-medicine-wf-gnode-kind">{node.kind}</span>
      <span className="cv-medicine-wf-gnode-label">{node.label}</span>
      {node.sublabel ? (
        <span className="cv-medicine-wf-gnode-sub">{node.sublabel}</span>
      ) : null}
    </button>
  );
}
