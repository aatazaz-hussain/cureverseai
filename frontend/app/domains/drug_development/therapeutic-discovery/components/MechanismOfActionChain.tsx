/**
 * CureVerseAI — Drug Development
 * Workflow 03 — Therapeutic Discovery
 * MechanismOfActionChain.
 *
 * Compact horizontal visualization of a candidate's
 * proposed chain:
 *
 *   compound -> target -> pathway -> disease
 *
 * Each step shows the entity name and, when applicable,
 * the support class of the edge entering it.
 */

"use client";

import type {
  MechanismOfActionBlock,
  TherapeuticDiscoveryResult,
} from "../types";

import { getSupportClassMeta } from "./types";

interface MechanismOfActionChainProps {
  result: TherapeuticDiscoveryResult;
  compoundId: string;
}

export default function MechanismOfActionChain({
  result,
  compoundId,
}: MechanismOfActionChainProps) {
  const graph = result.mechanism_of_action;
  const compoundNodeId = `compound:${compoundId}`;

  // Walk the graph from the compound to find the chain.
  const chainNodes = walkChain(graph, compoundNodeId);

  if (!chainNodes.length) {
    return (
      <div className="cv-thedisc-moa-empty">
        <span>
          No mechanism-of-action chain is available for this
          compound.
        </span>
      </div>
    );
  }

  // Extract the support class of each successive edge.
  const chain = chainNodes.map((nodeId, i) => {
    let supportClass: string | null = null;
    if (i > 0) {
      const prev = chainNodes[i - 1];
      const edge = graph.edges.find(
        (e) =>
          e.source_id === prev && e.target_id === nodeId,
      );
      supportClass = edge?.support_class ?? null;
    }
    const node = graph.nodes.find((n) => n.node_id === nodeId);
    return {
      node_id: nodeId,
      label: node?.name ?? nodeId,
      type: node?.node_type ?? "unknown",
      support_class: supportClass,
    };
  });

  return (
    <div className="cv-thedisc-moa">
      <div className="cv-thedisc-moa-label">
        MECHANISM OF ACTION
      </div>
      <div className="cv-thedisc-moa-strip">
        {chain.map((step, i) => {
          const meta = step.support_class
            ? getSupportClassMeta(step.support_class)
            : null;
          return (
            <div
              key={step.node_id}
              className="cv-thedisc-moa-step"
            >
              {i > 0 ? (
                <div
                  className="cv-thedisc-moa-arrow"
                  style={{
                    color: meta?.accent ?? "#5f5b55",
                  }}
                >
                  →
                  {meta ? (
                    <span
                      className="cv-thedisc-moa-arrow-label"
                      style={{ color: meta.accent }}
                    >
                      {meta.label}
                    </span>
                  ) : null}
                </div>
              ) : null}
              <div
                className={
                  "cv-thedisc-moa-node cv-thedisc-moa-node-" +
                  step.type
                }
              >
                <span className="cv-thedisc-moa-node-type">
                  {step.type}
                </span>
                <strong>{step.label}</strong>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

// ---------------------------------------------------------------------------
// Chain walker
// ---------------------------------------------------------------------------

function walkChain(
  graph: MechanismOfActionBlock,
  startId: string,
): string[] {
  const chain: string[] = [startId];
  let current = startId;
  const visited = new Set<string>([startId]);
  let guard = 0;

  while (guard < 6) {
    const next = graph.edges.find(
      (e) =>
        e.source_id === current &&
        !visited.has(e.target_id) &&
        (e.relationship_type === "binds_to" ||
          e.relationship_type === "inhibits" ||
          e.relationship_type === "participates_in" ||
          e.relationship_type === "associated_with"),
    );
    if (!next) break;
    chain.push(next.target_id);
    visited.add(next.target_id);
    current = next.target_id;
    guard += 1;
  }

  return chain;
}
