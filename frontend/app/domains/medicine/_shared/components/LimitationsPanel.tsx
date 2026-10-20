"use client";

/**
 * CureVerseAI — Medicine domain
 * Limitations and warnings panel.
 *
 * Renders two lists verbatim from the backend:
 *   result.limitations
 *   result.warnings
 *
 * Nothing is reworded or summarised.
 */

interface Props {
  limitations: string[];
  warnings: string[];
}

export default function LimitationsPanel({
  limitations,
  warnings,
}: Props) {
  const hasLimitations = limitations && limitations.length > 0;
  const hasWarnings = warnings && warnings.length > 0;

  if (!hasLimitations && !hasWarnings) {
    return null;
  }

  return (
    <div className="cv-medicine-wf-panel cv-medicine-wf-limits">
      <div className="cv-medicine-wf-panel-header">
        <h3 className="cv-medicine-wf-panel-title">
          Limitations & warnings
        </h3>
      </div>

      {hasLimitations ? (
        <div className="cv-medicine-wf-limits-block">
          <div className="cv-medicine-wf-limits-label">Limitations</div>
          <ul className="cv-medicine-wf-limits-list">
            {limitations.map((l, i) => (
              <li key={`lim-${i}`}>{l}</li>
            ))}
          </ul>
        </div>
      ) : null}

      {hasWarnings ? (
        <div className="cv-medicine-wf-limits-block">
          <div className="cv-medicine-wf-limits-label cv-medicine-wf-limits-label--warn">
            Warnings
          </div>
          <ul className="cv-medicine-wf-limits-list cv-medicine-wf-limits-list--warn">
            {warnings.map((w, i) => (
              <li key={`warn-${i}`}>{w}</li>
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}
