/**
 * CureVerseAI — Drug Development
 * Workflow 03 — Therapeutic Discovery
 * ReasoningSummary.
 *
 * Renders the four reasoning sections from the AI Engine:
 * supported findings, hypotheses, conflicts, evidence gaps.
 * No composite score. Each section is a labeled list.
 */

"use client";

import type {
  ReasoningBlock,
  ReasoningFinding,
} from "../types";

interface ReasoningSummaryProps {
  reasoning: ReasoningBlock;
}

export default function ReasoningSummary({
  reasoning,
}: ReasoningSummaryProps) {
  const groups: Array<{
    label: string;
    items: ReasoningFinding[];
    accent: string;
    className: string;
  }> = [
    {
      label: "Supported findings",
      items: reasoning.supported_findings,
      accent: "#7bcab5",
      className: "supported",
    },
    {
      label: "Hypotheses",
      items: reasoning.hypotheses,
      accent: "#6ee7f2",
      className: "hypotheses",
    },
    {
      label: "Conflicts",
      items: reasoning.conflicts,
      accent: "#e9c58c",
      className: "conflicts",
    },
    {
      label: "Evidence gaps",
      items: reasoning.evidence_gaps,
      accent: "#888e90",
      className: "gaps",
    },
  ];

  const total = groups.reduce(
    (n, g) => n + g.items.length,
    0,
  );
  if (!total) return null;

  return (
    <section className="cv-thedisc-reasoning">
      <div className="cv-thedisc-section-label">
        <span>Reasoning</span>
        <i />
      </div>

      {groups.map((g) => {
        if (!g.items.length) return null;

        return (
          <div
            key={g.className}
            className={
              "cv-thedisc-reasoning-group cv-thedisc-reasoning-group-" +
              g.className
            }
          >
            <h4>
              <i style={{ background: g.accent }} />
              {g.label} ({g.items.length})
            </h4>
            <ul>
              {g.items.map((item, i) => (
                <li key={i}>
                  {item.type ? (
                    <span className="cv-thedisc-reasoning-item-type">
                      {String(item.type)}
                    </span>
                  ) : null}
                  <p>
                    {String(item.statement ?? "")}
                  </p>
                </li>
              ))}
            </ul>
          </div>
        );
      })}
    </section>
  );
}
