/**
 * CureVerseAI — Drug Development
 * Workflow 02 — Reverse Disease Engineering
 * GraphEdge — a single SVG bezier edge.
 *
 * Pure presentational component. Receives its style object
 * (precomputed path, support-class meta, selection state).
 * Renders an SVG group with the curve, a target dot, and
 * an invisible wider hit-path.
 *
 * Visual structure:
 *
 *   <g class="cv-revdis-graph-edge">
 *     <path class="...-halo" />
 *     <path class="...-curve" />
 *     <circle class="...-target" />
 *     <path class="...-hit" />
 *   </g>
 *
 * The `halo` path is a wider, lower-opacity stroke used
 * for the hover/selected glow. The `curve` is the visible
 * stroke. The `hit` is a transparent but wide path so
 * hovering does not require pixel precision.
 *
 * The target dot marks the direction of the edge — it is
 * a small circle at the target anchor. Sourced from the
 * edge path's endpoint, which we can parse from the last
 * two numbers of the SVG "d" string.
 */

"use client";

import { useCallback } from "react";

import type { GraphEdgeStyle } from "../types";

// ---------------------------------------------------------------------------
// Path endpoint extraction
// ---------------------------------------------------------------------------

/**
 * Extract the target endpoint from an SVG cubic bezier
 * path. The path format produced by graphLayout.ts is:
 *
 *   M sx sy C c1x c1y c2x c2y tx ty
 *
 * The last two numbers are the target anchor. This is a
 * pure string operation with no regex backtracking risk.
 */
function extractTargetPoint(path: string): {
  x: number;
  y: number;
} | null {
  const parts = path.trim().split(/\s+/);
  if (parts.length < 10) return null;
  const tx = parseFloat(parts[parts.length - 2]);
  const ty = parseFloat(parts[parts.length - 1]);
  if (!isFinite(tx) || !isFinite(ty)) return null;
  return { x: tx, y: ty };
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

interface GraphEdgeProps {
  style: GraphEdgeStyle;
  onSelect: (edge_key: string) => void;
}

export default function GraphEdge({
  style,
  onSelect,
}: GraphEdgeProps) {
  const {
    edge,
    edge_key,
    path,
    meta,
    selected,
    dimmed,
    connected_to_selected,
  } = style;

  const classes = ["cv-revdis-graph-edge"];
  if (selected) classes.push("is-selected");
  if (dimmed) classes.push("is-dimmed");
  if (connected_to_selected && !selected) {
    classes.push("is-connected");
  }

  const handleClick = useCallback(() => {
    onSelect(edge_key);
  }, [edge_key, onSelect]);

  const endpoint = extractTargetPoint(path.path);

  const ariaLabel =
    `${meta.label}: ${edge.source_id} to ${edge.target_id}`;

  return (
    <g
      className={classes.join(" ")}
      role="button"
      tabIndex={-1}
      aria-label={ariaLabel}
      onClick={handleClick}
      style={{ cursor: "pointer" }}
    >
      {/* Halo — wider, lower opacity, for hover/selection. */}
      <path
        className="cv-revdis-graph-edge-halo"
        d={path.path}
        fill="none"
        stroke={meta.accent}
        strokeWidth={meta.strokeWidth + 5}
        strokeLinecap="round"
        opacity={selected ? 0.28 : connected_to_selected ? 0.14 : 0}
        pointerEvents="none"
      />

      {/* The visible curve. */}
      <path
        className="cv-revdis-graph-edge-curve"
        d={path.path}
        fill="none"
        stroke={meta.accent}
        strokeWidth={
          selected ? meta.strokeWidth + 1 : meta.strokeWidth
        }
        strokeLinecap="round"
        opacity={dimmed ? 0.12 : selected ? 1 : 0.62}
      />

      {/* Target dot — marks the edge's direction. */}
      {endpoint ? (
        <circle
          className="cv-revdis-graph-edge-target"
          cx={endpoint.x}
          cy={endpoint.y}
          r={selected ? 4 : 2.5}
          fill={meta.accent}
          opacity={dimmed ? 0.15 : selected ? 1 : 0.7}
          pointerEvents="none"
        />
      ) : null}

      {/* Invisible hit path — easier hovering. */}
      <path
        className="cv-revdis-graph-edge-hit"
        d={path.path}
        fill="none"
        stroke="transparent"
        strokeWidth={14}
        pointerEvents="stroke"
      />
    </g>
  );
}
