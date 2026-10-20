/**
 * CureVerseAI — Disease → Biological Impact
 * Scene controls.
 *
 * An HTML overlay that sits above the WebGL canvas. Shows
 * a legend of node types with counts, the currently
 * hovered node, and a reset-camera button.
 *
 * The overlay uses CSS pointer-events strategically: the
 * container is transparent to input so the canvas keeps
 * receiving orbit/zoom gestures, but interactive elements
 * (the reset button, legend rows) re-enable pointer
 * events for themselves.
 */

"use client";

import { useCallback } from "react";

import type { SceneLayout } from "./sceneLayout";

import {
  LEGEND_ORDER,
  NODE_COLORS,
  STAGE_TO_TYPES,
  type FocusStage,
} from "./constants";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface SceneControlsProps {
  layout: SceneLayout;
  hoveredNodeId: string | null;
  hoveredNodeLabel: string | null;
  hoveredNodeType: string | null;
  focusedStage: FocusStage;
  viewMode: "journey" | "graph";
  onResetCamera: () => void;
  onBackToJourney: () => void;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function SceneControls({
  layout,
  hoveredNodeId,
  hoveredNodeLabel,
  hoveredNodeType,
  focusedStage,
  viewMode,
  onResetCamera,
  onBackToJourney,
}: SceneControlsProps) {
  const handleReset = useCallback(() => {
    onResetCamera();
  }, [onResetCamera]);

  // Build a count per node type from the layout.
  const countsByType = new Map<string, number>();
  for (const node of layout.nodes) {
    countsByType.set(
      node.type,
      (countsByType.get(node.type) ?? 0) + 1,
    );
  }

  // Types belonging to the current focus stage. Used to
  // dim unrelated legend rows.
  const focusedTypes = new Set<string>(
    STAGE_TO_TYPES[focusedStage] ?? [],
  );

  const isImpactMode = focusedStage === "IMPACT";

  // Only show types that actually appear, in legend order.
  const visibleTypes = LEGEND_ORDER.filter((t) =>
    countsByType.has(t),
  );

  return (
    <div className="cv-dia-scene-controls">
      {/* ---- Legend ---- */}
      <div className="cv-dia-scene-legend">
        <div className="cv-dia-scene-legend-head">
          <span>GRAPH LAYERS</span>
          <i />
        </div>

        <ul className="cv-dia-scene-legend-list">
          {visibleTypes.map((type) => {
            const color =
              NODE_COLORS[type] ?? "#8a8a8a";
            const count = countsByType.get(type) ?? 0;

            const isFocused = focusedTypes.has(type);
            const dim =
              !isImpactMode && !isFocused;

            return (
              <li
                key={type}
                className={
                  "cv-dia-scene-legend-item" +
                  (dim
                    ? " cv-dia-scene-legend-item-dim"
                    : "")
                }
              >
                <span
                  className="cv-dia-scene-legend-swatch"
                  style={{ backgroundColor: color }}
                />
                <span className="cv-dia-scene-legend-label">
                  {type}
                </span>
                <span className="cv-dia-scene-legend-count">
                  {count}
                </span>
              </li>
            );
          })}
        </ul>
      </div>

      {/* ---- Hover readout ---- */}
      <div className="cv-dia-scene-hover">
        {hoveredNodeId && hoveredNodeLabel ? (
          <>
            <div className="cv-dia-scene-hover-type">
              {hoveredNodeType}
            </div>
            <div className="cv-dia-scene-hover-label">
              {hoveredNodeLabel}
            </div>
          </>
        ) : (
          <div className="cv-dia-scene-hover-idle">
            Hover a node to inspect
          </div>
        )}
      </div>

      {/* ---- Back to journey (graph mode only) ---- */}
      {viewMode === "graph" ? (
        <button
          type="button"
          className="cv-dia-scene-back"
          onClick={onBackToJourney}
          aria-label="Back to journey"
        >
          <span>← Back to journey</span>
        </button>
      ) : null}

      {/* ---- Reset button ---- */}
      <button
        type="button"
        className="cv-dia-scene-reset"
        onClick={handleReset}
        aria-label="Reset camera"
      >
        <span>Reset view</span>
      </button>
    </div>
  );
}
