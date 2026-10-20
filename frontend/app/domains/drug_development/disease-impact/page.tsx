"use client";

import {
  FormEvent,
  useEffect,
  useState,
} from "react";

import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";

import "./disease-impact.css";

import {
  ImpactProvider,
  useImpactStatus,
  useAnalyze,
  type ImpactStatus,
} from "./state";
import ImpactScene from "./scene/ImpactScene";
import StageBar from "./StageBar";

import type { FocusStage } from "./scene/constants";
import type {
  BiologicalImpactResult,
  ImpactNode,
} from "./types";
import { ApiError } from "./api";

// ---------------------------------------------------------------------------
// Static stage list (spec §15)
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// Page shell
// ---------------------------------------------------------------------------

export default function DiseaseImpactPage() {
  return (
    <ImpactProvider>
      <PageBody />
    </ImpactProvider>
  );
}

function PageBody() {
  const status = useImpactStatus();
  const analyze = useAnalyze();

  return (
    <main className="cv-dia-page">
      <Navbar />

      <Breadcrumb />

      <Hero />

      <InputRegion
        status={status}
        onSubmit={analyze}
      />

      <Results status={status} />

      <Footer />
    </main>
  );
}

// ---------------------------------------------------------------------------
// Breadcrumb
// ---------------------------------------------------------------------------

function Breadcrumb() {
  return (
    <div className="cv-dia-breadcrumb">
      <a href="/domains/drug_development">Drug Development</a>
      <i />
      <strong>Disease → Biological Impact</strong>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Hero
// ---------------------------------------------------------------------------

function Hero() {
  return (
    <section className="cv-dia-hero">
      <div className="cv-dia-hero-glow cv-dia-hero-glow-one" />
      <div className="cv-dia-hero-glow cv-dia-hero-glow-two" />

      <div className="cv-dia-hero-inner">
        <div className="cv-dia-hero-copy">
          <div className="cv-dia-hero-kicker">
            <span>01</span>
            <i />
            DISEASE → BIOLOGICAL IMPACT
          </div>

          <h1>
            Start with a disease.
            <br />
            <em>Trace the biology.</em>
          </h1>

          <p className="cv-dia-hero-sub">
            Enter any disease. CureVerseAI resolves it against
            biological knowledge sources, then builds a connected
            impact graph across systems, organs, tissues, cells,
            genes, proteins, and pathways — every relationship
            grounded in evidence.
          </p>
        </div>

        <div className="cv-dia-hero-visual">
          <div className="cv-dia-hero-visual-frame">
            <img
              src="/drug-development/disease-impact-hero.png"
              alt="Disease-affected cell visualisation"
              draggable={false}
            />
            <div className="cv-dia-hero-visual-scan" />
            <div className="cv-dia-hero-visual-label">
              <span>CELLULAR IMPACT</span>
              <strong>01 / 05</strong>
            </div>
          </div>
        </div>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Input region
// ---------------------------------------------------------------------------

function InputRegion({
  status,
  onSubmit,
}: {
  status: ImpactStatus;
  onSubmit: (query: string) => Promise<void>;
}) {
  const loading = status.kind === "loading";
  const [value, setValue] = useState("");

  // When a previous query finished, keep it in the field
  // for convenience (so the user can edit and re-run).
  useEffect(() => {
    if (status.kind === "loaded" || status.kind === "error") {
      setValue(status.query);
    }
  }, [status]);

  function handleSubmit(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();

    if (loading) return;

    const trimmed = value.trim();
    if (!trimmed) return;

    void onSubmit(trimmed);
  }

  return (
    <section className="cv-dia-input-region">
      <form
        className="cv-dia-input-form"
        onSubmit={handleSubmit}
      >
        <input
          className="cv-dia-input"
          type="text"
          placeholder="e.g. Alzheimer's disease, Type 2 diabetes, Breast cancer…"
          value={value}
          onChange={(e) => setValue(e.target.value)}
          disabled={loading}
          autoComplete="off"
          spellCheck={false}
        />

        <button
          className="cv-dia-input-submit"
          type="submit"
          disabled={loading || !value.trim()}
        >
          {loading ? "Analyzing…" : "Analyze"}
        </button>
      </form>

      <div className="cv-dia-input-hint">
        Full pipeline takes 40–90 seconds per disease
      </div>

      {loading ? (
        <LoadingBlock startedAt={status.startedAt} />
      ) : null}
    </section>
  );
}

// ---------------------------------------------------------------------------
// Loading
// ---------------------------------------------------------------------------

function LoadingBlock({ startedAt }: { startedAt: number }) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const tick = () => {
      setElapsed(
        Math.floor((Date.now() - startedAt) / 1000),
      );
    };

    tick();

    const id = setInterval(tick, 1000);

    return () => clearInterval(id);
  }, [startedAt]);

  return (
    <div className="cv-dia-loading">
      <div className="cv-dia-loading-spinner" />

      <div className="cv-dia-loading-copy">
        <strong>Running pipeline</strong>
        <span>
          Resolving disease, mapping systems, tissues,
          cells, molecular targets, and pathways.
        </span>
      </div>

      <div className="cv-dia-loading-timer">
        {elapsed}s
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Results dispatcher
// ---------------------------------------------------------------------------

function Results({ status }: { status: ImpactStatus }) {
  switch (status.kind) {
    case "idle":
    case "loading":
      return null;

    case "error":
      return <ErrorBlock error={status.error} />;

    case "loaded":
      if (status.result.resolution_status === "unresolved") {
        return <UnresolvedBlock result={status.result} />;
      }
      return <ResolvedBlock result={status.result} />;
  }
}

// ---------------------------------------------------------------------------
// Error block
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
        return "Analysis failed";
    }
  })();

  return (
    <section className="cv-dia-results">
      <div className="cv-dia-error">
        <div className="cv-dia-error-label">{label}</div>
        <p>{error.message}</p>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Unresolved block
// ---------------------------------------------------------------------------

function UnresolvedBlock({
  result,
}: {
  result: BiologicalImpactResult;
}) {
  return (
    <section className="cv-dia-results">
      <div className="cv-dia-unresolved">
        <div className="cv-dia-unresolved-label">
          Disease not resolved
        </div>
        <p>
          {result.failure_reason ||
            "No sufficiently supported biological record was found for this query."}
        </p>
      </div>
    </section>
  );
}

// ---------------------------------------------------------------------------
// Resolved block
// ---------------------------------------------------------------------------

function ResolvedBlock({
  result,
}: {
  result: BiologicalImpactResult;
}) {
  const [focusedStage, setFocusedStage] =
    useState<FocusStage>("IMPACT");

  return (
    <>
      <StageBar
        focusedStage={focusedStage}
        onStageChange={setFocusedStage}
      />

      <section className="cv-dia-results">
        {result.disease ? (
          <IdentityPanel result={result} />
        ) : null}

        <ImpactScene
          result={result}
          focusedStage={focusedStage}
        />

        <SummaryMetrics result={result} />

        {result.reasoning.summary ? (
          <ReasoningSummary result={result} />
        ) : null}

        <LayerBreakdown result={result} />

        {result.reasoning.limitations.length > 0 ? (
          <Limitations result={result} />
        ) : null}
      </section>
    </>
  );
}

// ---------------------------------------------------------------------------
// Stage bar
// ---------------------------------------------------------------------------

// ---------------------------------------------------------------------------
// Identity panel
// ---------------------------------------------------------------------------

function IdentityPanel({
  result,
}: {
  result: BiologicalImpactResult;
}) {
  const d = result.disease;
  if (!d) return null;

  return (
    <div className="cv-dia-identity">
      <h2 className="cv-dia-identity-name">
        {d.canonical_name || d.query}
      </h2>

      <div className="cv-dia-identity-query">
        Query: {d.query}
      </div>

      {d.identifiers.length > 0 ? (
        <div className="cv-dia-identity-ids">
          {d.identifiers.map((id, i) => (
            <div
              key={`${id.source}-${id.identifier}-${i}`}
              className="cv-dia-identity-id"
            >
              <span>{id.source}</span>
              {id.identifier}
            </div>
          ))}
        </div>
      ) : null}
    </div>
  );
}

// ---------------------------------------------------------------------------
// Summary metrics
// ---------------------------------------------------------------------------

function SummaryMetrics({
  result,
}: {
  result: BiologicalImpactResult;
}) {
  const s = result.metadata.summary;

  return (
    <div className="cv-dia-summary">
      <Metric number={s.node_count} label="Nodes" />
      <Metric
        number={s.relationship_count}
        label="Relationships"
      />
      <Metric
        number={s.evidence_count}
        label="Evidence records"
      />
      <Metric
        number={s.layers_run.length}
        label="Layers contributed"
      />
    </div>
  );
}

function Metric({
  number,
  label,
}: {
  number: number;
  label: string;
}) {
  return (
    <div className="cv-dia-metric">
      <strong>{number}</strong>
      <span>{label}</span>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Reasoning summary
// ---------------------------------------------------------------------------

function ReasoningSummary({
  result,
}: {
  result: BiologicalImpactResult;
}) {
  return (
    <div className="cv-dia-reasoning">
      <div className="cv-dia-section-label">
        <span>Reasoning</span>
        <i />
      </div>

      <p>{result.reasoning.summary}</p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Layer breakdown
// ---------------------------------------------------------------------------

const LAYER_ORDER = [
  "systems",
  "tissues",
  "cells",
  "molecular",
  "pathways",
] as const;

function LayerBreakdown({
  result,
}: {
  result: BiologicalImpactResult;
}) {
  return (
    <div className="cv-dia-layer-grid">
      {LAYER_ORDER.map((name) => (
        <LayerCard
          key={name}
          name={name}
          result={result}
        />
      ))}
    </div>
  );
}

function LayerCard({
  name,
  result,
}: {
  name: string;
  result: BiologicalImpactResult;
}) {
  // Count nodes of the types this layer owns.
  const ownedTypes: Record<string, string[]> = {
    systems: ["system"],
    tissues: ["tissue", "organ"],
    cells: ["cell"],
    molecular: ["gene", "protein"],
    pathways: ["pathway"],
  };

  const types = ownedTypes[name] || [];
  const layerNodes = result.nodes.filter((n: ImpactNode) =>
    types.includes(n.node_type),
  );

  const relationships = result.relationships.filter((r) => {
    return layerNodes.some(
      (n) =>
        n.node_id === r.source_id ||
        n.node_id === r.target_id,
    );
  });

  const nodeIds = new Set(layerNodes.map((n) => n.node_id));
  const evidenceIds = new Set<string>();

  relationships.forEach((r) => {
    r.evidence_ids.forEach((id) => evidenceIds.add(id));
  });

  const empty = layerNodes.length === 0;

  return (
    <div
      className={
        "cv-dia-layer-card" +
        (empty ? " cv-dia-layer-card-empty" : "")
      }
    >
      <div className="cv-dia-layer-card-head">
        <strong>{name}</strong>
        <span>{empty ? "no data" : "loaded"}</span>
      </div>

      <div className="cv-dia-layer-card-counts">
        <div>
          <strong>{layerNodes.length}</strong>
          <span>Nodes</span>
        </div>
        <div>
          <strong>{relationships.length}</strong>
          <span>Rels</span>
        </div>
        <div>
          <strong>{evidenceIds.size}</strong>
          <span>Evidence</span>
        </div>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Limitations
// ---------------------------------------------------------------------------

function Limitations({
  result,
}: {
  result: BiologicalImpactResult;
}) {
  const [open, setOpen] = useState(false);
  const limitations = result.reasoning.limitations;

  return (
    <div
      className={
        "cv-dia-limitations" +
        (open ? " cv-dia-limitations-open" : "")
      }
    >
      <button
        className="cv-dia-limitations-toggle"
        type="button"
        onClick={() => setOpen((v) => !v)}
        aria-expanded={open}
      >
        <span>
          Scientific limitations ({limitations.length})
        </span>
        <i>▾</i>
      </button>

      {open ? (
        <ul className="cv-dia-limitations-list">
          {limitations.map((l, i) => (
            <li key={i}>{l}</li>
          ))}
        </ul>
      ) : null}
    </div>
  );
}
