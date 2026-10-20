/**
 * CureVerseAI — Drug Development
 * Workflow 02 — Reverse Disease Engineering
 * ReasoningSummary.
 *
 * Renders the AI Engine's reasoning summary and finding
 * records:
 *
 *   - reasoning.summary       — one-paragraph narrative
 *   - reasoning.findings[]    — per-layer structured records
 *
 * Pure presentation. No state, no effects.
 */

"use client";

import type { Reasoning } from "../types";

interface ReasoningSummaryProps {
  reasoning: Reasoning;
}

export default function ReasoningSummary({
  reasoning,
}: ReasoningSummaryProps) {
  const summary = reasoning.summary;
  const findings = reasoning.findings ?? [];

  if (!summary && !findings.length) {
    return null;
  }

  return (
    <section className="cv-revdis-reasoning">
      <div className="cv-revdis-section-label">
        <span>Reasoning</span>
        <i />
      </div>

      {summary ? (
        <p className="cv-revdis-reasoning-summary">
          {summary}
        </p>
      ) : null}

      {findings.length ? (
        <ul className="cv-revdis-reasoning-findings">
          {findings.map((f, i) => (
            <li
              key={`${f.type ?? "finding"}-${i}`}
              className="cv-revdis-reasoning-finding"
            >
              <div className="cv-revdis-reasoning-finding-head">
                {f.layer ? (
                  <span className="cv-revdis-reasoning-finding-layer">
                    {f.layer}
                  </span>
                ) : null}
                {f.type ? (
                  <span className="cv-revdis-reasoning-finding-type">
                    {f.type}
                  </span>
                ) : null}
              </div>
              {f.statement ? (
                <p className="cv-revdis-reasoning-finding-stmt">
                  {f.statement}
                </p>
              ) : null}
            </li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}
