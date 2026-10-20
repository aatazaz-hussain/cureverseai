/**
 * CureVerseAI — Disease → Biological Impact
 * Stage bar.
 *
 * The 8-stage navigation bar from spec §15. Lives at the
 * page level (above the results section), not inside the
 * scene, per the Phase 15 Option 1 decision. The page's
 * ResolvedBlock owns the focus state and passes both the
 * current focus and a setter down.
 *
 * Stages:
 *
 *   01 DISEASE   → focus the root node
 *   02 SYSTEM    → focus the systems ring
 *   03 ORGAN     → focus the organs ring
 *   04 TISSUE    → focus the tissue ring
 *   05 CELL      → focus the cell ring
 *   06 MOLECULE  → focus gene + protein + molecule rings
 *   07 PATHWAY   → focus the pathway ring
 *   08 IMPACT    → overview, all rings
 */

"use client";

import { useCallback } from "react";

import type { FocusStage } from "./scene/constants";
import { STAGE_ORDER } from "./scene/constants";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface StageBarProps {
  focusedStage: FocusStage;
  onStageChange: (stage: FocusStage) => void;
}

// ---------------------------------------------------------------------------
// Stage labels
// ---------------------------------------------------------------------------

const STAGE_LABELS: Record<FocusStage, { n: string; label: string }> = {
  DISEASE:  { n: "01", label: "DISEASE" },
  SYSTEM:   { n: "02", label: "SYSTEM" },
  ORGAN:    { n: "03", label: "ORGAN" },
  TISSUE:   { n: "04", label: "TISSUE" },
  CELL:     { n: "05", label: "CELL" },
  MOLECULE: { n: "06", label: "MOLECULE" },
  PATHWAY:  { n: "07", label: "PATHWAY" },
  IMPACT:   { n: "08", label: "IMPACT" },
};

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function StageBar({
  focusedStage,
  onStageChange,
}: StageBarProps) {
  const handleClick = useCallback(
    (stage: FocusStage) => {
      onStageChange(stage);
    },
    [onStageChange],
  );

  return (
    <div className="cv-dia-stage-bar" role="tablist">
      {STAGE_ORDER.map((stage) => {
        const { n, label } = STAGE_LABELS[stage];
        const active = stage === focusedStage;

        return (
          <button
            key={stage}
            type="button"
            role="tab"
            aria-selected={active}
            className={
              "cv-dia-stage" +
              (active ? " cv-dia-stage-active" : "")
            }
            onClick={() => handleClick(stage)}
          >
            <strong>{n}</strong>
            <span>{label}</span>
          </button>
        );
      })}
    </div>
  );
}
