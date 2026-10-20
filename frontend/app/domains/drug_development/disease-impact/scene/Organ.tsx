/**
 * CureVerseAI — Disease → Biological Impact
 * Single organ renderer.
 *
 * Renders one OrganDef as a Three.js mesh. Supports four
 * primitive shapes:
 *
 *   sphere  — brain, kidneys, bladder, thyroid, thymus,
 *             adrenal glands, eyes
 *   capsule — spine, lungs
 *   box     — liver, stomach, pancreas, spleen, uterus
 *   torus   — ribs, pelvis, large intestine
 *
 * Visual states:
 *
 *   baseline    — dim but visible (no focus active)
 *   highlighted — part of the currently affected system;
 *                 full opacity + emissive glow + pulse
 *   dimmed      — a system is focused but this organ is
 *                 not in it; very low opacity
 *
 * Hover behavior: hovering an organ scales it up and
 * shows its label in the shared hover readout.
 */

"use client";

import { useCallback, useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import type { ThreeEvent } from "@react-three/fiber";
import type { Mesh } from "three";
import { Color, MathUtils } from "three";

import type { OrganDef } from "./organs";

import {
  ORGAN_BASE_EMISSIVE,
  ORGAN_BASE_OPACITY,
  ORGAN_DIMMED_OPACITY,
  ORGAN_HIGHLIGHT_COLOR,
  ORGAN_HIGHLIGHT_EMISSIVE,
  ORGAN_HIGHLIGHT_OPACITY,
  ORGAN_PULSE_PERIOD_S,
} from "./constants";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface OrganProps {
  organ: OrganDef;
  /** True when this organ belongs to the currently affected system. */
  highlighted: boolean;
  /** True when a focus mode is active but this organ is not in it. */
  dimmed: boolean;
  /** Currently hovered organ id. */
  hoveredId: string | null;
  /** Called on pointer enter/leave with this organ's id or null. */
  onHoverChange: (id: string | null) => void;
}

// ---------------------------------------------------------------------------
// Geometry factory
// ---------------------------------------------------------------------------

function OrganGeometry({ organ }: { organ: OrganDef }) {
  const { shape, size } = organ;

  switch (shape) {
    case "sphere":
      return (
        <sphereGeometry args={[size.r ?? 1, 24, 24]} />
      );

    case "capsule":
      return (
        <capsuleGeometry
          args={[
            size.r ?? 0.5,
            size.length ?? 2,
            12,
            20,
          ]}
        />
      );

    case "box":
      return (
        <boxGeometry
          args={size.box ?? [1, 1, 1]}
        />
      );

    case "torus":
      return (
        <torusGeometry
          args={[
            size.r ?? 1,
            size.tube ?? 0.2,
            12,
            32,
          ]}
        />
      );
  }
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function Organ({
  organ,
  highlighted,
  dimmed,
  hoveredId,
  onHoverChange,
}: OrganProps) {
  const meshRef = useRef<Mesh>(null);

  const isHovered = hoveredId === organ.id;
  const anyHover = hoveredId !== null;

  // ---- Color: base or highlight ---------------------------
  const baseColor = useMemo(
    () => new Color(organ.color),
    [organ.color],
  );

  const highlightColor = useMemo(
    () => new Color(ORGAN_HIGHLIGHT_COLOR),
    [],
  );

  // ---- Target opacity / emissive --------------------------
  const targetOpacity = (() => {
    if (isHovered) return 1.0;
    if (highlighted) return ORGAN_HIGHLIGHT_OPACITY;
    if (dimmed) return ORGAN_DIMMED_OPACITY;
    return ORGAN_BASE_OPACITY;
  })();

  const targetEmissive = (() => {
    if (isHovered) return ORGAN_HIGHLIGHT_EMISSIVE * 1.2;
    if (highlighted) return ORGAN_HIGHLIGHT_EMISSIVE;
    return ORGAN_BASE_EMISSIVE;
  })();

  // ---- Hover handlers -------------------------------------
  const handlePointerOver = useCallback(
    (e: ThreeEvent<PointerEvent>) => {
      e.stopPropagation();
      onHoverChange(organ.id);
      document.body.style.cursor = "pointer";
    },
    [organ.id, onHoverChange],
  );

  const handlePointerOut = useCallback(
    (e: ThreeEvent<PointerEvent>) => {
      e.stopPropagation();
      onHoverChange(null);
      document.body.style.cursor = "";
    },
    [onHoverChange],
  );

  // ---- Animation ------------------------------------------
  useFrame((state) => {
    const mesh = meshRef.current;
    if (!mesh) return;

    const delta = state.clock.getDelta();
    const damping = 1 - Math.pow(0.001, delta);

    // Smooth hover scale
    const targetScale = isHovered ? 1.35 : 1;
    const s = mesh.scale.x;
    const newS = s + (targetScale - s) * damping;
    mesh.scale.set(newS, newS, newS);

    // Pulse highlighted organs.
    // The material is a single MeshStandardMaterial by
    // construction; the union type from the three.js
    // typings needs an intermediate cast through unknown
    // before narrowing.
    const rawMat = mesh.material as unknown;
    const mat = rawMat as {
      emissiveIntensity: number;
      opacity: number;
      color: Color;
      emissive: Color;
    };

    let pulse = 0;
    if (highlighted && !dimmed) {
      const t = state.clock.getElapsedTime();
      pulse =
        0.35 *
        (0.5 + 0.5 * Math.sin((t / ORGAN_PULSE_PERIOD_S) * Math.PI * 2));
    }

    // Smooth emissive
    const targetE = targetEmissive + pulse;
    mat.emissiveIntensity = MathUtils.lerp(
      mat.emissiveIntensity,
      targetE,
      damping,
    );

    // Smooth opacity
    mat.opacity = MathUtils.lerp(
      mat.opacity,
      targetOpacity,
      damping,
    );

    // Color interpolation: highlight uses red, others use base
    const targetColor = highlighted ? highlightColor : baseColor;
    mat.color.lerp(targetColor, damping * 0.8);
    mat.emissive.lerp(targetColor, damping * 0.8);
  });

  return (
    <mesh
      ref={meshRef}
      position={organ.position}
      rotation={organ.rotation}
      onPointerOver={handlePointerOver}
      onPointerOut={handlePointerOut}
      userData={{
        organId: organ.id,
        organLabel: organ.label,
        organGroup: organ.group,
      }}
    >
      <OrganGeometry organ={organ} />

      <meshStandardMaterial
        color={organ.color}
        emissive={organ.color}
        emissiveIntensity={ORGAN_BASE_EMISSIVE}
        transparent
        opacity={ORGAN_BASE_OPACITY}
        roughness={0.55}
        metalness={0.08}
        depthWrite={false}
      />
    </mesh>
  );
}
