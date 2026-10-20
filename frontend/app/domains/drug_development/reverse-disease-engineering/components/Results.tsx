/**
 * CureVerseAI — Drug Development
 * Workflow 02 — Reverse Disease Engineering
 * Results — the dispatcher.
 *
 * Reads the fetch status from Context and renders one of
 * four states:
 *
 *   idle | loading    -> null (InputRegion handles it)
 *   error             -> ErrorBlock
 *   loaded unresolved -> UnresolvedBlock
 *   loaded partial    -> PartialBlock (ambiguity)
 *   loaded resolved   -> ResolvedLayout (the real thing)
 *
 * ResolvedLayout is the composition of every panel:
 *
 *   - DiseaseIdentityPanel
 *   - two-column region: MechanismGraph | EvidenceInspector + NarrationPanel
 *   - ReasoningSummary
 *   - UncertaintyPanel
 *   - Limitations
 *
 * It does not compute anything. Every child pulls its own
 * state from Context.
 */

"use client";

import { ApiError } from "../api";
import { useRDEStatus } from "../state";

import DiseaseIdentityPanel from "./DiseaseIdentityPanel";
import EvidenceInspector from "./EvidenceInspector";
import GraphExplainer from "./GraphExplainer";
import Limitations from "./Limitations";
import MechanismGraph from "./graph/MechanismGraph";
import NarrationPanel from "./NarrationPanel";
import ReasoningSummary from "./ReasoningSummary";
import UncertaintyPanel from "./UncertaintyPanel";

// ---------------------------------------------------------------------------
// Dispatcher
// ---------------------------------------------------------------------------

export default function Results() {
  const status = useRDEStatus();

  if (status.kind === "idle" || status.kind === "loading") {
    return null;
  }

  if (status.kind === "error") {
    return <ErrorBlock error={status.error} />;
  }

  const result = status.result;

  if (result.resolution_status === "unresolved") {
    return (
      <UnresolvedBlock
        query={status.query}
        reason={result.failure_reason}
      />
    );
  }

  if (result.resolution_status === "partial") {
    return (
      <PartialBlock
        query={status.query}
        reason={result.failure_reason}
        candidates={result.disease?.candidates ?? []}
      />
    );
  }

  return <ResolvedLayout />;
}

// ---------------------------------------------------------------------------
// Error
// ---------------------------------------------------------------------------

function ErrorBlock({ error }: { error: ApiError }) {
  const label = (() => {
    switch (error.kind) {
      case "network":
        return "Backend unreachable";
      case "timeout":
        return "Request timed out";
      case "server":
        return "Server error";
      case "client":
        return "Request rejected";
      case "invalid":
        return "Unexpected response";
      default:
        return "Investigation failed";
    }
  })();

  return (
    <section className="cv-revdis-results">
      <div className="cv-revdis-error">
        <div className="cv-revdis-error-label">{label}</div>
        <p>{error.message}</p>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Unresolved
// ---------------------------------------------------------------------------

function UnresolvedBlock({
  query,
  reason,
}: {
  query: string;
  reason: string | null;
}) {
  return (
    <section className="cv-revdis-results">
      <div className="cv-revdis-unresolved">
        <div className="cv-revdis-unresolved-label">
          DISEASE NOT RESOLVED
        </div>
        <h2 className="cv-revdis-unresolved-title">
          No record found for{" "}
          <em>&ldquo;{query}&rdquo;</em>
        </h2>
        <p className="cv-revdis-unresolved-body">
          {reason ??
            "No sufficiently supported biological record was found for this query in the sources consulted."}
        </p>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Partial (ambiguous)
// ---------------------------------------------------------------------------

interface CandidateLike {
  canonical_name: string | null;
  description: string | null;
  sources: string[];
  identifiers: {
    source: string;
    identifier: string;
    url: string | null;
  }[];
}

function PartialBlock({
  query,
  reason,
  candidates,
}: {
  query: string;
  reason: string | null;
  candidates: CandidateLike[];
}) {
  return (
    <section className="cv-revdis-results">
      <div className="cv-revdis-partial">
        <div className="cv-revdis-partial-label">
          DISEASE AMBIGUOUS
        </div>
        <h2 className="cv-revdis-partial-title">
          Multiple candidates for{" "}
          <em>&ldquo;{query}&rdquo;</em>
        </h2>
        <p className="cv-revdis-partial-body">
          {reason ??
            "Several disease records match this query. Pick the one you meant, or refine your query."}
        </p>

        {candidates.length > 0 ? (
          <ul className="cv-revdis-partial-list">
            {candidates.map((c, i) => (
              <li
                key={`${c.canonical_name ?? "candidate"}-${i}`}
                className="cv-revdis-partial-item"
              >
                <div className="cv-revdis-partial-item-head">
                  <strong>
                    {c.canonical_name ?? "(unnamed)"}
                  </strong>
                  {c.sources.length ? (
                    <span>{c.sources.join(" · ")}</span>
                  ) : null}
                </div>

                {c.description ? (
                  <p className="cv-revdis-partial-item-desc">
                    {c.description}
                  </p>
                ) : null}

                {c.identifiers.length ? (
                  <div className="cv-revdis-partial-item-ids">
                    {c.identifiers.map((id) => (
                      <span key={id.identifier}>
                        {id.source}: {id.identifier}
                      </span>
                    ))}
                  </div>
                ) : null}
              </li>
            ))}
          </ul>
        ) : null}
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Resolved layout
// ---------------------------------------------------------------------------

function ResolvedLayout() {
  const status = useRDEStatus();

  if (status.kind !== "loaded") return null;

  const { result } = status;

  return (
    <section className="cv-revdis-results">
      {result.disease ? (
        <DiseaseIdentityPanel disease={result.disease} />
      ) : null}

      <GraphExplainer />

      <div className="cv-revdis-graph-region">
        <MechanismGraph
          nodes={result.graph.nodes}
          edges={result.graph.edges}
        />
      </div>

      <div className="cv-revdis-panel-region">
        <EvidenceInspector />
        <NarrationPanel result={result} />
      </div>

      <ReasoningSummary reasoning={result.reasoning} />

      <UncertaintyPanel
        uncertainties={result.uncertainties}
      />

      <Limitations
        limitations={result.reasoning.limitations}
      />
    </section>
  );
}
