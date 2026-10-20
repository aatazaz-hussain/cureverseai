"use client";

/**
 * CureVerseAI — Medicine domain
 * Intervention selector.
 *
 * Free-text or canonical-id intervention input. The resolver
 * lives on the AI Engine; this component only manages input
 * and displays the resolved identity returned by the backend.
 */

import { useState } from "react";

interface Props {
  value: string;
  onChange: (value: string) => void;
  label: string;
  placeholder?: string;
  disabled?: boolean;
  hint?: string;
}

export default function InterventionSelector({
  value,
  onChange,
  label,
  placeholder = "e.g. montelukast or chembl:CHEMBL787",
  disabled,
  hint,
}: Props) {
  const [focus, setFocus] = useState(false);

  return (
    <div className="cv-medicine-wf-panel cv-medicine-wf-intervention">
      <div className="cv-medicine-wf-panel-header">
        <h3 className="cv-medicine-wf-panel-title">{label}</h3>
      </div>

      <input
        className="cv-medicine-wf-input"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        onFocus={() => setFocus(true)}
        onBlur={() => setFocus(false)}
        placeholder={placeholder}
        disabled={disabled}
        aria-label={label}
      />

      {focus && hint ? (
        <div className="cv-medicine-wf-search-hint">{hint}</div>
      ) : null}
    </div>
  );
}
