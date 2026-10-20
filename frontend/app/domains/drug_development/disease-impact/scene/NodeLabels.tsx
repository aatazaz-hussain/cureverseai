/**
 * CureVerseAI — Disease → Biological Impact
 * Node labels.
 *
 * HTML labels floating above nodes in the focused ring.
 * Labels are rendered through drei's <Html> so they're
 * crisp text (not 3D geometry) and participate in the
 * page's font stack.
 *
 * Behavior:
 *
 *   - Labels appear only for nodes belonging to the
 *     currently focused stage's ring (spec §15: "labels
 *     for the focused ring").
 *   - Hovered node's label is always shown, even if it is
 *     outside the focused ring — so hover works globally.
 *   - A hard cap (LABEL_MAX_PER_RING) prevents DOM
 *     explosion if a ring has hundreds of nodes.
 */

"use client";

import { Html } from "@react-three/drei";

import type { LaidOutNode } from "./sceneLayout";

import {
  LABEL_MAX_PER_RING,
  LABEL_OFFSET_Y,
  NODE_COLORS,
} from "./constants";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface NodeLabelsProps {
  nodes: LaidOutNode[];
  /** Node ids belonging to the focused ring. */
  focusedNodeIds: Set<string>;
  /** Currently hovered node id, or null. */
  hoveredId: string | null;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function NodeLabels({
  nodes,
  focusedNodeIds,
  hoveredId,
}: NodeLabelsProps) {
  // Decide which labels to render:
  //   1. Hovered node always (if it's in the scene)
  //   2. Focused-ring nodes, up to the cap
  const labels: LaidOutNode[] = [];

  const focusedList = nodes.filter((n) =>
    focusedNodeIds.has(n.id),
  );

  const hoveredNode = hoveredId
    ? nodes.find((n) => n.id === hoveredId) ?? null
    : null;

  // Hovered first
  if (hoveredNode) {
    labels.push(hoveredNode);
  }

  // Focused ring (skip duplicate if hovered is in it)
  for (const node of focusedList) {
    if (labels.length >= LABEL_MAX_PER_RING) break;
    if (hoveredNode && node.id === hoveredNode.id) continue;
    labels.push(node);
  }

  return (
    <>
      {labels.map((node) => {
        const isHovered = node.id === hoveredId;
        const [x, y, z] = node.position;
        const color =
          NODE_COLORS[node.type] ?? "#8a8a8a";

        return (
          <Html
            key={node.id}
            position={[x, y + LABEL_OFFSET_Y, z]}
            center
            distanceFactor={40}
            zIndexRange={[15, 0]}
            wrapperClass="cv-dia-label-wrapper"
            style={{
              pointerEvents: "none",
              whiteSpace: "nowrap",
            }}
          >
            <div
              className={
                "cv-dia-label" +
                (isHovered ? " cv-dia-label-hovered" : "")
              }
            >
              <span
                className="cv-dia-label-dot"
                style={{ backgroundColor: color }}
              />
              <span className="cv-dia-label-text">
                {node.label}
              </span>
            </div>
          </Html>
        );
      })}
    </>
  );
}
