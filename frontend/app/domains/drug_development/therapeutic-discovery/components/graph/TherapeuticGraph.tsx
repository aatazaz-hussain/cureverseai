/**
 * CureVerseAI — Drug Development
 * Workflow 03 — Therapeutic Discovery
 * TherapeuticGraph.
 *
 * The SVG graph container. Composes GraphNode and
 * GraphEdge, applies filters and selection state, and
 * renders column headers plus a background grid.
 *
 * Selection highlight rules:
 *
 *   - No selection: all elements pass through filters
 *   - Node/edge selected: dim everything except the
 *     selected element and its immediate neighbors
 *   - Candidate selected: dim everything except the
 *     candidate's MoA chain (compound -> target ->
 *     pathway -> disease)
 */

"use client";

import { useCallback, useMemo } from "react";

import type {
  ImpactNode,
  Relationship,
  TherapeuticDiscoveryResult,
} from "../../types";

import {
  getNodeTypeMeta,
  getSupportClassMeta,
  type GraphEdgeStyle,
  type GraphNodeStyle,
} from "../types";

import {
  computeColumnHeaders,
  computeGraphLayout,
} from "./graphLayout";

import GraphNode from "./GraphNode";
import GraphEdge from "./GraphEdge";

import {
  useTDSelection,
  useTDFilters,
  useTDActions,
} from "../../state";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface TherapeuticGraphProps {
  result: TherapeuticDiscoveryResult;
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function TherapeuticGraph({
  result,
}: TherapeuticGraphProps) {
  const graph = result.mechanism_of_action;

  // Cap visible compounds to the top 20 (matching the
  // candidate_comparisons list). The other candidates are
  // visible in the explorer only.
  const topCandidateIds = useMemo(() => {
    const set = new Set<string>();
    for (const c of result.candidate_comparisons) {
      set.add(`compound:${c.candidate_id}`);
    }
    return set;
  }, [result.candidate_comparisons]);

  const nodes = useMemo(
    () =>
      graph.nodes.filter((n) => {
        if (n.node_type !== "compound") return true;
        return topCandidateIds.has(n.node_id);
      }),
    [graph.nodes, topCandidateIds],
  );

  const edges = useMemo(
    () =>
      graph.edges.filter(
        (e) =>
          nodes.some((n) => n.node_id === e.source_id) &&
          nodes.some((n) => n.node_id === e.target_id),
      ),
    [graph.edges, nodes],
  );

  // ---- Layout --------------------------------------------
  const layout = useMemo(
    () => computeGraphLayout(nodes, edges),
    [nodes, edges],
  );

  const headers = useMemo(
    () => computeColumnHeaders(layout),
    [layout],
  );

  // ---- State --------------------------------------------
  const selection = useTDSelection();
  const filters = useTDFilters();
  const actions = useTDActions();

  // ---- Selection shortcuts ------------------------------
  const selectedNodeId =
    selection.selected?.kind === "node"
      ? selection.selected.node_id
      : null;

  const selectedEdgeKey =
    selection.selected?.kind === "edge"
      ? selection.selected.edge_key
      : null;

  const selectedCompoundId =
    selection.selected?.kind === "candidate"
      ? selection.selected.compound_id
      : null;

  // ---- Connected node ids -------------------------------
  // The set of node_ids that are connected to the current
  // selection, either directly (W02-style) or via the MoA
  // chain (W03 candidate selection).
  const connectedNodeIds = useMemo<Set<string>>(() => {
    const set = new Set<string>();

    // ---- Candidate chain highlight ---------------------
    if (selectedCompoundId) {
      const compoundNodeId = `compound:${selectedCompoundId}`;
      set.add(compoundNodeId);

      // Walk the MoA edges to find the candidate's chain.
      for (const e of edges) {
        if (
          e.source_id === compoundNodeId &&
          (e.relationship_type === "binds_to" ||
            e.relationship_type === "inhibits")
        ) {
          set.add(e.target_id);
        }
      }

      // Expand one hop: target -> pathway, pathway -> disease.
      // Repeat until closure (typically 1 extra hop for
      // W03's chain depth).
      let changed = true;
      let hops = 0;
      while (changed && hops < 3) {
        changed = false;
        for (const e of edges) {
          if (
            set.has(e.source_id) &&
            !set.has(e.target_id)
          ) {
            set.add(e.target_id);
            changed = true;
          }
        }
        hops += 1;
      }

      return set;
    }

    // ---- Node selection --------------------------------
    if (selectedNodeId) {
      set.add(selectedNodeId);
      for (const e of edges) {
        if (e.source_id === selectedNodeId) {
          set.add(e.target_id);
        }
        if (e.target_id === selectedNodeId) {
          set.add(e.source_id);
        }
      }
      return set;
    }

    // ---- Edge selection --------------------------------
    if (selectedEdgeKey) {
      for (const e of edges) {
        const key = `${e.source_id}|${e.relationship_type}|${e.target_id}`;
        if (key === selectedEdgeKey) {
          set.add(e.source_id);
          set.add(e.target_id);
        }
      }
    }

    return set;
  }, [selectedNodeId, selectedEdgeKey, selectedCompoundId, edges]);

  const connectedEdgeKeys = useMemo<Set<string>>(() => {
    const set = new Set<string>();

    if (selectedNodeId) {
      for (const e of edges) {
        if (
          e.source_id === selectedNodeId ||
          e.target_id === selectedNodeId
        ) {
          set.add(
            `${e.source_id}|${e.relationship_type}|${e.target_id}`,
          );
        }
      }
      return set;
    }

    if (selectedEdgeKey) {
      set.add(selectedEdgeKey);
      return set;
    }

    if (selectedCompoundId) {
      const compoundNodeId = `compound:${selectedCompoundId}`;
      // Any edge whose source or target is in the chain.
      for (const e of edges) {
        if (
          e.source_id === compoundNodeId ||
          e.target_id === compoundNodeId
        ) {
          set.add(
            `${e.source_id}|${e.relationship_type}|${e.target_id}`,
          );
        }
      }

      // Also include edges internal to the chain.
      for (const e of edges) {
        if (
          connectedNodeIds.has(e.source_id) &&
          connectedNodeIds.has(e.target_id)
        ) {
          set.add(
            `${e.source_id}|${e.relationship_type}|${e.target_id}`,
          );
        }
      }

      return set;
    }

    return set;
  }, [
    selectedNodeId,
    selectedEdgeKey,
    selectedCompoundId,
    connectedNodeIds,
    edges,
  ]);

  // ---- Handlers -----------------------------------------
  const handleNodeSelect = useCallback(
    (node_id: string) => {
      actions.select({ kind: "node", node_id });
    },
    [actions],
  );

  const handleEdgeSelect = useCallback(
    (edge_key: string) => {
      actions.select({ kind: "edge", edge_key });
    },
    [actions],
  );

  const handleHover = useCallback(
    (id: string | null) => {
      actions.hover(id);
    },
    [actions],
  );

  // ---- Compute edge styles ------------------------------
  const edgeStyles = useMemo<GraphEdgeStyle[]>(() => {
    const out: GraphEdgeStyle[] = [];

    for (const edgePath of layout.edges) {
      const edge = edges.find(
        (e) =>
          `${e.source_id}|${e.relationship_type}|${e.target_id}` ===
          edgePath.edge_key,
      );
      if (!edge) continue;

      const meta = getSupportClassMeta(edge.support_class);

      let dimmed = false;

      if (
        edge.support_class &&
        !filters.visibleSupportClasses.has(edge.support_class)
      ) {
        dimmed = true;
      }

      const connected = connectedEdgeKeys.has(
        edgePath.edge_key,
      );

      if (selection.selected && !connected) {
        dimmed = true;
      }

      out.push({
        edge,
        edge_key: edgePath.edge_key,
        path: edgePath,
        meta,
        selected: selectedEdgeKey === edgePath.edge_key,
        dimmed,
        connected_to_selected: connected,
      });
    }

    return out;
  }, [
    layout.edges,
    edges,
    filters.visibleSupportClasses,
    selection.selected,
    connectedEdgeKeys,
    selectedEdgeKey,
  ]);

  // ---- Compute node styles ------------------------------
  const nodeStyles = useMemo<GraphNodeStyle[]>(() => {
    const out: GraphNodeStyle[] = [];

    for (const position of layout.nodes) {
      const node = nodes.find(
        (n) => n.node_id === position.node_id,
      );
      if (!node) continue;

      const meta = getNodeTypeMeta(node.node_type);

      let dimmed = false;

      if (
        filters.highlightedNodeTypes.size > 0 &&
        !filters.highlightedNodeTypes.has(node.node_type)
      ) {
        dimmed = true;
      }

      const connected = connectedNodeIds.has(node.node_id);

      if (selection.selected && !connected) {
        dimmed = true;
      }

      out.push({
        node,
        position,
        meta,
        selected: selectedNodeId === node.node_id,
        hovered: selection.hoveredId === node.node_id,
        dimmed,
        connected_to_selected: connected,
      });
    }

    return out;
  }, [
    layout.nodes,
    nodes,
    filters.highlightedNodeTypes,
    selection.selected,
    selection.hoveredId,
    connectedNodeIds,
    selectedNodeId,
  ]);

  // ---- Empty state --------------------------------------
  if (!layout.nodes.length) {
    return (
      <div className="cv-thedisc-graph-empty">
        <span>No graph to display.</span>
      </div>
    );
  }

  // ---- Render -------------------------------------------
  return (
    <div className="cv-thedisc-graph-wrap">
      <div className="cv-thedisc-graph-scroll">
        <svg
          className="cv-thedisc-graph-svg"
          width={layout.width}
          height={layout.height}
          viewBox={`0 0 ${layout.width} ${layout.height}`}
          role="img"
          aria-label="Therapeutic discovery graph"
        >
          {/* Background grid */}
          <defs>
            <pattern
              id="cv-thedisc-grid"
              x="0"
              y="0"
              width="48"
              height="48"
              patternUnits="userSpaceOnUse"
            >
              <path
                d="M 48 0 L 0 0 0 48"
                fill="none"
                stroke="rgba(238,233,225,0.028)"
                strokeWidth="1"
              />
            </pattern>
          </defs>

          <rect
            x={0}
            y={0}
            width={layout.width}
            height={layout.height}
            fill="url(#cv-thedisc-grid)"
          />

          {/* Column headers */}
          <g className="cv-thedisc-graph-headers">
            {headers.map((h) => (
              <g key={h.column}>
                <line
                  x1={h.x}
                  y1={h.y + 10}
                  x2={h.x + 260}
                  y2={h.y + 10}
                  stroke="rgba(238,233,225,0.08)"
                  strokeWidth={1}
                />
                <text
                  x={h.x}
                  y={h.y}
                  fill="#e0525a"
                  fontSize={9}
                  fontWeight={700}
                  letterSpacing="0.2em"
                  fontFamily="'Space Grotesk', Arial, sans-serif"
                >
                  {h.label}
                </text>
              </g>
            ))}
          </g>

          {/* Edges */}
          <g className="cv-thedisc-graph-edges">
            {edgeStyles.map((style) => (
              <GraphEdge
                key={style.edge_key}
                style={style}
                onSelect={handleEdgeSelect}
              />
            ))}
          </g>

          {/* Nodes */}
          <g className="cv-thedisc-graph-nodes">
            {nodeStyles.map((style) => (
              <GraphNode
                key={style.node.node_id}
                style={style}
                onSelect={handleNodeSelect}
                onHover={handleHover}
              />
            ))}
          </g>
        </svg>
      </div>

      <div className="cv-thedisc-graph-scroll-hint" aria-hidden>
        <span>SCROLL</span>
        <i />
        <span>→</span>
      </div>
    </div>
  );
}
