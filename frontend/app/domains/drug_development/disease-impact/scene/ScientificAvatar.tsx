/**
 * CureVerseAI — Disease → Biological Impact
 * Scientific avatar.
 *
 * A 2D scientist character rendered bottom-left of the
 * scene. She animates (breathing, head bob, glow) while
 * the browser is speaking a narration phrase.
 *
 * Speaking state:
 *
 *   The parent scene calls `triggerSpeak(text)` when the
 *   journey changes level or a bubble is clicked. The
 *   avatar then:
 *     1. Plays the voice via voice.ts
 *     2. Shows a speaking indicator for the duration of
 *        the utterance
 *     3. Shows the narration text in a caption strip
 *
 * The avatar does not generate text. It only renders
 * what the parent passes in.
 */

"use client";

import {
  useCallback,
  useEffect,
  useRef,
  useState,
} from "react";

import { primeVoices, speak, stop } from "./voice";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface ScientificAvatarProps {
  /** Text to speak. Changes when the parent wants a new phrase. */
  narrationText: string | null;
  /**
   * Called when the speaking state changes so the parent
   * can coordinate other UI (e.g. pause animations).
   */
  onSpeakingChange?: (speaking: boolean) => void;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function ScientificAvatar({
  narrationText,
  onSpeakingChange,
}: ScientificAvatarProps) {
  const [speaking, setSpeaking] = useState(false);
  const [muted, setMutedState] = useState(false);

  const utteranceEndRef = useRef<number | null>(null);

  // ---- Prime voice list on mount --------------------------
  useEffect(() => {
    primeVoices();
  }, []);

  // ---- Speak whenever narrationText changes ---------------
  useEffect(() => {
    if (!narrationText) return;

    // Speak the phrase.
    speak(narrationText);

    // Estimate duration: ~350ms per word, min 900ms.
    const words = narrationText.trim().split(/\s+/).length;
    const durationMs = Math.max(
      900,
      words * 350,
    );

    setSpeaking(true);
    onSpeakingChange?.(true);

    // Clear any previous timer.
    if (utteranceEndRef.current !== null) {
      window.clearTimeout(utteranceEndRef.current);
    }

    utteranceEndRef.current = window.setTimeout(() => {
      setSpeaking(false);
      onSpeakingChange?.(false);
      utteranceEndRef.current = null;
    }, durationMs);

    return () => {
      if (utteranceEndRef.current !== null) {
        window.clearTimeout(utteranceEndRef.current);
        utteranceEndRef.current = null;
      }
    };
  }, [narrationText, onSpeakingChange]);

  // ---- Stop speech on unmount -----------------------------
  useEffect(() => {
    return () => {
      stop();
      if (utteranceEndRef.current !== null) {
        window.clearTimeout(utteranceEndRef.current);
      }
    };
  }, []);

  // ---- Mute toggle ----------------------------------------
  const handleToggleMute = useCallback(() => {
    setMutedState((prev) => {
      const next = !prev;
      if (next) {
        stop();
        setSpeaking(false);
        onSpeakingChange?.(false);
      }
      // Update the voice wrapper's mute state.
      // Imported lazily to avoid a circular dependency.
      import("./voice").then((mod) => mod.setMuted(next));
      return next;
    });
  }, [onSpeakingChange]);

  return (
    <div className="cv-dia-avatar">
      <div
        className={
          "cv-dia-avatar-figure" +
          (speaking ? " cv-dia-avatar-speaking" : "")
        }
      >
        <div className="cv-dia-avatar-glow" />
        <img
          src="/drug-development/avatar.png"
          alt="CureVerseAI scientific guide"
          draggable={false}
        />
        {/* Speaking waveform */}
        <div className="cv-dia-avatar-wave" aria-hidden="true">
          <span />
          <span />
          <span />
          <span />
          <span />
        </div>
      </div>

      <button
        type="button"
        className="cv-dia-avatar-mute"
        onClick={handleToggleMute}
        aria-label={muted ? "Unmute guide" : "Mute guide"}
        title={muted ? "Unmute guide" : "Mute guide"}
      >
        {muted ? "🔇" : "🔊"}
      </button>
    </div>
  );
}
