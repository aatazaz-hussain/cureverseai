"use client";

/**
 * CureVerseAI — Medicine domain
 * Scenario comparison.
 *
 * Renders N scenarios side by side against a baseline, using
 * the same indicator rows for every scenario. Used by W02
 * (two scenarios) and W03 (four scenarios).
 *
 * The overall interpretation is displayed verbatim from the
 * backend. No client-side ranking is performed here.
 */

import type {
  BiologicalState,
  FunctionalIndicator,
  OverallInterpretation,
  InteractionClass,
  Response,
} from "../types";

interface Props {
  indicators: FunctionalIndicator[];
  scenarios: BiologicalState[];
  responses: Response[];
  overallInterpretation: OverallInterpretation;
  interactionClass: InteractionClass | null;
  onCellSelect?: (scenarioStateId: string, indicatorId: string) => void;
}

function interpretationLabel(i: OverallInterpretation): string {
  switch (i) {
    case "best_supported":
      return "Best-supported scenario within the evaluated model";
    case "promising_uncertain":
      return "Promising but uncertain";
    case "no_defensible_winner":
      return "No defensible winner";
    case "potentially_adverse":
      return "Potentially adverse";
    case "not_modelled":
    default:
      return "Not modelled";
  }
}

function interactionLabel(i: InteractionClass | null): string | null {
  if (!i) return null;
  switch (i) {
    case "additive":
      return "Additive";
    case "synergistic":
      return "Synergistic";
    case "antagonistic":
      return "Antagonistic";
    case "overlapping":
      return "Overlapping";
    case "adverse":
      return "Adverse";
    case "unknown":
      return "Unknown interaction";
    case "insufficient_evidence":
    default:
      return "Not classified (insufficient evidence)";
  }
}

export default function ScenarioComparison({
  indicators,
  scenarios,
  responses,
  overallInterpretation,
  interactionClass,
  onCellSelect,
}: Props) {
  const responseByKey = new Map<string, Response>();
  for (const r of responses) {
    responseByKey.set(`${r.scenario_state_id}::${r.indicator_id}`, r);
  }

  // Column headers from the scenario state kinds.
  const headers = scenarios.map((s) => {
    switch (s.kind) {
      case "healthy_reference":
        return "Healthy";
      case "disease":
        return "Disease";
      case "intervention_single":
        return s.intervention_ref?.name ?? "Intervention";
      case "intervention_combination":
        return "Combination";
      default:
        return s.state_id;
    }
  });

  return (
    <div className="cv-medicine-wf-panel cv-medicine-wf-scenarios">
      <div className="cv-medicine-wf-panel-header">
        <h3 className="cv-medicine-wf-panel-title">
          Scenario comparison
        </h3>
        <div className="cv-medicine-wf-scenarios-badges">
          <span
            className={
              "cv-medicine-wf-chip cv-medicine-wf-chip--interp cv-medicine-wf-chip--interp-" +
              overallInterpretation
            }
          >
            {interpretationLabel(overallInterpretation)}
          </span>
          {interactionClass ? (
            <span
              className={
                "cv-medicine-wf-chip cv-medicine-wf-chip--interaction cv-medicine-wf-chip--interaction-" +
                interactionClass
              }
            >
              {interactionLabel(interactionClass)}
            </span>
          ) : null}
        </div>
      </div>

      <div className="cv-medicine-wf-table-wrap">
        <table className="cv-medicine-wf-table cv-medicine-wf-table--scenarios">
          <thead>
            <tr>
              <th>Indicator</th>
              {scenarios.map((s, i) => (
                <th key={s.state_id}>
                  <div className="cv-medicine-wf-scenario-head">
                    <span className="cv-medicine-wf-scenario-head-label">
                      {headers[i]}
                    </span>
                    <span className="cv-medicine-wf-scenario-head-kind">
                      {s.kind}
                    </span>
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {indicators.map((ind) => (
              <tr key={ind.id} className="cv-medicine-wf-table-row">
                <td className="cv-medicine-wf-table-cell-name">
                  <div className="cv-medicine-wf-table-name">
                    {ind.name}
                  </div>
                </td>
                {scenarios.map((s) => {
                  const key = `${s.state_id}::${ind.id}`;
                  const r = responseByKey.get(key);
                  const base = s.indicator_values?.[ind.id];
                  const direction = r?.direction_change ?? base?.direction ?? "unknown";
                  const method = r?.method ?? base?.method ?? "insufficient";

                  return (
                    <td
                      key={key}
                      className="cv-medicine-wf-scenario-cell"
                      onClick={() => onCellSelect?.(s.state_id, ind.id)}
                    >
                      <div
                        className={
                          "cv-medicine-wf-dir cv-medicine-wf-dir--" +
                          direction
                        }
                      >
                        {direction}
                      </div>
                      <div className="cv-medicine-wf-scenario-method">
                        {method}
                      </div>
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div className="cv-medicine-wf-table-footnote">
        Interpretation is categorical, not a numeric score. Ranking is
        only shown when the model and evidence support it.
      </div>
    </div>
  );
}
