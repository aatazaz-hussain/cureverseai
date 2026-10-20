/**
 * CureVerseAI — Drug Development
 * Workflow 02 — Reverse Disease Engineering
 * MechanismGraph — the SVG graph renderer.
 *
 * The visual centerpiece of the W02 interface. Composes a
 * pure SVG scene from:
 *
 *   - the layout (graphLayout.ts)
 *   - the current selection (state.tsx)
 *   - the current filters (state.tsx)
 *   - the component styles (components/types.ts)
 *
 * Renders:
 *   - a background grid (via SVG <pattern>)
 *   - column headers at the top of each active column
 *   - a <GraphEdge> for each edge
 *   - a <GraphNode> for each node
 *
 * Selection and filter logic is computed here once per
 * render and passed down as read-only style objects.
 * Children do not touch the state tree.
 */

"use client";

import { useMemo, useCallback } from "react";

import type {
  ImpactNode,
  Relationship,
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
  useRDESelection,
  useRDEFilters,
  useRDEActions,
} from "../../state";

// ---------------------------------------------------------------------------
// Props
// ---------------------------------------------------------------------------

interface MechanismGraphProps {
  nodes: ImpactNode[];
  edges: Relationship[];
}

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

export default function MechanismGraph({
  nodes,
  edges,
}: MechanismGraphProps) {
  // ---- Layout (pure, memoized) ---------------------------
  const layout = useMemo(
    () => computeGraphLayout(nodes, edges),
    [nodes, edges],
  );

  const headers = useMemo(
    () => computeColumnHeaders(layout),
    [layout],
  );

  // ---- State --------------------------------------------
  const selection = useRDESelection();
  const filters = useRDEFilters();
  const actions = useRDEActions();

  // ---- Selection shortcuts ------------------------------
  const selectedNodeId =
    selection.selected?.kind === "node"
      ? selection.selected.node_id
      : null;
  const selectedEdgeKey =
    selection.selected?.kind === "edge"
      ? selection.selected.edge_key
      : null;

  // ---- Neighbors of the selection ------------------------
  // Precompute the set of node_ids connected to the
  // currently selected node or edge. Used to set
  // `connected_to_selected` on each element.
  const connectedNodeIds = useMemo<Set<string>>(() => {
    const set = new Set<string>();

    if (selectedNodeId) {
      set.add(selectedNodeId);
      for (const edge of edges) {
        if (edge.source_id === selectedNodeId) {
          set.add(edge.target_id);
        }
        if (edge.target_id === selectedNodeId) {
          set.add(edge.source_id);
        }
      }
      return set;
    }

    if (selectedEdgeKey) {
      for (const edge of edges) {
        const key = `${edge.source_id}|${edge.relationship_type}|${edge.target_id}`;
        if (key === selectedEdgeKey) {
          set.add(edge.source_id);
          set.add(edge.target_id);
        }
      }
    }

    return set;
  }, [selectedNodeId, selectedEdgeKey, edges]);

  const connectedEdgeKeys = useMemo<Set<string>>(() => {
    const set = new Set<string>();

    if (selectedNodeId) {
      for (const edge of edges) {
        const key = `${edge.source_id}|${edge.relationship_type}|${edge.target_id}`;
        if (
          edge.source_id === selectedNodeId ||
          edge.target_id === selectedNodeId
        ) {
          set.add(key);
        }
      }
      return set;
    }

    if (selectedEdgeKey) {
      set.add(selectedEdgeKey);
    }

    return set;
  }, [selectedNodeId, selectedEdgeKey, edges]);

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

      // Filter dimming: if the edge's support class is
      // hidden, dim it. If a selection exists and this
      // edge is not connected, dim it further.
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

      // Node-type filter dimming: if any node types are
      // highlighted, dim nodes not in the set.
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
      <div className="cv-revdis-graph-empty">
        <span>No graph to display.</span>
      </div>
    );
  }

  // ---- Render -------------------------------------------
  return (
    <div className="cv-revdis-graph-wrap">
      <svg
        className="cv-revdis-graph-svg"
        width={layout.width}
        height={layout.height}
        viewBox={`0 0 ${layout.width} ${layout.height}`}
        preserveAspectRatio="xMidYMid meet"
        role="img"
        aria-label="Reverse disease mechanism graph"
      >
        {/* Background grid pattern */}
        <defs>
          <pattern
            id="cv-revdis-grid"
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

        {/* Background */}
        <rect
          x={0}
          y={0}
          width={layout.width}
          height={layout.height}
          fill="url(#cv-revdis-grid)"
        />

        {/* Column headers */}
        <g className="cv-revdis-graph-headers">
          {headers.map((h) => (
            <g key={h.column}>
              <line
                x1={h.x}
                y1={h.y + 10}
                x2={h.x + 220}
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

        {/* Edges layer */}
        <g className="cv-revdis-graph-edges">
          {edgeStyles.map((style) => (
            <GraphEdge
              key={style.edge_key}
              style={style}
              onSelect={handleEdgeSelect}
            />
          ))}
        </g>

        {/* Nodes layer */}
        <g className="cv-revdis-graph-nodes">
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
  );
}
