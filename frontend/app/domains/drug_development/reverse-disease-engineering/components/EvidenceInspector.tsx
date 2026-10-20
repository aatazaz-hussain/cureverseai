/**
 * CureVerseAI — Drug Development
 * Workflow 02 — Reverse Disease Engineering
 * EvidenceInspector.
 *
 * The right-side drawer. Three states:
 *
 *   - Closed / placeholder  : nothing selected
 *   - Node inspector        : a node is selected
 *   - Edge inspector        : an edge is selected
 *
 * The drawer reads the selection and the last loaded
 * result from the Context. It does not receive props.
 *
 * Node mode shows:
 *   - The node's label, type badge, description
 *   - Identifier
 *   - Metadata (rendered as a key/value list)
 *   - Any evidence records attached to the node
 *
 * Edge mode shows:
 *   - Source and target labels (resolved from graph nodes)
 *   - Relationship type and support-class badge
 *   - Description
 *   - Every evidence record on the edge, with source,
 *     relationship description, level, and external link
 *   - Any limitations in evidence metadata
 *
 * The drawer slides in via CSS. This component only sets
 * the class names and content.
 */

"use client";

import { useEffect, useMemo, useRef } from "react";

import type {
  ImpactEvidence,
  ImpactNode,
  Relationship,
} from "../types";

import {
  getNodeTypeMeta,
  getSupportClassMeta,
} from "./types";

import {
  useRDEStatus,
  useRDESelection,
  useRDENarration,
  useRDEActions,
} from "../state";

import { speak, stopSpeaking, isSpeechAvailable } from "../voice";

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function edgeKey(edge: Relationship): string {
  return `${edge.source_id}|${edge.relationship_type}|${edge.target_id}`;
}

/**
 * Return the first sentence of a string. Used to keep the
 * spoken summary short. If the string has no sentence
 * boundary, the whole string is returned (truncated at a
 * reasonable limit).
 */
function extractFirstSentence(text: string): string {
  if (!text) return "";
  const trimmed = text.trim();
  // Split on ". ", "! ", "? " while keeping the punctuation.
  const match = trimmed.match(/^[^.!?]*[.!?]/);
  if (match) return match[0].trim();
  if (trimmed.length > 220) {
    return trimmed.slice(0, 220).trim() + "…";
  }
  return trimmed;
}

function formatMetaValue(value: unknown): string {
  if (value === null || value === undefined) return "—";
  if (typeof value === "string") return value;
  if (typeof value === "number") return String(value);
  if (typeof value === "boolean") return value ? "yes" : "no";
  if (Array.isArray(value)) {
    if (!value.length) return "—";
    return value
      .slice(0, 8)
      .map((v) =>
        typeof v === "object" ? JSON.stringify(v) : String(v),
      )
      .join(", ");
  }
  if (typeof value === "object") {
    return JSON.stringify(value).slice(0, 200);
  }
  return String(value);
}

/**
 * Select interesting metadata keys for display. We do not
 * dump everything — some metadata is internal bookkeeping.
 */
const INTERESTING_META_KEYS = [
  "hpo_id",
  "ensembl_id",
  "approved_symbol",
  "approved_name",
  "biotype",
  "uniprot_id",
  "uniprot_protein_name",
  "uniprot_reviewed",
  "chembl_target_id",
  "chembl_status",
  "chembl_activity_count",
  "chembl_compound_count",
  "datatype_id",
  "targets_supporting",
  "mean_score",
  "reactome_id",
  "species",
  "supporting_genes",
  "supporting_gene_count",
  "namespace",
  "inheritance_like",
  "open_targets_score",
];

function pickMetadata(
  meta: Record<string, unknown>,
): Array<[string, string]> {
  const out: Array<[string, string]> = [];
  for (const key of INTERESTING_META_KEYS) {
    if (key in meta) {
      const value = meta[key];
      if (
        value === null ||
        value === undefined ||
        (Array.isArray(value) && value.length === 0)
      ) {
        continue;
      }
      out.push([key, formatMetaValue(value)]);
    }
  }
  return out;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function EvidenceInspector() {
  const status = useRDEStatus();
  const selection = useRDESelection();
  const narration = useRDENarration();
  const actions = useRDEActions();

  // Track the last thing we spoke so we don't repeat
  // ourselves when the same node is re-selected.
  const lastSpokenRef = useRef<string | null>(null);

  // Resolve the current selection to a usable entity.
  const entity = useMemo<{
    kind: "none" | "node" | "edge";
    node?: ImpactNode;
    edge?: Relationship;
  }>(() => {
    if (status.kind !== "loaded") return { kind: "none" };
    if (!selection.selected) return { kind: "none" };

    const { result } = status;

    if (selection.selected.kind === "node") {
      const id = selection.selected.node_id;
      const node = result.graph.nodes.find(
        (n) => n.node_id === id,
      );
      if (!node) return { kind: "none" };
      return { kind: "node", node };
    }

    const key = selection.selected.edge_key;
    const edge = result.graph.edges.find(
      (e) => edgeKey(e) === key,
    );
    if (!edge) return { kind: "none" };
    return { kind: "edge", edge };
  }, [status, selection.selected]);

  // Speak a short summary whenever the selection resolves
  // to a node or edge. Respects the voice toggle; skips if
  // the narration panel is currently playing a segment
  // (narration owns the voice in that mode).
  useEffect(() => {
    if (!narration.voiceEnabled) return;
    if (narration.isPlaying) return;
    if (!isSpeechAvailable()) return;

    let text = "";

    if (entity.kind === "node" && entity.node) {
      const node = entity.node;
      const meta = getNodeTypeMeta(node.node_type);

      // Short summary: type + name + first sentence of
      // description or the node's own description field.
      const summary =
        node.description ??
        (node.metadata &&
        typeof node.metadata.summary === "string"
          ? node.metadata.summary
          : "");

      const firstSentence = extractFirstSentence(summary);

      text = [
        `${meta.label}.`,
        node.name ? `${node.name}.` : "",
        firstSentence,
      ]
        .filter(Boolean)
        .join(" ");
    } else if (entity.kind === "edge" && entity.edge) {
      const edge = entity.edge;
      const supportMeta = getSupportClassMeta(
        edge.support_class,
      );

      // Resolve source/target names from the graph.
      let sourceName = edge.source_id;
      let targetName = edge.target_id;

      if (status.kind === "loaded") {
        const s = status.result.graph.nodes.find(
          (n) => n.node_id === edge.source_id,
        );
        const t = status.result.graph.nodes.find(
          (n) => n.node_id === edge.target_id,
        );
        if (s) sourceName = s.name;
        if (t) targetName = t.name;
      }

      const rel = edge.relationship_type.replace(/_/g, " ");

      text = `${sourceName} ${rel} ${targetName}. Support: ${supportMeta.label}.`;
    }

    if (!text) return;

    // Skip if this exact string was the last thing spoken.
    if (lastSpokenRef.current === text) return;
    lastSpokenRef.current = text;

    speak(text);
  }, [
    entity.kind,
    entity.node,
    entity.edge,
    narration.voiceEnabled,
    narration.isPlaying,
    status,
  ]);

  // Stop speaking when the panel is dismissed.
  useEffect(() => {
    if (entity.kind === "none") {
      stopSpeaking();
      lastSpokenRef.current = null;
    }
  }, [entity.kind]);

  const isOpen = entity.kind !== "none";

  return (
    <aside
      className={
        "cv-revdis-inspector" +
        (isOpen ? " is-open" : " is-closed")
      }
      aria-hidden={!isOpen}
    >
      {entity.kind === "none" ? (
        <EmptyInspector />
      ) : entity.kind === "node" && entity.node ? (
        <NodeInspector
          node={entity.node}
          onClose={() => actions.clearSelection()}
        />
      ) : entity.kind === "edge" && entity.edge ? (
        <EdgeInspector
          edge={entity.edge}
          onClose={() => actions.clearSelection()}
        />
      ) : null}
    </aside>
  );
}

// ---------------------------------------------------------------------------
// Empty state
// ---------------------------------------------------------------------------

function EmptyInspector() {
  return (
    <div className="cv-revdis-inspector-empty">
      <div className="cv-revdis-inspector-empty-icon">◌</div>
      <h3>Evidence inspector</h3>
      <p>
        Select a node or an edge in the graph to inspect
        its supporting evidence, source records, and
        limitations.
      </p>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Node inspector
// ---------------------------------------------------------------------------

function NodeInspector({
  node,
  onClose,
}: {
  node: ImpactNode;
  onClose: () => void;
}) {
  const meta = getNodeTypeMeta(node.node_type);
  const metadataRows = pickMetadata(node.metadata);

  return (
    <div className="cv-revdis-inspector-body">
      <header className="cv-revdis-inspector-head">
        <div className="cv-revdis-inspector-head-kicker">
          <span
            className="cv-revdis-inspector-head-dot"
            style={{ background: meta.accent }}
          />
          {meta.label}
        </div>
        <button
          type="button"
          className="cv-revdis-inspector-close"
          onClick={onClose}
          aria-label="Close inspector"
        >
          ×
        </button>
      </header>

      <h3 className="cv-revdis-inspector-title">
        {node.name}
      </h3>

      {node.identifier ? (
        <div className="cv-revdis-inspector-id">
          {node.identifier}
        </div>
      ) : null}

      {node.description ? (
        <p className="cv-revdis-inspector-desc">
          {node.description}
        </p>
      ) : null}

      <div className="cv-revdis-inspector-section">
        <div className="cv-revdis-inspector-section-label">
          Description
        </div>
        <p className="cv-revdis-inspector-section-body">
          {meta.description}
        </p>
      </div>

      {metadataRows.length ? (
        <div className="cv-revdis-inspector-section">
          <div className="cv-revdis-inspector-section-label">
            Metadata
          </div>
          <dl className="cv-revdis-inspector-meta">
            {metadataRows.map(([k, v]) => (
              <div key={k} className="cv-revdis-inspector-meta-row">
                <dt>{k}</dt>
                <dd>{v}</dd>
              </div>
            ))}
          </dl>
        </div>
      ) : null}

      <EvidenceList
        evidenceIds={node.evidence_ids}
        emptyMessage="No evidence records are attached directly to this node. Evidence for this entity is attached to its relationships."
      />
    </div>
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
  const status = useRDEStatus();

  const supportMeta = getSupportClassMeta(edge.support_class);

  // Resolve source/target nodes for display.
  const { sourceNode, targetNode, edgeEvidence } = useMemo(() => {
    if (status.kind !== "loaded") {
      return {
        sourceNode: null,
        targetNode: null,
        edgeEvidence: [] as ImpactEvidence[],
      };
    }

    const { result } = status;

    const s = result.graph.nodes.find(
      (n) => n.node_id === edge.source_id,
    ) ?? null;
    const t = result.graph.nodes.find(
      (n) => n.node_id === edge.target_id,
    ) ?? null;

    const evidenceIds = new Set(edge.evidence_ids);
    const ev = result.evidence.filter((e) =>
      evidenceIds.has(e.evidence_id),
    );

    return { sourceNode: s, targetNode: t, edgeEvidence: ev };
  }, [status, edge]);

  return (
    <div className="cv-revdis-inspector-body">
      <header className="cv-revdis-inspector-head">
        <div className="cv-revdis-inspector-head-kicker">
          <span
            className="cv-revdis-inspector-head-dot"
            style={{ background: supportMeta.accent }}
          />
          Relationship
        </div>
        <button
          type="button"
          className="cv-revdis-inspector-close"
          onClick={onClose}
          aria-label="Close inspector"
        >
          ×
        </button>
      </header>

      <div className="cv-revdis-inspector-relation">
        <div className="cv-revdis-inspector-relation-node">
          <span>FROM</span>
          <strong>{sourceNode?.name ?? edge.source_id}</strong>
          {sourceNode?.identifier ? (
            <small>{sourceNode.identifier}</small>
          ) : null}
        </div>

        <div className="cv-revdis-inspector-relation-arrow">
          {edge.relationship_type.replace(/_/g, " ")}
        </div>

        <div className="cv-revdis-inspector-relation-node">
          <span>TO</span>
          <strong>{targetNode?.name ?? edge.target_id}</strong>
          {targetNode?.identifier ? (
            <small>{targetNode.identifier}</small>
          ) : null}
        </div>
      </div>

      <div className="cv-revdis-inspector-section">
        <div className="cv-revdis-inspector-section-label">
          Support classification
        </div>
        <div
          className="cv-revdis-inspector-support-pill"
          style={{ borderColor: supportMeta.accent, color: supportMeta.accent }}
        >
          {supportMeta.label}
        </div>
        <p className="cv-revdis-inspector-section-body">
          {supportMeta.description}
        </p>
      </div>

      {edge.description ? (
        <div className="cv-revdis-inspector-section">
          <div className="cv-revdis-inspector-section-label">
            Relationship
          </div>
          <p className="cv-revdis-inspector-section-body">
            {edge.description}
          </p>
        </div>
      ) : null}

      <EvidenceList
        evidence={edgeEvidence}
        emptyMessage="No evidence records are attached to this relationship."
      />
    </div>
  );
}

// ---------------------------------------------------------------------------
// Evidence list
// ---------------------------------------------------------------------------

interface EvidenceListProps {
  evidence?: ImpactEvidence[];
  evidenceIds?: string[];
  emptyMessage: string;
}

function EvidenceList({
  evidence,
  evidenceIds,
  emptyMessage,
}: EvidenceListProps) {
  // If only IDs are provided, look them up from the result.
  const status = useRDEStatus();

  const resolved = useMemo<ImpactEvidence[]>(() => {
    if (evidence) return evidence;

    if (evidenceIds && evidenceIds.length && status.kind === "loaded") {
      const set = new Set(evidenceIds);
      return status.result.evidence.filter((e) =>
        set.has(e.evidence_id),
      );
    }

    return [];
  }, [evidence, evidenceIds, status]);

  return (
    <div className="cv-revdis-inspector-section">
      <div className="cv-revdis-inspector-section-label">
        Evidence ({resolved.length})
      </div>

      {resolved.length === 0 ? (
        <p className="cv-revdis-inspector-section-body cv-revdis-inspector-empty-note">
          {emptyMessage}
        </p>
      ) : (
        <ul className="cv-revdis-inspector-evidence">
          {resolved.map((ev) => (
            <li
              key={ev.evidence_id}
              className="cv-revdis-inspector-evidence-item"
            >
              <div className="cv-revdis-inspector-evidence-head">
                <strong>{ev.source}</strong>
                <span>{ev.evidence_level}</span>
              </div>
              <p className="cv-revdis-inspector-evidence-desc">
                {ev.relationship_description}
              </p>
              {ev.reference?.url ? (
                <a
                  className="cv-revdis-inspector-evidence-link"
                  href={ev.reference.url}
                  target="_blank"
                  rel="noopener noreferrer"
                >
                  Open source record ↗
                </a>
              ) : null}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
