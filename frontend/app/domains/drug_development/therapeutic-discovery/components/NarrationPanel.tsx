/**
 * CureVerseAI — Drug Development
 * Workflow 03 — Therapeutic Discovery
 * NarrationPanel.
 *
 * Renders the W03 narration segments as a scrollable
 * transcript. Each segment is tied to a node or edge.
 * Auto-advances when isPlaying is true. Speaks via browser
 * TTS when voiceEnabled.
 */

"use client";

import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
} from "react";

import type {
  NarrationSegment,
  TherapeuticDiscoveryResult,
} from "../types";

import {
  getNodeTypeMeta,
  getSupportClassMeta,
} from "./types";

import {
  useTDNarration,
  useTDActions,
} from "../state";

import {
  speak,
  stopSpeaking,
  isSpeechAvailable,
} from "../voice";

interface NarrationPanelProps {
  result: TherapeuticDiscoveryResult;
}

export default function NarrationPanel({
  result,
}: NarrationPanelProps) {
  const narration = useTDNarration();
  const actions = useTDActions();

  const segments = result.narration?.segments ?? [];
  const total = segments.length;

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

  // Speak and advance.
  useEffect(() => {
    if (!narration.isPlaying) return;
    if (narration.currentSegmentIndex < 0) return;
    if (narration.currentSegmentIndex >= total) return;

    const segment = segments[narration.currentSegmentIndex];
    if (!segment) return;

    // Select the target.
    if (segment.target_kind === "node") {
      if (segment.target_id.startsWith("compound:")) {
        const cid = segment.target_id.replace("compound:", "");
        actions.select({ kind: "candidate", compound_id: cid });
      } else {
        actions.select({
          kind: "node",
          node_id: segment.target_id,
        });
      }
    } else {
      actions.select({
        kind: "edge",
        edge_key: segment.target_id,
      });
    }

    let cancelled = false;

    if (narration.voiceEnabled && isSpeechAvailable()) {
      speak(segment.text, {
        onEnd: () => {
          if (cancelled) return;
          actions.nextSegment(total);
        },
      });
    } else {
      const timer = setTimeout(() => {
        if (cancelled) return;
        actions.nextSegment(total);
      }, 5000);
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
    (segment: NarrationSegment) => {
      if (segment.target_kind === "node") {
        if (segment.target_id.startsWith("compound:")) {
          const cid = segment.target_id.replace("compound:", "");
          actions.select({
            kind: "candidate",
            compound_id: cid,
          });
        } else {
          actions.select({
            kind: "node",
            node_id: segment.target_id,
          });
        }
      } else {
        actions.select({
          kind: "edge",
          edge_key: segment.target_id,
        });
      }
    },
    [actions],
  );

  if (!total) {
    return (
      <div className="cv-thedisc-narration cv-thedisc-narration-empty">
        <p>No narration segments were returned.</p>
      </div>
    );
  }

  return (
    <div className="cv-thedisc-narration">
      <header className="cv-thedisc-narration-head">
        <div className="cv-thedisc-narration-head-left">
          <span className="cv-thedisc-narration-eyebrow">
            SCIENTIFIC GUIDE
          </span>
          <strong>
            {total} segment{total === 1 ? "" : "s"}
          </strong>
        </div>

        <div className="cv-thedisc-narration-controls">
          <button
            type="button"
            className="cv-thedisc-narration-btn"
            onClick={handlePrev}
            disabled={narration.currentSegmentIndex <= 0}
            aria-label="Previous segment"
          >
            ‹
          </button>

          <button
            type="button"
            className="cv-thedisc-narration-btn cv-thedisc-narration-btn-play"
            onClick={handleStop}
            aria-label="Stop narration"
          >
            ■
          </button>

          <button
            type="button"
            className="cv-thedisc-narration-btn"
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
              "cv-thedisc-narration-btn cv-thedisc-narration-btn-voice" +
              (narration.voiceEnabled ? " is-on" : "")
            }
            onClick={handleToggleVoice}
            aria-label="Toggle voice"
          >
            {narration.voiceEnabled ? "♪" : "♪̸"}
          </button>
        </div>
      </header>

      <div
        className="cv-thedisc-narration-list"
        ref={containerRef}
      >
        <ol>
          {segments.map((seg, i) => {
            const isActive =
              i === narration.currentSegmentIndex;

            let accent = "#6ee7f2";
            if (seg.support_class) {
              accent =
                getSupportClassMeta(seg.support_class).accent;
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
                  "cv-thedisc-narration-item" +
                  (isActive ? " is-active" : "")
                }
                style={{ ["--seg-accent" as string]: accent }}
              >
                <div className="cv-thedisc-narration-item-head">
                  <span className="cv-thedisc-narration-item-num">
                    {String(i + 1).padStart(2, "0")}
                  </span>
                  <span className="cv-thedisc-narration-item-kind">
                    {seg.target_kind === "node"
                      ? "node"
                      : "relationship"}
                  </span>
                  <div className="cv-thedisc-narration-item-actions">
                    <button
                      type="button"
                      className="cv-thedisc-narration-item-btn"
                      onClick={() => handlePlay(i)}
                    >
                      ▶
                    </button>
                    <button
                      type="button"
                      className="cv-thedisc-narration-item-btn"
                      onClick={() => handleJump(seg)}
                    >
                      →
                    </button>
                  </div>
                </div>
                <p className="cv-thedisc-narration-item-text">
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
