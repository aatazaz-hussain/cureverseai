"use client";

/**
 * CureVerseAI — Medicine domain
 * Workflow 01 specific components.
 *
 * Pieces that only W01 uses. Everything shared lives in
 * _shared/components.
 */

import type {
  BiologicalState,
  FunctionalIndicator,
  SimulationResult,
} from "../../_shared/types";

interface OverviewProps {
  result: SimulationResult;
  selectedIndicatorId: string | null;
  onIndicatorSelect: (id: string) => void;
}

import CellStateView from "../../_shared/components/CellStateView";
import FunctionalComparisonTable from "../../_shared/components/FunctionalComparisonTable";

export function W01Overview({
  result,
  selectedIndicatorId,
  onIndicatorSelect,
}: OverviewProps) {
  const healthy: BiologicalState | null =
    result.states.find((s) => s.kind === "healthy_reference") ?? null;
  const disease: BiologicalState | null =
    result.states.find((s) => s.kind === "disease") ?? null;

  const indicators: FunctionalIndicator[] = result.indicators;
  const responses = result.comparison?.responses ?? [];

  return (
    <div className="cv-medicine-wf-ds-overview">
      <CellStateView
        healthy={healthy}
        disease={disease}
        indicators={indicators}
        selectedIndicatorId={selectedIndicatorId}
        onIndicatorSelect={onIndicatorSelect}
      />

      <FunctionalComparisonTable
        indicators={indicators}
        responses={responses}
        selectedIndicatorId={selectedIndicatorId}
        onRowSelect={onIndicatorSelect}
      />
    </div>
  );
}

interface EvidenceListProps {
  result: SimulationResult;
}

export function W01EvidenceList({ result }: EvidenceListProps) {
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
    <div className="cv-medicine-wf-panel cv-medicine-wf-ds-evidence">
      <div className="cv-medicine-wf-panel-header">
        <h3 className="cv-medicine-wf-panel-title">
          Evidence records
        </h3>
        <span className="cv-medicine-wf-chip">
          {result.evidence.length} total
        </span>
      </div>

      <ul className="cv-medicine-wf-evidence-list">
        {result.evidence.map((e) => (
          <li
            key={e.evidence_id}
            className="cv-medicine-wf-evidence-item"
          >
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
