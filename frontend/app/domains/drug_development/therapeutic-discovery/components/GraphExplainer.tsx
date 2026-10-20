/**
 * CureVerseAI — Drug Development
 * Workflow 03 — Therapeutic Discovery
 * GraphExplainer.
 *
 * Plain-language legend above the graph. Dismissible.
 */

"use client";

import { useState } from "react";

export default function GraphExplainer() {
  const [dismissed, setDismissed] = useState(false);

  if (dismissed) return null;

  return (
    <aside className="cv-thedisc-explainer">
      <div className="cv-thedisc-explainer-head">
        <span className="cv-thedisc-explainer-eyebrow">
          HOW TO READ THIS GRAPH
        </span>
        <button
          type="button"
          className="cv-thedisc-explainer-close"
          onClick={() => setDismissed(true)}
          aria-label="Dismiss explainer"
        >
          ×
        </button>
      </div>

      <div className="cv-thedisc-explainer-body">
        <p>
          This graph traces how a candidate compound could
          modify the selected mechanism. Every link is
          labeled with how strongly it is supported.
        </p>

        <ul className="cv-thedisc-explainer-legend">
          <li>
            <span
              className="cv-thedisc-explainer-swatch"
              style={{ background: "#7bcab5" }}
            />
            <div>
              <strong>Experimental</strong>
              <span>
                Backed by an actual assay record against
                the target.
              </span>
            </div>
          </li>
          <li>
            <span
              className="cv-thedisc-explainer-swatch"
              style={{ background: "#6ee7f2" }}
            />
            <div>
              <strong>Recorded fact</strong>
              <span>
                Directly recorded in a scientific
                database.
              </span>
            </div>
          </li>
          <li>
            <span
              className="cv-thedisc-explainer-swatch"
              style={{ background: "#e0525a" }}
            />
            <div>
              <strong>Research link</strong>
              <span>
                Association from research, not a causal
                claim.
              </span>
            </div>
          </li>
        </ul>

        <p className="cv-thedisc-explainer-note">
          Measured activity against a target is not clinical
          efficacy. This graph is a hypothesis generator,
          not a treatment recommendation. Click a node, an
          edge, or a compound to inspect the underlying
          evidence.
        </p>
      </div>
    </aside>
  );
}
