"use client";

/**
 * CureVerseAI — Medicine domain
 * Cell state view (Workflow 01).
 *
 * Side-by-side stylized cell representations for the healthy
 * reference state and the disease state. Highlights are driven
 * ONLY by indicator directions returned by the backend. No
 * magnitude, no percentage, no fabricated colour intensity.
 *
 * The visual is a stylized schematic, not a 3D simulation. It
 * does not imply a full cellular simulation has been performed.
 */

import type {
  BiologicalState,
  FunctionalIndicator,
  ResponseDirection,
} from "../types";

interface Props {
  healthy: BiologicalState | null;
  disease: BiologicalState | null;
  indicators: FunctionalIndicator[];
  selectedIndicatorId?: string | null;
  onIndicatorSelect?: (indicatorId: string) => void;
}

function directionClass(dir: ResponseDirection | undefined): string {
  switch (dir) {
    case "increase":
      return "cv-medicine-wf-cell-region--up";
    case "decrease":
      return "cv-medicine-wf-cell-region--down";
    case "unchanged":
      return "cv-medicine-wf-cell-region--unchanged";
    default:
      return "cv-medicine-wf-cell-region--unknown";
  }
}

function renderCell(
  label: string,
  state: BiologicalState | null,
  indicators: FunctionalIndicator[],
  selectedIndicatorId: string | null | undefined,
  onIndicatorSelect: ((id: string) => void) | undefined,
) {
  return (
    <div className="cv-medicine-wf-cell">
      <div className="cv-medicine-wf-cell-label">{label}</div>
      <div className="cv-medicine-wf-cell-svg-wrap">
        <svg
          className="cv-medicine-wf-cell-svg"
          viewBox="0 0 200 200"
          role="img"
          aria-label={label}
        >
          <defs>
            <radialGradient id={`cellbg-${label}`} cx="50%" cy="50%" r="50%">
              <stop offset="0%" stopColor="rgba(255,255,255,0.06)" />
              <stop offset="100%" stopColor="rgba(255,255,255,0.01)" />
            </radialGradient>
          </defs>
          <circle cx="100" cy="100" r="86" fill={`url(#cellbg-${label})`} stroke="rgba(255,255,255,0.16)" />
          <ellipse cx="100" cy="100" rx="34" ry="26" fill="rgba(255,255,255,0.05)" stroke="rgba(255,255,255,0.12)" />
        </svg>

        {indicators.map((ind, i) => {
          const value = state?.indicator_values?.[ind.id];
          const direction = value?.direction;
          const isSelected = selectedIndicatorId === ind.id;
          const angle = (i / Math.max(indicators.length, 1)) * 2 * Math.PI;
          const cx = 100 + Math.cos(angle) * 62;
          const cy = 100 + Math.sin(angle) * 62;

          return (
            <button
              key={ind.id}
              type="button"
              className={
                "cv-medicine-wf-cell-region " +
                directionClass(direction) +
                (isSelected
                  ? " cv-medicine-wf-cell-region--selected"
                  : "")
              }
              style={{
                left: `calc(${(cx / 200) * 100}% - 10px)`,
                top: `calc(${(cy / 200) * 100}% - 10px)`,
              }}
              onClick={() => onIndicatorSelect?.(ind.id)}
              title={`${ind.name} — ${value?.direction ?? "unknown"} (${value?.method ?? "insufficient"})`}
              aria-label={ind.name}
            >
              <span className="cv-medicine-wf-cell-region-dot" />
              <span className="cv-medicine-wf-cell-region-name">
                {ind.name}
              </span>
            </button>
          );
        })}
      </div>
    </div>
  );
}

export default function CellStateView({
  healthy,
  disease,
  indicators,
  selectedIndicatorId,
  onIndicatorSelect,
}: Props) {
  return (
    <div className="cv-medicine-wf-panel cv-medicine-wf-cellstate">
      <div className="cv-medicine-wf-panel-header">
        <h3 className="cv-medicine-wf-panel-title">
          Cell state comparison
        </h3>
        <span className="cv-medicine-wf-chip cv-medicine-wf-chip--ghost">
          Schematic — not a 3D simulation
        </span>
      </div>

      <div className="cv-medicine-wf-cellstate-grid">
        {renderCell(
          "Healthy reference",
          healthy,
          indicators,
          selectedIndicatorId,
          onIndicatorSelect,
        )}
        {renderCell(
          "Disease state",
          disease,
          indicators,
          selectedIndicatorId,
          onIndicatorSelect,
        )}
      </div>

      <div className="cv-medicine-wf-cellstate-legend">
        <span className="cv-medicine-wf-cellstate-legend-item cv-medicine-wf-cell-region--up">Increase</span>
        <span className="cv-medicine-wf-cellstate-legend-item cv-medicine-wf-cell-region--down">Decrease</span>
        <span className="cv-medicine-wf-cellstate-legend-item cv-medicine-wf-cell-region--unchanged">Unchanged</span>
        <span className="cv-medicine-wf-cellstate-legend-item cv-medicine-wf-cell-region--unknown">Unknown</span>
      </div>
    </div>
  );
}
