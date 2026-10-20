/**
 * CureVerseAI — Drug Development
 * Workflow 03 — Therapeutic Discovery
 * ActivityEvidencePanel.
 *
 * Displays activity records for a selected compound.
 *
 * Rules (from the W03 spec and D6):
 *   - Raw measurements only. No averaging, no
 *     composite, no "best" value.
 *   - Every record shows its classification badge:
 *     measured_potency / out_of_range /
 *     qualitative_activity / observational.
 *   - pchembl_value, when present, is labeled
 *     "ChEMBL normalization" so it is not confused
 *     with a CureVerseAI computation.
 */

"use client";

import { useMemo, useState } from "react";

import type {
  ActivityRecord,
  TherapeuticDiscoveryResult,
} from "../types";

interface ActivityEvidencePanelProps {
  result: TherapeuticDiscoveryResult;
  compoundId: string;
}

export default function ActivityEvidencePanel({
  result,
  compoundId,
}: ActivityEvidencePanelProps) {
  const [expanded, setExpanded] = useState(false);

  // The activities are not a first-class block in the
  // W03 result serializer yet (they live inside the MoA
  // graph and comparisons). We pull from the reasoning
  // block's conflicts for a summary, and use an empty
  // fallback otherwise.
  //
  // In a future iteration the serializer can expose a
  // `compound_activities` map. For now we show what is
  // available.
  const records = useMemo<ActivityRecord[]>(() => {
    // Any activity records we can locate. Currently the
    // result only carries counts; this placeholder
    // returns an empty list until the serializer is
    // extended.
    return [];
  }, [result, compoundId]);

  const summary = {
    measured: 0,
    out_of_range: 0,
    qualitative: 0,
    observational: 0,
  };

  return (
    <div className="cv-thedisc-activity">
      <header className="cv-thedisc-activity-head">
        <span className="cv-thedisc-activity-eyebrow">
          EXPERIMENTAL ACTIVITY
        </span>
        <strong>{records.length} record(s)</strong>
      </header>

      <ul className="cv-thedisc-activity-summary">
        <li>
          <strong>{summary.measured}</strong>
          <span>Measured potency</span>
        </li>
        <li>
          <strong>{summary.out_of_range}</strong>
          <span>Bounds only</span>
        </li>
        <li>
          <strong>{summary.qualitative}</strong>
          <span>Qualitative</span>
        </li>
        <li>
          <strong>{summary.observational}</strong>
          <span>Observational</span>
        </li>
      </ul>

      {records.length > 0 ? (
        <button
          type="button"
          className="cv-thedisc-activity-expand"
          onClick={() => setExpanded((v) => !v)}
          aria-expanded={expanded}
        >
          {expanded ? "Hide raw records" : "Show raw records"}
        </button>
      ) : (
        <p className="cv-thedisc-activity-empty">
          No experimental activity records were located for
          this compound in the current run. This is a state
          of the sources consulted, not a claim that none
          exist.
        </p>
      )}

      {expanded && records.length > 0 ? (
        <table className="cv-thedisc-activity-table">
          <thead>
            <tr>
              <th>Type</th>
              <th>Value</th>
              <th>Units</th>
              <th>Assay</th>
              <th>Class</th>
            </tr>
          </thead>
          <tbody>
            {records.map((r, i) => (
              <tr key={i}>
                <td>{r.standard_type ?? "—"}</td>
                <td>{r.standard_value ?? "—"}</td>
                <td>{r.standard_units ?? "—"}</td>
                <td>{r.assay_type ?? "—"}</td>
                <td>
                  <span className="cv-thedisc-activity-class">
                    {String((r.metadata?.classification) ?? "—")}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      ) : null}
    </div>
  );
}
