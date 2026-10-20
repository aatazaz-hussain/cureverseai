/**
 * CureVerseAI — Drug Development
 * Workflow 03 — Therapeutic Discovery
 * CompoundDetail.
 *
 * Right-side panel. Shown when a candidate compound is
 * selected. Composes:
 *   - Compound identity
 *   - Mechanism of action chain
 *   - Comparison dimensions
 *   - Activity evidence panel
 */

"use client";

import { useEffect, useMemo, useRef } from "react";

import {
  useTDStatus,
  useTDSelection,
  useTDNarration,
  useTDActions,
} from "../state";

import { speak, stopSpeaking, isSpeechAvailable } from "../voice";

import MechanismOfActionChain from "./MechanismOfActionChain";
import ActivityEvidencePanel from "./ActivityEvidencePanel";

import {
  ACTIVITY_QUALITY_LABELS,
  MECHANISM_LINK_LABELS,
} from "./types";

export default function CompoundDetail() {
  const status = useTDStatus();
  const selection = useTDSelection();
  const actions = useTDActions();

  const compoundId =
    selection.selected?.kind === "candidate"
      ? selection.selected.compound_id
      : null;

  const data = useMemo(() => {
    if (!compoundId || status.kind !== "loaded") {
      return null;
    }
    const { result } = status;

    const candidate = result.candidates.find(
      (c) => c.compound_id === compoundId,
    );
    if (!candidate) return null;

    const comparison =
      result.candidate_comparisons.find(
        (c) => c.candidate_id === compoundId,
      ) ?? null;

    return { result, candidate, comparison };
  }, [compoundId, status]);

  const narration = useTDNarration();
  const lastSpokenRef = useRef<string | null>(null);

  useEffect(() => {
    if (!narration.voiceEnabled) return;
    if (narration.isPlaying) return;
    if (!isSpeechAvailable()) return;
    if (!data) return;

    const { candidate, comparison } = data;

    const parts: string[] = [];
    parts.push(`Compound ${candidate.name ?? candidate.compound_id}.`);

    if (comparison) {
      if (comparison.activity_quality === "measured") {
        parts.push("Has measured activity.");
      } else if (comparison.activity_quality === "qualitative") {
        parts.push("Only qualitative activity.");
      } else {
        parts.push("No measured activity.");
      }

      if (comparison.mechanism_link_strength === "direct") {
        parts.push("Chain reaches the disease.");
      } else if (
        comparison.mechanism_link_strength === "two_hop"
      ) {
        parts.push("Chain reaches the pathway only.");
      }

      if (comparison.data_gaps > 0) {
        parts.push(
          `${comparison.data_gaps} unresolved link(s).`,
        );
      }
    } else {
      parts.push("Not ranked in the top 20.");
    }

    const text = parts.join(" ");
    if (lastSpokenRef.current === text) return;
    lastSpokenRef.current = text;
    speak(text);
  }, [data, narration.voiceEnabled, narration.isPlaying]);

  useEffect(() => {
    if (!compoundId) {
      stopSpeaking();
      lastSpokenRef.current = null;
    }
  }, [compoundId]);

  if (!compoundId) {
    return (
      <aside className="cv-thedisc-compound is-empty">
        <div className="cv-thedisc-compound-empty">
          <div className="cv-thedisc-compound-empty-icon">
            ◆
          </div>
          <h3>Compound detail</h3>
          <p>
            Select a compound from the graph or from the
            candidate explorer to inspect its target, its
            measured activity, and its
            mechanism-of-action chain.
          </p>
        </div>
      </aside>
    );
  }

  if (!data) {
    return (
      <aside className="cv-thedisc-compound is-empty">
        <div className="cv-thedisc-compound-empty">
          <h3>Compound not found</h3>
          <p>
            The selected compound is not present in the
            current result.
          </p>
        </div>
      </aside>
    );
  }

  const { result, candidate, comparison } = data;

  const chemblUrl = candidate.parent_chembl_id
    ? `https://www.ebi.ac.uk/chembl/compound_report_card/${candidate.parent_chembl_id}/`
    : candidate.compound_id
    ? `https://www.ebi.ac.uk/chembl/compound_report_card/${candidate.compound_id}/`
    : null;

  return (
    <aside className="cv-thedisc-compound is-open">
      <header className="cv-thedisc-compound-head">
        <div className="cv-thedisc-compound-head-kicker">
          <span className="cv-thedisc-compound-head-dot" />
          COMPOUND
        </div>
        <button
          type="button"
          className="cv-thedisc-compound-close"
          onClick={() => actions.clearSelection()}
          aria-label="Close compound detail"
        >
          ×
        </button>
      </header>

      <h3 className="cv-thedisc-compound-title">
        {candidate.name ?? candidate.compound_id}
      </h3>

      <div className="cv-thedisc-compound-id">
        {candidate.compound_id}
      </div>

      {candidate.canonical_smiles ? (
        <div className="cv-thedisc-compound-smiles">
          <span className="cv-thedisc-compound-smiles-label">
            SMILES
          </span>
          <code>{candidate.canonical_smiles}</code>
        </div>
      ) : null}

      {chemblUrl ? (
        <a
          className="cv-thedisc-compound-link"
          href={chemblUrl}
          target="_blank"
          rel="noopener noreferrer"
        >
          Open ChEMBL record ↗
        </a>
      ) : null}

      <MechanismOfActionChain
        result={result}
        compoundId={compoundId}
      />

      {comparison ? (
        <div className="cv-thedisc-compound-comparison">
          <div className="cv-thedisc-section-label">
            <span>Evidence dimensions</span>
            <i />
          </div>
          <ul>
            <li>
              <span>Activity</span>
              <strong>
                {
                  ACTIVITY_QUALITY_LABELS[
                    comparison.activity_quality
                  ]
                }
              </strong>
            </li>
            <li>
              <span>Link strength</span>
              <strong>
                {
                  MECHANISM_LINK_LABELS[
                    comparison.mechanism_link_strength
                  ]
                }
              </strong>
            </li>
            <li>
              <span>Evidence diversity</span>
              <strong>
                {comparison.evidence_diversity}
              </strong>
            </li>
            <li>
              <span>Data gaps</span>
              <strong>{comparison.data_gaps}</strong>
            </li>
          </ul>
          {comparison.notes.length ? (
            <ul className="cv-thedisc-compound-notes">
              {comparison.notes.map((n, i) => (
                <li key={i}>{n}</li>
              ))}
            </ul>
          ) : null}
        </div>
      ) : null}

      <ActivityEvidencePanel
        result={result}
        compoundId={compoundId}
      />
    </aside>
  );
}
