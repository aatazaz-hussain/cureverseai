/**
 * CureVerseAI — Drug Development
 * Workflow 02 — Reverse Disease Engineering
 * ScientificAvatar.
 *
 * Bottom-left guide indicator. Uses the avatar PNG as the
 * visual, with an SVG ring overlay that animates while
 * speech is active.
 *
 * Speech availability is checked in an effect (not during
 * render) to avoid an SSR/client hydration mismatch.
 */

"use client";

import { useEffect, useState } from "react";

import { isSpeechAvailable } from "../voice";

export default function ScientificAvatar() {
  // null = not yet determined (server render + first paint)
  // true/false = resolved on client after mount
  const [available, setAvailable] = useState<boolean | null>(null);
  const [speaking, setSpeaking] = useState(false);

  // Resolve availability after mount.
  useEffect(() => {
    setAvailable(isSpeechAvailable());
  }, []);

  // Poll the speech state while mounted and available.
  useEffect(() => {
    if (available !== true) return;

    const tick = () => {
      try {
        setSpeaking(window.speechSynthesis.speaking);
      } catch {
        setSpeaking(false);
      }
    };

    tick();
    const id = setInterval(tick, 180);
    return () => clearInterval(id);
  }, [available]);

  // Do not render during SSR or before the client knows
  // whether speech is available. This keeps the server
  // and client markup identical for the first paint.
  if (available !== true) {
    return null;
  }

  return (
    <div
      className={
        "cv-revdis-avatar" +
        (speaking ? " is-speaking" : "")
      }
      aria-hidden="true"
    >
      <div className="cv-revdis-avatar-halo" />

      <div className="cv-revdis-avatar-stage">
        <svg
          className="cv-revdis-avatar-ring"
          viewBox="0 0 100 100"
          xmlns="http://www.w3.org/2000/svg"
        >
          <circle
            cx="50"
            cy="50"
            r="47"
            fill="none"
            stroke="rgba(238,233,225,0.18)"
            strokeWidth="1"
            strokeDasharray="3 5"
          />
          <circle
            cx="50"
            cy="50"
            r="44"
            fill="none"
            stroke="rgba(224,82,90,0.14)"
            strokeWidth="0.5"
          />
        </svg>

        <div className="cv-revdis-avatar-frame">
          <img
            src="/drug-development/avatar.png"
            alt=""
            draggable={false}
          />
        </div>

        <div className="cv-revdis-avatar-scan" />
      </div>

      <div className="cv-revdis-avatar-label">
        <i />
        <span>
          {speaking ? "SPEAKING" : "SCIENTIFIC GUIDE"}
        </span>
      </div>
    </div>
  );
}
