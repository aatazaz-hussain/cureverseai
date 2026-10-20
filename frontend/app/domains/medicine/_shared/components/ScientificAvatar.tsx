"use client";

/**
 * CureVerseAI — Medicine domain
 * Scientific avatar.
 *
 * Copied from
 * frontend/app/domains/drug_development/reverse-disease-engineering/components/ScientificAvatar.tsx
 * with the class namespace adjusted to cv-medicine-wf-*.
 * Behaviour is intentionally identical.
 */

import { useEffect } from "react";

interface Props {
  speaking: boolean;
  caption?: string;
}

export default function ScientificAvatar({ speaking, caption }: Props) {
  // Presence-only component; the speaking flag drives the
  // animated ring via CSS. No behaviour beyond that.

  useEffect(() => {
    // reserved for future per-frame animation if needed
  }, [speaking]);

  return (
    <div
      className={
        "cv-medicine-wf-avatar" +
        (speaking ? " cv-medicine-wf-avatar--speaking" : "")
      }
      aria-hidden="true"
    >
      <div className="cv-medicine-wf-avatar-ring" />
      <div className="cv-medicine-wf-avatar-core">
        <span>CV</span>
      </div>
      {caption ? (
        <div className="cv-medicine-wf-avatar-caption">{caption}</div>
      ) : null}
    </div>
  );
}
