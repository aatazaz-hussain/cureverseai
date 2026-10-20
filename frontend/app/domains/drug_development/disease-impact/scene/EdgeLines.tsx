/**
 * CureVerseAI — Disease → Biological Impact
 * Scene edges — curved, color-coded.
 *
 * Every edge is a quadratic bezier from source to
 * target, with a control point offset perpendicular to
 * the straight-line direction. This turns the starburst
 * (168 straight lines radiating from the disease node)
 * into a fan where each edge has visible spatial
 * separation.
 *
 * Vertex colors:
 *
 *   The color of each edge comes from its TARGET node
 *   type. That way, a glance at the graph reveals the
 *   composition of the disease's evidence:
 *
 *     blue    -> genes / proteins
 *     tan     -> tissues
 *     teal    -> cells
 *     magenta -> pathways
 *     amber   -> systems
 *
 * Brightness encodes opacity (see buildColors). The
 * final color written to the vertex buffer is
 * color * alpha, which on the dark background reads as
 * transparent.
 *
 * Hover behavior:
 *   - Hovered node's edges brighten to HIGHLIGHT_EDGE_OPACITY.
 *   - Other edges dim to DIMMED_EDGE_OPACITY.
 *   - When nothing is hovered, edges use their per-edge
 *     evidence-level opacity, damped globally by
 *     IMPACT_EDGE_DAMPING.
 */

"use client";

import { useEffect, useMemo, useRef } from "react";
import {
  BufferAttribute,
  BufferGeometry,
  Color,
  LineBasicMaterial,
} from "three";
import type { LineSegments } from "three";

import type { LaidOutEdge, LaidOutNode } from "./sceneLayout";

import {
  DIMMED_EDGE_OPACITY,
  HIGHLIGHT_EDGE_OPACITY,
  IMPACT_EDGE_DAMPING,
  NODE_COLORS,
} from "./constants";
import type { NodeType } from "../types";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

/** Segments per curve. Higher = smoother, more vertices. */
const SEGMENTS_PER_CURVE = 8;

/**
 * Perpendicular offset magnitude as a fraction of the
 * edge length. 0.08 gives a subtle fan; 0.15 is more
 * dramatic; 0.25 is a strong horseshoe.
 */
const CURVE_BOW = 0.12;

// ---------------------------------------------------------------------------
// Per-edge control point
// ---------------------------------------------------------------------------

/**
 * Compute the quadratic bezier control point for an edge.
 *
 * The control point sits at the midpoint of the straight
 * line, offset perpendicular to it. A stable per-edge
 * sign keeps the fan visually coherent.
 */
function controlPoint(
  src: [number, number, number],
  dst: [number, number, number],
  sign: number,
): [number, number, number] {
  const mx = (src[0] + dst[0]) * 0.5;
  const my = (src[1] + dst[1]) * 0.5;
  const mz = (src[2] + dst[2]) * 0.5;

  // Direction from src to dst.
  const dx = dst[0] - src[0];
  const dy = dst[1] - src[1];
  const dz = dst[2] - src[2];

  const len = Math.sqrt(dx * dx + dy * dy + dz * dz) || 1;

  // Perpendicular in the plane defined by (dir, world up).
  // If dir is nearly vertical, use world X instead.
  const upX = 0;
  const upY = 1;
  const upZ = 0;

  // cross(dir, up)
  let px = dy * upZ - dz * upY;
  let py = dz * upX - dx * upZ;
  let pz = dx * upY - dy * upX;

  const plen = Math.sqrt(px * px + py * py + pz * pz) || 1;

  px /= plen;
  py /= plen;
  pz /= plen;

  const bow = CURVE_BOW * len * sign;

  return [mx + px * bow, my + py * bow, mz + pz * bow];
}

// ---------------------------------------------------------------------------
// Geometry build
// ---------------------------------------------------------------------------

/**
 * Build flat position and color buffers for all edges.
 *
 * Each edge contributes SEGMENTS_PER_CURVE line segments,
 * so the position array has
 *   edges.length * SEGMENTS_PER_CURVE * 6
 * floats.
 *
 * Colors are per-vertex. Source vertex gets the target
 * node's color at 40% brightness; successive segments
 * brighten toward the target end, which gets 100%.
 * This gives a natural "flow" from disease to leaf.
 */
function buildBuffers(
  edges: LaidOutEdge[],
  nodeColorsById: Map<string, string>,
  hoveredId: string | null,
  connectedIds: Set<string> | null,
  focusedNodeIds: Set<string> | null,
): { positions: Float32Array; colors: Float32Array } {
  const segCount = SEGMENTS_PER_CURVE;
  const totalSegs = edges.length * segCount;

  const positions = new Float32Array(totalSegs * 6);
  const colors = new Float32Array(totalSegs * 6);

  const tmpColor = new Color();

  let pOffset = 0;
  let cOffset = 0;

  for (let i = 0; i < edges.length; i++) {
    const edge = edges[i];

    // ---- Focus filter -----------------------------------
    if (focusedNodeIds !== null) {
      const touchesFocus =
        focusedNodeIds.has(edge.source) ||
        focusedNodeIds.has(edge.target);
      if (!touchesFocus) continue;
    }

    // ---- Alpha decision ---------------------------------
    let alpha: number;

    if (hoveredId === null) {
      alpha = edge.opacity * IMPACT_EDGE_DAMPING;
    } else {
      const touchesHover =
        edge.source === hoveredId ||
        edge.target === hoveredId ||
        (connectedIds !== null &&
          (connectedIds.has(edge.source) ||
            connectedIds.has(edge.target)));

      alpha = touchesHover
        ? HIGHLIGHT_EDGE_OPACITY
        : DIMMED_EDGE_OPACITY;
    }

    if (alpha <= 0.001) continue;

    // ---- Control point ----------------------------------
    // Deterministic sign from a hash of the edge key so
    // the fan looks stable across renders.
    let h = 0;
    for (let k = 0; k < edge.key.length; k++) {
      h = (h * 31 + edge.key.charCodeAt(k)) | 0;
    }
    const sign = (h & 1) === 0 ? 1 : -1;

    const ctrl = controlPoint(
      edge.sourcePos,
      edge.targetPos,
      sign,
    );

    const [sx, sy, sz] = edge.sourcePos;
    const [tx, ty, tz] = edge.targetPos;
    const [cx, cy, cz] = ctrl;

    // ---- Target color -----------------------------------
    const targetColorHex =
      nodeColorsById.get(edge.target) ??
      NODE_COLORS[
        "disease" as NodeType
      ] ??
      "#8a8a8a";

    // ---- Emit segments ----------------------------------
    let prevX = sx;
    let prevY = sy;
    let prevZ = sz;

    for (let s = 1; s <= segCount; s++) {
      const t = s / segCount;

      // Quadratic bezier
      const oneMinusT = 1 - t;
      const x =
        oneMinusT * oneMinusT * sx +
        2 * oneMinusT * t * cx +
        t * t * tx;
      const y =
        oneMinusT * oneMinusT * sy +
        2 * oneMinusT * t * cy +
        t * t * ty;
      const z =
        oneMinusT * oneMinusT * sz +
        2 * oneMinusT * t * cz +
        t * t * tz;

      // ---- Position -------------------------------------
      positions[pOffset + 0] = prevX;
      positions[pOffset + 1] = prevY;
      positions[pOffset + 2] = prevZ;
      positions[pOffset + 3] = x;
      positions[pOffset + 4] = y;
      positions[pOffset + 5] = z;
      pOffset += 6;

      // ---- Colors ---------------------------------------
      // Brightness ramps from 0.35 at the source end to 1.0
      // at the target end, then multiplied by alpha.
      const startBrightness = (0.35 + 0.65 * ((s - 1) / segCount)) * alpha;
      const endBrightness = (0.35 + 0.65 * (s / segCount)) * alpha;

      tmpColor.set(targetColorHex);

      colors[cOffset + 0] = tmpColor.r * startBrightness;
      colors[cOffset + 1] = tmpColor.g * startBrightness;
      colors[cOffset + 2] = tmpColor.b * startBrightness;

      colors[cOffset + 3] = tmpColor.r * endBrightness;
      colors[cOffset + 4] = tmpColor.g * endBrightness;
      colors[cOffset + 5] = tmpColor.b * endBrightness;
      cOffset += 6;

      prevX = x;
      prevY = y;
      prevZ = z;
    }
  }

  // Trim unused tail of the arrays.
  const usedPositions = positions.slice(0, pOffset);
  const usedColors = colors.slice(0, cOffset);

  return {
    positions: usedPositions,
    colors: usedColors,
  };
}

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface EdgeLinesProps {
  edges: LaidOutEdge[];
  /** All nodes in the layout, used to look up target colors. */
  nodes: LaidOutNode[];
  hoveredId: string | null;
  connectedToHover: Set<string> | null;
  focusedTypes?: Set<string> | null;
  focusedNodeIds?: Set<string> | null;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function EdgeLines({
  edges,
  nodes,
  hoveredId,
  connectedToHover,
  focusedTypes = null,
  focusedNodeIds = null,
}: EdgeLinesProps) {
  const geometryRef = useRef<BufferGeometry>(null);
  const linesRef = useRef<LineSegments>(null);

  // Node id -> hex color. Built once per node set.
  const nodeColorsById = useMemo(() => {
    const map = new Map<string, string>();
    for (const node of nodes) {
      const color =
        NODE_COLORS[node.type] ?? "#8a8a8a";
      map.set(node.id, color);
    }
    return map;
  }, [nodes]);

  // Rebuild position + color buffers whenever hover,
  // focus, or edge set changes.
  const { positions, colors } = useMemo(
    () =>
      buildBuffers(
        edges,
        nodeColorsById,
        hoveredId,
        connectedToHover,
        focusedTypes ? focusedNodeIds ?? null : null,
      ),
    [
      edges,
      nodeColorsById,
      hoveredId,
      connectedToHover,
      focusedTypes,
      focusedNodeIds,
    ],
  );

  // Attach geometry attributes.
  useEffect(() => {
    const geo = geometryRef.current;
    if (!geo) return;

    geo.setAttribute(
      "position",
      new BufferAttribute(positions, 3),
    );
    geo.setAttribute(
      "color",
      new BufferAttribute(colors, 3),
    );
    geo.computeBoundingSphere();
  }, [positions, colors]);

  // Material — vertexColors turns on per-vertex coloring.
  // No transparent: we bake alpha into brightness.
  const material = useMemo(
    () =>
      new LineBasicMaterial({
        vertexColors: true,
        transparent: true,
        opacity: 1,
        blending: 2, // AdditiveBlending
        depthWrite: false,
      }),
    [],
  );

  useEffect(() => {
    return () => {
      material.dispose();
    };
  }, [material]);

  return (
    <lineSegments
      ref={linesRef}
      frustumCulled={false}
    >
      <bufferGeometry ref={geometryRef} />
      <primitive object={material} attach="material" />
    </lineSegments>
  );
}
