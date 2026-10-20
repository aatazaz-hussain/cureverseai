/**
 * CureVerseAI — Drug Development
 * Workflow 03 — Therapeutic Discovery
 * GraphNode.
 *
 * Single SVG node. Pure presentational. Receives its
 * style object and callbacks. No state.
 */

"use client";

import { useCallback, type KeyboardEvent } from "react";

import type { GraphNodeStyle } from "../types";

// ---------------------------------------------------------------------------
// Label wrapping
// ---------------------------------------------------------------------------

function splitLabel(
  name: string,
  charsPerLine = 26,
  maxLines = 4,
): string[] {
  const trimmed = name.trim();
  if (!trimmed) return [""];

  const words = trimmed.split(/\s+/);
  const lines: string[] = [];
  let current = "";

  for (const word of words) {
    if (word.length > charsPerLine) {
      if (current) {
        lines.push(current);
        current = "";
      }
      lines.push(word.slice(0, charsPerLine - 1) + "\u2026");
      continue;
    }

    const candidate = current ? current + " " + word : word;
    if (candidate.length <= charsPerLine) {
      current = candidate;
    } else {
      if (current) lines.push(current);
      current = word;
    }
  }

  if (current) lines.push(current);

  if (lines.length > maxLines) {
    const kept = lines.slice(0, maxLines);
    kept[maxLines - 1] =
      kept[maxLines - 1].slice(0, charsPerLine - 1) + "\u2026";
    return kept;
  }

  return lines;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

interface GraphNodeProps {
  style: GraphNodeStyle;
  onSelect: (node_id: string) => void;
  onHover: (node_id: string | null) => void;
}

export default function GraphNode({
  style,
  onSelect,
  onHover,
}: GraphNodeProps) {
  const {
    node,
    position,
    meta,
    selected,
    hovered,
    dimmed,
    connected_to_selected,
  } = style;

  const lines = splitLabel(node.name);

  const classes = [
    "cv-thedisc-graph-node",
    `cv-thedisc-graph-node-type-${node.node_type}`,
  ];
  if (selected) classes.push("is-selected");
  if (hovered) classes.push("is-hovered");
  if (dimmed) classes.push("is-dimmed");
  if (connected_to_selected && !selected) {
    classes.push("is-connected");
  }

  const handleClick = useCallback(
    () => onSelect(node.node_id),
    [node.node_id, onSelect],
  );
  const handleEnter = useCallback(
    () => onHover(node.node_id),
    [node.node_id, onHover],
  );
  const handleLeave = useCallback(
    () => onHover(null),
    [onHover],
  );
  const handleKey = useCallback(
    (e: KeyboardEvent<SVGGElement>) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        onSelect(node.node_id);
      }
    },
    [node.node_id, onSelect],
  );

  const { x, y, width, height } = position;

  const ACCENT_W = 3;
  const GLYPH_R = 13;
  const GLYPH_CX = x + ACCENT_W + 20;
  const GLYPH_CY = y + height / 2;
  const LABEL_X = GLYPH_CX + GLYPH_R + 12;

  const LINE_HEIGHT = 20;
  const labelCenterY = y + height / 2;
  const firstLineOffset =
    -((lines.length - 1) * LINE_HEIGHT) / 2;

  const ariaLabel = `${meta.label}: ${node.name}`;

  return (
    <g
      className={classes.join(" ")}
      role="button"
      tabIndex={0}
      aria-label={ariaLabel}
      onClick={handleClick}
      onMouseEnter={handleEnter}
      onMouseLeave={handleLeave}
      onKeyDown={handleKey}
      style={{ cursor: "pointer" }}
    >
      <rect
        className="cv-thedisc-graph-node-ring"
        x={x - 4}
        y={y - 4}
        width={width + 8}
        height={height + 8}
        rx={6}
        ry={6}
        fill="none"
        stroke={meta.accent}
        strokeWidth={1}
        opacity={selected ? 1 : 0}
      />

      <rect
        className="cv-thedisc-graph-node-body"
        x={x}
        y={y}
        width={width}
        height={height}
        rx={4}
        ry={4}
        fill="rgba(13,16,16,0.94)"
        stroke="rgba(238,233,225,0.14)"
        strokeWidth={1}
      />

      <rect
        className="cv-thedisc-graph-node-accent"
        x={x}
        y={y}
        width={ACCENT_W}
        height={height}
        fill={meta.accent}
      />

      <circle
        className="cv-thedisc-graph-node-glyph-bg"
        cx={GLYPH_CX}
        cy={GLYPH_CY}
        r={GLYPH_R}
        fill="rgba(238,233,225,0.04)"
        stroke={meta.accent}
        strokeWidth={1}
      />

      <text
        className="cv-thedisc-graph-node-glyph"
        x={GLYPH_CX}
        y={GLYPH_CY}
        textAnchor="middle"
        dominantBaseline="central"
        fill={meta.accent}
        fontSize={14}
        fontFamily="'Space Grotesk', Arial, sans-serif"
      >
        {meta.glyph}
      </text>

      <text
        className="cv-thedisc-graph-node-label"
        x={LABEL_X}
        y={labelCenterY + firstLineOffset}
        fill="#eee9e1"
        fontSize={13}
        fontFamily="'Space Grotesk', Arial, sans-serif"
      >
        {lines.map((line, i) => (
          <tspan key={i} x={LABEL_X} dy={i === 0 ? 0 : LINE_HEIGHT}>
            {line}
          </tspan>
        ))}
      </text>

      <rect
        className="cv-thedisc-graph-node-hit"
        x={x - 6}
        y={y - 6}
        width={width + 12}
        height={height + 12}
        fill="transparent"
        pointerEvents="all"
      />

      <title>{ariaLabel}</title>
    </g>
  );
}
