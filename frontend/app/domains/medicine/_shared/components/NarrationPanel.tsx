"use client";

/**
 * CureVerseAI — Medicine domain
 * Narration panel.
 *
 * Copied and adapted from the RDE NarrationPanel. Provides a
 * transcript of narration segments and a voice toggle.
 *
 * The panel is agnostic to where the segments came from; the
 * workflow supplies them.
 */

import { useEffect, useState } from "react";

import {
  getActiveVoiceName,
  isSpeechAvailable,
  speak,
  stopSpeaking,
} from "../voice";

export interface NarrationSegment {
  id: string;
  text: string;
}

interface Props {
  segments: NarrationSegment[];
  currentIndex: number;
  onIndexChange: (index: number) => void;
  voiceEnabled: boolean;
  onToggleVoice: () => void;
  isPlaying: boolean;
  onPlay: () => void;
  onPause: () => void;
}

export default function NarrationPanel({
  segments,
  currentIndex,
  onIndexChange,
  voiceEnabled,
  onToggleVoice,
  isPlaying,
  onPlay,
  onPause,
}: Props) {
  const [speechAvailable, setSpeechAvailable] = useState(false);
  const [activeVoice, setActiveVoice] = useState<string | null>(null);

  useEffect(() => {
    setSpeechAvailable(isSpeechAvailable());
    setActiveVoice(getActiveVoiceName());
  }, []);

  useEffect(() => {
    if (!voiceEnabled || !isPlaying) return;
    const segment = segments[currentIndex];
    if (!segment) return;
    if (!speechAvailable) return;

    speak(segment.text);

    return () => {
      stopSpeaking();
    };
  }, [currentIndex, isPlaying, voiceEnabled, segments, speechAvailable]);

  if (!segments || segments.length === 0) {
    return (
      <div className="cv-medicine-wf-panel">
        <div className="cv-medicine-wf-panel-header">
          <h3 className="cv-medicine-wf-panel-title">Narration</h3>
        </div>
        <p className="cv-medicine-wf-subtitle">
          No narration segments were produced for this result.
        </p>
      </div>
    );
  }

  return (
    <div className="cv-medicine-wf-panel cv-medicine-wf-narration">
      <div className="cv-medicine-wf-panel-header">
        <h3 className="cv-medicine-wf-panel-title">Narration</h3>
        <div className="cv-medicine-wf-narration-controls">
          <button
            type="button"
            className="cv-medicine-wf-btn cv-medicine-wf-btn--ghost"
            onClick={isPlaying ? onPause : onPlay}
          >
            {isPlaying ? "Pause" : "Play"}
          </button>
          <button
            type="button"
            className="cv-medicine-wf-btn cv-medicine-wf-btn--ghost"
            onClick={onToggleVoice}
            aria-pressed={voiceEnabled}
          >
            {voiceEnabled ? "Voice on" : "Voice off"}
          </button>
        </div>
      </div>

      <div className="cv-medicine-wf-narration-body">
        {segments.map((segment, index) => (
          <button
            key={segment.id}
            type="button"
            className={
              "cv-medicine-wf-narration-segment" +
              (index === currentIndex
                ? " cv-medicine-wf-narration-segment--active"
                : "")
            }
            onClick={() => onIndexChange(index)}
          >
            <span className="cv-medicine-wf-narration-index">
              {String(index + 1).padStart(2, "0")}
            </span>
            <span className="cv-medicine-wf-narration-text">
              {segment.text}
            </span>
          </button>
        ))}
      </div>

      {speechAvailable && activeVoice ? (
        <div className="cv-medicine-wf-narration-footnote">
          Voice: {activeVoice}
        </div>
      ) : null}
    </div>
  );
}
