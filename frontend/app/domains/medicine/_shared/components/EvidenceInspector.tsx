"use client";

/**
 * CureVerseAI — Medicine domain
 * Evidence inspector.
 *
 * Right-side drawer. Opens when an evidence-backed element is
 * selected. Shows every MedicineEvidence record referenced by
 * the current selection, plus its provenance.
 */

import { useEffect } from "react";

import type { MedicineEvidence } from "../types";

interface Props {
  open: boolean;
  title: string;
  evidence: MedicineEvidence[];
  onClose: () => void;
}

export default function EvidenceInspector({
  open,
  title,
  evidence,
  onClose,
}: Props) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") onClose();
    };
    window.addEventListener("keydown", onKey);
    return () => window.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  if (!open) return null;

  return (
    <div
      className="cv-medicine-wf-inspector-backdrop"
      onClick={onClose}
      role="presentation"
    >
      <aside
        className="cv-medicine-wf-inspector"
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-label={title}
      >
        <header className="cv-medicine-wf-inspector-head">
          <div>
            <div className="cv-medicine-wf-kicker">Evidence</div>
            <h3 className="cv-medicine-wf-inspector-title">{title}</h3>
          </div>
          <button
            type="button"
            className="cv-medicine-wf-btn cv-medicine-wf-btn--ghost"
            onClick={onClose}
            aria-label="Close"
          >
            Close
          </button>
        </header>

        <div className="cv-medicine-wf-inspector-body">
          {evidence.length === 0 ? (
            <div className="cv-medicine-wf-empty-inline">
              No evidence records are attached to this selection.
            </div>
          ) : (
            <ul className="cv-medicine-wf-evidence-list">
              {evidence.map((e) => (
                <li
                  key={e.evidence_id}
                  className="cv-medicine-wf-evidence-item"
                >
                  <div className="cv-medicine-wf-evidence-head">
                    <span className="cv-medicine-wf-chip">
                      {e.source}
                    </span>
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
          )}
        </div>
      </aside>
    </div>
  );
}
