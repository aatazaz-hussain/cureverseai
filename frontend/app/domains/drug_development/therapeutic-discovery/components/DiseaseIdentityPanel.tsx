/**
 * CureVerseAI — Drug Development
 * Workflow 03 — Therapeutic Discovery
 * DiseaseIdentityPanel.
 *
 * Small identity block above the graph. Presentational.
 */

"use client";

import type { DiseaseBlock } from "../types";

function PerLetterText({
  text,
}: {
  text: string;
}) {
  const letters = Array.from(text);
  return (
    <span className="cv-thedisc-per-letter">
      {letters.map((ch, i) => (
        <span
          key={i}
          className="cv-thedisc-letter"
          style={{ ["--i" as string]: i }}
          aria-hidden="true"
        >
          {ch === " " ? "\u00A0" : ch}
        </span>
      ))}
    </span>
  );
}

interface DiseaseIdentityPanelProps {
  disease: DiseaseBlock;
}

export default function DiseaseIdentityPanel({
  disease,
}: DiseaseIdentityPanelProps) {
  const name = disease.resolved_name ?? disease.query;
  const status = disease.resolution_status;

  const statusLabel =
    status === "resolved"
      ? "Resolved"
      : status === "partial"
      ? "Ambiguous"
      : "Unresolved";

  return (
    <section className="cv-thedisc-identity">
      <div className="cv-thedisc-identity-head">
        <span className="cv-thedisc-identity-eyebrow">
          DISEASE IDENTITY
        </span>
        <span
          className={`cv-thedisc-identity-status cv-thedisc-identity-status-${status}`}
        >
          <i />
          {statusLabel}
        </span>
      </div>

      <h2 className="cv-thedisc-identity-name">
        <PerLetterText text={name} />
      </h2>

      {disease.description ? (
        <p className="cv-thedisc-identity-desc">
          {disease.description}
        </p>
      ) : null}

      {disease.identifiers.length > 0 ? (
        <div className="cv-thedisc-identity-ids">
          {disease.identifiers.map((id, i) => (
            <div
              key={`${id.source}-${id.identifier}-${i}`}
              className="cv-thedisc-identity-id"
            >
              <span>{id.source}</span>
              <strong>{id.identifier}</strong>
            </div>
          ))}
        </div>
      ) : null}
    </section>
  );
}
