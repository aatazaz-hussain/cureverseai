/**
 * CureVerseAI — Drug Development
 * Workflow 02 — Reverse Disease Engineering
 * UncertaintyPanel.
 *
 * Collapsible list of uncertainty notes returned by the
 * AI Engine. Notes are grouped by severity (info /
 * warning / error) and each related_id is a clickable
 * action that selects the corresponding node or edge in
 * the graph.
 *
 * The panel does not filter or rank uncertainties. It
 * shows exactly what the AI Engine returned.
 */

"use client";

import { useState, useCallback } from "react";

import type { Uncertainty } from "../types";

import { useRDEActions } from "../state";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface UncertaintyPanelProps {
  uncertainties: Uncertainty[];
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

const SEVERITY_ORDER: Array<
  Uncertainty["severity"]
> = ["error", "warning", "info"];

const SEVERITY_LABEL: Record<
  Uncertainty["severity"],
  string
> = {
  error: "Errors",
  warning: "Warnings",
  info: "Notes",
};

export default function UncertaintyPanel({
  uncertainties,
}: UncertaintyPanelProps) {
  const [open, setOpen] = useState(true);
  const actions = useRDEActions();

  const handleToggle = useCallback(() => {
    setOpen((v) => !v);
  }, []);

  // Group by severity, keeping the AI Engine's order
  // within each group.
  const grouped = SEVERITY_ORDER.map((sev) => ({
    severity: sev,
    items: uncertainties.filter(
      (u) => u.severity === sev,
    ),
  })).filter((g) => g.items.length > 0);

  if (!uncertainties.length) {
    return null;
  }

  return (
    <section
      className={
        "cv-revdis-uncertainty" +
        (open ? " is-open" : "")
      }
    >
      <button
        type="button"
        className="cv-revdis-uncertainty-toggle"
        onClick={handleToggle}
        aria-expanded={open}
      >
        <span>
          Scientific uncertainties ({uncertainties.length})
        </span>
        <i>▾</i>
      </button>

      {open ? (
        <div className="cv-revdis-uncertainty-body">
          {grouped.map((group) => (
            <div
              key={group.severity}
              className={
                "cv-revdis-uncertainty-group cv-revdis-uncertainty-group-" +
                group.severity
              }
            >
              <h4>{SEVERITY_LABEL[group.severity]}</h4>
              <ul>
                {group.items.map((u, i) => (
                  <li key={`${u.type}-${i}`}>
                    <div className="cv-revdis-uncertainty-item-head">
                      <span className="cv-revdis-uncertainty-type">
                        {u.type}
                      </span>
                    </div>
                    <p>{u.statement}</p>

                    {u.related_ids.length > 0 ? (
                      <div className="cv-revdis-uncertainty-related">
                        {u.related_ids
                          .slice(0, 6)
                          .map((id) => {
                            const isEdge =
                              id.includes("|");
                            return (
                              <button
                                key={id}
                                type="button"
                                className="cv-revdis-uncertainty-related-btn"
                                onClick={() =>
                                  isEdge
                                    ? actions.select({
                                        kind: "edge",
                                        edge_key: id,
                                      })
                                    : actions.select({
                                        kind: "node",
                                        node_id: id,
                                      })
                                }
                              >
                                {isEdge
                                  ? "relationship"
                                  : id}
                              </button>
                            );
                          })}
                        {u.related_ids.length > 6 ? (
                          <span className="cv-revdis-uncertainty-related-more">
                            +{u.related_ids.length - 6} more
                          </span>
                        ) : null}
                      </div>
                    ) : null}
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
