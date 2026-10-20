/**
 * CureVerseAI — Disease → Biological Impact
 * Bubble journey orchestrator.
 *
 * Manages the current level of the journey, the
 * breadcrumb, hover state, and the transition into the
 * full graph when a terminal bubble is clicked.
 *
 * State machine:
 *
 *   idle     — no journey data available (empty result)
 *   journey  — showing a bubble level; the current level's
 *              parent path is in `path`
 *   graph    — user clicked a terminal bubble; the full
 *              abstract graph is now displayed
 *
 * Clicking a non-terminal bubble advances to its
 * children. Clicking a breadcrumb segment jumps back.
 * Clicking a terminal bubble opens the graph.
 */

"use client";

import {
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import type { BiologicalImpactResult } from "../types";

import BubbleLevel from "./BubbleLevel";
import BubbleBreadcrumb from "./BubbleBreadcrumb";

import {
  buildJourney,
  type Bubble,
} from "./bubbleJourney";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface BubbleJourneyProps {
  result: BiologicalImpactResult;
  /** Called when the user clicks a terminal bubble. */
  onOpenGraph: () => void;
  /**
   * Called whenever the journey's current label changes —
   * either the level is loaded or a bubble is clicked.
   * The parent uses this to trigger avatar narration.
   */
  onNarrate: (label: string) => void;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function BubbleJourney({
  result,
  onOpenGraph,
  onNarrate,
}: BubbleJourneyProps) {
  // ---- Build the journey tree once per result -------------
  const root = useMemo(
    () => buildJourney(result),
    [result],
  );

  // ---- Path from root to the currently displayed level ----
  // The last element of `path` is the parent whose children
  // are shown. An empty path means the root bubble itself
  // is shown as a single-bubble level.
  const [path, setPath] = useState<Bubble[]>([]);

  const [hoveredId, setHoveredId] = useState<string | null>(
    null,
  );

  // Reset path when the result changes.
  useEffect(() => {
    setPath([]);
    setHoveredId(null);
  }, [result]);

  // Narrate whenever the current level changes.
  useEffect(() => {
    if (!root) return;

    if (path.length === 0) {
      // Root level — narrate the system name.
      onNarrate(root.label);
      return;
    }

    // Deeper level — narrate the parent we just opened.
    const parent = path[path.length - 1];
    onNarrate(parent.label);
  }, [path, root, onNarrate]);

  // ---- Derive the current level's bubbles -----------------

  const currentBubbles: Bubble[] = useMemo(() => {
    if (!root) return [];

    if (path.length === 0) {
      // First level: show the root bubble alone.
      return [root];
    }

    const parent = path[path.length - 1];
    return parent.children;
  }, [root, path]);

  // ---- Interaction handlers -------------------------------

  const handleBubbleClick = useCallback(
    (bubble: Bubble) => {
      if (bubble.opensGraph) {
        onOpenGraph();
        return;
      }

      if (bubble.children.length > 0) {
        // Descend one level.
        setPath((prev) => [...prev, bubble]);
        setHoveredId(null);
      } else {
        // Leaf with no children and no graph flag —
        // treat as terminal anyway.
        onOpenGraph();
      }
    },
    [onOpenGraph],
  );

  const handleBreadcrumbJump = useCallback(
    (depth: number) => {
      // depth = -1 → back to root (empty path)
      // depth = 0 → show root's children
      // depth = n → show level n
      if (depth < 0) {
        setPath([]);
      } else {
        setPath((prev) => prev.slice(0, depth + 1));
      }
      setHoveredId(null);
    },
    [],
  );

  // ---- Empty case -----------------------------------------

  if (!root) {
    return null;
  }

  // ---- Render ---------------------------------------------

  return (
    <group>
      <BubbleLevel
        bubbles={currentBubbles}
        depth={path.length}
        hoveredId={hoveredId}
        onHoverChange={setHoveredId}
        onClick={handleBubbleClick}
      />

      {/* Breadcrumb is an HTML overlay anchored at world
          origin so it moves with the level. drei's <Html>
          attaches to the 3D space. */}
      <BubbleBreadcrumb
        root={root}
        path={path}
        onJump={handleBreadcrumbJump}
      />
    </group>
  );
}
