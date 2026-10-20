/**
 * CureVerseAI — Drug Development
 * Workflow 02 — Reverse Disease Engineering
 * InputRegion.
 *
 * Disease input form + loading indicator.
 *
 * Differs from W01's input by one control: a small ChEMBL
 * toggle. The toggle is honest — the UI explains that
 * ChEMBL adds ~30s per run.
 *
 * When the previous request completes, the input keeps
 * the last query so the user can edit and re-run.
 */

"use client";

import {
  FormEvent,
  useCallback,
  useEffect,
  useState,
} from "react";

import { useRDEStatus, useRDEActions } from "../state";

export default function InputRegion() {
  const status = useRDEStatus();
  const actions = useRDEActions();

  const [value, setValue] = useState("");
  const [fetchChembl, setFetchChembl] = useState(false);

  const loading = status.kind === "loading";

  // Restore the last query after a request finishes.
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

      void actions.analyze(trimmed, fetchChembl);
    },
    [actions, fetchChembl, loading, value],
  );

  return (
    <section className="cv-revdis-input">
      <form
        className="cv-revdis-input-form"
        onSubmit={handleSubmit}
      >
        <div className="cv-revdis-input-field">
          <label htmlFor="cv-revdis-disease">
            DISEASE QUERY
          </label>
          <input
            id="cv-revdis-disease"
            className="cv-revdis-input-control"
            type="text"
            placeholder="e.g. Asthma, Alzheimer's disease, Type 2 diabetes…"
            value={value}
            onChange={(e) => setValue(e.target.value)}
            disabled={loading}
            autoComplete="off"
            spellCheck={false}
          />
        </div>

        <div className="cv-revdis-input-options">
          <label className="cv-revdis-input-check">
            <input
              type="checkbox"
              checked={fetchChembl}
              onChange={(e) =>
                setFetchChembl(e.target.checked)
              }
              disabled={loading}
            />
            <span>
              Include ChEMBL bioactivity evidence
              <small>adds ~30 seconds</small>
            </span>
          </label>
        </div>

        <button
          className="cv-revdis-input-submit"
          type="submit"
          disabled={loading || !value.trim()}
        >
          {loading ? "Investigating…" : "Investigate"}
        </button>
      </form>

      <div className="cv-revdis-input-hint">
        Full pipeline: 2–5s warm, 20–40s cold. ChEMBL adds
        ~30s.
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
// Loading indicator
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

  return (
    <div className="cv-revdis-loading">
      <div className="cv-revdis-loading-spinner" />

      <div className="cv-revdis-loading-copy">
        <strong>Reconstructing mechanism</strong>
        <span>
          Resolving <em>{query}</em>, retrieving phenotypes,
          mechanisms, genes, and pathways.
        </span>
      </div>

      <div className="cv-revdis-loading-timer">
        {elapsed}s
      </div>
    </div>
  );
}
