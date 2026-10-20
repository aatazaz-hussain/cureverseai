"use client";

/**
 * CureVerseAI — Medicine domain
 * Workflow 03 specific components.
 */

import type { SimulationResult } from "../../_shared/types";

import ScenarioComparison from "../../_shared/components/ScenarioComparison";
import MechanismGraph from "../../_shared/components/MechanismGraph";

interface ScenariosProps {
  result: SimulationResult;
  selectedIndicatorId: string | null;
  onIndicatorSelect: (id: string) => void;
  onCellSelect: (scenarioStateId: string, indicatorId: string) => void;
}

export function W03Scenarios({
  result,
  selectedIndicatorId,
  onIndicatorSelect,
  onCellSelect,
}: ScenariosProps) {
  return (
    <ScenarioComparison
      indicators={result.indicators}
      scenarios={result.comparison?.scenarios ?? result.states}
      responses={result.comparison?.responses ?? []}
      overallInterpretation={
        result.comparison?.overall_interpretation ?? "not_modelled"
      }
      interactionClass={result.comparison?.interaction_class ?? null}
      onCellSelect={onCellSelect}
    />
  );
}

export function W03Mechanism({
  result,
  onIndicatorSelect,
}: {
  result: SimulationResult;
  onIndicatorSelect: (id: string) => void;
}) {
  // Show the first intervention (A) as the anchor for the graph.
  const interventionA =
    result.states
      .filter((s) => s.kind === "intervention_single")
      .map((s) => s.intervention_ref)
      .filter((r): r is NonNullable<typeof r> => Boolean(r))[0] ?? null;

  return (
    <MechanismGraph
      intervention={interventionA}
      indicators={result.indicators}
      responses={result.comparison?.responses ?? []}
      onSelect={onIndicatorSelect}
    />
  );
}

export function W03EvidenceList({ result }: { result: SimulationResult }) {
  if (result.evidence.length === 0) {
    return (
      <div className="cv-medicine-wf-panel">
        <div className="cv-medicine-wf-empty-inline">
          No evidence records were produced for this result.
        </div>
      </div>
    );
  }

  return (
    <div className="cv-medicine-wf-panel cv-medicine-wf-ct-evidence">
      <div className="cv-medicine-wf-panel-header">
        <h3 className="cv-medicine-wf-panel-title">Evidence records</h3>
        <span className="cv-medicine-wf-chip">
          {result.evidence.length} total
        </span>
      </div>

      <ul className="cv-medicine-wf-evidence-list">
        {result.evidence.map((e) => (
          <li key={e.evidence_id} className="cv-medicine-wf-evidence-item">
            <div className="cv-medicine-wf-evidence-head">
              <span className="cv-medicine-wf-chip">{e.source}</span>
              {e.evidence_level ? (
                <span className="cv-medicine-wf-chip cv-medicine-wf-chip--ghost">
                  {e.evidence_level}
                </span>
              ) : null}
            </div>
            <div className="cv-medicine-wf-evidence-desc">
              {e.description}
            </div>
            {e.provenance ? (
              <div className="cv-medicine-wf-evidence-prov">
                <span>
                  {e.provenance.source}
                  {e.provenance.source_id
                    ? ` · ${e.provenance.source_id}`
                    : ""}
                </span>
                {e.provenance.url ? (
                  <a
                    href={e.provenance.url}
                    target="_blank"
                    rel="noreferrer"
                    className="cv-medicine-wf-evidence-link"
                  >
                    Open source
                  </a>
                ) : null}
              </div>
            ) : null}
          </li>
        ))}
      </ul>
    </div>
  );
}
