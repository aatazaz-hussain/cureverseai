/**
 * CureVerseAI — Disease → Biological Impact
 * Scene layout.
 *
 * Pure function that converts a BiologicalImpactResult
 * into a deterministic, laid-out scene:
 *
 *     {
 *       nodes: [{ id, type, label, position, color, ... }],
 *       edges: [{ source, target, sourcePos, targetPos, opacity }],
 *       rings: [{ type, radius, count }],
 *       bounds: { maxRadius }
 *     }
 *
 * Design:
 *
 *   - Disease node sits at the origin.
 *   - Every other node type gets its own concentric ring.
 *   - Angular position within a ring is index / count * 2π,
 *     offset by a per-ring phase so nodes on different
 *     rings do not align radially.
 *   - Edges are deduplicated by (source, target) tuple;
 *     the first-seen evidence_level wins.
 *
 * No randomness. Same input → same output, always. This
 * makes the demo reproducible.
 */

import type {
  BiologicalImpactResult,
  ImpactNode,
  NodeType,
} from "../types";

import {
  DEFAULT_NODE_COLOR,
  DEFAULT_EDGE_OPACITY,
  EVIDENCE_OPACITY,
  MIN_RING_GAP,
  NODE_COLORS,
  RING_ANGULAR_OFFSETS,
  RING_COUNT_STEP,
  RING_RADII,
  RING_SOFT_COUNT,
  RING_Y_OFFSETS,
} from "./constants";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

export interface LaidOutNode {
  id: string;
  type: NodeType;
  label: string;
  position: [number, number, number];
  color: string;
  /** Metadata bag from the original ImpactNode, for tooltips. */
  metadata: Record<string, unknown>;
  /** Original node — kept for reference in interaction handlers. */
  source: ImpactNode;
}

export interface LaidOutEdge {
  key: string;
  source: string;
  target: string;
  sourcePos: [number, number, number];
  targetPos: [number, number, number];
  opacity: number;
  relationshipType: string;
  evidenceLevel: string;
}

export interface LaidOutRing {
  type: NodeType;
  radius: number;
  count: number;
}

export interface SceneLayout {
  nodes: LaidOutNode[];
  edges: LaidOutEdge[];
  rings: LaidOutRing[];
  bounds: { maxRadius: number };
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/**
 * Choose a ring radius for a node type. Falls back to a
 * sensible default when the type has no explicit radius.
 */
function radiusFor(type: NodeType): number {
  const r = RING_RADII[type];
  if (typeof r === "number") return r;
  return 80;
}

function yOffsetFor(type: NodeType): number {
  const y = RING_Y_OFFSETS[type];
  if (typeof y === "number") return y;
  return 0;
}

function phaseFor(type: NodeType): number {
  const p = RING_ANGULAR_OFFSETS[type];
  if (typeof p === "number") return p;
  return 0;
}

function colorFor(type: NodeType): string {
  return NODE_COLORS[type] ?? DEFAULT_NODE_COLOR;
}

/**
 * Compute the effective ring radii for all types present
 * in the layout, in the spec walk order (disease →
 * systems → tissues → cells → molecular → pathways).
 *
 * Each ring's radius is the max of its base radius and a
 * count-scaled radius, then clamped to be at least
 * MIN_RING_GAP larger than the previous ring.
 *
 * This is what makes a 38-node tissue ring spread out
 * without overlapping a 26-node cell ring.
 */
const RADIUS_ORDER: NodeType[] = [
  "system",
  "organ",
  "tissue",
  "cell",
  "gene",
  "protein",
  "molecule",
  "pathway",
];

function computeRingRadii(
  counts: Map<NodeType, number>,
): Map<NodeType, number> {
  const radii = new Map<NodeType, number>();

  let previous = 0;

  for (const type of RADIUS_ORDER) {
    const count = counts.get(type) ?? 0;
    if (count === 0) {
      // Skip empty types entirely — no ring, no clash.
      continue;
    }

    const base = RING_RADII[type] ?? 80;

    const scaled =
      base + Math.max(0, count - RING_SOFT_COUNT) * RING_COUNT_STEP;

    const withGap = Math.max(scaled, previous + MIN_RING_GAP);

    radii.set(type, withGap);
    previous = withGap;
  }

  return radii;
}

function opacityFor(level: string | null | undefined): number {
  if (!level) return DEFAULT_EDGE_OPACITY;
  return EVIDENCE_OPACITY[level] ?? DEFAULT_EDGE_OPACITY;
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

/**
 * Build a full layout from an impact result.
 *
 * The function never throws. A result with zero nodes
 * returns an empty layout. Nodes whose type is not in
 * RING_RADII are still placed (at the fallback radius)
 * so nothing is silently dropped.
 */
export function layoutScene(
  result: BiologicalImpactResult,
): SceneLayout {
  const rawNodes = result.nodes ?? [];

  // ---- Group by type ----------------------------------------

  const byType = new Map<NodeType, ImpactNode[]>();

  for (const node of rawNodes) {
    const list = byType.get(node.node_type) ?? [];
    list.push(node);
    byType.set(node.node_type, list);
  }

  // ---- Position nodes ---------------------------------------

  const positionById = new Map<
    string,
    [number, number, number]
  >();

  const laidOut: LaidOutNode[] = [];

  // 1) Disease root at origin
  const diseaseNodes = byType.get("disease") ?? [];

  for (const node of diseaseNodes) {
    const position: [number, number, number] = [0, 0, 0];

    positionById.set(node.node_id, position);

    laidOut.push({
      id: node.node_id,
      type: node.node_type,
      label: node.name,
      position,
      color: colorFor(node.node_type),
      metadata: node.metadata ?? {},
      source: node,
    });
  }

  // 2) Compute dynamic radii for every non-empty type
  const nodeCounts = new Map<NodeType, number>();
  for (const [type, nodes] of byType.entries()) {
    if (type === "disease") continue;
    nodeCounts.set(type, nodes.length);
  }

  const dynamicRadii = computeRingRadii(nodeCounts);

  // 3) Every other type on its own ring (dynamic radius)
  for (const [type, nodes] of byType.entries()) {
    if (type === "disease") continue;

    const radius =
      dynamicRadii.get(type) ?? radiusFor(type);
    const y = yOffsetFor(type);
    const phase = phaseFor(type);
    const count = nodes.length;

    // Sort by node_id for determinism, then place
    const sorted = [...nodes].sort((a, b) =>
      a.node_id.localeCompare(b.node_id),
    );

    sorted.forEach((node, index) => {
      const angle =
        phase + (index / Math.max(count, 1)) * Math.PI * 2;

      const x = Math.cos(angle) * radius;
      const z = Math.sin(angle) * radius;

      const position: [number, number, number] = [x, y, z];

      positionById.set(node.node_id, position);

      laidOut.push({
        id: node.node_id,
        type: node.node_type,
        label: node.name,
        position,
        color: colorFor(node.node_type),
        metadata: node.metadata ?? {},
        source: node,
      });
    });
  }

  // ---- Position edges ---------------------------------------

  const seenEdgeKeys = new Set<string>();
  const edges: LaidOutEdge[] = [];

  for (const rel of result.relationships ?? []) {
    const sourcePos = positionById.get(rel.source_id);
    const targetPos = positionById.get(rel.target_id);

    // Skip edges whose endpoints are not in the graph.
    // This cannot happen for valid results (integrity is
    // checked by the AI Engine) but is defensive.
    if (!sourcePos || !targetPos) continue;

    const key = `${rel.source_id}->${rel.target_id}`;

    if (seenEdgeKeys.has(key)) continue;

    seenEdgeKeys.add(key);

    edges.push({
      key,
      source: rel.source_id,
      target: rel.target_id,
      sourcePos,
      targetPos,
      opacity: opacityFor(rel.evidence_level),
      relationshipType: rel.relationship_type,
      evidenceLevel: rel.evidence_level ?? "unknown",
    });
  }

  // ---- Ring summary (for the legend) ------------------------

  const rings: LaidOutRing[] = [];

  for (const [type, nodes] of byType.entries()) {
    rings.push({
      type,
      radius:
        type === "disease"
          ? 0
          : dynamicRadii.get(type) ?? radiusFor(type),
      count: nodes.length,
    });
  }

  rings.sort((a, b) => a.radius - b.radius);

  // ---- Bounds -----------------------------------------------

  let maxRadius = 0;

  for (const node of laidOut) {
    const [x, , z] = node.position;
    const r = Math.sqrt(x * x + z * z);
    if (r > maxRadius) maxRadius = r;
  }

  return {
    nodes: laidOut,
    edges,
    rings,
    bounds: { maxRadius: Math.max(maxRadius, 1) },
  };
}
