"use client";

/**
 * CureVerseAI — Medicine
 * Workflow 02 — Treatment Simulation
 *
 * Route: /domains/medicine/treatment-simulation
 *
 * Self-contained. Consumes the real wire shape of
 * SimulationResult including the medicine_effect field that
 * the AI Engine now places in result metadata.
 *
 * Every visual element is driven by real backend fields.
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

import "./treatment-simulation.css";

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type Direction = "increase" | "decrease" | "unchanged" | "unknown";
type ResponseMethod =
  | "observed"
  | "model_predicted"
  | "mechanistic_inference"
  | "insufficient";
type UncertaintyLevel = "low" | "medium" | "high" | "unknown";
type EffectState =
  | "restored"
  | "partially_restored"
  | "worsened"
  | "unchanged"
  | "unknown";

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
  disease_direction: Direction;
  state: EffectState;
  reason: string;
  intersecting_pathways: string[];
  shared_top_levels?: string[];
  medicine_chain: MedicineChainItem[];
}

interface MedicineEffect {
  version: string;
  intervention_id: string;
  intervention_name: string;
  mechanism_targets: {
    target_id: string;
    name: string;
    action_type: string | null;
    uniprot_accession: string | null;
  }[];
  per_function: PerFunctionEffect[];
  summary: {
    restored_count: number;
    partially_restored_count: number;
    worsened_count: number;
    unchanged_count: number;
    unknown_count: number;
    total_functions: number;
  };
}

interface InterventionRef {
  id: string;
  name: string;
  source: string;
  source_id: string;
  targets: {
    id: string;
    name: string;
    source: string;
    source_id: string;
    metadata: Record<string, unknown>;
  }[];
  resolution_status: string;
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
  status: string;
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
  evidence: Record<string, unknown>[];
  source_status: SourceStatus[];
  limitations: string[];
  warnings: string[];
  metadata: {
    workflow?: string;
    intervention?: InterventionRef;
    medicine_effect?: MedicineEffect;
    [k: string]: unknown;
  };
}

interface AnalyzeEnvelope {
  success: boolean;
  domain: string;
  task: string;
  data: {
    status: string;
    result: SimulationResult;
  };
}

type Status =
  | { kind: "idle" }
  | { kind: "loading"; query: string; intervention: string; startedAt: number }
  | { kind: "loaded"; query: string; intervention: string; result: SimulationResult }
  | { kind: "error"; query: string; intervention: string; message: string };

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

async function runTreatmentSimulation(
  disease: string,
  intervention: string,
): Promise<SimulationResult> {
  const res = await fetch(`${apiBase()}/api/v1/analyze`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "application/json",
    },
    body: JSON.stringify({
      domain: "medicine",
      task: "treatment_simulation",
      input: { disease, intervention_id: intervention },
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
// Animated cell — re-uses the W01 cell, adds medicine-state colours
// ---------------------------------------------------------------------------

interface CellVisualProps {
  indicators: FunctionalIndicator[];
  diseaseState: BiologicalState | null;
  effectByIndicator: Map<string, PerFunctionEffect>;
  onSelect: (indicatorId: string) => void;
  selectedIndicatorId: string | null;
}

function CellVisual({
  indicators,
  diseaseState,
  effectByIndicator,
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
      const eff = effectByIndicator.get(ind.id);
      return {
        id: ind.id,
        name: ind.name,
        cx,
        cy,
        diseaseDirection: (dv?.direction ?? "unknown") as Direction,
        medicineState: (eff?.state ?? "unchanged") as EffectState,
      };
    });
  }, [indicators, diseaseState, effectByIndicator]);

  return (
    <div className="cv-medicine-wf-cell-wrap cv-medicine-wf-cell-wrap--treat">
      <svg
        viewBox="0 0 300 300"
        className="cv-medicine-wf-cell-svg"
        role="img"
        aria-label="Cell after treatment — animated functional zones"
      >
        <defs>
          <radialGradient id="cvMedCellMembraneT" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="rgba(233,197,140,0.05)" />
            <stop offset="70%" stopColor="rgba(224,82,90,0.06)" />
            <stop offset="100%" stopColor="rgba(8,10,11,0.9)" />
          </radialGradient>
          <radialGradient id="cvMedNucleusT" cx="50%" cy="50%" r="50%">
            <stop offset="0%" stopColor="rgba(233,197,140,0.18)" />
            <stop offset="100%" stopColor="rgba(233,197,140,0.02)" />
          </radialGradient>
        </defs>

        <circle
          cx="150"
          cy="150"
          r="120"
          fill="url(#cvMedCellMembraneT)"
          stroke="rgba(238,233,225,0.16)"
          strokeWidth="1.2"
          className="cv-medicine-wf-cell-membrane"
        />
        <circle
          cx="150"
          cy="150"
          r="90"
          fill="none"
          stroke="rgba(238,233,225,0.05)"
          strokeWidth="0.6"
          strokeDasharray="2 4"
        />
        <ellipse
          cx="150"
          cy="150"
          rx="42"
          ry="34"
          fill="url(#cvMedNucleusT)"
          stroke="rgba(233,197,140,0.35)"
          strokeWidth="0.8"
          className="cv-medicine-wf-cell-nucleus"
        />

        {zones.map((z) => (
          <line
            key={`spoke-${z.id}`}
            x1="150"
            y1="150"
            x2={z.cx}
            y2={z.cy}
            stroke={
              z.medicineState === "restored"
                ? "rgba(123,207,139,0.32)"
                : z.medicineState === "worsened"
                ? "rgba(224,82,90,0.32)"
                : "rgba(238,233,225,0.08)"
            }
            strokeWidth="0.7"
            strokeDasharray="2 3"
          />
        ))}

        {zones.map((z) => {
          const isSel = selectedIndicatorId === z.id;
          const cls = `cv-medicine-wf-cell-zone cv-medicine-wf-cell-zone--eff-${z.medicineState}${
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
        <span>Post-treatment functional map</span>
        <i />
        <span>Click a zone for its medicine chain</span>
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Page
// ---------------------------------------------------------------------------

export default function TreatmentSimulationPage() {
  const [disease, setDisease] = useState("");
  const [intervention, setIntervention] = useState("");
  const [status, setStatus] = useState<Status>({ kind: "idle" });
  const [selectedIndicatorId, setSelectedIndicatorId] = useState<string | null>(null);
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
    const iv = intervention.trim();
    if (!q || !iv) return;
    setSelectedIndicatorId(null);
    setElapsed(0);
    setStatus({ kind: "loading", query: q, intervention: iv, startedAt: Date.now() });
    try {
      const result = await runTreatmentSimulation(q, iv);
      setStatus({ kind: "loaded", query: q, intervention: iv, result });
    } catch (err) {
      setStatus({
        kind: "error",
        query: q,
        intervention: iv,
        message: err instanceof Error ? err.message : String(err),
      });
    }
  }, [disease, intervention]);

  const handleSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    if (status.kind === "loading") return;
    void run();
  };

  const loaded = status.kind === "loaded" ? status.result : null;
  const diseaseState = loaded?.states.find((s) => s.kind === "disease") ?? null;
  const medicineEffect = loaded?.metadata?.medicine_effect;
  const interventionRef = loaded?.metadata?.intervention ?? null;

  const effectByIndicator = useMemo(() => {
    const m = new Map<string, PerFunctionEffect>();
    if (medicineEffect) for (const f of medicineEffect.per_function) m.set(f.indicator_id, f);
    return m;
  }, [medicineEffect]);

  const selectedIndicator =
    loaded?.indicators.find((i) => i.id === selectedIndicatorId) ?? null;
  const selectedEffect =
    selectedIndicatorId ? effectByIndicator.get(selectedIndicatorId) ?? null : null;

  return (
    <main className="cv-medicine-wf-page cv-medicine-wf-ts-page">
      <Navbar />

      <div className="cv-medicine-wf-breadcrumb">
        <a href="/domains/medicine">Medicine</a>
        <i />
        <strong>Treatment simulation</strong>
      </div>

      <section className="cv-medicine-wf-hero">
        <div className="cv-medicine-wf-hero-grid" />
        <div className="cv-medicine-wf-hero-glow cv-medicine-wf-hero-glow-one" />
        <div className="cv-medicine-wf-hero-glow cv-medicine-wf-hero-glow-two" />

        <div className="cv-medicine-wf-hero-inner">
          <div className="cv-medicine-wf-hero-copy">
            <div className="cv-medicine-wf-hero-kicker">
              <span>02</span>
              <i />
              MEDICINE / TREATMENT SIMULATION
            </div>

            <h1 className="cv-medicine-wf-hero-title">
              Apply a medicine.
              <br />
              <em>See what changes.</em>
            </h1>

            <p className="cv-medicine-wf-hero-sub">
              Enter any disease and any medicine. CureVerseAI resolves the
              medicine to its mechanism targets, checks the Reactome pathways
              those targets participate in, and reports per function whether
              the medicine restores, worsens, or does not touch it.
            </p>
          </div>

          <div className="cv-medicine-wf-hero-visual">
            <div className="cv-medicine-wf-hero-visual-frame">
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img
                src="/medicine/workflow02_hero.png"
                alt="Treatment intervention"
                draggable={false}
              />
              <div className="cv-medicine-wf-hero-visual-scan" />
              <div className="cv-medicine-wf-hero-visual-label">
                <span>INTERVENTION</span>
                <strong>02 / 03</strong>
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
            placeholder="Disease — e.g. asthma, lung cancer, Alzheimer disease…"
            value={disease}
            onChange={(e) => setDisease(e.target.value)}
            disabled={status.kind === "loading"}
            autoComplete="off"
            spellCheck={false}
          />
          <input
            className="cv-medicine-wf-input-control"
            type="text"
            placeholder="Medicine — e.g. montelukast, erlotinib, metformin…"
            value={intervention}
            onChange={(e) => setIntervention(e.target.value)}
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
              !intervention.trim()
            }
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
              <strong>Running treatment simulation</strong>
              <span>
                Resolving medicine, fetching mechanism targets, intersecting
                Reactome pathways.
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
              <strong>Enter a disease and a medicine above</strong>
              <p>
                The result will show the intervention's mechanism targets,
                the Reactome pathway intersection, and per-function states.
              </p>
            </div>
          </div>
        ) : null}

        {loaded ? (
          <>
            <div className="cv-medicine-wf-identity">
              <div className="cv-medicine-wf-identity-head">
                <div className="cv-medicine-wf-identity-eyebrow">
                  TREATMENT SCENARIO
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
                {interventionRef ? (
                  <>
                    <div className="cv-medicine-wf-identity-id">
                      <span>INTERVENTION</span>
                      <strong>{interventionRef.name}</strong>
                    </div>
                    <div className="cv-medicine-wf-identity-id">
                      <span>ID</span>
                      <strong>{interventionRef.id}</strong>
                    </div>
                    <div className="cv-medicine-wf-identity-id">
                      <span>MECHANISM TARGETS</span>
                      <strong>
                        {medicineEffect?.mechanism_targets.length ??
                          interventionRef.targets.length}
                      </strong>
                    </div>
                  </>
                ) : null}
                <div className="cv-medicine-wf-identity-id">
                  <span>FUNCTIONS</span>
                  <strong>{loaded.indicators.length}</strong>
                </div>
              </div>
            </div>

            {/* Effect summary row */}
            {medicineEffect ? (
              <div className="cv-medicine-wf-summary">
                <div className="cv-medicine-wf-summary-item cv-medicine-wf-summary-item--restored">
                  <strong>{medicineEffect.summary.restored_count}</strong>
                  <span>Restored</span>
                </div>
                <div className="cv-medicine-wf-summary-item cv-medicine-wf-summary-item--worsened">
                  <strong>{medicineEffect.summary.worsened_count}</strong>
                  <span>Worsened</span>
                </div>
                <div className="cv-medicine-wf-summary-item">
                  <strong>{medicineEffect.summary.unchanged_count}</strong>
                  <span>Unchanged</span>
                </div>
                <div className="cv-medicine-wf-summary-item">
                  <strong>{medicineEffect.summary.unknown_count}</strong>
                  <span>Unknown</span>
                </div>
              </div>
            ) : null}

            <div className="cv-medicine-wf-split">
              <div className="cv-medicine-wf-split-left">
                <div className="cv-medicine-wf-section-label">
                  <span>POST-TREATMENT CELL MAP</span>
                  <i />
                </div>
                <CellVisual
                  indicators={loaded.indicators}
                  diseaseState={diseaseState}
                  effectByIndicator={effectByIndicator}
                  onSelect={setSelectedIndicatorId}
                  selectedIndicatorId={selectedIndicatorId}
                />
              </div>

              <div className="cv-medicine-wf-split-right">
                <div className="cv-medicine-wf-section-label">
                  <span>PER-FUNCTION EFFECT</span>
                  <i />
                </div>
                <div className="cv-medicine-wf-table-wrap">
                  <table className="cv-medicine-wf-table">
                    <thead>
                      <tr>
                        <th>Function</th>
                        <th>Disease</th>
                        <th>Effect</th>
                      </tr>
                    </thead>
                    <tbody>
                      {loaded.indicators.map((ind) => {
                        const eff = effectByIndicator.get(ind.id);
                        const ddir =
                          diseaseState?.indicator_values[ind.id]?.direction ??
                          "unknown";
                        const state = eff?.state ?? "unchanged";
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
                                className={`cv-medicine-wf-dir cv-medicine-wf-dir--${ddir}`}
                              >
                                {ddir}
                              </span>
                            </td>
                            <td>
                              <span
                                className={`cv-medicine-wf-effect cv-medicine-wf-effect--${state}`}
                              >
                                {state}
                              </span>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>

            {/* Mechanism targets panel */}
            {medicineEffect && medicineEffect.mechanism_targets.length > 0 ? (
              <div className="cv-medicine-wf-targets">
                <div className="cv-medicine-wf-section-label">
                  <span>MECHANISM TARGETS</span>
                  <i />
                </div>
                <ul className="cv-medicine-wf-targets-list">
                  {medicineEffect.mechanism_targets.map((t) => (
                    <li key={t.target_id} className="cv-medicine-wf-target">
                      <div className="cv-medicine-wf-target-head">
                        <strong>{t.name}</strong>
                        {t.action_type ? (
                          <span className="cv-medicine-wf-target-action">
                            {t.action_type}
                          </span>
                        ) : null}
                      </div>
                      <div className="cv-medicine-wf-target-ids">
                        <span>{t.target_id}</span>
                        {t.uniprot_accession ? (
                          <span>{t.uniprot_accession}</span>
                        ) : null}
                      </div>
                    </li>
                  ))}
                </ul>
              </div>
            ) : null}

            {/* Evidence chain for selected function */}
            {selectedIndicator && selectedEffect ? (
              <div className="cv-medicine-wf-inspector">
                <div className="cv-medicine-wf-inspector-head">
                  <div className="cv-medicine-wf-inspector-kicker">
                    <span>MECHANISM</span>
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
                      className={`cv-medicine-wf-effect cv-medicine-wf-effect--${selectedEffect.state}`}
                    >
                      {selectedEffect.state}
                    </span>
                    <p>{selectedEffect.reason}</p>
                  </div>

                  {selectedEffect.medicine_chain.length > 0 ? (
                    <div className="cv-medicine-wf-inspector-section">
                      <div className="cv-medicine-wf-inspector-section-label">
                        MEDICINE CHAIN
                      </div>
                      <ul className="cv-medicine-wf-chain">
                        {selectedEffect.medicine_chain.map((c, i) => (
                          <li key={i} className="cv-medicine-wf-chain-item">
                            <div className="cv-medicine-wf-chain-node">
                              <span>MEDICINE</span>
                              <strong>{medicineEffect?.intervention_name}</strong>
                            </div>
                            <div className="cv-medicine-wf-chain-arrow">→</div>
                            <div className="cv-medicine-wf-chain-node">
                              <span>TARGET</span>
                              <strong>{c.target_name}</strong>
                              {c.action_type ? (
                                <em>{c.action_type}</em>
                              ) : null}
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

                  {selectedEffect.shared_top_levels &&
                  selectedEffect.shared_top_levels.length > 0 ? (
                    <div className="cv-medicine-wf-inspector-section">
                      <div className="cv-medicine-wf-inspector-section-label">
                        SHARED FUNCTIONAL AREA
                      </div>
                      <div className="cv-medicine-wf-inspector-top">
                        {selectedEffect.shared_top_levels.join(" · ")}
                      </div>
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
