"use client";

/**
 * CureVerseAI — Medicine domain
 * Disease search.
 *
 * Free-text disease input plus a list of curated suggestions
 * fetched from the backend. Suggestions come from the backend;
 * they are never hardcoded here.
 */

import { useState } from "react";

import type { CuratedPair } from "../types";

interface Props {
  value: string;
  onChange: (value: string) => void;
  onSubmit: () => void;
  disabled?: boolean;
  curated: CuratedPair[];
  curatedLoading?: boolean;
  label?: string;
  placeholder?: string;
}

export default function DiseaseSearch({
  value,
  onChange,
  onSubmit,
  disabled,
  curated,
  curatedLoading,
  label = "Disease",
  placeholder = "e.g. asthma",
}: Props) {
  const [focus, setFocus] = useState(false);

  return (
    <div className="cv-medicine-wf-panel cv-medicine-wf-search">
      <div className="cv-medicine-wf-panel-header">
        <h3 className="cv-medicine-wf-panel-title">{label}</h3>
      </div>

      <div className="cv-medicine-wf-search-row">
        <input
          className="cv-medicine-wf-input"
          value={value}
          onChange={(e) => onChange(e.target.value)}
          onFocus={() => setFocus(true)}
          onBlur={() => setFocus(false)}
          onKeyDown={(e) => {
            if (e.key === "Enter" && !disabled && value.trim()) {
              onSubmit();
            }
          }}
          placeholder={placeholder}
          disabled={disabled}
          aria-label={label}
        />
        <button
          type="button"
          className="cv-medicine-wf-btn cv-medicine-wf-btn--primary"
          onClick={onSubmit}
          disabled={disabled || !value.trim()}
        >
          Simulate
        </button>
      </div>

      <div className="cv-medicine-wf-search-curated">
        <span className="cv-medicine-wf-search-curated-label">
          {curatedLoading
            ? "Loading curated set…"
            : curated.length > 0
            ? "Curated:"
            : "No curated diseases available."}
        </span>

        {curated.map((pair) => (
          <button
            key={pair.disease_id}
            type="button"
            className="cv-medicine-wf-chip cv-medicine-wf-chip--suggestion"
            onClick={() => {
              onChange(pair.disease_name);
            }}
            disabled={disabled}
            title={`Curated cell context: ${pair.cell_context_name}`}
          >
            {pair.disease_name}
          </button>
        ))}
      </div>

      {focus ? (
        <div className="cv-medicine-wf-search-hint">
          Only curated diseases can be simulated end to end. Other
          diseases will return an honest partial result.
        </div>
      ) : null}
    </div>
  );
}
