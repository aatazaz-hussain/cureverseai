"use client";

/**
 * CureVerseAI — Medicine domain
 * Workflow 02 specific components.
 */

import type {
  BiologicalState,
  FunctionalIndicator,
  SimulationResult,
} from "../../_shared/types";

import MechanismGraph from "../../_shared/components/MechanismGraph";
import ScenarioComparison from "../../_shared/components/ScenarioComparison";
import FunctionalComparisonTable from "../../_shared/components/FunctionalComparisonTable";

interface OverviewProps {
  result: SimulationResult;
  selectedIndicatorId: string | null;
  onIndicatorSelect: (id: string) => void;
}

export function W02Overview({
  result,
  selectedIndicatorId,
  onIndicatorSelect,
}: OverviewProps) {
  const intervention = result.states.find(
    (s) => s.kind === "intervention_single",
  )?.intervention_ref ?? null;

  const responses = result.comparison?.responses ?? [];

  return (
    <div className="cv-medicine-wf-ts-overview">
      <MechanismGraph
        intervention={intervention}
        indicators={result.indicators}
        responses={responses}
        onSelect={onIndicatorSelect}
      />

      <ScenarioComparison
        indicators={result.indicators}
        scenarios={result.comparison?.scenarios ?? result.states}
        responses={responses}
        overallInterpretation={
          result.comparison?.overall_interpretation ??
          "no_defensible_winner"
        }
        interactionClass={result.comparison?.interaction_class ?? null}
      />
    </div>
  );
}

interface ComparisonProps {
  result: SimulationResult;
  selectedIndicatorId: string | null;
  onIndicatorSelect: (id: string) => void;
}

export function W02Comparison({
  result,
  selectedIndicatorId,
  onIndicatorSelect,
}: ComparisonProps) {
  return (
    <FunctionalComparisonTable
      indicators={result.indicators}
      responses={result.comparison?.responses ?? []}
      selectedIndicatorId={selectedIndicatorId}
      onRowSelect={onIndicatorSelect}
    />
  );
}

interface EvidenceListProps {
  result: SimulationResult;
}

export function W02EvidenceList({ result }: EvidenceListProps) {
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
    <div className="cv-medicine-wf-panel cv-medicine-wf-ts-evidence">
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

export function W02StateNote({ result }: { result: SimulationResult }) {
  const linkSupported = Boolean(
    (result.run.metadata as Record<string, unknown>)?.link_supported,
  );

  if (linkSupported) return null;

  return (
    <div className="cv-medicine-wf-banner cv-medicine-wf-banner--warn">
      <strong>No disease-context linkage.</strong>
      <span style={{ marginLeft: 8 }}>
        The intervention&apos;s targets were not linked to the selected
        disease by the available sources. No beneficial response is
        claimed.
      </span>
    </div>
  );
}
