/**
 * CureVerseAI — Drug Development
 * Workflow 02 — Reverse Disease Engineering
 * NarrationPanel.
 *
 * Renders the W02 explanation segments as a scrollable
 * transcript. Each segment is tied to a specific graph
 * node or edge.
 *
 * Responsibilities:
 *   - List all explanation segments
 *   - Highlight the currently playing segment
 *   - Synchronise with the graph (select the target on play)
 *   - Offer per-segment "Jump to graph" action
 *   - Auto-advance when isPlaying is true
 *   - Speak segments via browser TTS when voiceEnabled
 *
 * The panel does not render an avatar. The spec calls for a
 * scientific guide, not a chatbot; a transcript is the
 * guide.
 */

"use client";

import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
} from "react";

import type {
  Explanation,
  ReverseDiseaseResult,
} from "../types";

import {
  getNodeTypeMeta,
  getSupportClassMeta,
} from "./types";

import {
  useRDENarration,
  useRDEActions,
} from "../state";

import { speak, stopSpeaking, isSpeechAvailable } from "../voice";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface NarrationPanelProps {
  result: ReverseDiseaseResult;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function NarrationPanel({
  result,
}: NarrationPanelProps) {
  const narration = useRDENarration();
  const actions = useRDEActions();

  const segments = result.explanations ?? [];
  const total = segments.length;

  // ---- Scroll-to-active-ref -----------------------------
  const activeRef = useRef<HTMLLIElement | null>(null);
  const containerRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    if (
      narration.currentSegmentIndex < 0 ||
      !activeRef.current ||
      !containerRef.current
    ) {
      return;
    }
    activeRef.current.scrollIntoView({
      behavior: "smooth",
      block: "nearest",
    });
  }, [narration.currentSegmentIndex]);

  // ---- TTS integration ----------------------------------
  // When the current segment changes and voice is enabled
  // and narration is playing, speak it and advance when
  // finished.
  useEffect(() => {
    if (!narration.isPlaying) return;
    if (narration.currentSegmentIndex < 0) return;
    if (narration.currentSegmentIndex >= total) return;

    const segment = segments[narration.currentSegmentIndex];
    if (!segment) return;

    // Select the target in the graph.
    if (segment.target_kind === "node") {
      actions.select({ kind: "node", node_id: segment.target_id });
    } else {
      actions.select({ kind: "edge", edge_key: segment.target_id });
    }

    // Speak, if voice is enabled and TTS is available.
    let cancelled = false;

    if (narration.voiceEnabled && isSpeechAvailable()) {
      speak(segment.text, {
        onEnd: () => {
          if (cancelled) return;
          actions.nextSegment(total);
        },
      });
    } else {
      // Text-only mode: advance after a short pause.
      const timer = setTimeout(() => {
        if (cancelled) return;
        actions.nextSegment(total);
      }, 4500);
      return () => {
        cancelled = true;
        clearTimeout(timer);
      };
    }

    return () => {
      cancelled = true;
      stopSpeaking();
    };
  }, [
    narration.currentSegmentIndex,
    narration.isPlaying,
    narration.voiceEnabled,
    segments,
    total,
    actions,
  ]);

  // ---- Handlers -----------------------------------------
  const handlePlay = useCallback(
    (index: number) => {
      actions.playSegment(index);
    },
    [actions],
  );

  const handleStop = useCallback(() => {
    stopSpeaking();
    actions.stopNarration();
  }, [actions]);

  const handlePrev = useCallback(() => {
    actions.prevSegment();
  }, [actions]);

  const handleNext = useCallback(() => {
    actions.nextSegment(total);
  }, [actions, total]);

  const handleToggleVoice = useCallback(() => {
    actions.toggleVoice();
  }, [actions]);

  const handleJump = useCallback(
    (segment: Explanation) => {
      if (segment.target_kind === "node") {
        actions.select({ kind: "node", node_id: segment.target_id });
      } else {
        actions.select({ kind: "edge", edge_key: segment.target_id });
      }
    },
    [actions],
  );

  // ---- Empty state --------------------------------------
  if (!total) {
    return (
      <div className="cv-revdis-narration cv-revdis-narration-empty">
        <p>No narration segments were returned.</p>
      </div>
    );
  }

  // ---- Render -------------------------------------------
  return (
    <div className="cv-revdis-narration">
      <header className="cv-revdis-narration-head">
        <div className="cv-revdis-narration-head-left">
          <span className="cv-revdis-narration-eyebrow">
            SCIENTIFIC GUIDE
          </span>
          <strong>
            {total} segment{total === 1 ? "" : "s"}
          </strong>
        </div>

        <div className="cv-revdis-narration-controls">
          <button
            type="button"
            className="cv-revdis-narration-btn"
            onClick={handlePrev}
            disabled={narration.currentSegmentIndex <= 0}
            aria-label="Previous segment"
          >
            ‹
          </button>

          <button
            type="button"
            className="cv-revdis-narration-btn cv-revdis-narration-btn-play"
            onClick={handleStop}
            aria-label="Stop narration"
          >
            ■
          </button>

          <button
            type="button"
            className="cv-revdis-narration-btn"
            onClick={handleNext}
            disabled={
              narration.currentSegmentIndex >= total - 1
            }
            aria-label="Next segment"
          >
            ›
          </button>

          <button
            type="button"
            className={
              "cv-revdis-narration-btn cv-revdis-narration-btn-voice" +
              (narration.voiceEnabled ? " is-on" : "")
            }
            onClick={handleToggleVoice}
            aria-label="Toggle voice"
            title={
              isSpeechAvailable()
                ? "Voice on/off"
                : "Voice unavailable in this browser"
            }
          >
            {narration.voiceEnabled ? "♪" : "♪̸"}
          </button>
        </div>
      </header>

      <div
        className="cv-revdis-narration-list"
        ref={containerRef}
      >
        <ol>
          {segments.map((seg, i) => {
            const isActive =
              i === narration.currentSegmentIndex;

            // Color hint from metadata or support class.
            let accent = "#6ee7f2";
            if (seg.target_kind === "edge" && seg.support_class) {
              accent = getSupportClassMeta(seg.support_class).accent;
            } else if (seg.metadata?.node_type) {
              accent = getNodeTypeMeta(
                String(seg.metadata.node_type),
              ).accent;
            }

            return (
              <li
                key={seg.explanation_id}
                ref={isActive ? activeRef : null}
                className={
                  "cv-revdis-narration-item" +
                  (isActive ? " is-active" : "")
                }
                style={{ ["--seg-accent" as string]: accent }}
              >
                <div className="cv-revdis-narration-item-head">
                  <span className="cv-revdis-narration-item-num">
                    {String(i + 1).padStart(2, "0")}
                  </span>
                  <span className="cv-revdis-narration-item-kind">
                    {seg.target_kind === "node"
                      ? "node"
                      : "relationship"}
                  </span>
                  <div className="cv-revdis-narration-item-actions">
                    <button
                      type="button"
                      className="cv-revdis-narration-item-btn"
                      onClick={() => handlePlay(i)}
                    >
                      ▶
                    </button>
                    <button
                      type="button"
                      className="cv-revdis-narration-item-btn"
                      onClick={() => handleJump(seg)}
                    >
                      →
                    </button>
                  </div>
                </div>
                <p className="cv-revdis-narration-item-text">
                  {seg.text}
                </p>
              </li>
            );
          })}
        </ol>
      </div>
    </div>
  );
}
