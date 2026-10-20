/**
 * CureVerseAI — Disease → Biological Impact
 * Human body renderer.
 *
 * Assembles the body shell, the skeleton, and every
 * organ into one scene group. The body is a schematic
 * medical illustration — a semi-transparent skin layer
 * over a simplified skeleton with the organs inside.
 *
 * Sizing and position:
 *
 *   The body is BODY_HEIGHT (40) units tall, centered
 *   vertically at BODY_CENTER_Y (0). Head is at +20,
 *   feet at -20. Organs are positioned in the same
 *   coordinate system (see organs.ts).
 *
 * Highlight semantics:
 *
 *   `highlightedOrganIds` — organs in the set are
 *   rendered as "affected": full opacity, red emissive,
 *   pulsing. Every other organ is at baseline opacity.
 *
 *   `focusActive` — when true (a system is focused in
 *   the stage bar), organs NOT in the highlighted set
 *   dim further so the affected ones stand out.
 */

"use client";

import { useCallback } from "react";

import Organ from "./Organ";
import { ORGANS, type OrganDef } from "./organs";

import {
  BODY_CENTER_Y,
  BODY_HEIGHT,
  BODY_SHELL_COLOR,
  BODY_SHELL_OPACITY,
  BODY_SKELETON_COLOR,
  BODY_SKELETON_OPACITY,
} from "./constants";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface HumanBodyProps {
  /** Organ ids that are currently highlighted (affected). */
  highlightedOrganIds: Set<string>;
  /** True when a specific stage is focused (not IMPACT). */
  focusActive: boolean;
  /** Currently hovered organ id, or null. */
  hoveredOrganId: string | null;
  /** Called when an organ is hovered / unhovered. */
  onOrganHover: (id: string | null) => void;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function HumanBody({
  highlightedOrganIds,
  focusActive,
  hoveredOrganId,
  onOrganHover,
}: HumanBodyProps) {
  const handleOrganHover = useCallback(
    (id: string | null) => {
      onOrganHover(id);
    },
    [onOrganHover],
  );

  // Head is above the neck. We render a simplified shell
  // rather than a full anatomical mesh.
  const headRadius = BODY_HEIGHT * 0.075; // ~3 units
  const torsoHeight = BODY_HEIGHT * 0.32; // ~12.8 units
  const torsoRadius = BODY_HEIGHT * 0.115; // ~4.6 units
  const limbRadius = BODY_HEIGHT * 0.03; // ~1.2 units
  const limbLength = BODY_HEIGHT * 0.4; // ~16 units

  const headY = BODY_HEIGHT * 0.44; // ~17.6
  const torsoY = BODY_HEIGHT * 0.01; // ~0.4
  const armX = BODY_HEIGHT * 0.155; // ~6.2
  const legX = BODY_HEIGHT * 0.055; // ~2.2

  return (
    <group position={[0, BODY_CENTER_Y, 0]}>
      {/* ---- Body shell (semi-transparent skin) ---- */}

      {/* Head */}
      <mesh position={[0, headY, 0]}>
        <sphereGeometry args={[headRadius, 24, 24]} />
        <meshStandardMaterial
          color={BODY_SHELL_COLOR}
          transparent
          opacity={BODY_SHELL_OPACITY}
          roughness={0.9}
          metalness={0.0}
          depthWrite={false}
        />
      </mesh>

      {/* Neck */}
      <mesh position={[0, headY - headRadius - 0.8, 0]}>
        <cylinderGeometry
          args={[
            headRadius * 0.4,
            headRadius * 0.5,
            1.6,
            16,
          ]}
        />
        <meshStandardMaterial
          color={BODY_SHELL_COLOR}
          transparent
          opacity={BODY_SHELL_OPACITY * 0.8}
          roughness={0.9}
          depthWrite={false}
        />
      </mesh>

      {/* Torso */}
      <mesh position={[0, torsoY, 0]}>
        <capsuleGeometry
          args={[torsoRadius, torsoHeight, 12, 20]}
        />
        <meshStandardMaterial
          color={BODY_SHELL_COLOR}
          transparent
          opacity={BODY_SHELL_OPACITY * 0.85}
          roughness={0.9}
          depthWrite={false}
        />
      </mesh>

      {/* Arms */}
      <mesh
        position={[armX, torsoY - 1, 0]}
        rotation={[0, 0, Math.PI / 12]}
      >
        <capsuleGeometry
          args={[limbRadius, limbLength * 0.6, 8, 12]}
        />
        <meshStandardMaterial
          color={BODY_SHELL_COLOR}
          transparent
          opacity={BODY_SHELL_OPACITY * 0.7}
          roughness={0.9}
          depthWrite={false}
        />
      </mesh>
      <mesh
        position={[-armX, torsoY - 1, 0]}
        rotation={[0, 0, -Math.PI / 12]}
      >
        <capsuleGeometry
          args={[limbRadius, limbLength * 0.6, 8, 12]}
        />
        <meshStandardMaterial
          color={BODY_SHELL_COLOR}
          transparent
          opacity={BODY_SHELL_OPACITY * 0.7}
          roughness={0.9}
          depthWrite={false}
        />
      </mesh>

      {/* Legs */}
      <mesh position={[legX, torsoY - torsoHeight * 0.5 - limbLength * 0.5, 0]}>
        <capsuleGeometry
          args={[limbRadius * 1.1, limbLength * 0.9, 8, 12]}
        />
        <meshStandardMaterial
          color={BODY_SHELL_COLOR}
          transparent
          opacity={BODY_SHELL_OPACITY * 0.7}
          roughness={0.9}
          depthWrite={false}
        />
      </mesh>
      <mesh position={[-legX, torsoY - torsoHeight * 0.5 - limbLength * 0.5, 0]}>
        <capsuleGeometry
          args={[limbRadius * 1.1, limbLength * 0.9, 8, 12]}
        />
        <meshStandardMaterial
          color={BODY_SHELL_COLOR}
          transparent
          opacity={BODY_SHELL_OPACITY * 0.7}
          roughness={0.9}
          depthWrite={false}
        />
      </mesh>

      {/* ---- Skeleton hints ---- */}

      {/* Simplified ribcage outline */}
      <mesh
        position={[0, BODY_HEIGHT * 0.21, -0.2]}
        rotation={[Math.PI / 2, 0, 0]}
      >
        <torusGeometry args={[torsoRadius * 0.85, 0.12, 8, 32]} />
        <meshStandardMaterial
          color={BODY_SKELETON_COLOR}
          transparent
          opacity={BODY_SKELETON_OPACITY}
          roughness={0.6}
          depthWrite={false}
        />
      </mesh>

      {/* Simplified pelvis outline */}
      <mesh
        position={[0, -BODY_HEIGHT * 0.1, -0.2]}
        rotation={[Math.PI / 2, 0, 0]}
      >
        <torusGeometry args={[torsoRadius * 0.6, 0.15, 8, 32]} />
        <meshStandardMaterial
          color={BODY_SKELETON_COLOR}
          transparent
          opacity={BODY_SKELETON_OPACITY}
          roughness={0.6}
          depthWrite={false}
        />
      </mesh>

      {/* ---- Organs ---- */}

      {ORGANS.map((organ: OrganDef) => {
        const highlighted = highlightedOrganIds.has(organ.id);
        const dimmed = focusActive && !highlighted;

        return (
          <Organ
            key={organ.id}
            organ={organ}
            highlighted={highlighted}
            dimmed={dimmed}
            hoveredId={hoveredOrganId}
            onHoverChange={handleOrganHover}
          />
        );
      })}
    </group>
  );
}
