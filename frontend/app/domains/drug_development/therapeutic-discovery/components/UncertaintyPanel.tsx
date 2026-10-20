/**
 * CureVerseAI — Drug Development
 * Workflow 03 — Therapeutic Discovery
 * UncertaintyPanel.
 */

"use client";

import { useCallback, useState } from "react";

interface Uncertainty {
  type: string;
  statement: string;
  related_ids: string[];
  severity: "info" | "warning" | "error";
}

interface UncertaintyPanelProps {
  uncertainties: Uncertainty[];
}

export default function UncertaintyPanel({
  uncertainties,
}: UncertaintyPanelProps) {
  const [open, setOpen] = useState(true);

  const handleToggle = useCallback(() => {
    setOpen((v) => !v);
  }, []);

  if (!uncertainties.length) return null;

  const groups = [
    {
      label: "Errors",
      sev: "error" as const,
      items: uncertainties.filter(
        (u) => u.severity === "error",
      ),
    },
    {
      label: "Warnings",
      sev: "warning" as const,
      items: uncertainties.filter(
        (u) => u.severity === "warning",
      ),
    },
    {
      label: "Notes",
      sev: "info" as const,
      items: uncertainties.filter(
        (u) => u.severity === "info",
      ),
    },
  ].filter((g) => g.items.length);

  return (
    <section
      className={
        "cv-thedisc-uncertainty" +
        (open ? " is-open" : "")
      }
    >
      <button
        type="button"
        className="cv-thedisc-uncertainty-toggle"
        onClick={handleToggle}
        aria-expanded={open}
      >
        <span>
          Scientific uncertainties ({uncertainties.length})
        </span>
        <i>▾</i>
      </button>

      {open ? (
        <div className="cv-thedisc-uncertainty-body">
          {groups.map((g) => (
            <div
              key={g.sev}
              className={
                "cv-thedisc-uncertainty-group cv-thedisc-uncertainty-group-" +
                g.sev
              }
            >
              <h4>{g.label}</h4>
              <ul>
                {g.items.map((u, i) => (
                  <li key={i}>
                    <div className="cv-thedisc-uncertainty-item-head">
                      <span className="cv-thedisc-uncertainty-type">
                        {u.type}
                      </span>
                    </div>
                    <p>{u.statement}</p>
                  </li>
                ))}
              </ul>
            </div>
          ))}
        </div>
      ) : null}
    </section>
  );
}
