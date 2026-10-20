/**
 * CureVerseAI — Drug Development
 * Workflow 02 — Reverse Disease Engineering
 * GraphNode — a single SVG node.
 *
 * Pure presentational component. Receives its style object
 * (position, meta, selection state) and two callbacks
 * (onSelect, onHover). Renders an SVG group. No state, no
 * effects, no layout math.
 *
 * Visual structure:
 *
 *   <g class="cv-revdis-graph-node">
 *     <rect class="...-body" />
 *     <rect class="...-accent" />
 *     <circle class="...-glyph-bg" />
 *     <text class="...-glyph" />
 *     <text class="...-label" />
 *     [two-line label variant]
 *   </g>
 *
 * CSS classes are declared in components/graph/graph.css
 * (written at Step 20). This component only sets classes
 * and inline geometry.
 *
 * Accessibility:
 *   - role="button"
 *   - tabIndex=0
 *   - aria-label with the node name and type
 *   - Enter/Space triggers onSelect
 */

"use client";

import { useCallback, type KeyboardEvent } from "react";

import type { GraphNodeStyle } from "../types";

// ---------------------------------------------------------------------------
// Label helpers
// ---------------------------------------------------------------------------

/**
 * Split a name into up to two lines for display. Names
 * shorter than the wrap threshold stay on one line.
 *
 * The split is by whitespace, nearest the midpoint. If
 * the name has no whitespace, we do not break it (long
 * single tokens are rare — mostly gene symbols like
 * ADORA2B, which are short).
 */
function splitLabel(
  name: string,
  singleLineMax = 24,
  twoLineMax = 48,
): string[] {
  const trimmed = name.trim();

  if (trimmed.length <= singleLineMax) {
    return [trimmed];
  }

  if (trimmed.length > twoLineMax) {
    // Truncate the second line with an ellipsis.
    const head = trimmed.slice(0, twoLineMax);
    const cut = head.lastIndexOf(" ");
    const safeHead =
      cut > singleLineMax ? head.slice(0, cut) : head;
    const parts = safeHead.split(/\s+/);
    if (parts.length === 1) {
      return [safeHead + "…"];
    }
    const mid = Math.ceil(parts.length / 2);
    const lineOne = parts.slice(0, mid).join(" ");
    const lineTwo =
      parts.slice(mid).join(" ") + "…";
    return [lineOne, lineTwo];
  }

  const parts = trimmed.split(/\s+/);
  if (parts.length === 1) {
    return [trimmed];
  }

  const mid = Math.ceil(parts.length / 2);
  return [
    parts.slice(0, mid).join(" "),
    parts.slice(mid).join(" "),
  ];
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
  const { node, position, meta, selected, hovered, dimmed, connected_to_selected } =
    style;

  const lines = splitLabel(node.name);

  // Class composition. Every visual state is a discrete
  // class so CSS in graph.css can target it. No inline
  // styling of visual states.
  const classes = [
    "cv-revdis-graph-node",
    `cv-revdis-graph-node-type-${node.node_type}`,
  ];
  if (selected) classes.push("is-selected");
  if (hovered) classes.push("is-hovered");
  if (dimmed) classes.push("is-dimmed");
  if (connected_to_selected && !selected) {
    classes.push("is-connected");
  }

  const handleClick = useCallback(() => {
    onSelect(node.node_id);
  }, [node.node_id, onSelect]);

  const handleMouseEnter = useCallback(() => {
    onHover(node.node_id);
  }, [node.node_id, onHover]);

  const handleMouseLeave = useCallback(() => {
    onHover(null);
  }, [onHover]);

  const handleKeyDown = useCallback(
    (e: KeyboardEvent<SVGGElement>) => {
      if (e.key === "Enter" || e.key === " ") {
        e.preventDefault();
        onSelect(node.node_id);
      }
    },
    [node.node_id, onSelect],
  );

  // Geometry.
  const { x, y, width, height } = position;

  // The accent bar: 3px wide vertical strip on the left.
  const ACCENT_W = 3;

  // The glyph sits inside a small circle at the left.
  const GLYPH_R = 11;
  const GLYPH_CX = x + ACCENT_W + 16;
  const GLYPH_CY = y + height / 2;

  // The label starts just to the right of the glyph.
  const LABEL_X = GLYPH_CX + GLYPH_R + 10;
  const LABEL_MAX_W = x + width - LABEL_X - 12;

  // Label vertical anchoring. One-line: centered. Two-line:
  // lines straddle the vertical center.
  const isTwoLine = lines.length === 2;
  const LINE_HEIGHT = 14;
  const labelCenterY = y + height / 2;
  const firstLineOffset = -((lines.length - 1) * LINE_HEIGHT) / 2;

  const ariaLabel = `${meta.label}: ${node.name}`;

  return (
    <g
      className={classes.join(" ")}
      role="button"
      tabIndex={0}
      aria-label={ariaLabel}
      onClick={handleClick}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      onKeyDown={handleKeyDown}
      style={{ cursor: "pointer" }}
    >
      {/* Selection ring, only visible when selected. */}
      <rect
        className="cv-revdis-graph-node-ring"
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

      {/* Node body. */}
      <rect
        className="cv-revdis-graph-node-body"
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

      {/* Left accent bar. */}
      <rect
        className="cv-revdis-graph-node-accent"
        x={x}
        y={y}
        width={ACCENT_W}
        height={height}
        fill={meta.accent}
      />

      {/* Glyph circle. */}
      <circle
        className="cv-revdis-graph-node-glyph-bg"
        cx={GLYPH_CX}
        cy={GLYPH_CY}
        r={GLYPH_R}
        fill="rgba(238,233,225,0.04)"
        stroke={meta.accent}
        strokeWidth={1}
      />

      {/* Glyph character. */}
      <text
        className="cv-revdis-graph-node-glyph"
        x={GLYPH_CX}
        y={GLYPH_CY}
        textAnchor="middle"
        dominantBaseline="central"
        fill={meta.accent}
        fontSize={12}
        fontFamily="'Space Grotesk', Arial, sans-serif"
      >
        {meta.glyph}
      </text>

      {/* Label — 1..N lines, vertically centered. */}
      <text
        className="cv-revdis-graph-node-label"
        x={LABEL_X}
        y={labelCenterY + firstLineOffset}
        fill="#eee9e1"
        fontSize={13}
        fontFamily="'Space Grotesk', Arial, sans-serif"
      >
        {lines.map((line, i) => (
          <tspan
            key={i}
            x={LABEL_X}
            dy={i === 0 ? 0 : LINE_HEIGHT}
          >
            {line}
          </tspan>
        ))}
      </text>

      {/* Invisible wider hit-area, so hovering the node
          does not require precision. */}
      <rect
        className="cv-revdis-graph-node-hit"
        x={x - 6}
        y={y - 6}
        width={width + 12}
        height={height + 12}
        fill="transparent"
        pointerEvents="all"
      />

      {/* Truncation guard — kept for future work. */}
      <title>{ariaLabel}</title>
    </g>
  );
}
