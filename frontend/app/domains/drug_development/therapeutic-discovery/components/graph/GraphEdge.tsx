/**
 * CureVerseAI — Drug Development
 * Workflow 03 — Therapeutic Discovery
 * GraphEdge.
 *
 * Single SVG bezier edge. Pure presentational.
 */

"use client";

import { useCallback } from "react";

import type { GraphEdgeStyle } from "../types";

function extractTargetPoint(
  path: string,
): { x: number; y: number } | null {
  const parts = path.trim().split(/\s+/);
  if (parts.length < 10) return null;
  const tx = parseFloat(parts[parts.length - 2]);
  const ty = parseFloat(parts[parts.length - 1]);
  if (!isFinite(tx) || !isFinite(ty)) return null;
  return { x: tx, y: ty };
}

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

  const classes = ["cv-thedisc-graph-edge"];
  if (selected) classes.push("is-selected");
  if (dimmed) classes.push("is-dimmed");
  if (connected_to_selected && !selected) {
    classes.push("is-connected");
  }

  const handleClick = useCallback(
    () => onSelect(edge_key),
    [edge_key, onSelect],
  );

  const endpoint = extractTargetPoint(path.path);

  const ariaLabel = `${meta.label}: ${edge.source_id} to ${edge.target_id}`;

  return (
    <g
      className={classes.join(" ")}
      role="button"
      tabIndex={-1}
      aria-label={ariaLabel}
      onClick={handleClick}
      style={{ cursor: "pointer" }}
    >
      <path
        className="cv-thedisc-graph-edge-halo"
        d={path.path}
        fill="none"
        stroke={meta.accent}
        strokeWidth={meta.strokeWidth + 5}
        strokeLinecap="round"
        opacity={
          selected ? 0.28 : connected_to_selected ? 0.14 : 0
        }
        pointerEvents="none"
      />

      <path
        className="cv-thedisc-graph-edge-curve"
        d={path.path}
        fill="none"
        stroke={meta.accent}
        strokeWidth={
          selected ? meta.strokeWidth + 1 : meta.strokeWidth
        }
        strokeLinecap="round"
        opacity={dimmed ? 0.12 : selected ? 1 : 0.62}
      />

      {endpoint ? (
        <circle
          className="cv-thedisc-graph-edge-target"
          cx={endpoint.x}
          cy={endpoint.y}
          r={selected ? 4 : 2.5}
          fill={meta.accent}
          opacity={dimmed ? 0.15 : selected ? 1 : 0.7}
          pointerEvents="none"
        />
      ) : null}

      <path
        className="cv-thedisc-graph-edge-hit"
        d={path.path}
        fill="none"
        stroke="transparent"
        strokeWidth={14}
        pointerEvents="stroke"
      />
    </g>
  );
}
