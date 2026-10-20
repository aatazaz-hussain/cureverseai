/**
 * CureVerseAI — Drug Development
 * Workflow 03 — Therapeutic Discovery
 * Results — the dispatcher.
 *
 * Reads the fetch status from Context and renders one of
 * the W03 result states:
 *
 *   idle | loading          -> null
 *   error                    -> ErrorBlock
 *   unresolved               -> UnresolvedBlock
 *   invalid_input            -> InvalidInputBlock
 *   partial                  -> PartialBlock
 *   no_candidates            -> NoCandidatesBlock
 *   resolved                 -> ResolvedLayout
 */

"use client";

import { ApiError } from "../api";
import { useTDStatus } from "../state";

import DiseaseIdentityPanel from "./DiseaseIdentityPanel";
import SelectedMechanismPanel from "./SelectedMechanismPanel";
import TherapeuticGraph from "./graph/TherapeuticGraph";
import TargetListPanel from "./TargetListPanel";
import CandidateExplorer from "./CandidateExplorer";
import Inspector from "./Inspector";
import NarrationPanel from "./NarrationPanel";
import ReasoningSummary from "./ReasoningSummary";
import UncertaintyPanel from "./UncertaintyPanel";
import Limitations from "./Limitations";
import GraphExplainer from "./GraphExplainer";

// ---------------------------------------------------------------------------
// Dispatcher
// ---------------------------------------------------------------------------

export default function Results() {
  const status = useTDStatus();

  if (status.kind === "idle" || status.kind === "loading") {
    return null;
  }

  if (status.kind === "error") {
    return <ErrorBlock error={status.error} />;
  }

  const result = status.result;

  switch (result.resolution_status) {
    case "unresolved":
      return (
        <UnresolvedBlock
          query={status.query}
          reason={result.failure_reason}
        />
      );

    case "invalid_input":
      return (
        <InvalidInputBlock
          query={status.query}
          reason={result.failure_reason}
        />
      );

    case "partial":
      return (
        <PartialBlock
          query={status.query}
          reason={result.failure_reason}
          candidates={result.disease?.candidates ?? []}
        />
      );

    case "no_candidates":
      return <NoCandidatesBlock />;

    case "resolved":
      return <ResolvedLayout />;

    default:
      return <UnresolvedBlock
        query={status.query}
        reason={result.failure_reason}
      />;
  }
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
    <section className="cv-thedisc-results">
      <div className="cv-thedisc-error">
        <div className="cv-thedisc-error-label">{label}</div>
        <p>{error.message}</p>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Unresolved / invalid
// ---------------------------------------------------------------------------

function UnresolvedBlock({
  query,
  reason,
}: {
  query: string;
  reason: string | null;
}) {
  return (
    <section className="cv-thedisc-results">
      <div className="cv-thedisc-unresolved">
        <div className="cv-thedisc-unresolved-label">
          DISEASE NOT RESOLVED
        </div>
        <h2 className="cv-thedisc-unresolved-title">
          No record found for <em>&ldquo;{query}&rdquo;</em>
        </h2>
        <p className="cv-thedisc-unresolved-body">
          {reason ??
            "No sufficiently supported biological record was found for this query."}
        </p>
      </div>
    </section>
  );
}

function InvalidInputBlock({
  query,
  reason,
}: {
  query: string;
  reason: string | null;
}) {
  return (
    <section className="cv-thedisc-results">
      <div className="cv-thedisc-unresolved">
        <div className="cv-thedisc-unresolved-label">
          INVALID HANDOFF
        </div>
        <h2 className="cv-thedisc-unresolved-title">
          A mechanism or target identifier could not be
          parsed.
        </h2>
        <p className="cv-thedisc-unresolved-body">
          {reason ??
            "The supplied mechanism_id or target_id is not in a recognized form. Try a pathway:R-HSA-* identifier."}
        </p>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Partial
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
    <section className="cv-thedisc-results">
      <div className="cv-thedisc-partial">
        <div className="cv-thedisc-partial-label">
          DISEASE AMBIGUOUS
        </div>
        <h2 className="cv-thedisc-partial-title">
          Multiple candidates for{" "}
          <em>&ldquo;{query}&rdquo;</em>
        </h2>
        <p className="cv-thedisc-partial-body">
          {reason ??
            "Several disease records match this query."}
        </p>

        {candidates.length > 0 ? (
          <ul className="cv-thedisc-partial-list">
            {candidates.map((c, i) => (
              <li
                key={`${c.canonical_name ?? "c"}-${i}`}
                className="cv-thedisc-partial-item"
              >
                <div className="cv-thedisc-partial-item-head">
                  <strong>
                    {c.canonical_name ?? "(unnamed)"}
                  </strong>
                  {c.sources.length ? (
                    <span>{c.sources.join(" · ")}</span>
                  ) : null}
                </div>
                {c.description ? (
                  <p className="cv-thedisc-partial-item-desc">
                    {c.description}
                  </p>
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
// No candidates
// ---------------------------------------------------------------------------

function NoCandidatesBlock() {
  return (
    <section className="cv-thedisc-results">
      <div className="cv-thedisc-unresolved">
        <div className="cv-thedisc-unresolved-label">
          NO CANDIDATES FOUND
        </div>
        <h2 className="cv-thedisc-unresolved-title">
          The mechanism was identified, but ChEMBL returned
          no compounds.
        </h2>
        <p className="cv-thedisc-unresolved-body">
          No candidate compounds were retrieved for the
          identified targets. This is a state of the sources
          consulted, not a claim that no compounds exist.
        </p>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Resolved
// ---------------------------------------------------------------------------

function ResolvedLayout() {
  const status = useTDStatus();

  if (status.kind !== "loaded") return null;

  const { result } = status;

  return (
    <section className="cv-thedisc-results">
      {result.disease ? (
        <DiseaseIdentityPanel disease={result.disease} />
      ) : null}

      {result.selected_mechanism ? (
        <SelectedMechanismPanel
          mechanism={result.selected_mechanism}
        />
      ) : null}

      <GraphExplainer />

      <div className="cv-thedisc-graph-region">
        <TherapeuticGraph result={result} />
      </div>

      <div className="cv-thedisc-grid">
        <div className="cv-thedisc-grid-main">
          <CandidateExplorer result={result} />
        </div>
        <div className="cv-thedisc-grid-side">
          <Inspector />
          <TargetListPanel result={result} />
          <NarrationPanel result={result} />
        </div>
      </div>

      <ReasoningSummary reasoning={result.reasoning} />

      <UncertaintyPanel
        uncertainties={
          result.reasoning.evidence_gaps
            .concat(result.reasoning.conflicts)
            .map((f) => ({
              type: String(f.type ?? "unknown"),
              statement: String(f.statement ?? ""),
              related_ids: [],
              severity: "info" as const,
            }))
        }
      />

      <Limitations limitations={result.limitations} />
    </section>
  );
}
