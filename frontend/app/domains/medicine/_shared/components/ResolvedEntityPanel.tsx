"use client";

/**
 * CureVerseAI — Medicine domain
 * Resolved entity panel.
 *
 * Shows the identity the backend resolved for a disease, cell
 * context, or intervention. Fields are rendered as "—" when
 * absent. Nothing is fabricated.
 */

import type {
  CellContext,
  DiseaseRef,
  InterventionRef,
} from "../types";

interface Row {
  label: string;
  value: string | null;
  hint?: string;
}

function toRow(label: string, value: string | null | undefined, hint?: string): Row {
  const v = value === undefined || value === null || value === ""
    ? null
    : String(value);
  return { label, value: v, hint };
}

function entityRows(
  entity: DiseaseRef | CellContext | InterventionRef | null,
): Row[] {
  if (!entity) return [];

  if ("resolution_status" in entity && "identifiers" in entity) {
    // DiseaseRef
    const d = entity as DiseaseRef;
    return [
      toRow("Name", d.name),
      toRow("Canonical id", d.id),
      toRow("Source", d.source),
      toRow("Status", d.resolution_status),
    ];
  }

  if ("ontology_id" in entity && "source" in entity) {
    // CellContext
    const c = entity as CellContext;
    return [
      toRow("Name", c.name),
      toRow("Ontology id", c.ontology_id),
      toRow("Source", c.source),
    ];
  }

  if ("targets" in entity) {
    // InterventionRef
    const i = entity as InterventionRef;
    return [
      toRow("Name", i.name),
      toRow("Canonical id", i.id),
      toRow("Source", i.source),
      toRow("Source id", i.source_id),
      toRow("Type", i.intervention_type),
      toRow("Targets", String(i.targets.length)),
    ];
  }

  return [];
}

interface Props {
  title: string;
  entity: DiseaseRef | CellContext | InterventionRef | null;
}

export default function ResolvedEntityPanel({ title, entity }: Props) {
  const rows = entityRows(entity);

  if (!entity || rows.length === 0) {
    return (
      <div className="cv-medicine-wf-panel">
        <div className="cv-medicine-wf-panel-header">
          <h3 className="cv-medicine-wf-panel-title">{title}</h3>
        </div>
        <div className="cv-medicine-wf-empty-inline">
          Not resolved.
        </div>
      </div>
    );
  }

  return (
    <div className="cv-medicine-wf-panel cv-medicine-wf-entity">
      <div className="cv-medicine-wf-panel-header">
        <h3 className="cv-medicine-wf-panel-title">{title}</h3>
      </div>
      <dl className="cv-medicine-wf-entity-list">
        {rows.map((row) => (
          <div
            key={row.label}
            className="cv-medicine-wf-entity-row"
            title={row.hint}
          >
            <dt>{row.label}</dt>
            <dd>{row.value ?? "—"}</dd>
          </div>
        ))}
      </dl>
    </div>
  );
}
