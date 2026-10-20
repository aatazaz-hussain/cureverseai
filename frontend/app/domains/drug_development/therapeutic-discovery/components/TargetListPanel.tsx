/**
 * CureVerseAI — Drug Development
 * Workflow 03 — Therapeutic Discovery
 * TargetListPanel.
 *
 * List of candidate targets split into two groups:
 *
 *   - mechanism members (targets in the selected pathway)
 *   - Open Targets only (disease associations without
 *     pathway membership)
 *
 * Every row is read-only. No composite score is shown.
 */

"use client";

import type {
  TargetBlock,
  TherapeuticDiscoveryResult,
} from "../types";

interface TargetListPanelProps {
  result: TherapeuticDiscoveryResult;
}

export default function TargetListPanel({
  result,
}: TargetListPanelProps) {
  const targets = result.targets ?? [];

  if (!targets.length) return null;

  const members = targets.filter(
    (t) => t.mechanism_membership,
  );
  const others = targets.filter(
    (t) => !t.mechanism_membership,
  );

  return (
    <div className="cv-thedisc-targets">
      <header className="cv-thedisc-targets-head">
        <span className="cv-thedisc-targets-eyebrow">
          CANDIDATE TARGETS
        </span>
        <strong>{targets.length} total</strong>
      </header>

      {members.length ? (
        <div className="cv-thedisc-targets-group">
          <h4>
            <i className="is-member" />
            Mechanism members ({members.length})
          </h4>
          <ul>
            {members.slice(0, 10).map((t) => (
              <TargetRow key={t.target_id} target={t} />
            ))}
          </ul>
        </div>
      ) : null}

      {others.length ? (
        <div className="cv-thedisc-targets-group">
          <h4>
            <i className="is-other" />
            Disease associations ({others.length})
          </h4>
          <ul>
            {others.slice(0, 10).map((t) => (
              <TargetRow key={t.target_id} target={t} />
            ))}
          </ul>
        </div>
      ) : null}
    </div>
  );
}

function TargetRow({ target }: { target: TargetBlock }) {
  const ot = target.open_targets_score;

  return (
    <li className="cv-thedisc-target-row">
      <div className="cv-thedisc-target-row-name">
        <strong>{target.gene_symbol ?? target.label}</strong>
        {target.uniprot_id ? (
          <span>{target.uniprot_id}</span>
        ) : null}
      </div>
      <div className="cv-thedisc-target-row-meta">
        {target.mechanism_membership ? (
          <span className="cv-thedisc-target-badge is-member">
            pathway
          </span>
        ) : null}
        {ot !== null ? (
          <span className="cv-thedisc-target-score">
            OT {ot.toFixed(2)}
          </span>
        ) : null}
      </div>
    </li>
  );
}
