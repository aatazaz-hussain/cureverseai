/**
 * CureVerseAI — Disease → Biological Impact
 * Bubble level.
 *
 * Renders one level of the bubble journey — a set of
 * sibling bubbles positioned on the surface of an
 * invisible sphere using a Fibonacci distribution.
 *
 * Fibonacci spacing produces a visually even spread
 * across the sphere without the clumping of naive
 * latitude/longitude layouts, and without the chaos of
 * random placement. Same input -> same positions, always.
 *
 * The level animates in as a whole: bubbles spawn in
 * sequence, staggered by their index.
 */

"use client";

import { useMemo } from "react";

import Bubble from "./Bubble";
import type { Bubble as BubbleData } from "./bubbleJourney";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

/** Radius of the invisible sphere the bubbles sit on. */
const LEVEL_RADIUS = 11;

/** Spawn stagger between bubbles, in seconds. */
const STAGGER_S = 0.055;

// ---------------------------------------------------------------------------
// Fibonacci sphere distribution
// ---------------------------------------------------------------------------

/**
 * Return n points roughly evenly distributed on a sphere
 * of radius r, centered at origin.
 *
 * Uses the golden-angle formula:
 *   y_i = 1 - 2 * (i + 0.5) / n       (in [-1, 1])
 *   r_i = sqrt(1 - y_i^2)
 *   phi_i = i * GOLDEN_ANGLE
 *   x_i = cos(phi_i) * r_i
 *   z_i = sin(phi_i) * r_i
 *
 * This is the standard Fibonacci lattice — deterministic,
 * evenly spread, no clumping at the poles.
 */
function fibonacciSphere(
  n: number,
  r: number,
): [number, number, number][] {
  if (n === 0) return [];
  if (n === 1) return [[0, 0, 0]];

  const golden = Math.PI * (3 - Math.sqrt(5));
  const points: [number, number, number][] = [];

  for (let i = 0; i < n; i++) {
    const y = 1 - (2 * (i + 0.5)) / n;
    const radiusAtY = Math.sqrt(Math.max(0, 1 - y * y));
    const phi = i * golden;

    const x = Math.cos(phi) * radiusAtY;
    const z = Math.sin(phi) * radiusAtY;

    points.push([x * r, y * r, z * r]);
  }

  return points;
}

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface BubbleLevelProps {
  bubbles: BubbleData[];
  /** Journey depth of this level (0=system, 1=tissue, 2=cell, 3=molecule). */
  depth: number;
  hoveredId: string | null;
  onHoverChange: (id: string | null) => void;
  onClick: (bubble: BubbleData) => void;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function BubbleLevel({
  bubbles,
  depth,
  hoveredId,
  onHoverChange,
  onClick,
}: BubbleLevelProps) {
  const positions = useMemo(
    () => fibonacciSphere(bubbles.length, LEVEL_RADIUS),
    [bubbles.length],
  );

  return (
    <group>
      {bubbles.map((bubble, i) => (
        <Bubble
          key={bubble.id}
          bubble={bubble}
          position={positions[i]}
          depth={depth}
          delay={i * STAGGER_S}
          hoveredId={hoveredId}
          onHoverChange={onHoverChange}
          onClick={onClick}
        />
      ))}
    </group>
  );
}
