"use client";

/**
 * CureVerseAI — Medicine domain
 * Uncertainty badge.
 *
 * Small chip: low / medium / high / unknown. The tooltip is
 * populated from the backend's uncertainty.reasons list.
 */

import type { Uncertainty, UncertaintyLevel } from "../types";

interface Props {
  uncertainty: Uncertainty | null;
  compact?: boolean;
}

const LEVEL_LABELS: Record<UncertaintyLevel, string> = {
  low: "Low",
  medium: "Medium",
  high: "High",
  unknown: "Unknown",
};

export default function UncertaintyBadge({
  uncertainty,
  compact,
}: Props) {
  if (!uncertainty) {
    return (
      <span
        className="cv-medicine-wf-chip cv-medicine-wf-unc cv-medicine-wf-unc--unknown"
        title="No uncertainty information was provided."
      >
        {compact ? "?" : "Unknown"}
      </span>
    );
  }

  const tooltip =
    uncertainty.reasons.length > 0
      ? uncertainty.reasons.join(" • ")
      : "No explanation provided.";

  return (
    <span
      className={
        "cv-medicine-wf-chip cv-medicine-wf-unc cv-medicine-wf-unc--" +
        uncertainty.level
      }
      title={tooltip}
    >
      {compact ? uncertainty.level.charAt(0).toUpperCase() : LEVEL_LABELS[uncertainty.level]}
    </span>
  );
}
