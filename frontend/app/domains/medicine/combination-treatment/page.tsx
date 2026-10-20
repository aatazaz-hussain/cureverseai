"use client";

/**
 * CureVerseAI — Medicine
 * Workflow 03 — Combination Treatment Simulator
 *
 * Route: /domains/medicine/combination-treatment
 *
 * Self-contained. Renders four scenarios (baseline, A, B, A+B)
 * plus the ranking the AI Engine derived from real ChEMBL
 * mechanism targets and Reactome pathway intersections.
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

import "./combination-treatment.css";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type Direction = "increase" | "decrease" | "unchanged" | "unknown";
type EffectState =
  | "restored"
  | "partially_restored"
  | "worsened"
  | "unchanged"
  | "unknown";
type CombinedState =
  | "restored"
  | "worsened"
  | "overlapping"
  | "conflicting"
  | "unchanged"
  | "unknown";

interface Uncertainty {
  level: string;
  reasons: string[];
  sources: string[];
}

interface IndicatorValue {
  indicator_id: string;
  direction: Direction;
  method: string;
  qualitative_label: string | null;
  evidence_ids: string[];
  uncertainty: Uncertainty | null;
  notes: string[];
}

interface BiologicalState {
  state_id: string;
  kind: string;
  run_id: string;
  indicator_values: Record<string, IndicatorValue>;
  notes: string[];
  metadata: Record<string, unknown>;
}

interface FunctionalIndicator {
  id: string;
  name: string;
  direction_of_benefit: string;
  description: string | null;
  metadata: Record<string, unknown>;
}

interface MedicineChainItem {
  target_id: string;
  target_name: string;
  action_type: string | null;
  pathway: string;
  uniprot_accession: string | null;
}

interface PerFunctionEffect {
  indicator_id: string;
  indicator_name: string;
  a_state: EffectState;
  b_state: EffectState;
  combined_state: CombinedState;
  combined_reason: string;
  a_chain: MedicineChainItem[];
  b_chain: MedicineChainItem[];
}

interface RankingRow {
  scenario_id: string;
  restored_count: number;
  conflicting_count: number;
  worsened_count: number;
  unchanged_count: number;
  unknown_count: number;
  total_functions: number;
}

interface CombinationEffect {
  version: string;
  intervention_a_id: string;
  intervention_a_name: string;
  intervention_b_id: string;
  intervention_b_name: string;
  per_function: PerFunctionEffect[];
  summaries: Record<string, Record<string, number>>;
  ranking: RankingRow[];
  overall_interpretation: string;
}

interface DiseaseRef {
  id: string | null;
  name: string;
  resolution_status: string;
}

interface SimulationRun {
  run_id: string;
  task: string;
  disease: DiseaseRef;
  status: string;
}

interface SimulationResult {
  run: SimulationRun;
  indicators: FunctionalIndicator[];
  states: BiologicalState[];
  comparison: null | Record<string, unknown>;
  evidence: Record<string, unknown>[];
  source_status: Record<string, unknown>[];
  limitations: string[];
  warnings: string[];
  metadata: {
    combination_effect?: CombinationEffect;
    [k: string]: unknown;
  };
}

interface AnalyzeEnvelope {
  success: boolean;
  data: { status: string; result: SimulationResult };
}

type Status =
  | { kind: "idle" }
  | {
      kind: "loading";
      disease: string;
      a: string;
      b: string;
      startedAt: number;
    }
  | {
      kind: "loaded";
      disease: string;
      a: string;
      b: string;
      result: SimulationResult;
    }
  | { kind: "error"; disease: string; a: string; b: string; message: string };

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

async function runCombinationSimulation(
  disease: string,
  a: string,
  b: string,
): Promise<SimulationResult> {
  const res = await fetch(`${apiBase()}/api/v1/analyze`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify({
      domain: "medicine",
      task: "combination_treatment_simulation",
      input: {
        disease,
        intervention_a_id: a,
        intervention_b_id: b,
      },
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
      /* default */
    }
    throw new Error(msg);
  }

  const envelope = (await res.json()) as AnalyzeEnvelope;
  return envelope.data.result;
}

// ---------------------------------------------------------------------------
// Animated cell — 4 mini SVGs in a row
// ---------------------------------------------------------------------------

interface MiniCellProps {
  label: string;
  indicators: FunctionalIndicator[];
  states: Record<string, string>;
  selectedIndicatorId: string | null;
  onSelect: (id: string) => void;
}

function MiniCell({
  label,
  indicators,
  states,
  selectedIndicatorId,
  onSelect,
}: MiniCellProps) {
  const zones = useMemo(() => {
    const n = Math.max(indicators.length, 1);
    return indicators.map((ind, i) => {
      const angle = (i / n) * Math.PI * 2 - Math.PI / 2;
      const cx = 100 + Math.cos(angle) * 62;
      const cy = 100 + Math.sin(angle) * 62;
      return {
        id: ind.id,
        name: ind.name,
        cx,
        cy,
        state: states[ind.id] ?? "unchanged",
      };
    });
  }, [indicators, states]);

  return (
    <div className="cv-medicine-wf-minicell">
      <div className="cv-medicine-wf-minicell-label">{label}</div>
      <svg viewBox="0 0 200 200" className="cv-medicine-wf-minicell-svg">
        <defs>
          <radialGradient id={`mcg-${label}`} cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="rgba(233,197,140,0.05)" />
            <stop offset="100%" stopColor="rgba(8,10,11,0.9)" />
          </radialGradient>
        </defs>
        <circle
          cx="100"
          cy="100"
          r="80"
          fill={`url(#mcg-${label})`}
          stroke="rgba(238,233,225,0.14)"
          strokeWidth="1"
          className="cv-medicine-wf-minicell-membrane"
        />
        <ellipse
          cx="100"
          cy="100"
          rx="26"
          ry="20"
          fill="rgba(233,197,140,0.12)"
          stroke="rgba(233,197,140,0.3)"
          strokeWidth="0.7"
        />
        {zones.map((z) => {
          const isSel = selectedIndicatorId === z.id;
          return (
            <g
              key={z.id}
              className={`cv-medicine-wf-minizone cv-medicine-wf-minizone--${z.state}${
                isSel ? " is-selected" : ""
              }`}
              onClick={() => onSelect(z.id)}
            >
              <circle cx={z.cx} cy={z.cy} r="10" className="cv-medicine-wf-minizone-halo" />
              <circle cx={z.cx} cy={z.cy} r="5" className="cv-medicine-wf-minizone-dot" />
            </g>
          );
        })}
      </svg>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function CombinationTreatmentPage() {
  const [disease, setDisease] = useState("");
  const [a, setA] = useState("");
  const [b, setB] = useState("");
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
    const d = disease.trim();
    const av = a.trim();
    const bv = b.trim();
    if (!d || !av || !bv) return;
    setSelectedIndicatorId(null);
    setElapsed(0);
    setStatus({
      kind: "loading",
      disease: d,
      a: av,
      b: bv,
      startedAt: Date.now(),
    });
    try {
      const result = await runCombinationSimulation(d, av, bv);
      setStatus({
        kind: "loaded",
        disease: d,
        a: av,
        b: bv,
        result,
      });
    } catch (err) {
      setStatus({
        kind: "error",
        disease: d,
        a: av,
        b: bv,
        message: err instanceof Error ? err.message : String(err),
      });
    }
  }, [disease, a, b]);

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (status.kind === "loading") return;
    void run();
  };

  const loaded = status.kind === "loaded" ? status.result : null;
  const combinationEffect = loaded?.metadata?.combination_effect ?? null;

  const diseaseState =
    loaded?.states.find((s) => s.kind === "disease") ?? null;
  const stateA =
    loaded?.states.find(
      (s) => s.kind === "intervention_single" && s.state_id.includes("::")
    ) ?? null;

  // Map indicators -> per-scenario states for the mini cells
  const baselineStates = useMemo(() => {
    const m: Record<string, string> = {};
    if (!diseaseState) return m;
    for (const [id, iv] of Object.entries(diseaseState.indicator_values)) {
      m[id] =
        iv.direction === "increase"
          ? "increase"
          : iv.direction === "decrease"
          ? "decrease"
          : "unchanged";
    }
    return m;
  }, [diseaseState]);

  const stateAByIndicator = useMemo(() => {
    const m: Record<string, string> = {};
    if (!combinationEffect) return m;
    for (const f of combinationEffect.per_function) m[f.indicator_id] = f.a_state;
    return m;
  }, [combinationEffect]);

  const stateBByIndicator = useMemo(() => {
    const m: Record<string, string> = {};
    if (!combinationEffect) return m;
    for (const f of combinationEffect.per_function) m[f.indicator_id] = f.b_state;
    return m;
  }, [combinationEffect]);

  const combinedByIndicator = useMemo(() => {
    const m: Record<string, string> = {};
    if (!combinationEffect) return m;
    for (const f of combinationEffect.per_function)
      m[f.indicator_id] = f.combined_state;
    return m;
  }, [combinationEffect]);

  const selectedEffect = useMemo(() => {
    if (!combinationEffect || !selectedIndicatorId) return null;
    return (
      combinationEffect.per_function.find(
        (f) => f.indicator_id === selectedIndicatorId,
      ) ?? null
    );
  }, [combinationEffect, selectedIndicatorId]);

  const selectedIndicator =
    loaded?.indicators.find((i) => i.id === selectedIndicatorId) ?? null;

  return (
    <main className="cv-medicine-wf-page cv-medicine-wf-ct-page">
      <Navbar />

      <div className="cv-medicine-wf-breadcrumb">
        <a href="/domains/medicine">Medicine</a>
        <i />
        <strong>Combination treatment</strong>
      </div>

      <section className="cv-medicine-wf-hero">
        <div className="cv-medicine-wf-hero-grid" />
        <div className="cv-medicine-wf-hero-glow cv-medicine-wf-hero-glow-one" />
        <div className="cv-medicine-wf-hero-glow cv-medicine-wf-hero-glow-two" />

        <div className="cv-medicine-wf-hero-inner">
          <div className="cv-medicine-wf-hero-copy">
            <div className="cv-medicine-wf-hero-kicker">
              <span>03</span>
              <i />
              MEDICINE / COMBINATION TREATMENT
            </div>

            <h1 className="cv-medicine-wf-hero-title">
              Two medicines.
              <br />
              <em>One comparison.</em>
            </h1>

            <p className="cv-medicine-wf-hero-sub">
              Enter a disease and two medicines. CureVerseAI resolves both
              interventions to their mechanism targets, intersects their
              Reactome pathways with the disease's affected functions, and
              compares A alone, B alone, and A + B.
            </p>
          </div>

          <div className="cv-medicine-wf-hero-visual">
            <div className="cv-medicine-wf-hero-visual-frame">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src="/medicine/workflow03_hero.png"
                alt="Combination treatment"
                draggable={false}
              />
              <div className="cv-medicine-wf-hero-visual-scan" />
              <div className="cv-medicine-wf-hero-visual-label">
                <span>COMBINATION</span>
                <strong>03 / 03</strong>
              </div>
            </div>
          </div>
        </div>
      </section>

      <section className="cv-medicine-wf-input">
        <form className="cv-medicine-wf-input-form" onSubmit={handleSubmit}>
          <input
            className="cv-medicine-wf-input-control"
            type="text"
            placeholder="Disease — e.g. asthma, lung cancer…"
            value={disease}
            onChange={(e) => setDisease(e.target.value)}
            disabled={status.kind === "loading"}
            autoComplete="off"
            spellCheck={false}
          />
          <input
            className="cv-medicine-wf-input-control"
            type="text"
            placeholder="Medicine A"
            value={a}
            onChange={(e) => setA(e.target.value)}
            disabled={status.kind === "loading"}
            autoComplete="off"
            spellCheck={false}
          />
          <input
            className="cv-medicine-wf-input-control"
            type="text"
            placeholder="Medicine B"
            value={b}
            onChange={(e) => setB(e.target.value)}
            disabled={status.kind === "loading"}
            autoComplete="off"
            spellCheck={false}
          />
          <button
            className="cv-medicine-wf-input-submit"
            type="submit"
            disabled={
              status.kind === "loading" ||
              !disease.trim() ||
              !a.trim() ||
              !b.trim()
            }
          >
            {status.kind === "loading" ? "Simulating…" : "Simulate"}
          </button>
        </form>

        <div className="cv-medicine-wf-input-hint">
          Cold run takes 30–90 seconds. Warm runs are sub-second.
        </div>

        {status.kind === "loading" ? (
          <div className="cv-medicine-wf-loading">
            <div className="cv-medicine-wf-loading-spinner" />
            <div className="cv-medicine-wf-loading-copy">
              <strong>Running combination simulation</strong>
              <span>
                Resolving both medicines, computing four scenarios, ranking.
              </span>
            </div>
            <div className="cv-medicine-wf-loading-timer">{elapsed}s</div>
          </div>
        ) : null}
      </section>

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
              <strong>Enter a disease and two medicines above</strong>
              <p>
                The result will show the ranking, the per-function states
                for each scenario, and the medicine chains behind them.
              </p>
            </div>
          </div>
        ) : null}

        {loaded && combinationEffect ? (
          <>
            {/* Identity */}
            <div className="cv-medicine-wf-identity">
              <div className="cv-medicine-wf-identity-head">
                <div className="cv-medicine-wf-identity-eyebrow">
                  COMBINATION SCENARIO
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
                <div className="cv-medicine-wf-identity-id">
                  <span>DISEASE</span>
                  <strong>{loaded.run.disease.id ?? "—"}</strong>
                </div>
                <div className="cv-medicine-wf-identity-id">
                  <span>A</span>
                  <strong>{combinationEffect.intervention_a_name}</strong>
                </div>
                <div className="cv-medicine-wf-identity-id">
                  <span>B</span>
                  <strong>{combinationEffect.intervention_b_name}</strong>
                </div>
                <div className="cv-medicine-wf-identity-id">
                  <span>FUNCTIONS</span>
                  <strong>{loaded.indicators.length}</strong>
                </div>
              </div>
            </div>

            {/* Ranking */}
            <div className="cv-medicine-wf-ranking">
              <div className="cv-medicine-wf-section-label">
                <span>RANKING</span>
                <i />
              </div>

              <div className="cv-medicine-wf-ranking-overall">
                <span>OVERALL INTERPRETATION</span>
                <strong
                  className={`cv-medicine-wf-overall cv-medicine-wf-overall--${combinationEffect.overall_interpretation}`}
                >
                  {combinationEffect.overall_interpretation}
                </strong>
              </div>

              <ul className="cv-medicine-wf-ranking-list">
                {combinationEffect.ranking.map((row, i) => (
                  <li key={row.scenario_id} className="cv-medicine-wf-ranking-row">
                    <span className="cv-medicine-wf-ranking-pos">#{i + 1}</span>
                    <div className="cv-medicine-wf-ranking-scenario">
                      {row.scenario_id === "A_alone"
                        ? "A alone"
                        : row.scenario_id === "B_alone"
                        ? "B alone"
                        : "A + B"}
                    </div>
                    <div className="cv-medicine-wf-ranking-stats">
                      <span>
                        <em>{row.restored_count}</em> restored
                      </span>
                      <span>
                        <em>{row.worsened_count}</em> worsened
                      </span>
                      <span>
                        <em>{row.unchanged_count}</em> unchanged
                      </span>
                      <span>
                        <em>{row.unknown_count}</em> unknown
                      </span>
                    </div>
                  </li>
                ))}
              </ul>
            </div>

            {/* Four-scenario mini cells */}
            <div className="cv-medicine-wf-scenarios">
              <div className="cv-medicine-wf-section-label">
                <span>FOUR-SCENARIO CELL MAP</span>
                <i />
              </div>

              <div className="cv-medicine-wf-scenarios-grid">
                <MiniCell
                  label="DISEASE"
                  indicators={loaded.indicators}
                  states={baselineStates}
                  selectedIndicatorId={selectedIndicatorId}
                  onSelect={setSelectedIndicatorId}
                />
                <MiniCell
                  label="A ALONE"
                  indicators={loaded.indicators}
                  states={stateAByIndicator}
                  selectedIndicatorId={selectedIndicatorId}
                  onSelect={setSelectedIndicatorId}
                />
                <MiniCell
                  label="B ALONE"
                  indicators={loaded.indicators}
                  states={stateBByIndicator}
                  selectedIndicatorId={selectedIndicatorId}
                  onSelect={setSelectedIndicatorId}
                />
                <MiniCell
                  label="A + B"
                  indicators={loaded.indicators}
                  states={combinedByIndicator}
                  selectedIndicatorId={selectedIndicatorId}
                  onSelect={setSelectedIndicatorId}
                />
              </div>
            </div>

            {/* Per-function table */}
            <div className="cv-medicine-wf-table-wrap cv-medicine-wf-table-wrap--wide">
              <table className="cv-medicine-wf-table">
                <thead>
                  <tr>
                    <th>Function</th>
                    <th>A alone</th>
                    <th>B alone</th>
                    <th>A + B</th>
                  </tr>
                </thead>
                <tbody>
                  {combinationEffect.per_function.map((f) => {
                    const isSel = selectedIndicatorId === f.indicator_id;
                    return (
                      <tr
                        key={f.indicator_id}
                        className={
                          "cv-medicine-wf-table-row" +
                          (isSel ? " is-selected" : "")
                        }
                        onClick={() => setSelectedIndicatorId(f.indicator_id)}
                      >
                        <td className="cv-medicine-wf-table-name">
                          {f.indicator_name}
                        </td>
                        <td>
                          <span
                            className={`cv-medicine-wf-effect cv-medicine-wf-effect--${f.a_state}`}
                          >
                            {f.a_state}
                          </span>
                        </td>
                        <td>
                          <span
                            className={`cv-medicine-wf-effect cv-medicine-wf-effect--${f.b_state}`}
                          >
                            {f.b_state}
                          </span>
                        </td>
                        <td>
                          <span
                            className={`cv-medicine-wf-combined cv-medicine-wf-combined--${f.combined_state}`}
                          >
                            {f.combined_state}
                          </span>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>

            {/* Selected function inspector */}
            {selectedIndicator && selectedEffect ? (
              <div className="cv-medicine-wf-inspector">
                <div className="cv-medicine-wf-inspector-head">
                  <div className="cv-medicine-wf-inspector-kicker">
                    <span>COMBINATION</span>
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

                <div className="cv-medicine-wf-inspector-body">
                  <div className="cv-medicine-wf-inspector-state">
                    <span
                      className={`cv-medicine-wf-combined cv-medicine-wf-combined--${selectedEffect.combined_state}`}
                    >
                      {selectedEffect.combined_state}
                    </span>
                    <p>{selectedEffect.combined_reason}</p>
                  </div>

                  {selectedEffect.a_chain.length > 0 ? (
                    <div className="cv-medicine-wf-inspector-section">
                      <div className="cv-medicine-wf-inspector-section-label">
                        A — {combinationEffect.intervention_a_name}
                      </div>
                      <ul className="cv-medicine-wf-chain">
                        {selectedEffect.a_chain.map((c, i) => (
                          <li key={`a-${i}`} className="cv-medicine-wf-chain-item">
                            <div className="cv-medicine-wf-chain-node">
                              <span>TARGET</span>
                              <strong>{c.target_name}</strong>
                              {c.action_type ? <em>{c.action_type}</em> : null}
                            </div>
                            <div className="cv-medicine-wf-chain-arrow">→</div>
                            <div className="cv-medicine-wf-chain-node">
                              <span>PATHWAY</span>
                              <strong>{c.pathway}</strong>
                            </div>
                          </li>
                        ))}
                      </ul>
                    </div>
                  ) : null}

                  {selectedEffect.b_chain.length > 0 ? (
                    <div className="cv-medicine-wf-inspector-section">
                      <div className="cv-medicine-wf-inspector-section-label">
                        B — {combinationEffect.intervention_b_name}
                      </div>
                      <ul className="cv-medicine-wf-chain">
                        {selectedEffect.b_chain.map((c, i) => (
                          <li key={`b-${i}`} className="cv-medicine-wf-chain-item">
                            <div className="cv-medicine-wf-chain-node">
                              <span>TARGET</span>
                              <strong>{c.target_name}</strong>
                              {c.action_type ? <em>{c.action_type}</em> : null}
                            </div>
                            <div className="cv-medicine-wf-chain-arrow">→</div>
                            <div className="cv-medicine-wf-chain-node">
                              <span>PATHWAY</span>
                              <strong>{c.pathway}</strong>
                            </div>
                          </li>
                        ))}
                      </ul>
                    </div>
                  ) : null}
                </div>
              </div>
            ) : null}

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
