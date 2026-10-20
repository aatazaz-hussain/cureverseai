"use client";

/**
 * CureVerseAI — Medicine domain
 * Mechanism graph.
 *
 * Renders intervention → targets → pathways → indicators as a
 * simple node/edge diagram. Edges are drawn from the backend's
 * data; direct vs inferred edges are visually distinct. This
 * component does not infer any relationship that the backend
 * did not return.
 */

import type {
  FunctionalIndicator,
  InterventionRef,
  Response,
} from "../types";

interface Props {
  intervention: InterventionRef | null;
  indicators: FunctionalIndicator[];
  responses: Response[];
  onSelect?: (id: string) => void;
}

interface LayoutNode {
  id: string;
  label: string;
  kind: "intervention" | "target" | "indicator";
  x: number;
  y: number;
}

export default function MechanismGraph({
  intervention,
  indicators,
  responses,
  onSelect,
}: Props) {
  if (!intervention) {
    return (
      <div className="cv-medicine-wf-panel">
        <div className="cv-medicine-wf-panel-header">
          <h3 className="cv-medicine-wf-panel-title">
            Mechanism overview
          </h3>
        </div>
        <div className="cv-medicine-wf-empty-inline">
          No intervention is currently resolved.
        </div>
      </div>
    );
  }

  const nodes: LayoutNode[] = [];
  const width = 800;
  const height = 360;

  nodes.push({
    id: intervention.id,
    label: intervention.name,
    kind: "intervention",
    x: 120,
    y: height / 2,
  });

  const targetCount = Math.min(intervention.targets.length, 6);
  intervention.targets.slice(0, targetCount).forEach((t, i) => {
    const y = 60 + ((height - 120) / Math.max(targetCount - 1, 1)) * i;
    nodes.push({
      id: t.id,
      label: t.name,
      kind: "target",
      x: width / 2 - 40,
      y,
    });
  });

  const responseByInd = new Map<string, Response>();
  for (const r of responses) responseByInd.set(r.indicator_id, r);

  indicators.forEach((ind, i) => {
    const y =
      60 + ((height - 120) / Math.max(indicators.length - 1, 1)) * i;
    nodes.push({
      id: ind.id,
      label: ind.name,
      kind: "indicator",
      x: width - 200,
      y,
    });
  });

  return (
    <div className="cv-medicine-wf-panel cv-medicine-wf-mechgraph">
      <div className="cv-medicine-wf-panel-header">
        <h3 className="cv-medicine-wf-panel-title">
          Mechanism overview
        </h3>
        <span className="cv-medicine-wf-chip cv-medicine-wf-chip--ghost">
          Schematic
        </span>
      </div>

      <div className="cv-medicine-wf-mechgraph-wrap">
        <svg
          viewBox={`0 0 ${width} ${height}`}
          className="cv-medicine-wf-mechgraph-svg"
          role="img"
          aria-label="Mechanism overview"
        >
          {nodes
            .filter((n) => n.kind === "target")
            .map((n) => (
              <line
                key={`e-target-${n.id}`}
                x1={120}
                y1={height / 2}
                x2={n.x}
                y2={n.y}
                className="cv-medicine-wf-mechgraph-edge cv-medicine-wf-mechgraph-edge--target"
              />
            ))}

          {indicators.map((ind, i) => {
            const y =
              60 +
              ((height - 120) / Math.max(indicators.length - 1, 1)) * i;
            const r = responseByInd.get(ind.id);
            const cls =
              r && r.method === "observed"
                ? "cv-medicine-wf-mechgraph-edge--observed"
                : r && r.method === "mechanistic_inference"
                ? "cv-medicine-wf-mechgraph-edge--inferred"
                : "cv-medicine-wf-mechgraph-edge--insufficient";
            return (
              <line
                key={`e-ind-${ind.id}`}
                x1={width / 2 - 40}
                y1={height / 2}
                x2={width - 200}
                y2={y}
                className={`cv-medicine-wf-mechgraph-edge ${cls}`}
              />
            );
          })}

          {nodes.map((n) => (
            <g
              key={n.id}
              transform={`translate(${n.x},${n.y})`}
              className={`cv-medicine-wf-mechgraph-node cv-medicine-wf-mechgraph-node--${n.kind}`}
              onClick={() => onSelect?.(n.id)}
              role="button"
              tabIndex={0}
            >
              <circle r="22" />
              <text
                y="36"
                textAnchor="middle"
                className="cv-medicine-wf-mechgraph-label"
              >
                {n.label.length > 22
                  ? n.label.slice(0, 20) + "…"
                  : n.label}
              </text>
            </g>
          ))}
        </svg>
      </div>

      <div className="cv-medicine-wf-mechgraph-legend">
        <span className="cv-medicine-wf-mechgraph-legend-item cv-medicine-wf-mechgraph-edge--observed">
          Observed
        </span>
        <span className="cv-medicine-wf-mechgraph-legend-item cv-medicine-wf-mechgraph-edge--inferred">
          Inferred
        </span>
        <span className="cv-medicine-wf-mechgraph-legend-item cv-medicine-wf-mechgraph-edge--insufficient">
          Insufficient
        </span>
      </div>
    </div>
  );
}
