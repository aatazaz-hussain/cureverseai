/**
 * CureVerseAI — Drug Development
 * Workflow 03 — Therapeutic Discovery
 * Inspector.
 *
 * Unified right-side panel. Renders one of:
 *   - empty state (nothing selected)
 *   - candidate inspector (delegates to CompoundDetail)
 *   - node inspector (target / pathway / mechanism / disease)
 *   - edge inspector
 *
 * Also triggers browser TTS on selection so the guide
 * narrates what the user clicked.
 */

"use client";

import { useEffect, useMemo, useRef } from "react";

import type {
  ImpactNode,
  Relationship,
  TherapeuticDiscoveryResult,
} from "../types";

import {
  getNodeTypeMeta,
  getSupportClassMeta,
} from "./types";

import {
  useTDStatus,
  useTDSelection,
  useTDNarration,
  useTDActions,
} from "../state";

import { speak, stopSpeaking, isSpeechAvailable } from "../voice";

import CompoundDetail from "./CompoundDetail";

export default function Inspector() {
  const status = useTDStatus();
  const selection = useTDSelection();
  const narration = useTDNarration();
  const actions = useTDActions();

  const lastSpokenRef = useRef<string | null>(null);

  // ---- Resolve the current selection to a concrete entity ----
  const resolved = useMemo(() => {
    if (status.kind !== "loaded") return { kind: "none" as const };
    if (!selection.selected) return { kind: "none" as const };

    const { result } = status;

    // Candidate — delegate to CompoundDetail.
    if (selection.selected.kind === "candidate") {
      return { kind: "candidate" as const };
    }

    // Node.
    if (selection.selected.kind === "node") {
      const id = selection.selected.node_id;
      const node = result.mechanism_of_action.nodes.find(
        (n) => n.node_id === id,
      );
      if (!node) return { kind: "none" as const };
      return { kind: "node" as const, node };
    }

    // Edge.
    if (selection.selected.kind === "edge") {
      const key = selection.selected.edge_key;
      const edge = result.mechanism_of_action.edges.find(
        (e) =>
          `${e.source_id}|${e.relationship_type}|${e.target_id}` === key,
      );
      if (!edge) return { kind: "none" as const };
      return { kind: "edge" as const, edge, edge_key: key };
    }

    return { kind: "none" as const };
  }, [status, selection.selected]);

  // ---- Voice effect ----------------------------------------
  useEffect(() => {
    if (!narration.voiceEnabled) return;
    if (narration.isPlaying) return; // narration owns the voice
    if (!isSpeechAvailable()) return;

    let text = "";

    if (resolved.kind === "node") {
      const node = resolved.node;
      const meta = getNodeTypeMeta(node.node_type);
      const parts: string[] = [`${meta.label}.`, node.name + "."];

      // Add meaningful details based on node type.
      const m = node.metadata ?? {};
      if (node.node_type === "gene") {
        if (m.gene_symbol) {
          parts.push(`Gene symbol ${String(m.gene_symbol)}.`);
        }
        if (m.mechanism_membership) {
          parts.push("Member of the selected mechanism.");
        }
        if (typeof m.open_targets_score === "number") {
          parts.push(
            `Open Targets score ${(m.open_targets_score as number).toFixed(2)}.`,
          );
        }
      } else if (node.node_type === "pathway") {
        if (node.identifier) {
          parts.push(`Reactome identifier ${node.identifier}.`);
        }
      } else if (node.node_type === "mechanism") {
        if (m.source) {
          parts.push(`Source: ${String(m.source)}.`);
        }
      } else if (node.node_type === "disease") {
        if (node.description) {
          const first = node.description.split(". ")[0];
          parts.push(first + ".");
        }
      }

      text = parts.join(" ");
    } else if (resolved.kind === "edge") {
      const e = resolved.edge;
      const meta = getSupportClassMeta(e.support_class);

      // Resolve source/target names from the graph.
      let srcName = e.source_id;
      let tgtName = e.target_id;
      if (status.kind === "loaded") {
        const s = status.result.mechanism_of_action.nodes.find(
          (n) => n.node_id === e.source_id,
        );
        const t = status.result.mechanism_of_action.nodes.find(
          (n) => n.node_id === e.target_id,
        );
        if (s) srcName = s.name;
        if (t) tgtName = t.name;
      }

      const rel = e.relationship_type.replace(/_/g, " ");
      text = `${srcName} ${rel} ${tgtName}. Support: ${meta.label}.`;
    }

    if (!text) return;
    if (lastSpokenRef.current === text) return;
    lastSpokenRef.current = text;
    speak(text);
  }, [resolved, narration.voiceEnabled, narration.isPlaying, status]);

  // Stop speaking when nothing is selected.
  useEffect(() => {
    if (resolved.kind === "none") {
      stopSpeaking();
      lastSpokenRef.current = null;
    }
  }, [resolved.kind]);

  // ---- Render -----------------------------------------------
  if (resolved.kind === "candidate") {
    return <CompoundDetail />;
  }

  if (resolved.kind === "node") {
    return <NodeInspector node={resolved.node} />;
  }

  if (resolved.kind === "edge") {
    return (
      <EdgeInspector
        edge={resolved.edge}
        onClose={() => actions.clearSelection()}
      />
    );
  }

  return (
    <aside className="cv-thedisc-compound is-empty">
      <div className="cv-thedisc-compound-empty">
        <div className="cv-thedisc-compound-empty-icon">◌</div>
        <h3>Inspector</h3>
        <p>
          Select a node, an edge, or a compound to inspect its
          content and its evidence.
        </p>
      </div>
    </aside>
  );
}

// ---------------------------------------------------------------------------
// Node inspector
// ---------------------------------------------------------------------------

function NodeInspector({ node }: { node: ImpactNode }) {
  const actions = useTDActions();
  const meta = getNodeTypeMeta(node.node_type);
  const m = (node.metadata ?? {}) as Record<string, unknown>;

  const rows: Array<[string, string]> = [];
  const add = (key: string, value: unknown) => {
    if (value === null || value === undefined) return;
    if (typeof value === "string" && !value.trim()) return;

    // Format floats to 2 decimals for display.
    if (typeof value === "number" && !Number.isInteger(value)) {
      rows.push([key, value.toFixed(2)]);
      return;
    }

    // Friendly boolean display.
    if (typeof value === "boolean") {
      rows.push([key, value ? "yes" : "no"]);
      return;
    }

    if (typeof value === "object") {
      try {
        rows.push([key, JSON.stringify(value).slice(0, 140)]);
      } catch {
        // skip
      }
      return;
    }

    rows.push([key, String(value)]);
  };

  add("gene_symbol", m.gene_symbol);
  add("uniprot_id", m.uniprot_id);
  add("ensembl_id", m.ensembl_id);
  add("chembl_target_id", m.chembl_target_id);
  add("reactome_id", m.reactome_id);
  add("mechanism_membership", m.mechanism_membership);
  add("open_targets_score", m.open_targets_score);
  add("source", m.source);
  add("origin_id", m.origin_id);

  return (
    <aside className="cv-thedisc-compound is-open">
      <header className="cv-thedisc-compound-head">
        <div className="cv-thedisc-compound-head-kicker">
          <span
            className="cv-thedisc-compound-head-dot"
            style={{ background: meta.accent }}
          />
          {meta.label.toUpperCase()}
        </div>
        <button
          type="button"
          className="cv-thedisc-compound-close"
          onClick={() => actions.clearSelection()}
          aria-label="Close inspector"
        >
          ×
        </button>
      </header>

      <h3 className="cv-thedisc-compound-title">{node.name}</h3>

      {node.identifier ? (
        <div className="cv-thedisc-compound-id">{node.identifier}</div>
      ) : null}

      {node.description ? (
        <p className="cv-thedisc-compound-desc">{node.description}</p>
      ) : null}

      {rows.length > 0 ? (
        <div className="cv-thedisc-compound-comparison">
          <div className="cv-thedisc-section-label">
            <span>Metadata</span>
            <i />
          </div>
          <ul>
            {rows.map(([k, v]) => (
              <li key={k}>
                <span>{k}</span>
                <strong>{v}</strong>
              </li>
            ))}
          </ul>
        </div>
      ) : null}
    </aside>
  );
}

// ---------------------------------------------------------------------------
// Edge inspector
// ---------------------------------------------------------------------------

function EdgeInspector({
  edge,
  onClose,
}: {
  edge: Relationship;
  onClose: () => void;
}) {
  const status = useTDStatus();
  const meta = getSupportClassMeta(edge.support_class);

  const { sourceName, targetName } = useMemo(() => {
    let src = edge.source_id;
    let tgt = edge.target_id;
    if (status.kind === "loaded") {
      const s = status.result.mechanism_of_action.nodes.find(
        (n) => n.node_id === edge.source_id,
      );
      const t = status.result.mechanism_of_action.nodes.find(
        (n) => n.node_id === edge.target_id,
      );
      if (s) src = s.name;
      if (t) tgt = t.name;
    }
    return { sourceName: src, targetName: tgt };
  }, [edge, status]);

  return (
    <aside className="cv-thedisc-compound is-open">
      <header className="cv-thedisc-compound-head">
        <div className="cv-thedisc-compound-head-kicker">
          <span
            className="cv-thedisc-compound-head-dot"
            style={{ background: meta.accent }}
          />
          RELATIONSHIP
        </div>
        <button
          type="button"
          className="cv-thedisc-compound-close"
          onClick={onClose}
          aria-label="Close inspector"
        >
          ×
        </button>
      </header>

      <div className="cv-thedisc-inspector-relation">
        <div>
          <span>FROM</span>
          <strong>{sourceName}</strong>
        </div>
        <div className="cv-thedisc-inspector-relation-arrow">
          {edge.relationship_type.replace(/_/g, " ")}
        </div>
        <div>
          <span>TO</span>
          <strong>{targetName}</strong>
        </div>
      </div>

      <div className="cv-thedisc-compound-comparison">
        <div className="cv-thedisc-section-label">
          <span>Support classification</span>
          <i />
        </div>
        <div
          className="cv-thedisc-inspector-support-pill"
          style={{ borderColor: meta.accent, color: meta.accent }}
        >
          {meta.label}
        </div>
        <p className="cv-thedisc-inspector-support-desc">
          {meta.description}
        </p>
      </div>

      {edge.description ? (
        <div className="cv-thedisc-compound-comparison">
          <div className="cv-thedisc-section-label">
            <span>Description</span>
            <i />
          </div>
          <p className="cv-thedisc-inspector-support-desc">
            {edge.description}
          </p>
        </div>
      ) : null}
    </aside>
  );
}
