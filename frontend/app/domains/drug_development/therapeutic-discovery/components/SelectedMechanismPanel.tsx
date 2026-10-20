/**
 * CureVerseAI — Drug Development
 * Workflow 03 — Therapeutic Discovery
 * SelectedMechanismPanel.
 *
 * Shows the mechanism under investigation and how it was
 * chosen. When the mechanism arrived from Workflow 02, the
 * source is labeled "from Workflow 02". When W03 discovered
 * it, the source is labeled "discovered from disease".
 */

"use client";

import type { SelectedMechanismBlock } from "../types";

interface SelectedMechanismPanelProps {
  mechanism: SelectedMechanismBlock;
}

export default function SelectedMechanismPanel({
  mechanism,
}: SelectedMechanismPanelProps) {
  const sourceLabel =
    mechanism.source === "w02_handoff"
      ? "from Workflow 02"
      : mechanism.source === "user_supplied"
      ? "supplied in request"
      : "discovered from disease";

  const others = (mechanism.candidate_mechanisms ?? []).filter(
    (m) => m.mechanism_id !== mechanism.mechanism_id,
  );

  return (
    <section className="cv-thedisc-mechanism">
      <div className="cv-thedisc-mechanism-head">
        <span className="cv-thedisc-mechanism-eyebrow">
          MECHANISM UNDER INVESTIGATION
        </span>
        <span className="cv-thedisc-mechanism-source">
          <i />
          {sourceLabel}
        </span>
      </div>

      <h3 className="cv-thedisc-mechanism-name">
        {mechanism.label ?? mechanism.mechanism_id}
      </h3>

      {mechanism.identifier ? (
        <div className="cv-thedisc-mechanism-id">
          {mechanism.identifier}
        </div>
      ) : null}

      {others.length > 0 ? (
        <details className="cv-thedisc-mechanism-alts">
          <summary>
            {others.length} alternative mechanism
            {others.length === 1 ? "" : "s"} discovered
          </summary>
          <ul>
            {others.slice(0, 10).map((m, i) => (
              <li key={`${m.mechanism_id}-${i}`}>
                <strong>{m.label ?? m.mechanism_id}</strong>
                {m.identifier ? (
                  <span>{m.identifier}</span>
                ) : null}
              </li>
            ))}
          </ul>
        </details>
      ) : null}
    </section>
  );
}
