/**
 * CureVerseAI — Disease → Biological Impact
 * The 3D scene.
 *
 * Two view modes:
 *
 *   JOURNEY (default)
 *     A single bubble for the most affected system,
 *     which bursts into children on click, walking
 *     System -> Tissue -> Cell -> Molecule.
 *
 *   GRAPH
 *     The full abstract graph (nodes + edges) for the
 *     same result. Reached by clicking a terminal
 *     bubble in the journey.
 *
 * Camera:
 *   In JOURNEY mode, the camera orbits a fixed point
 *   at origin looking at the current bubble level.
 *   In GRAPH mode, the camera uses the same focus
 *   behavior as Phase 15 (stage bar -> ring focus).
 *
 * The stage bar remains wired through the page: clicking
 * SYSTEM / TISSUE / CELL etc. focuses the corresponding
 * ring in GRAPH mode. In JOURNEY mode the stage bar is
 * display-only.
 */

"use client";

import {
  useCallback,
  useMemo,
  useRef,
  useState,
} from "react";
import { Canvas } from "@react-three/fiber";
import { OrbitControls } from "@react-three/drei";
import type { OrbitControls as OrbitControlsImpl } from "three-stdlib";

import type { BiologicalImpactResult } from "../types";

import "./scene.css";
import "./bubble.css";
import "./avatar.css";

import NodeMesh from "./NodeMesh";
import EdgeLines from "./EdgeLines";
import SceneControls from "./SceneControls";
import CameraRig from "./CameraRig";
import NodeLabels from "./NodeLabels";
import BubbleJourney from "./BubbleJourney";
import ScientificAvatar from "./ScientificAvatar";

import { layoutScene } from "./sceneLayout";

import {
  CAMERA_FOV,
  CAMERA_POSITION,
  CAMERA_TARGET,
  CAMERA_TRANSITION_MAX_MS,
  CAMERA_TRANSITION_MIN_MS,
  CAMERA_TRANSITION_SCALE,
  CANVAS_BACKGROUND,
  CONTROLS_DAMPING,
  CONTROLS_MAX_DISTANCE,
  CONTROLS_MIN_DISTANCE,
  FOCUS_HEIGHT_RATIO,
  FOCUS_MIN_DISTANCE,
  FOG_FAR,
  FOG_NEAR,
  STAGE_FOCUS_DISTANCE_MULT,
  STAGE_TO_TYPES,
  type FocusStage,
} from "./constants";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface ImpactSceneProps {
  result: BiologicalImpactResult;
  focusedStage: FocusStage;
}

type ViewMode = "journey" | "graph";

// ---------------------------------------------------------------------------
// Journey camera
// ---------------------------------------------------------------------------

const JOURNEY_CAMERA_POSITION: [number, number, number] = [
  0, 6, 34,
];
const JOURNEY_CAMERA_LOOKAT: [number, number, number] = [
  0, 0, 0,
];

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function ImpactScene({
  result,
  focusedStage,
}: ImpactSceneProps) {
  // ---- View mode ------------------------------------------
  const [viewMode, setViewMode] = useState<ViewMode>("journey");

  // ---- Graph layout ---------------------------------------
  const layout = useMemo(
    () => layoutScene(result),
    [result],
  );

  // ---- Hover state ----------------------------------------
  const [hoveredId, setHoveredId] = useState<string | null>(
    null,
  );

  // ---- Narration state -----------------------------------
  // The avatar speaks whenever this changes. We append a
  // sequence counter so re-speaking the same label (e.g.
  // clicking the same bubble twice) still triggers speech.
  const [narrationText, setNarrationText] = useState<
    string | null
  >(null);
  const narrationSeq = useRef(0);

  const handleNarrate = useCallback((label: string) => {
    const seq = narrationSeq.current++;
    setNarrationText(`${label}::${seq}`);
  }, []);

  // The avatar receives the raw label, not the sequence
  // suffix. Strip it back off before passing down.
  const avatarText = narrationText
    ? narrationText.replace(/::\d+$/, "")
    : null;

  const controlsRef = useRef<OrbitControlsImpl | null>(null);

  // ---- Focus computation (graph mode) ---------------------
  const isImpactMode = focusedStage === "IMPACT";
  const isJourneyMode = viewMode === "journey";

  const focusedTypes = useMemo(
    () => new Set<string>(STAGE_TO_TYPES[focusedStage] ?? []),
    [focusedStage],
  );

  const focusedNodeIds = useMemo(() => {
    const ids = new Set<string>();
    for (const node of layout.nodes) {
      if (focusedTypes.has(node.type)) {
        ids.add(node.id);
      }
    }
    return ids;
  }, [layout, focusedTypes]);

  // ---- Hover connectivity (graph mode) --------------------
  const connectedByNode = useMemo(() => {
    const map = new Map<string, Set<string>>();
    const addLink = (a: string, b: string) => {
      const set = map.get(a) ?? new Set<string>();
      set.add(b);
      map.set(a, set);
    };
    for (const edge of layout.edges) {
      addLink(edge.source, edge.target);
      addLink(edge.target, edge.source);
    }
    return map;
  }, [layout]);

  const connectedToHover = useMemo<Set<string> | null>(() => {
    if (!hoveredId) return null;
    return connectedByNode.get(hoveredId) ?? new Set<string>();
  }, [hoveredId, connectedByNode]);

  // ---- Camera targets -------------------------------------

  const { cameraTarget, cameraLookAt, cameraDuration } =
    useMemo(() => {
      if (isJourneyMode) {
        return {
          cameraTarget: JOURNEY_CAMERA_POSITION,
          cameraLookAt: JOURNEY_CAMERA_LOOKAT,
          cameraDuration: 900,
        };
      }

      if (isImpactMode) {
        return {
          cameraTarget: CAMERA_POSITION as [
            number,
            number,
            number,
          ],
          cameraLookAt: CAMERA_TARGET as [
            number,
            number,
            number,
          ],
          cameraDuration: 1200,
        };
      }

      let maxRingRadius = 0;
      for (const node of layout.nodes) {
        if (!focusedTypes.has(node.type)) continue;
        const [x, , z] = node.position;
        const r = Math.sqrt(x * x + z * z);
        if (r > maxRingRadius) maxRingRadius = r;
      }

      const mult =
        STAGE_FOCUS_DISTANCE_MULT[focusedStage] ?? 2.6;

      const distance = Math.max(
        FOCUS_MIN_DISTANCE,
        maxRingRadius * mult,
      );

      const height = distance * FOCUS_HEIGHT_RATIO;

      const duration = Math.min(
        CAMERA_TRANSITION_MAX_MS,
        Math.max(
          CAMERA_TRANSITION_MIN_MS,
          CAMERA_TRANSITION_MIN_MS +
            distance * CAMERA_TRANSITION_SCALE,
        ),
      );

      return {
        cameraTarget: [0, height, distance] as [
          number,
          number,
          number,
        ],
        cameraLookAt: [0, 0, 0] as [number, number, number],
        cameraDuration: duration,
      };
    }, [
      layout,
      focusedTypes,
      focusedStage,
      isImpactMode,
      isJourneyMode,
    ]);

  // ---- Callbacks ------------------------------------------

  const handleHoverChange = useCallback(
    (nodeId: string | null) => {
      setHoveredId(nodeId);
    },
    [],
  );

  const handleReset = useCallback(() => {
    const controls = controlsRef.current;
    if (!controls) return;

    const target = isJourneyMode
      ? JOURNEY_CAMERA_POSITION
      : CAMERA_POSITION;
    const look = isJourneyMode
      ? JOURNEY_CAMERA_LOOKAT
      : CAMERA_TARGET;

    controls.object.position.set(
      target[0],
      target[1],
      target[2],
    );
    controls.target.set(look[0], look[1], look[2]);
    controls.update();
  }, [isJourneyMode]);

  const handlePointerMissed = useCallback(() => {
    setHoveredId(null);
  }, []);

  const handleOpenGraph = useCallback(() => {
    setViewMode("graph");
    handleNarrate("Biological impact graph");
  }, [handleNarrate]);

  const handleBackToJourney = useCallback(() => {
    setViewMode("journey");
    setHoveredId(null);
  }, []);

  // ---- Hover readout --------------------------------------

  const hoveredNode = hoveredId
    ? layout.nodes.find((n) => n.id === hoveredId) ?? null
    : null;

  const labelNodeIds = useMemo(() => {
    if (isJourneyMode || isImpactMode) {
      return new Set<string>(
        hoveredId ? [hoveredId] : [],
      );
    }
    return focusedNodeIds;
  }, [isJourneyMode, isImpactMode, focusedNodeIds, hoveredId]);

  // ---- Render ---------------------------------------------

  return (
    <div className="cv-dia-scene">
      <Canvas
        dpr={[1, 2]}
        camera={{
          fov: CAMERA_FOV,
          position: JOURNEY_CAMERA_POSITION,
          near: 0.5,
          far: 1000,
        }}
        gl={{
          antialias: true,
          alpha: false,
        }}
        onPointerMissed={handlePointerMissed}
      >
        <color
          attach="background"
          args={[CANVAS_BACKGROUND]}
        />

        <fog
          attach="fog"
          args={[CANVAS_BACKGROUND, FOG_NEAR, FOG_FAR * 2]}
        />

        {/* Lights */}
        <ambientLight intensity={0.55} />
        <directionalLight
          position={[20, 60, 40]}
          intensity={0.85}
        />
        <directionalLight
          position={[-40, -20, -30]}
          intensity={0.3}
        />
        <pointLight
          position={[0, 0, 0]}
          intensity={0.6}
          color="#e0525a"
          distance={80}
        />
        <pointLight
          position={[10, 20, 10]}
          intensity={0.4}
          color="#e9c58c"
          distance={100}
        />

        {/* ---- Journey mode ---- */}
        {isJourneyMode ? (
          <BubbleJourney
            result={result}
            onOpenGraph={handleOpenGraph}
            onNarrate={handleNarrate}
          />
        ) : null}

        {/* ---- Graph mode ---- */}
        {!isJourneyMode ? (
          <group>
            <EdgeLines
              edges={layout.edges}
              nodes={layout.nodes}
              hoveredId={hoveredId}
              connectedToHover={connectedToHover}
              focusedTypes={
                isImpactMode ? null : focusedTypes
              }
              focusedNodeIds={
                isImpactMode ? null : focusedNodeIds
              }
            />

            {layout.nodes.map((node) => {
              const inFocus = focusedTypes.has(node.type);
              const dimmed =
                !isImpactMode && !inFocus;

              return (
                <NodeMesh
                  key={node.id}
                  node={node}
                  hoveredId={hoveredId}
                  connectedToHover={connectedToHover}
                  onHoverChange={handleHoverChange}
                  dimmed={dimmed}
                />
              );
            })}

            <NodeLabels
              nodes={layout.nodes}
              focusedNodeIds={labelNodeIds}
              hoveredId={hoveredId}
            />
          </group>
        ) : null}

        {/* Camera animation */}
        <CameraRig
          controlsRef={controlsRef}
          targetPosition={cameraTarget}
          targetLookAt={cameraLookAt}
          durationMs={cameraDuration}
        />

        {/* Controls */}
        <OrbitControls
          ref={controlsRef}
          enableDamping
          dampingFactor={CONTROLS_DAMPING}
          minDistance={CONTROLS_MIN_DISTANCE}
          maxDistance={CONTROLS_MAX_DISTANCE}
          makeDefault
        />
      </Canvas>

      <ScientificAvatar narrationText={avatarText} />

      <SceneControls
        layout={layout}
        hoveredNodeId={hoveredId}
        hoveredNodeLabel={hoveredNode?.label ?? null}
        hoveredNodeType={hoveredNode?.type ?? null}
        focusedStage={focusedStage}
        viewMode={viewMode}
        onResetCamera={handleReset}
        onBackToJourney={handleBackToJourney}
      />
    </div>
  );
}
