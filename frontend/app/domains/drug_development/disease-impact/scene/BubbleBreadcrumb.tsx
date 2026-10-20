/**
 * CureVerseAI — Disease → Biological Impact
 * Bubble journey breadcrumb.
 *
 * An HTML overlay that shows the path from root to the
 * currently displayed level, with clickable segments that
 * jump back to any ancestor.
 *
 * Rendered via drei's <Html> attached to the world
 * origin, so it stays fixed in world space while the
 * camera orbits. A CSS transform pulls it up out of the
 * scene's center.
 */

"use client";

import { Html } from "@react-three/drei";

import type { Bubble } from "./bubbleJourney";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface BubbleBreadcrumbProps {
  root: Bubble;
  /** Path from root to current parent. Empty means root is the current level. */
  path: Bubble[];
  /** Called when a breadcrumb segment is clicked. */
  onJump: (depth: number) => void;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function BubbleBreadcrumb({
  root,
  path,
  onJump,
}: BubbleBreadcrumbProps) {
  // Segments to display:
  //   - "ROOT" always (depth -1)
  //   - "root.label" (depth 0)
  //   - each path element (depth i+1)
  //
  // When path is empty, we show only "root.label".
  const segments: { label: string; depth: number }[] = [];

  segments.push({ label: root.label, depth: -1 });

  path.forEach((bubble, i) => {
    segments.push({ label: bubble.label, depth: i });
  });

  return (
    <Html
      position={[0, 14, 0]}
      center
      zIndexRange={[14, 0]}
      style={{ pointerEvents: "none" }}
    >
      <nav
        className="cv-dia-bubble-crumb"
        aria-label="Journey breadcrumb"
      >
        {segments.map((seg, i) => {
          const isLast = i === segments.length - 1;

          return (
            <span key={`${seg.label}-${i}`}>
              {i > 0 ? (
                <i className="cv-dia-bubble-crumb-sep">›</i>
              ) : null}

              {isLast ? (
                <span className="cv-dia-bubble-crumb-current">
                  {seg.label}
                </span>
              ) : (
                <button
                  type="button"
                  className="cv-dia-bubble-crumb-btn"
                  onClick={() => onJump(seg.depth)}
                >
                  {seg.label}
                </button>
              )}
            </span>
          );
        })}
      </nav>
    </Html>
  );
}
