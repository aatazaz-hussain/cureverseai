/**
 * CureVerseAI — Drug Development
 * Workflow 03 — Therapeutic Discovery
 * ScientificAvatar.
 *
 * Bottom-left guide indicator. Uses the avatar PNG with an
 * SVG ring overlay that animates while speaking.
 */

"use client";

import { useEffect, useState } from "react";

import { isSpeechAvailable } from "../voice";

export default function ScientificAvatar() {
  const [available, setAvailable] = useState<boolean | null>(
    null,
  );
  const [speaking, setSpeaking] = useState(false);

  useEffect(() => {
    setAvailable(isSpeechAvailable());
  }, []);

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

  if (available !== true) return null;

  return (
    <div
      className={
        "cv-thedisc-avatar" +
        (speaking ? " is-speaking" : "")
      }
      aria-hidden="true"
    >
      <div className="cv-thedisc-avatar-halo" />

      <div className="cv-thedisc-avatar-stage">
        <svg
          className="cv-thedisc-avatar-ring"
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

        <div className="cv-thedisc-avatar-frame">
          <img
            src="/drug-development/avatar.png"
            alt=""
            draggable={false}
          />
        </div>

        <div className="cv-thedisc-avatar-scan" />
      </div>

      <div className="cv-thedisc-avatar-label">
        <i />
        <span>
          {speaking ? "SPEAKING" : "SCIENTIFIC GUIDE"}
        </span>
      </div>
    </div>
  );
}
