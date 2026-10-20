/**
 * CureVerseAI — Disease → Biological Impact
 * Scene node.
 *
 * One sphere per ImpactNode. Handles hover highlighting
 * and reflects the global hover state passed down by the
 * parent scene.
 *
 * Hover semantics:
 *
 *   - The hovered node scales up.
 *   - If ANY node is hovered, nodes not connected to it
 *     dim to DIMMED_NODE_OPACITY.
 *   - If no node is hovered, every node is at full opacity.
 *
 * The component never mutates state. It reports hover
 * changes via onHoverChange and renders based on the
 * hoveredId prop the parent controls.
 */

"use client";

import { useCallback, useMemo, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import type { ThreeEvent } from "@react-three/fiber";
import type { Mesh } from "three";

import type { LaidOutNode } from "./sceneLayout";

import {
  DISEASE_NODE_RADIUS,
  DIMMED_NODE_OPACITY,
  FOCUSED_NODE_OPACITY,
  HOVER_SCALE,
  NODE_RADIUS,
  SPHERE_SEGMENTS,
  UNFOCUSED_NODE_OPACITY,
} from "./constants";

interface NodeMeshProps {
  node: LaidOutNode;
  /** Currently hovered node id (any node in the scene), or null. */
  hoveredId: string | null;
  /** Ids of nodes connected to the hovered node (any direction). */
  connectedToHover: Set<string> | null;
  /** True when this node is not part of the focused stage. */
  dimmed?: boolean;
  /** Called when the pointer enters or leaves this node. */
  onHoverChange: (nodeId: string | null) => void;
}

export default function NodeMesh({
  node,
  hoveredId,
  connectedToHover,
  dimmed = false,
  onHoverChange,
}: NodeMeshProps) {
  const meshRef = useRef<Mesh>(null);

  const baseRadius = useMemo(
    () =>
      node.type === "disease"
        ? DISEASE_NODE_RADIUS
        : NODE_RADIUS,
    [node.type],
  );

  // Is this node the hovered one?
  const isHovered = hoveredId === node.id;

  // Is any node hovered at all?
  const anyHover = hoveredId !== null;

  // Is this node connected to the hovered node?
  const isConnected =
    isHovered ||
    (connectedToHover !== null &&
      connectedToHover.has(node.id));

  // ---- Effective opacity ----
  const targetOpacity = (() => {
    if (anyHover) {
      if (isHovered) return FOCUSED_NODE_OPACITY;
      if (isConnected) return FOCUSED_NODE_OPACITY;
      return DIMMED_NODE_OPACITY;
    }
    if (dimmed) return UNFOCUSED_NODE_OPACITY;
    return FOCUSED_NODE_OPACITY;
  })();

  // ---- Effective scale ----
  const targetScale = isHovered ? HOVER_SCALE : 1;

  // Smooth the transitions with useFrame so hover changes
  // feel responsive but not jarring.
  useFrame((_, delta) => {
    const mesh = meshRef.current;
    if (!mesh) return;

    const damping = 1 - Math.pow(0.001, delta);

    // Scale
    const s = mesh.scale.x;
    const newS = s + (targetScale - s) * damping;
    mesh.scale.set(newS, newS, newS);
  });

  // ---- Pointer handlers ----
  const handlePointerOver = useCallback(
    (e: ThreeEvent<PointerEvent>) => {
      e.stopPropagation();
      onHoverChange(node.id);
      document.body.style.cursor = "pointer";
    },
    [node.id, onHoverChange],
  );

  const handlePointerOut = useCallback(
    (e: ThreeEvent<PointerEvent>) => {
      e.stopPropagation();
      onHoverChange(null);
      document.body.style.cursor = "";
    },
    [onHoverChange],
  );

  // ---- Material props ----
  const emissiveIntensity = isHovered ? 0.9 : 0.18;

  return (
    <mesh
      ref={meshRef}
      position={node.position}
      onPointerOver={handlePointerOver}
      onPointerOut={handlePointerOut}
      userData={{
        nodeId: node.id,
        nodeType: node.type,
      }}
    >
      <sphereGeometry
        args={[baseRadius, SPHERE_SEGMENTS, SPHERE_SEGMENTS]}
      />

      <meshStandardMaterial
        color={node.color}
        emissive={node.color}
        emissiveIntensity={emissiveIntensity}
        transparent
        opacity={targetOpacity}
        roughness={0.42}
        metalness={0.18}
      />
    </mesh>
  );
}
