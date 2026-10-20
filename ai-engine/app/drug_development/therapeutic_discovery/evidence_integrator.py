"""
CureVerseAI — Drug Development
Workflow 03 — Therapeutic Discovery
Evidence Integrator.

Produces the reasoning payload and provenance block for a
W03 run.

Reasoning sections
------------------

supported_findings
    Statements backed by experimental or database records.
    Each finding cites the evidence or counts that produced
    it.

hypotheses
    Inferred connections and plausibility statements.
    Clearly labeled as hypotheses; never presented as
    established knowledge.

conflicts
    Contradictory evidence preserved side-by-side. W03
    records conflicts only when they exist in the data —
    it does not invent disagreement.

evidence_gaps
    Explicit missing links. Every gap is either a step
    the pipeline attempted and could not complete, or a
    state the workflow openly does not cover in this
    phase (e.g. clinical outcomes).

Fixed limitations
-----------------

W03 has a fixed limitations list describing what the
workflow does NOT claim:

    - molecular activity is not a clinical claim
    - ChEMBL records are assay observations
    - mechanism-of-action chains are hypotheses
    - candidate comparisons are not a therapeutic ranking
    - no clinical recommendation is produced

These limitations are always present.

Provenance
----------

Sources queried, source failures, and total records
retrieved are all recorded. A missing source does not
silently become a successful empty result — the failure
is in the provenance block.

Pure module, no I/O.
"""

from __future__ import annotations

from typing import Any, Dict, List

from app.drug_development.therapeutic_discovery.schemas import (
    ActivityRecord,
    CandidateComparison,
    CandidateCompound,
    MechanismOfActionChain,
    ProvenanceBlock,
    ReasoningBlock,
    SelectedMechanism,
    TargetSummary,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


FIXED_LIMITATIONS = [
    (
        "Molecular activity is not a clinical claim. A "
        "compound measured against a target is not thereby "
        "effective or safe in patients."
    ),
    (
        "ChEMBL activity records are assay observations. "
        "They establish what has been measured, not what "
        "will happen in a clinical setting."
    ),
    (
        "Mechanism-of-action chains in this workflow are "
        "supported hypotheses, not proven disease-modifying "
        "mechanisms."
    ),
    (
        "Candidate comparisons expose evidence dimensions. "
        "They do not rank candidates by therapeutic value, "
        "and no composite score exists."
    ),
    (
        "This workflow does not produce clinical "
        "recommendations, dosing, or safety judgements."
    ),
    (
        "Target relevance to the disease is sourced from "
        "Open Targets association evidence. It is not a "
        "causal claim."
    ),
]


# ---------------------------------------------------------------------------
# Integrator
# ---------------------------------------------------------------------------


class EvidenceIntegrator:
    """
    Merge candidate, activity, chain, and target data into
    a structured reasoning payload.
    """

    def __init__(self) -> None:
        pass

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def integrate(
        self,
        disease_label: str,
        mechanism: SelectedMechanism,
        targets: List[TargetSummary],
        candidates: List[CandidateCompound],
        activities: List[ActivityRecord],
        chains: List[MechanismOfActionChain],
        comparisons: List[CandidateComparison],
        sources_queried: List[str],
        source_failures: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Build the reasoning payload.
        """

        supported = self._build_supported_findings(
            disease_label=disease_label,
            mechanism=mechanism,
            targets=targets,
            candidates=candidates,
            activities=activities,
            chains=chains,
            comparisons=comparisons,
        )

        hypotheses = self._build_hypotheses(
            disease_label=disease_label,
            mechanism=mechanism,
            targets=targets,
            candidates=candidates,
        )

        conflicts = self._build_conflicts(
            activities=activities,
        )

        gaps = self._build_evidence_gaps(
            mechanism=mechanism,
            targets=targets,
            candidates=candidates,
            chains=chains,
        )

        summary = self._build_summary(
            disease_label=disease_label,
            mechanism=mechanism,
            targets=targets,
            candidates=candidates,
            activities=activities,
        )

        reasoning = ReasoningBlock(
            supported_findings=supported,
            hypotheses=hypotheses,
            conflicts=conflicts,
            evidence_gaps=gaps,
        )

        provenance = ProvenanceBlock(
            sources_queried=list(sources_queried),
            source_failures=list(source_failures),
            records_retrieved=(
                len(candidates)
                + len(activities)
                + len(targets)
            ),
            metadata={
                "candidates": len(candidates),
                "activities": len(activities),
                "targets": len(targets),
                "chains": len(chains),
            },
        )

        return {
            "summary": summary,
            "reasoning": reasoning,
            "provenance": provenance,
            "limitations": list(FIXED_LIMITATIONS),
            "metadata": {
                "supported_findings": len(supported),
                "hypotheses": len(hypotheses),
                "conflicts": len(conflicts),
                "evidence_gaps": len(gaps),
            },
        }

    # ------------------------------------------------------------------
    # Supported findings
    # ------------------------------------------------------------------

    @staticmethod
    def _build_supported_findings(
        disease_label: str,
        mechanism: SelectedMechanism,
        targets: List[TargetSummary],
        candidates: List[CandidateCompound],
        activities: List[ActivityRecord],
        chains: List[MechanismOfActionChain],
        comparisons: List[CandidateComparison],
    ) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []

        mech_label = mechanism.label or mechanism.mechanism_id

        out.append(
            {
                "type": "mechanism",
                "statement": (
                    f"The investigation focused on the "
                    f"biological process '{mech_label}'."
                ),
                "mechanism_id": mechanism.mechanism_id,
                "source": mechanism.source,
            }
        )

        out.append(
            {
                "type": "targets",
                "statement": (
                    f"{len(targets)} candidate targets were "
                    f"identified from the mechanism and "
                    f"Open Targets disease associations."
                ),
                "count": len(targets),
            }
        )

        if candidates:
            out.append(
                {
                    "type": "candidates",
                    "statement": (
                        f"{len(candidates)} candidate "
                        f"compounds were retrieved from "
                        f"ChEMBL."
                    ),
                    "count": len(candidates),
                }
            )

        measured = sum(
            1
            for c in comparisons
            if c.activity_quality == "measured"
        )
        if measured > 0:
            out.append(
                {
                    "type": "measured_activity",
                    "statement": (
                        f"{measured} candidates have at "
                        f"least one measured activity "
                        f"record (IC50, Ki, or EC50) in "
                        f"ChEMBL."
                    ),
                    "count": measured,
                }
            )

        full_chains = sum(
            1 for c in chains if not c.unresolved_links
        )
        if full_chains > 0:
            out.append(
                {
                    "type": "mechanism_links",
                    "statement": (
                        f"{full_chains} candidates have a "
                        f"complete chain connecting the "
                        f"compound to its target, to the "
                        f"mechanism's pathway, and to the "
                        f"disease."
                    ),
                    "count": full_chains,
                }
            )

        if not candidates:
            out.append(
                {
                    "type": "no_candidates",
                    "statement": (
                        "No candidate compounds were "
                        "retrieved for the identified "
                        "targets."
                    ),
                }
            )

        return out

    # ------------------------------------------------------------------
    # Hypotheses
    # ------------------------------------------------------------------

    @staticmethod
    def _build_hypotheses(
        disease_label: str,
        mechanism: SelectedMechanism,
        targets: List[TargetSummary],
        candidates: List[CandidateCompound],
    ) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []

        mech_label = mechanism.label or mechanism.mechanism_id

        if targets and candidates:
            top_targets = [
                t.label
                for t in targets
                if t.mechanism_membership
            ][:5]

            if top_targets:
                out.append(
                    {
                        "type": "mechanism_hypothesis",
                        "statement": (
                            f"Modifying {mech_label} through "
                            f"the targets "
                            f"{', '.join(top_targets)} "
                            f"may affect {disease_label}. "
                            f"This is a mechanism hypothesis, "
                            f"not a demonstrated clinical "
                            f"effect."
                        ),
                        "targets": top_targets,
                        "mechanism_id": mechanism.mechanism_id,
                    }
                )

        out.append(
            {
                "type": "evidence_plausibility",
                "statement": (
                    "A compound with measured activity "
                    "against a target in the mechanism's "
                    "pathway is a plausible candidate for "
                    "further experimental investigation. "
                    "Plausibility is not efficacy."
                ),
            }
        )

        return out

    # ------------------------------------------------------------------
    # Conflicts
    # ------------------------------------------------------------------

    @staticmethod
    def _build_conflicts(
        activities: List[ActivityRecord],
    ) -> List[Dict[str, Any]]:
        """
        Detect cases where multiple assays for the same
        compound-target pair report numeric values that
        differ substantially.
        """

        out: List[Dict[str, Any]] = []

        # Group measured values by (compound, target).
        grouped: Dict[
            tuple, List[ActivityRecord]
        ] = {}

        for r in activities:
            classification = (r.metadata or {}).get(
                "classification"
            )
            if classification != "measured_potency":
                continue

            key = (r.compound_chembl_id, r.target_chembl_id)
            grouped.setdefault(key, []).append(r)

        for (cid, tid), records in grouped.items():
            if len(records) < 2:
                continue

            # Collect numeric values in nM where possible.
            values: List[float] = []
            for r in records:
                v = _to_float(r.standard_value)
                if v is None or v <= 0:
                    continue
                if (r.standard_units or "").lower() not in (
                    "nm",
                    "nanomolar",
                ):
                    continue
                values.append(v)

            if len(values) < 2:
                continue

            lo = min(values)
            hi = max(values)
            if lo <= 0:
                continue

            ratio = hi / lo
            if ratio < 100:
                continue

            out.append(
                {
                    "type": "conflicting_activity",
                    "statement": (
                        f"{cid} has measured activity "
                        f"against {tid} across "
                        f"{len(values)} assays with values "
                        f"spanning {lo:.1f} nM to {hi:.1f} "
                        f"nM (approx. {ratio:.0f}-fold "
                        f"spread). Both measurements are "
                        f"preserved."
                    ),
                    "compound_chembl_id": cid,
                    "target_chembl_id": tid,
                    "min_value_nm": lo,
                    "max_value_nm": hi,
                    "assay_count": len(values),
                }
            )

        return out

    # ------------------------------------------------------------------
    # Evidence gaps
    # ------------------------------------------------------------------

    @staticmethod
    def _build_evidence_gaps(
        mechanism: SelectedMechanism,
        targets: List[TargetSummary],
        candidates: List[CandidateCompound],
        chains: List[MechanismOfActionChain],
    ) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []

        if not mechanism.identifier:
            out.append(
                {
                    "type": "mechanism_identifier",
                    "statement": (
                        "The mechanism under investigation "
                        "does not carry a stable external "
                        "identifier."
                    ),
                }
            )

        no_member_targets = [
            t.label
            for t in targets
            if not t.mechanism_membership
        ]
        if no_member_targets and len(no_member_targets) == len(
            targets
        ):
            out.append(
                {
                    "type": "target_mechanism_link",
                    "statement": (
                        "None of the candidate targets are "
                        "members of the selected mechanism's "
                        "pathway."
                    ),
                }
            )

        if not candidates:
            out.append(
                {
                    "type": "no_candidates",
                    "statement": (
                        "No candidate compounds were "
                        "identified. This is a state of the "
                        "sources consulted, not a claim that "
                        "no compounds exist."
                    ),
                }
            )

        unresolved_total = sum(
            len(c.unresolved_links) for c in chains
        )
        if unresolved_total > 0:
            out.append(
                {
                    "type": "chain_gaps",
                    "statement": (
                        f"{unresolved_total} link(s) across "
                        f"the candidate chains could not be "
                        f"established from the sources "
                        f"consulted."
                    ),
                    "count": unresolved_total,
                }
            )

        out.append(
            {
                "type": "clinical_evidence",
                "statement": (
                    "The workflow does not retrieve "
                    "clinical trial outcomes, safety data, "
                    "or patient-level evidence. Those are "
                    "outside the scope of the sources "
                    "consulted."
                ),
            }
        )

        return out

    # ------------------------------------------------------------------
    # Summary
    # ------------------------------------------------------------------

    @staticmethod
    def _build_summary(
        disease_label: str,
        mechanism: SelectedMechanism,
        targets: List[TargetSummary],
        candidates: List[CandidateCompound],
        activities: List[ActivityRecord],
    ) -> str:
        mech_label = mechanism.label or mechanism.mechanism_id

        parts = [
            f"Therapeutic discovery for '{disease_label}' "
            f"through the mechanism '{mech_label}'."
        ]

        parts.append(
            f"{len(targets)} candidate targets were "
            f"identified."
        )

        if candidates:
            parts.append(
                f"{len(candidates)} compounds were retrieved "
                f"from ChEMBL, with "
                f"{len(activities)} activity records."
            )
        else:
            parts.append(
                "No candidate compounds were retrieved for "
                "the identified targets."
            )

        parts.append(
            "Every activity record is preserved as "
            "reported. No potency averaging or composite "
            "candidate ranking is performed."
        )

        return " ".join(parts)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _to_float(value: Any) -> float | None:
    if value is None:
        return None
    try:
        return float(str(value).strip())
    except (TypeError, ValueError):
        return None


# ---------------------------------------------------------------------------
# Convenience
# ---------------------------------------------------------------------------


def integrate_evidence(
    disease_label: str,
    mechanism: SelectedMechanism,
    targets: List[TargetSummary],
    candidates: List[CandidateCompound],
    activities: List[ActivityRecord],
    chains: List[MechanismOfActionChain],
    comparisons: List[CandidateComparison],
    sources_queried: List[str],
    source_failures: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    One-shot entry point.
    """
    return EvidenceIntegrator().integrate(
        disease_label=disease_label,
        mechanism=mechanism,
        targets=targets,
        candidates=candidates,
        activities=activities,
        chains=chains,
        comparisons=comparisons,
        sources_queried=sources_queried,
        source_failures=source_failures,
    )
