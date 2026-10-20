/**
 * CureVerseAI — Drug Development
 * Workflow 03 — Therapeutic Discovery
 * InputRegion.
 *
 * Disease input + optional mechanism/target handoff.
 *
 * The two handoff fields are hidden behind a small
 * "Advanced" toggle so the default experience is a single
 * disease query, matching W01/W02. Users arriving from
 * Workflow 02 can paste the mechanism_id there.
 */

"use client";

import {
  FormEvent,
  useCallback,
  useEffect,
  useState,
} from "react";

import { useTDStatus, useTDActions } from "../state";

export default function InputRegion() {
  const status = useTDStatus();
  const actions = useTDActions();

  const [value, setValue] = useState("");
  const [mechanismId, setMechanismId] = useState("");
  const [targetId, setTargetId] = useState("");
  const [showAdvanced, setShowAdvanced] = useState(false);

  const loading = status.kind === "loading";

  // Restore last query after a request completes.
  useEffect(() => {
    if (status.kind === "loaded" || status.kind === "error") {
      setValue(status.query);
    }
  }, [status]);

  const handleSubmit = useCallback(
    (e: FormEvent<HTMLFormElement>) => {
      e.preventDefault();
      if (loading) return;

      const trimmed = value.trim();
      if (!trimmed) return;

      void actions.analyze(
        trimmed,
        mechanismId.trim() || null,
        targetId.trim() || null,
      );
    },
    [actions, loading, value, mechanismId, targetId],
  );

  return (
    <section className="cv-thedisc-input">
      <form
        className="cv-thedisc-input-form"
        onSubmit={handleSubmit}
      >
        <div className="cv-thedisc-input-field">
          <label htmlFor="cv-thedisc-disease">
            DISEASE QUERY
          </label>
          <input
            id="cv-thedisc-disease"
            className="cv-thedisc-input-control"
            type="text"
            placeholder="e.g. Asthma, Parkinson disease, Breast cancer…"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            disabled={loading}
            autoComplete="off"
            spellCheck={false}
          />
        </div>

        <button
          className="cv-thedisc-input-submit"
          type="submit"
          disabled={loading || !value.trim()}
        >
          {loading ? "Investigating…" : "Investigate"}
        </button>
      </form>

      {/* Advanced: W02 handoff fields */}
      <div className="cv-thedisc-input-advanced">
        <button
          type="button"
          className="cv-thedisc-input-advanced-toggle"
          onClick={() => setShowAdvanced((v) => !v)}
          aria-expanded={showAdvanced}
        >
          <i />
          <span>
            {showAdvanced
              ? "Hide advanced handoff"
              : "Advanced: continue from Workflow 02"}
          </span>
        </button>

        {showAdvanced ? (
          <div className="cv-thedisc-input-advanced-body">
            <div className="cv-thedisc-input-field-small">
              <label htmlFor="cv-thedisc-mechanism">
                MECHANISM ID (optional)
              </label>
              <input
                id="cv-thedisc-mechanism"
                className="cv-thedisc-input-control-small"
                type="text"
                placeholder="e.g. pathway:R-HSA-6785807"
                value={mechanismId}
                onChange={(e) =>
                  setMechanismId(e.target.value)
                }
                disabled={loading}
                autoComplete="off"
                spellCheck={false}
              />
            </div>

            <div className="cv-thedisc-input-field-small">
              <label htmlFor="cv-thedisc-target">
                TARGET ID (optional)
              </label>
              <input
                id="cv-thedisc-target"
                className="cv-thedisc-input-control-small"
                type="text"
                placeholder="e.g. target:IL4R"
                value={targetId}
                onChange={(e) => setTargetId(e.target.value)}
                disabled={loading}
                autoComplete="off"
                spellCheck={false}
              />
            </div>
          </div>
        ) : null}
      </div>

      <div className="cv-thedisc-input-hint">
        First run for a disease: 60–150s. Cached runs: 15–40s.
      </div>

      {loading ? (
        <LoadingBlock
          startedAt={status.startedAt}
          query={status.query}
        />
      ) : null}
    </section>
  );
}

// ---------------------------------------------------------------------------
// Loading
// ---------------------------------------------------------------------------

function LoadingBlock({
  startedAt,
  query,
}: {
  startedAt: number;
  query: string;
}) {
  const [elapsed, setElapsed] = useState(0);

  useEffect(() => {
    const tick = () =>
      setElapsed(Math.floor((Date.now() - startedAt) / 1000));
    tick();
    const id = setInterval(tick, 1000);
    return () => clearInterval(id);
  }, [startedAt]);

  const slow = elapsed >= 45;

  return (
    <div
      className={
        "cv-thedisc-loading" + (slow ? " is-slow" : "")
      }
    >
      <div className="cv-thedisc-loading-spinner" />

      <div className="cv-thedisc-loading-copy">
        <strong>Running therapeutic investigation</strong>
        <span>
          Resolving <em>{query}</em>, identifying targets,
          retrieving compounds from ChEMBL, and assembling
          the mechanism-of-action graph.
        </span>
        {slow ? (
          <span className="cv-thedisc-loading-note">
            Still working. First runs for a new disease query
            ChEMBL for each candidate target and can take up
            to 2–3 minutes.
          </span>
        ) : null}
      </div>

      <div className="cv-thedisc-loading-timer">{elapsed}s</div>
    </div>
  );
}
