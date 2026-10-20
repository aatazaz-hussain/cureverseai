/**
 * CureVerseAI — Drug Development
 * Workflow 03 — Therapeutic Discovery
 * Limitations.
 *
 * Collapsible list of scientific limitations.
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

  if (!limitations.length) return null;

  return (
    <section
      className={
        "cv-thedisc-limitations" +
        (open ? " is-open" : "")
      }
    >
      <button
        type="button"
        className="cv-thedisc-limitations-toggle"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
      >
        <span>
          Scientific limitations ({limitations.length})
        </span>
        <i>▾</i>
      </button>

      {open ? (
        <ul className="cv-thedisc-limitations-list">
          {limitations.map((l, i) => (
            <li key={i}>{l}</li>
          ))}
        </ul>
      ) : null}
    </section>
  );
}
