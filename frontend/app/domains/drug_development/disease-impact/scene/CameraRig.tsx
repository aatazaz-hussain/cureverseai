/**
 * CureVerseAI — Disease → Biological Impact
 * Camera rig.
 *
 * Animates the camera between focus targets with eased
 * interpolation. No new dependencies — uses useFrame from
 * react-three-fiber plus a simple easing function.
 *
 * The rig is a controller, not a visual. It holds no
 * geometry. It only moves controls.object.position and
 * controls.target over time.
 *
 * When a new target arrives before the previous animation
 * completes, the rig re-targets from the CURRENT position
 * — no snapping, no queue.
 */

"use client";

import { useEffect, useRef } from "react";
import { useFrame } from "@react-three/fiber";
import type { OrbitControls as OrbitControlsImpl } from "three-stdlib";
import { Vector3 } from "three";

// ---------------------------------------------------------------------------
// Easing
// ---------------------------------------------------------------------------

/**
 * Standard cubic ease-in-out.
 */
function easeInOutCubic(t: number): number {
  return t < 0.5
    ? 4 * t * t * t
    : 1 - Math.pow(-2 * t + 2, 3) / 2;
}

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface CameraRigProps {
  controlsRef: React.RefObject<OrbitControlsImpl | null>;
  /** Absolute camera position to reach. */
  targetPosition: [number, number, number];
  /** Absolute look-at point to reach. */
  targetLookAt: [number, number, number];
  /** Animation duration in milliseconds. */
  durationMs: number;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function CameraRig({
  controlsRef,
  targetPosition,
  targetLookAt,
  durationMs,
}: CameraRigProps) {
  const anim = useRef({
    startTime: 0,
    startPosition: new Vector3(),
    startLookAt: new Vector3(),
    targetPosition: new Vector3(...targetPosition),
    targetLookAt: new Vector3(...targetLookAt),
    duration: durationMs / 1000,
    active: false,
  });

  useEffect(() => {
    const controls = controlsRef.current;
    if (!controls) return;

    const startPosition = controls.object.position.clone();
    const startLookAt = controls.target.clone();

    anim.current.startTime = performance.now() / 1000;
    anim.current.startPosition.copy(startPosition);
    anim.current.startLookAt.copy(startLookAt);
    anim.current.targetPosition.set(...targetPosition);
    anim.current.targetLookAt.set(...targetLookAt);
    anim.current.duration = durationMs / 1000;
    anim.current.active = true;
  }, [targetPosition, targetLookAt, durationMs, controlsRef]);

  useFrame(() => {
    if (!anim.current.active) return;

    const controls = controlsRef.current;
    if (!controls) return;

    const now = performance.now() / 1000;
    const elapsed = now - anim.current.startTime;
    const raw = Math.min(elapsed / anim.current.duration, 1);
    const eased = easeInOutCubic(raw);

    const pos = anim.current.startPosition
      .clone()
      .lerp(anim.current.targetPosition, eased);

    const look = anim.current.startLookAt
      .clone()
      .lerp(anim.current.targetLookAt, eased);

    controls.object.position.copy(pos);
    controls.target.copy(look);
    controls.update();

    if (raw >= 1) {
      anim.current.active = false;
    }
  });

  return null;
}
