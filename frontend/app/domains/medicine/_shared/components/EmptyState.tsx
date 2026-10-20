"use client";

/**
 * CureVerseAI — Medicine domain
 * Empty / loading / error states.
 */

import type { ReactNode } from "react";

interface Props {
  kind: "idle" | "loading" | "error" | "empty";
  title?: string;
  message?: string;
  action?: ReactNode;
}

const DEFAULT_TITLES: Record<Props["kind"], string> = {
  idle: "Ready",
  loading: "Simulating…",
  error: "Simulation error",
  empty: "No data",
};

const DEFAULT_MESSAGES: Record<Props["kind"], string> = {
  idle: "Enter a value above and start the simulation.",
  loading: "Contacting the AI Engine. This can take up to a minute.",
  error: "The simulation could not be completed.",
  empty: "The simulation returned no content for this view.",
};

export default function EmptyState({
  kind,
  title,
  message,
  action,
}: Props) {
  return (
    <div className={`cv-medicine-wf-empty cv-medicine-wf-empty--${kind}`}>
      <div className="cv-medicine-wf-empty-inner">
        <div className="cv-medicine-wf-empty-title">
          {title ?? DEFAULT_TITLES[kind]}
        </div>
        <div className="cv-medicine-wf-empty-msg">
          {message ?? DEFAULT_MESSAGES[kind]}
        </div>
        {action ? (
          <div className="cv-medicine-wf-empty-action">{action}</div>
        ) : null}
      </div>
    </div>
  );
}
