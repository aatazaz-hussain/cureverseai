/**
 * CureVerseAI — Drug Development
 * Workflow 02 — Reverse Disease Engineering
 * GraphExplainer — a plain-language legend for the graph.
 *
 * Renders once, above the graph, the first time results
 * load. Dismissible. No state beyond `dismissed`. Local to
 * the component so a fresh query does not resurrect it if
 * the user has dismissed it — the dismissal persists for
 * the session.
 *
 * Purpose: non-expert viewers should not have to guess what
 * the colors and columns mean.
 */

"use client";

import { useState } from "react";

export default function GraphExplainer() {
  const [dismissed, setDismissed] = useState(false);

  if (dismissed) return null;

  return (
    <aside className="cv-revdis-explainer">
      <div className="cv-revdis-explainer-head">
        <span className="cv-revdis-explainer-eyebrow">
          HOW TO READ THIS GRAPH
        </span>
        <button
          type="button"
          className="cv-revdis-explainer-close"
          onClick={() => setDismissed(true)}
          aria-label="Dismiss explainer"
        >
          ×
        </button>
      </div>

      <div className="cv-revdis-explainer-body">
        <p>
          Every connection in this graph is labeled with how
          strongly it is supported.
        </p>

        <ul className="cv-revdis-explainer-legend">
          <li>
            <span
              className="cv-revdis-explainer-swatch"
              style={{ background: "#6ee7f2" }}
            />
            <div>
              <strong>Recorded fact</strong>
              <span>
                Directly in a scientific database. No inference.
              </span>
            </div>
          </li>
          <li>
            <span
              className="cv-revdis-explainer-swatch"
              style={{ background: "#e0525a" }}
            />
            <div>
              <strong>Research link</strong>
              <span>
                Backed by published research or DNA studies. A
                likely link, not proof of cause.
              </span>
            </div>
          </li>
          <li>
            <span
              className="cv-revdis-explainer-swatch"
              style={{ background: "#e9c58c" }}
            />
            <div>
              <strong>Inferred link</strong>
              <span>
                Inferred by combining other supported links.
              </span>
            </div>
          </li>
        </ul>

        <p className="cv-revdis-explainer-note">
          Click any node or edge to see the source record.
          This graph is not a diagnosis and not a list of
          causes — it is a traceable summary of what the
          world&rsquo;s scientific databases say about this
          disease.
        </p>
      </div>
    </aside>
  );
}
