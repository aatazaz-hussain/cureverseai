/**
 * CureVerseAI — Drug Development
 * Workflow 02 — Reverse Disease Engineering
 * DiseaseIdentityPanel.
 *
 * Renders the disease identity block above the graph:
 *
 *   - The canonical disease name, large
 *   - A resolution-status pill (resolved / partial / unresolved)
 *   - All identifiers (MONDO, EFO, Orphanet, etc.) as chips
 *   - The description, if present
 *
 * Purely presentational. No state, no effects.
 */

"use client";

import type { DiseaseBlock } from "../types";

// ---------------------------------------------------------------------------
// Per-letter text — produces a cascade hover effect.
// ---------------------------------------------------------------------------

function PerLetterText({
  text,
  className = "",
}: {
  text: string;
  className?: string;
}) {
  const letters = Array.from(text);
  return (
    <span className={`cv-revdis-per-letter ${className}`.trim()}>
      {letters.map((ch, i) => (
        <span
          key={i}
          className="cv-revdis-letter"
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
    <section className="cv-revdis-identity">
      <div className="cv-revdis-identity-head">
        <span className="cv-revdis-identity-eyebrow">
          DISEASE IDENTITY
        </span>
        <span
          className={`cv-revdis-identity-status cv-revdis-identity-status-${status}`}
        >
          <i />
          {statusLabel}
        </span>
      </div>

      <h2 className="cv-revdis-identity-name">
        <PerLetterText text={name} />
      </h2>

      {disease.description ? (
        <p className="cv-revdis-identity-desc">
          {disease.description}
        </p>
      ) : null}

      {disease.identifiers.length > 0 ? (
        <div className="cv-revdis-identity-ids">
          {disease.identifiers.map((id, i) => (
            <div
              key={`${id.source}-${id.identifier}-${i}`}
              className="cv-revdis-identity-id"
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
