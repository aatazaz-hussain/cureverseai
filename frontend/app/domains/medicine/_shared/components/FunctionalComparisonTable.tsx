"use client";

/**
 * CureVerseAI — Medicine domain
 * Functional comparison table.
 *
 * One row per indicator. Shows direction of change, method
 * (observed / model_predicted / mechanistic_inference /
 * insufficient), and uncertainty level. Values that are not
 * present render as "—" with a tooltip sourced from the
 * backend's uncertainty.reasons list.
 */

import type {
  FunctionalIndicator,
  Response,
} from "../types";

interface Props {
  indicators: FunctionalIndicator[];
  responses: Response[];
  onRowSelect?: (indicatorId: string) => void;
  selectedIndicatorId?: string | null;
}

const METHOD_LABELS: Record<string, string> = {
  observed: "Observed",
  model_predicted: "Model-predicted",
  mechanistic_inference: "Mechanistic inference",
  insufficient: "Insufficient",
};

const DIRECTION_GLYPHS: Record<string, string> = {
  increase: "↑",
  decrease: "↓",
  unchanged: "→",
  unknown: "?",
};

export default function FunctionalComparisonTable({
  indicators,
  responses,
  onRowSelect,
  selectedIndicatorId,
}: Props) {
  const byIndicator = new Map<string, Response>();
  for (const r of responses) byIndicator.set(r.indicator_id, r);

  return (
    <div className="cv-medicine-wf-panel cv-medicine-wf-tablepanel">
      <div className="cv-medicine-wf-panel-header">
        <h3 className="cv-medicine-wf-panel-title">
          Functional comparison
        </h3>
      </div>

      <div className="cv-medicine-wf-table-wrap">
        <table className="cv-medicine-wf-table">
          <thead>
            <tr>
              <th>Indicator</th>
              <th>Change</th>
              <th>Method</th>
              <th>Uncertainty</th>
              <th>Evidence</th>
            </tr>
          </thead>
          <tbody>
            {indicators.map((ind) => {
              const r = byIndicator.get(ind.id);
              const selected = selectedIndicatorId === ind.id;
              const uncertaintyLevel =
                r?.uncertainty?.level ?? "unknown";
              const reasons =
                r?.uncertainty?.reasons ?? [];
              const tooltip =
                reasons.length > 0
                  ? reasons.join(" • ")
                  : "No explanation provided by the backend.";

              return (
                <tr
                  key={ind.id}
                  className={
                    "cv-medicine-wf-table-row" +
                    (selected
                      ? " cv-medicine-wf-table-row--selected"
                      : "")
                  }
                  onClick={() => onRowSelect?.(ind.id)}
                  tabIndex={0}
                  onKeyDown={(e) => {
                    if (e.key === "Enter" || e.key === " ") {
                      e.preventDefault();
                      onRowSelect?.(ind.id);
                    }
                  }}
                >
                  <td className="cv-medicine-wf-table-cell-name">
                    <div className="cv-medicine-wf-table-name">
                      {ind.name}
                    </div>
                    {ind.description ? (
                      <div className="cv-medicine-wf-table-desc">
                        {ind.description}
                      </div>
                    ) : null}
                  </td>
                  <td>
                    <span
                      className={
                        "cv-medicine-wf-dir cv-medicine-wf-dir--" +
                        (r?.direction_change ?? "unknown")
                      }
                    >
                      {DIRECTION_GLYPHS[r?.direction_change ?? "unknown"]}{" "}
                      {r?.direction_change ?? "unknown"}
                    </span>
                  </td>
                  <td>
                    <span className="cv-medicine-wf-method">
                      {METHOD_LABELS[r?.method ?? "insufficient"] ??
                        (r?.method ?? "insufficient")}
                    </span>
                  </td>
                  <td>
                    <span
                      className={
                        "cv-medicine-wf-unc cv-medicine-wf-unc--" +
                        uncertaintyLevel
                      }
                      title={tooltip}
                    >
                      {uncertaintyLevel}
                    </span>
                  </td>
                  <td className="cv-medicine-wf-table-cell-ev">
                    {r && r.evidence_ids.length > 0
                      ? `${r.evidence_ids.length} source${r.evidence_ids.length === 1 ? "" : "s"}`
                      : "—"}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      <div className="cv-medicine-wf-table-footnote">
        This table does not contain a composite score. Directions are
        categorical, not numeric.
      </div>
    </div>
  );
}
