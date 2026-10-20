"use client";

/**
 * CureVerseAI — Medicine
 * Workflow 01 — Virtual Disease Simulation
 *
 * Route: /domains/medicine/disease-simulation
 *
 * Self-contained page. All types, fetch logic, and rendering
 * live in this file. Styling lives in disease-simulation.css.
 *
 * Consumes the real wire shape of SimulationResult:
 *   { run, indicators, states, comparison, evidence,
 *     source_status, limitations, warnings, metadata }
 *
 * Every visual element is driven by real backend fields.
 * No fabricated values, no placeholder text.
 */

import {
  FormEvent,
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import Navbar from "@/components/Navbar";
import Footer from "@/components/Footer";

import "./disease-simulation.css";

// ---------------------------------------------------------------------------
// Types (mirror the real wire shape)
// ---------------------------------------------------------------------------

type Direction = "increase" | "decrease" | "unchanged" | "unknown";
type ResponseMethod =
  | "observed"
  | "model_predicted"
  | "mechanistic_inference"
  | "insufficient";
type UncertaintyLevel = "low" | "medium" | "high" | "unknown";

interface Uncertainty {
  level: UncertaintyLevel;
  reasons: string[];
  sources: string[];
}

interface IndicatorValue {
  indicator_id: string;
  direction: Direction;
  method: ResponseMethod;
  qualitative_label: string | null;
  measurement: null | Record<string, unknown>;
  evidence_ids: string[];
  uncertainty: Uncertainty | null;
  notes: string[];
}

interface BiologicalState {
  state_id: string;
  kind: string;
  run_id: string;
  indicator_values: Record<string, IndicatorValue>;
  intervention_ref: null | Record<string, unknown>;
  intervention_b_ref: null | Record<string, unknown>;
  evidence_ids: string[];
  notes: string[];
  metadata: Record<string, unknown>;
}

interface FunctionalIndicator {
  id: string;
  name: string;
  direction_of_benefit: string;
  unit: string | null;
  description: string | null;
  evidence_level: string | null;
  measurement: null | Record<string, unknown>;
  metadata: Record<string, unknown>;
}

interface Provenance {
  source: string;
  source_id: string;
  source_type: string | null;
  url: string | null;
}

interface MedicineEvidence {
  evidence_id: string;
  source: string;
  description: string;
  evidence_level: string | null;
  support_class: string | null;
  provenance: Provenance | null;
  identifiers: Record<string, string>;
  metadata: Record<string, unknown>;
}

interface DiseaseRef {
  id: string | null;
  name: string;
  query: string;
  source: string;
  resolution_status: string;
  identifiers: Record<string, string>;
  metadata: Record<string, unknown>;
}

interface CellContext {
  id: string;
  name: string;
  source: string;
  ontology_id: string | null;
  metadata: Record<string, unknown>;
}

interface SimulationRun {
  run_id: string;
  task: string;
  disease: DiseaseRef;
  cell_context: CellContext;
  function_mapper_version: string;
  pipeline_version: string;
  created_at: string;
  status: string;
  metadata: Record<string, unknown>;
}

interface SourceStatus {
  source: string;
  reachable: boolean;
  returned_records: number;
  error: string | null;
}

interface SimulationResult {
  run: SimulationRun;
  indicators: FunctionalIndicator[];
  states: BiologicalState[];
  comparison: null | { responses: Record<string, unknown>[] };
  evidence: MedicineEvidence[];
  source_status: SourceStatus[];
  limitations: string[];
  warnings: string[];
  metadata: Record<string, unknown>;
}

interface AnalyzeEnvelope {
  success: boolean;
  domain: string;
  task: string;
  data: {
    domain: string;
    task: string;
    engine: string;
    status: string;
    result: SimulationResult;
  };
}

type Status =
  | { kind: "idle" }
  | { kind: "loading"; query: string; startedAt: number }
  | { kind: "loaded"; query: string; result: SimulationResult }
  | { kind: "error"; query: string; message: string };

// ---------------------------------------------------------------------------
// API
// ---------------------------------------------------------------------------

function apiBase(): string {
  const raw =
    process.env.NEXT_PUBLIC_CUREVERSEAI_API_URL ||
    process.env.NEXT_PUBLIC_API_BASE_URL ||
    "http://localhost:8000";
  return raw.replace(/\/+$/, "");
}

async function runVirtualDiseaseSimulation(
  disease: string,
): Promise<SimulationResult> {
  const res = await fetch(`${apiBase()}/api/v1/analyze`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify({
      domain: "medicine",
      task: "virtual_disease_simulation",
      input: { disease },
    }),
  });

  if (!res.ok) {
    let msg = `Backend returned ${res.status}.`;
    try {
      const body = await res.json();
      const detail = (body as { detail?: unknown }).detail;
      if (typeof detail === "string") msg = detail;
      else if (detail && typeof detail === "object" && "message" in detail) {
        msg = String((detail as { message?: unknown }).message);
      }
    } catch {
      /* keep default */
    }
    throw new Error(msg);
  }

  const envelope = (await res.json()) as AnalyzeEnvelope;
  return envelope.data.result;
}

// ---------------------------------------------------------------------------
// Cell visual — SVG with animated hot-zones per function
// ---------------------------------------------------------------------------

interface CellVisualProps {
  indicators: FunctionalIndicator[];
  diseaseState: BiologicalState | null;
  healthyState: BiologicalState | null;
  onSelect: (indicatorId: string) => void;
  selectedIndicatorId: string | null;
}

function CellVisual({
  indicators,
  diseaseState,
  healthyState,
  onSelect,
  selectedIndicatorId,
}: CellVisualProps) {
  const zones = useMemo(() => {
    const n = Math.max(indicators.length, 1);
    return indicators.map((ind, i) => {
      const angle = (i / n) * Math.PI * 2 - Math.PI / 2;
      const cx = 150 + Math.cos(angle) * 92;
      const cy = 150 + Math.sin(angle) * 92;
      const dv = diseaseState?.indicator_values?.[ind.id];
      const hv = healthyState?.indicator_values?.[ind.id];
      return {
        id: ind.id,
        name: ind.name,
        cx,
        cy,
        direction: (dv?.direction ?? "unknown") as Direction,
        healthyDirection: (hv?.direction ?? "unknown") as Direction,
        uncertainty: dv?.uncertainty?.level ?? "unknown",
      };
    });
  }, [indicators, diseaseState, healthyState]);

  return (
    <div className="cv-medicine-wf-cell-wrap">
      <svg
        viewBox="0 0 300 300"
        className="cv-medicine-wf-cell-svg"
        role="img"
        aria-label="Disease-affected cell — animated functional zones"
      >
        <defs>
          <radialGradient id="cvMedCellMembrane" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="rgba(110,231,242,0.04)" />
            <stop offset="70%" stopColor="rgba(224,82,90,0.06)" />
            <stop offset="100%" stopColor="rgba(8,10,11,0.9)" />
          </radialGradient>
          <radialGradient id="cvMedNucleus" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="rgba(233,197,140,0.16)" />
            <stop offset="100%" stopColor="rgba(233,197,140,0.02)" />
          </radialGradient>
        </defs>

        {/* Outer membrane — slow pulse */}
        <circle
          cx="150"
          cy="150"
          r="120"
          fill="url(#cvMedCellMembrane)"
          stroke="rgba(238,233,225,0.16)"
          strokeWidth="1.2"
          className="cv-medicine-wf-cell-membrane"
        />

        {/* Inner grid — subtle, static */}
        <circle
          cx="150"
          cy="150"
          r="90"
          fill="none"
          stroke="rgba(238,233,225,0.05)"
          strokeWidth="0.6"
          strokeDasharray="2 4"
        />

        {/* Nucleus */}
        <ellipse
          cx="150"
          cy="150"
          rx="42"
          ry="34"
          fill="url(#cvMedNucleus)"
          stroke="rgba(233,197,140,0.35)"
          strokeWidth="0.8"
          className="cv-medicine-wf-cell-nucleus"
        />

        {/* Connecting spokes */}
        {zones.map((z) => (
          <line
            key={`spoke-${z.id}`}
            x1="150"
            y1="150"
            x2={z.cx}
            y2={z.cy}
            stroke={
              z.direction === "increase"
                ? "rgba(224,82,90,0.24)"
                : z.direction === "decrease"
                ? "rgba(110,231,242,0.24)"
                : "rgba(238,233,225,0.08)"
            }
            strokeWidth="0.7"
            strokeDasharray="2 3"
          />
        ))}

        {/* Function zones */}
        {zones.map((z) => {
          const isSel = selectedIndicatorId === z.id;
          const cls = `cv-medicine-wf-cell-zone cv-medicine-wf-cell-zone--${z.direction}${
            isSel ? " is-selected" : ""
          }`;
          return (
            <g
              key={z.id}
              className={cls}
              onClick={() => onSelect(z.id)}
              role="button"
              tabIndex={0}
              aria-label={z.name}
            >
              <circle cx={z.cx} cy={z.cy} r="14" className="cv-medicine-wf-cell-zone-halo" />
              <circle cx={z.cx} cy={z.cy} r="7" className="cv-medicine-wf-cell-zone-dot" />
              <text
                x={z.cx}
                y={z.cy + 24}
                textAnchor="middle"
                className="cv-medicine-wf-cell-zone-label"
              >
                {z.name.length > 26 ? z.name.slice(0, 24) + "…" : z.name}
              </text>
            </g>
          );
        })}
      </svg>

      <div className="cv-medicine-wf-cell-caption">
        <span>Animated functional map</span>
        <i />
        <span>Click a zone for its evidence</span>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function VirtualDiseaseSimulationPage() {
  const [disease, setDisease] = useState("");
  const [status, setStatus] = useState<Status>({ kind: "idle" });
  const [selectedIndicatorId, setSelectedIndicatorId] = useState<string | null>(
    null,
  );
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    if (status.kind !== "loading") return;
    const tick = () =>
      setElapsed(Math.floor((Date.now() - status.startedAt) / 1000));
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [status]);

  const run = useCallback(async () => {
    const q = disease.trim();
    if (!q) return;
    setSelectedIndicatorId(null);
    setElapsed(0);
    setStatus({ kind: "loading", query: q, startedAt: Date.now() });
    try {
      const result = await runVirtualDiseaseSimulation(q);
      setStatus({ kind: "loaded", query: q, result });
    } catch (err) {
      setStatus({
        kind: "error",
        query: q,
        message: err instanceof Error ? err.message : String(err),
      });
    }
  }, [disease]);

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (status.kind === "loading") return;
    void run();
  };

  const loaded = status.kind === "loaded" ? status.result : null;
  const diseaseState = loaded?.states.find((s) => s.kind === "disease") ?? null;
  const healthyState =
    loaded?.states.find((s) => s.kind === "healthy_reference") ?? null;

  const selectedIndicator =
    loaded?.indicators.find((i) => i.id === selectedIndicatorId) ?? null;
  const selectedEvidence = useMemo(() => {
    if (!loaded || !selectedIndicatorId || !diseaseState) return [];
    const iv = diseaseState.indicator_values[selectedIndicatorId];
    if (!iv) return [];
    const ids = new Set(iv.evidence_ids);
    return loaded.evidence.filter((e) => ids.has(e.evidence_id));
  }, [loaded, selectedIndicatorId, diseaseState]);

  return (
    <main className="cv-medicine-wf-page cv-medicine-wf-ds-page">
      <Navbar />

      {/* Breadcrumb */}
      <div className="cv-medicine-wf-breadcrumb">
        <a href="/domains/medicine">Medicine</a>
        <i />
        <strong>Virtual disease simulation</strong>
      </div>

      {/* Hero */}
      <section className="cv-medicine-wf-hero">
        <div className="cv-medicine-wf-hero-grid" />
        <div className="cv-medicine-wf-hero-glow cv-medicine-wf-hero-glow-one" />
        <div className="cv-medicine-wf-hero-glow cv-medicine-wf-hero-glow-two" />

        <div className="cv-medicine-wf-hero-inner">
          <div className="cv-medicine-wf-hero-copy">
            <div className="cv-medicine-wf-hero-kicker">
              <span>01</span>
              <i />
              MEDICINE / VIRTUAL DISEASE SIMULATION
            </div>

            <h1 className="cv-medicine-wf-hero-title">
              Start with a disease.
              <br />
              <em>See the biology change.</em>
            </h1>

            <p className="cv-medicine-wf-hero-sub">
              Enter any disease. CureVerseAI resolves it, derives the
              biological functions it perturbs from real sources, and
              produces a comparable healthy-versus-disease view on the same
              function set.
            </p>
          </div>

          <div className="cv-medicine-wf-hero-visual">
            <div className="cv-medicine-wf-hero-visual-frame">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src="/medicine/workflow01_hero.png"
                alt="Disease-affected cell"
                draggable={false}
              />
              <div className="cv-medicine-wf-hero-visual-scan" />
              <div className="cv-medicine-wf-hero-visual-label">
                <span>VIRTUAL CELL</span>
                <strong>01 / 03</strong>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Input */}
      <section className="cv-medicine-wf-input">
        <form className="cv-medicine-wf-input-form" onSubmit={handleSubmit}>
          <input
            className="cv-medicine-wf-input-control"
            type="text"
            placeholder="e.g. asthma, lung cancer, Alzheimer disease, type 2 diabetes…"
            value={disease}
            onChange={(e) => setDisease(e.target.value)}
            disabled={status.kind === "loading"}
            autoComplete="off"
            spellCheck={false}
          />
          <button
            className="cv-medicine-wf-input-submit"
            type="submit"
            disabled={status.kind === "loading" || !disease.trim()}
          >
            {status.kind === "loading" ? "Simulating…" : "Simulate"}
          </button>
        </form>

        <div className="cv-medicine-wf-input-hint">
          Cold run takes 20–60 seconds. Warm runs are sub-second.
        </div>

        {status.kind === "loading" ? (
          <div className="cv-medicine-wf-loading">
            <div className="cv-medicine-wf-loading-spinner" />
            <div className="cv-medicine-wf-loading-copy">
              <strong>Running simulation</strong>
              <span>
                Resolving disease, deriving functions, retrieving evidence.
              </span>
            </div>
            <div className="cv-medicine-wf-loading-timer">{elapsed}s</div>
          </div>
        ) : null}
      </section>

      {/* Results */}
      <section className="cv-medicine-wf-results">
        {status.kind === "error" ? (
          <div className="cv-medicine-wf-error">
            <div className="cv-medicine-wf-error-label">Simulation failed</div>
            <p>{status.message}</p>
          </div>
        ) : null}

        {!loaded && status.kind !== "error" ? (
          <div className="cv-medicine-wf-empty">
            <div className="cv-medicine-wf-empty-inner">
              <strong>Enter a disease above to begin</strong>
              <p>
                The result will show the disease state, the affected
                functions, and the evidence behind each change.
              </p>
            </div>
          </div>
        ) : null}

        {loaded ? (
          <>
            {/* Identity */}
            <div className="cv-medicine-wf-identity">
              <div className="cv-medicine-wf-identity-head">
                <div className="cv-medicine-wf-identity-eyebrow">
                  DISEASE IDENTITY
                </div>
                <div
                  className={`cv-medicine-wf-identity-status cv-medicine-wf-identity-status-${loaded.run.disease.resolution_status}`}
                >
                  <i />
                  {loaded.run.disease.resolution_status}
                </div>
              </div>

              <h2 className="cv-medicine-wf-identity-name">
                {loaded.run.disease.name}
              </h2>

              <div className="cv-medicine-wf-identity-ids">
                {loaded.run.disease.id ? (
                  <div className="cv-medicine-wf-identity-id">
                    <span>ID</span>
                    <strong>{loaded.run.disease.id}</strong>
                  </div>
                ) : null}
                <div className="cv-medicine-wf-identity-id">
                  <span>CELL</span>
                  <strong>{loaded.run.cell_context.name}</strong>
                </div>
                {loaded.run.cell_context.ontology_id ? (
                  <div className="cv-medicine-wf-identity-id">
                    <span>ONTOLOGY</span>
                    <strong>{loaded.run.cell_context.ontology_id}</strong>
                  </div>
                ) : null}
                <div className="cv-medicine-wf-identity-id">
                  <span>FUNCTIONS</span>
                  <strong>{loaded.indicators.length}</strong>
                </div>
                <div className="cv-medicine-wf-identity-id">
                  <span>EVIDENCE</span>
                  <strong>{loaded.evidence.length}</strong>
                </div>
              </div>
            </div>

            {/* Animated cell + table */}
            <div className="cv-medicine-wf-split">
              <div className="cv-medicine-wf-split-left">
                <div className="cv-medicine-wf-section-label">
                  <span>FUNCTIONAL CELL MAP</span>
                  <i />
                </div>
                <CellVisual
                  indicators={loaded.indicators}
                  diseaseState={diseaseState}
                  healthyState={healthyState}
                  onSelect={setSelectedIndicatorId}
                  selectedIndicatorId={selectedIndicatorId}
                />
              </div>

              <div className="cv-medicine-wf-split-right">
                <div className="cv-medicine-wf-section-label">
                  <span>FUNCTION COMPARISON</span>
                  <i />
                </div>
                <div className="cv-medicine-wf-table-wrap">
                  <table className="cv-medicine-wf-table">
                    <thead>
                      <tr>
                        <th>Function</th>
                        <th>Healthy</th>
                        <th>Disease</th>
                        <th>Method</th>
                      </tr>
                    </thead>
                    <tbody>
                      {loaded.indicators.map((ind) => {
                        const hv =
                          healthyState?.indicator_values[ind.id]?.direction ??
                          "unknown";
                        const dv =
                          diseaseState?.indicator_values[ind.id]?.direction ??
                          "unknown";
                        const method =
                          diseaseState?.indicator_values[ind.id]?.method ??
                          "insufficient";
                        const isSel = selectedIndicatorId === ind.id;
                        return (
                          <tr
                            key={ind.id}
                            className={
                              "cv-medicine-wf-table-row" +
                              (isSel ? " is-selected" : "")
                            }
                            onClick={() => setSelectedIndicatorId(ind.id)}
                          >
                            <td className="cv-medicine-wf-table-name">
                              {ind.name}
                            </td>
                            <td>
                              <span
                                className={`cv-medicine-wf-dir cv-medicine-wf-dir--${hv}`}
                              >
                                {hv}
                              </span>
                            </td>
                            <td>
                              <span
                                className={`cv-medicine-wf-dir cv-medicine-wf-dir--${dv}`}
                              >
                                {dv}
                              </span>
                            </td>
                            <td className="cv-medicine-wf-table-method">
                              {method}
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            {/* Evidence inspector */}
            {selectedIndicator ? (
              <div className="cv-medicine-wf-inspector">
                <div className="cv-medicine-wf-inspector-head">
                  <div className="cv-medicine-wf-inspector-kicker">
                    <span>EVIDENCE</span>
                    <i />
                    <strong>{selectedIndicator.name}</strong>
                  </div>
                  <button
                    className="cv-medicine-wf-inspector-close"
                    type="button"
                    onClick={() => setSelectedIndicatorId(null)}
                    aria-label="Close"
                  >
                    ×
                  </button>
                </div>

                {selectedIndicator.description ? (
                  <p className="cv-medicine-wf-inspector-desc">
                    {selectedIndicator.description}
                  </p>
                ) : null}

                {selectedEvidence.length === 0 ? (
                  <div className="cv-medicine-wf-inspector-empty">
                    No evidence records attached to this function.
                  </div>
                ) : (
                  <ul className="cv-medicine-wf-inspector-list">
                    {selectedEvidence.map((ev) => (
                      <li
                        key={ev.evidence_id}
                        className="cv-medicine-wf-inspector-item"
                      >
                        <div className="cv-medicine-wf-inspector-item-head">
                          <strong>{ev.source}</strong>
                          <span>{ev.evidence_level ?? "contextual"}</span>
                        </div>
                        <p className="cv-medicine-wf-inspector-item-desc">
                          {ev.description}
                        </p>
                        {ev.provenance?.url ? (
                          <a
                            className="cv-medicine-wf-inspector-link"
                            href={ev.provenance.url}
                            target="_blank"
                            rel="noreferrer"
                          >
                            Open {ev.provenance.source_id}
                          </a>
                        ) : null}
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            ) : null}

            {/* Limitations */}
            {loaded.limitations.length > 0 ? (
              <div className="cv-medicine-wf-limits">
                <div className="cv-medicine-wf-section-label">
                  <span>LIMITATIONS</span>
                  <i />
                </div>
                <ul className="cv-medicine-wf-limits-list">
                  {loaded.limitations.map((l, i) => (
                    <li key={i}>{l}</li>
                  ))}
                </ul>
              </div>
            ) : null}
          </>
        ) : null}
      </section>

      <Footer />
    </main>
  );
}
