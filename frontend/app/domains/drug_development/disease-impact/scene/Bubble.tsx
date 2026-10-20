/**
 * CureVerseAI — Disease → Biological Impact
 * Single journey bubble.
 *
 * A sphere sized by child count, colored by node type,
 * with a label rendered as an HTML overlay. Hover lifts
 * and glows. Click bursts — the parent orchestrator
 * handles the level transition.
 *
 * Entrance animation: bubbles scale in from 0 when they
 * mount, staggered by index so the level "blooms".
 */

"use client";

import { useCallback, useEffect, useRef, useState } from "react";
import { useFrame } from "@react-three/fiber";
import type { ThreeEvent } from "@react-three/fiber";
import { Html } from "@react-three/drei";
import type { Mesh } from "three";
import { Color, MathUtils } from "three";

import type { Bubble as BubbleData } from "./bubbleJourney";

import { NODE_COLORS } from "./constants";

// ---------------------------------------------------------------------------
// Constants
// ---------------------------------------------------------------------------

/**
 * Per-depth bubble radii.
 *
 *   0 = system  (root — big and dominant)
 *   1 = tissue  (medium)
 *   2 = cell    (small)
 *   3 = molecule (small)
 *
 * A separate RADIUS_TERMINAL is used for leaf bubbles so
 * molecules remain clickable without growing to tissue
 * size.
 */
const RADIUS_BY_DEPTH = [5.8, 1.9, 1.35, 1.05] as const;
const RADIUS_TERMINAL = 1.05;

/**
 * Label vertical offset above the bubble surface.
 * Scaled per depth so bigger bubbles push their labels
 * clear of neighbors and their own geometry.
 */
const LABEL_OFFSET_BY_DEPTH = [2.5, 1.5, 1.1, 1.0] as const;
const LABEL_OFFSET_TERMINAL = 1.0;

/** Hover scale multiplier. */
const HOVER_SCALE = 1.14;

/** Base emissive intensity when idle. */
const BASE_EMISSIVE = 0.35;

/** Emissive intensity when hovered. */
const HOVER_EMISSIVE = 1.2;

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface BubbleProps {
  bubble: BubbleData;
  /** Cartesian position in the parent group's space. */
  position: [number, number, number];
  /**
   * Depth in the journey:
   *   0 = system, 1 = tissue, 2 = cell, 3 = molecule
   */
  depth: number;
  /** Entrance animation delay in seconds (stagger). */
  delay: number;
  /** Currently hovered bubble id, or null. */
  hoveredId: string | null;
  /** Called on pointer enter / leave. */
  onHoverChange: (id: string | null) => void;
  /** Called on click. */
  onClick: (bubble: BubbleData) => void;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function Bubble({
  bubble,
  position,
  depth,
  delay,
  hoveredId,
  onHoverChange,
  onClick,
}: BubbleProps) {
  const meshRef = useRef<Mesh>(null);
  const spawnedRef = useRef(false);
  const spawnStartRef = useRef(0);

  const [visible, setVisible] = useState(false);

  // Radius depends on the journey depth:
  //   system bubbles are large and dominant
  //   tissue bubbles are medium
  //   cell / molecule bubbles are small
  //
  // Terminal (leaf) bubbles always use RADIUS_TERMINAL so
  // molecules stay small and clickable.
  const radius = (() => {
    if (bubble.childCount === 0) return RADIUS_TERMINAL;
    const idx = Math.min(
      Math.max(depth, 0),
      RADIUS_BY_DEPTH.length - 1,
    );
    return RADIUS_BY_DEPTH[idx];
  })();

  const labelOffset = (() => {
    if (bubble.childCount === 0) return LABEL_OFFSET_TERMINAL;
    const idx = Math.min(
      Math.max(depth, 0),
      LABEL_OFFSET_BY_DEPTH.length - 1,
    );
    return LABEL_OFFSET_BY_DEPTH[idx];
  })();

  // Base color from node type.
  const color = NODE_COLORS[bubble.type] ?? "#8a8a8a";

  // Delay before spawning.
  useEffect(() => {
    const t = setTimeout(() => {
      spawnStartRef.current = performance.now() / 1000;
      spawnedRef.current = true;
      setVisible(true);
    }, delay * 1000);

    return () => clearTimeout(t);
  }, [delay]);

  const isHovered = hoveredId === bubble.id;

  const handlePointerOver = useCallback(
    (e: ThreeEvent<PointerEvent>) => {
      e.stopPropagation();
      onHoverChange(bubble.id);
      document.body.style.cursor = "pointer";
    },
    [bubble.id, onHoverChange],
  );

  const handlePointerOut = useCallback(
    (e: ThreeEvent<PointerEvent>) => {
      e.stopPropagation();
      onHoverChange(null);
      document.body.style.cursor = "";
    },
    [onHoverChange],
  );

  const handleClick = useCallback(
    (e: ThreeEvent<MouseEvent>) => {
      e.stopPropagation();
      onClick(bubble);
    },
    [bubble, onClick],
  );

  // Animate spawn + hover.
  useFrame((_, delta) => {
    const mesh = meshRef.current;
    if (!mesh) return;

    const damping = 1 - Math.pow(0.001, delta);

    // ---- Spawn scale ----
    let spawnScale = 1;

    if (spawnedRef.current && visible) {
      const elapsed =
        performance.now() / 1000 - spawnStartRef.current;
      const raw = Math.min(elapsed / 0.9, 1);
      // ease out cubic
      spawnScale = 1 - Math.pow(1 - raw, 3);
      if (raw >= 1) spawnedRef.current = false;
    } else if (!visible) {
      spawnScale = 0;
    }

    // ---- Hover scale ----
    const hoverScale = isHovered ? HOVER_SCALE : 1;
    const targetScale = spawnScale * hoverScale;

    const s = mesh.scale.x;
    const newS = s + (targetScale - s) * damping;
    mesh.scale.set(newS, newS, newS);

    // ---- Material animation ----
    const mat = mesh.material as unknown as {
      emissiveIntensity: number;
      color: Color;
      emissive: Color;
    };

    const targetEmissive = isHovered
      ? HOVER_EMISSIVE
      : BASE_EMISSIVE;

    mat.emissiveIntensity = MathUtils.lerp(
      mat.emissiveIntensity,
      targetEmissive,
      damping * 0.6,
    );
  });

  if (!visible) return null;

  return (
    <group position={position}>
      <mesh
        ref={meshRef}
        onPointerOver={handlePointerOver}
        onPointerOut={handlePointerOut}
        onClick={handleClick}
        userData={{
          bubbleId: bubble.id,
          bubbleType: bubble.type,
        }}
      >
        <sphereGeometry args={[radius, 32, 32]} />

        <meshStandardMaterial
          color={color}
          emissive={color}
          emissiveIntensity={BASE_EMISSIVE}
          transparent
          opacity={0.92}
          roughness={0.35}
          metalness={0.15}
        />
      </mesh>

      {/* Label */}
      <Html
        position={[0, radius + labelOffset, 0]}
        center
        distanceFactor={45}
        zIndexRange={[12, 0]}
        style={{ pointerEvents: "none", whiteSpace: "nowrap" }}
      >
        <div
          className={
            "cv-dia-bubble-label" +
            (isHovered ? " cv-dia-bubble-label-hovered" : "")
          }
        >
          <span className="cv-dia-bubble-label-text">
            {bubble.label}
          </span>
          {bubble.childCount > 0 ? (
            <span className="cv-dia-bubble-label-count">
              {bubble.childCount}
            </span>
          ) : null}
        </div>
      </Html>
    </group>
  );
}
