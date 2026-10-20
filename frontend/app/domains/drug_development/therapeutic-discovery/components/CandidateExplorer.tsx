/**
 * CureVerseAI — Drug Development
 * Workflow 03 — Therapeutic Discovery
 * CandidateExplorer.
 *
 * The candidate list — master side of the master-detail
 * pattern. Sortable table with the four evidence
 * dimensions. No composite score.
 */

"use client";

import { useMemo, useState } from "react";

import type {
  CandidateBlock,
  CandidateComparisonBlock,
  TherapeuticDiscoveryResult,
} from "../types";

import {
  useTDSelection,
  useTDFilters,
  useTDActions,
} from "../state";

import {
  ACTIVITY_QUALITY_LABELS,
  MECHANISM_LINK_LABELS,
  type CandidateSortKey,
} from "./types";

interface CandidateExplorerProps {
  result: TherapeuticDiscoveryResult;
}

const QUALITY_RANK = {
  measured: 0,
  qualitative: 1,
  none: 2,
} as const;

const LINK_RANK = {
  direct: 0,
  two_hop: 1,
  indirect: 2,
} as const;

type Row = {
  candidate: CandidateBlock;
  comparison: CandidateComparisonBlock | null;
};

function sortCandidates(
  rows: Row[],
  key: CandidateSortKey,
  ascending: boolean,
): Row[] {
  const sorted = [...rows].sort((a, b) => {
    const ac = a.comparison;
    const bc = b.comparison;

    switch (key) {
      case "activity_quality": {
        const av = ac ? QUALITY_RANK[ac.activity_quality] : 99;
        const bv = bc ? QUALITY_RANK[bc.activity_quality] : 99;
        return av - bv;
      }
      case "mechanism_link_strength": {
        const av = ac
          ? LINK_RANK[ac.mechanism_link_strength]
          : 99;
        const bv = bc
          ? LINK_RANK[bc.mechanism_link_strength]
          : 99;
        return av - bv;
      }
      case "evidence_diversity": {
        const av = ac?.evidence_diversity ?? 0;
        const bv = bc?.evidence_diversity ?? 0;
        return bv - av;
      }
      case "data_gaps": {
        const av = ac?.data_gaps ?? 0;
        const bv = bc?.data_gaps ?? 0;
        return av - bv;
      }
      case "compound_id":
      default:
        return a.candidate.compound_id.localeCompare(
          b.candidate.compound_id,
        );
    }
  });

  return ascending ? sorted.reverse() : sorted;
}

export default function CandidateExplorer({
  result,
}: CandidateExplorerProps) {
  const selection = useTDSelection();
  const filters = useTDFilters();
  const actions = useTDActions();

  const [sortKey, setSortKey] = useState<CandidateSortKey>(
    "activity_quality",
  );
  const [ascending, setAscending] = useState(false);

  const selectedId =
    selection.selected?.kind === "candidate"
      ? selection.selected.compound_id
      : null;

  const rows = useMemo<Row[]>(() => {
    const byId = new Map<string, CandidateComparisonBlock>();
    for (const c of result.candidate_comparisons) {
      byId.set(c.candidate_id, c);
    }
    return result.candidates.map((candidate) => ({
      candidate,
      comparison: byId.get(candidate.compound_id) ?? null,
    }));
  }, [result.candidates, result.candidate_comparisons]);

  const visible = useMemo(() => {
    return rows.filter((r) => {
      if (!filters.visibleActivityQualities.size) return true;
      const q = r.comparison?.activity_quality ?? "none";
      return filters.visibleActivityQualities.has(q);
    });
  }, [rows, filters.visibleActivityQualities]);

  const sorted = useMemo(
    () => sortCandidates(visible, sortKey, ascending),
    [visible, sortKey, ascending],
  );

  const handleSort = (key: CandidateSortKey) => {
    if (sortKey === key) setAscending((v) => !v);
    else {
      setSortKey(key);
      setAscending(false);
    }
  };

  const summary = useMemo(() => {
    const s = {
      total: rows.length,
      ranked: result.candidate_comparisons.length,
      measured: 0,
      qualitative: 0,
      none: 0,
    };
    for (const c of result.candidate_comparisons) {
      s[c.activity_quality] += 1;
    }
    return s;
  }, [rows, result.candidate_comparisons]);

  if (!rows.length) return null;

  return (
    <section className="cv-thedisc-explorer">
      <header className="cv-thedisc-explorer-head">
        <div>
          <span className="cv-thedisc-explorer-eyebrow">
            CANDIDATE COMPOUNDS
          </span>
          <strong>
            {summary.total} candidates · top{" "}
            {summary.ranked} ranked below
          </strong>
        </div>
        <div className="cv-thedisc-explorer-summary">
          <span>
            <i style={{ background: "#7bcab5" }} />
            {summary.measured} measured
          </span>
          <span>
            <i style={{ background: "#e9c58c" }} />
            {summary.qualitative} qualitative
          </span>
          <span>
            <i style={{ background: "#888e90" }} />
            {summary.none} no activity
          </span>
          <span>
            <i style={{ background: "#5f5b55" }} />
            {summary.total - summary.ranked} not ranked
          </span>
        </div>
      </header>

      <div className="cv-thedisc-explorer-filters">
        {(["measured", "qualitative", "none"] as const).map(
          (q) => (
            <button
              key={q}
              type="button"
              className={
                "cv-thedisc-explorer-filter" +
                (filters.visibleActivityQualities.has(q)
                  ? " is-on"
                  : "")
              }
              onClick={() =>
                actions.toggleActivityQuality(q)
              }
            >
              {ACTIVITY_QUALITY_LABELS[q]}
            </button>
          ),
        )}
      </div>

      <div className="cv-thedisc-explorer-table-wrap">
        <table className="cv-thedisc-explorer-table">
          <thead>
            <tr>
              <th>Compound</th>
              <th
                className={
                  sortKey === "activity_quality"
                    ? "is-sorted"
                    : ""
                }
                onClick={() =>
                  handleSort("activity_quality")
                }
              >
                Activity
                {sortKey === "activity_quality"
                  ? ascending
                    ? " ↑"
                    : " ↓"
                  : ""}
              </th>
              <th
                className={
                  sortKey === "mechanism_link_strength"
                    ? "is-sorted"
                    : ""
                }
                onClick={() =>
                  handleSort("mechanism_link_strength")
                }
              >
                Link
                {sortKey === "mechanism_link_strength"
                  ? ascending
                    ? " ↑"
                    : " ↓"
                  : ""}
              </th>
              <th
                className={
                  sortKey === "evidence_diversity"
                    ? "is-sorted"
                    : ""
                }
                onClick={() =>
                  handleSort("evidence_diversity")
                }
              >
                Sources
                {sortKey === "evidence_diversity"
                  ? ascending
                    ? " ↑"
                    : " ↓"
                  : ""}
              </th>
              <th
                className={
                  sortKey === "data_gaps"
                    ? "is-sorted"
                    : ""
                }
                onClick={() => handleSort("data_gaps")}
              >
                Gaps
                {sortKey === "data_gaps"
                  ? ascending
                    ? " ↑"
                    : " ↓"
                  : ""}
              </th>
            </tr>
          </thead>
          <tbody>
            {sorted.slice(0, 100).map((row) => {
              const c = row.candidate;
              const comp = row.comparison;
              const isSelected =
                selectedId === c.compound_id;

              return (
                <tr
                  key={c.compound_id}
                  className={
                    isSelected ? "is-selected" : ""
                  }
                  onClick={() =>
                    actions.select({
                      kind: "candidate",
                      compound_id: c.compound_id,
                    })
                  }
                >
                  <td>
                    <div className="cv-thedisc-explorer-cell-name">
                      <strong>
                        {c.name ?? c.compound_id}
                      </strong>
                      {c.name ? (
                        <span>{c.compound_id}</span>
                      ) : null}
                    </div>
                  </td>
                  <td>
                    {comp
                      ? ACTIVITY_QUALITY_LABELS[
                          comp.activity_quality
                        ]
                      : "not ranked"}
                  </td>
                  <td>
                    {comp
                      ? MECHANISM_LINK_LABELS[
                          comp.mechanism_link_strength
                        ]
                      : "—"}
                  </td>
                  <td>
                    {comp ? comp.evidence_diversity : "—"}
                  </td>
                  <td>
                    {comp ? comp.data_gaps : "—"}
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
        {sorted.length > 100 ? (
          <p className="cv-thedisc-explorer-note">
            Showing the first 100 of {sorted.length}{" "}
            candidates. Refine filters to narrow the list.
          </p>
        ) : null}
      </div>
    </section>
  );
}
