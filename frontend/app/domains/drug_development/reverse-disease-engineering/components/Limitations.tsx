/**
 * CureVerseAI — Drug Development
 * Workflow 02 — Reverse Disease Engineering
 * Limitations.
 *
 * Collapsible list of scientific limitations returned by
 * the AI Engine. These describe what the workflow does not
 * claim — they are part of the spec, not decoration.
 *
 * Matches the W01 disease-impact page's collapse pattern
 * for visual consistency.
 */

"use client";

import { useState } from "react";

interface LimitationsProps {
  limitations: string[];
}

export default function Limitations({
  limitations,
}: LimitationsProps) {
  const [open, setOpen] = useState(false);

  if (!limitations.length) {
    return null;
  }

  return (
    <section
      className={
        "cv-revdis-limitations" +
        (open ? " is-open" : "")
      }
    >
      <button
        type="button"
        className="cv-revdis-limitations-toggle"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
      >
        <span>
          Scientific limitations ({limitations.length})
        </span>
        <i>▾</i>
      </button>

      {open ? (
        <ul className="cv-revdis-limitations-list">
          {limitations.map((l, i) => (
            <li key={i}>{l}</li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}
