"""
CureVerseAI — Drug Development
Workflow 03 — Therapeutic Discovery
Candidate Evaluation.

Produces a CandidateComparison for each candidate compound
using four orthogonal evidence dimensions.

Dimensions
----------

activity_quality
    "measured"    at least one activity record with
                  classification in
                  {measured_potency, out_of_range}
    "qualitative" only qualitative_activity records
    "none"        no activity records, or only
                  observational records

mechanism_link_strength
    "direct"      the candidate's chain reaches the
                  pathway AND the disease
    "two_hop"     the candidate reaches the pathway only,
                  or reaches the disease without going
                  through the pathway
    "indirect"    the candidate only reaches its target

evidence_diversity
    Count of distinct source names appearing in the
    chain's metadata.source fields. Typically 2
    (ChEMBL, Reactome), sometimes 3 (ChEMBL, Reactome,
    Open Targets). Never combined into a score.

data_gaps
    Count of unresolved_links on the chain.

No composite score
------------------

There is deliberately no combined number. A candidate
with measured activity but a broken pathway link is
not "better" or "worse" than one with supported links
but only qualitative activity. The frontend displays the
four dimensions separately and lets the user sort by
any single one.

Sort order (for the capped output list)
---------------------------------------

    1. activity_quality  measured > qualitative > none
    2. mechanism_link_strength  direct > two_hop > indirect
    3. evidence_diversity  higher first
    4. data_gaps  lower first
    5. candidate_id  alphabetical

Pure module, no I/O.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

from app.drug_development.therapeutic_discovery.schemas import (
    ActivityRecord,
    CandidateComparison,
    CandidateCompound,
    MechanismOfActionChain,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


_MAX_COMPARISONS = 20

_ACTIVITY_RANK = {
    "measured": 0,
    "qualitative": 1,
    "none": 2,
}

_LINK_RANK = {
    "direct": 0,
    "two_hop": 1,
    "indirect": 2,
}


# ---------------------------------------------------------------------------
# Evaluator
# ---------------------------------------------------------------------------


class CandidateEvaluator:
    """
    Produce CandidateComparison records for a set of
    candidates.
    """

    def __init__(self) -> None:
        pass

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def evaluate(
        self,
        candidates: List[CandidateCompound],
        activities: List[ActivityRecord],
        chains: List[MechanismOfActionChain],
    ) -> Dict[str, Any]:
        """
        Compute comparisons for every candidate.

        Returns the top-N as `comparisons` and the full
        list as `all_comparisons`.
        """

        if not candidates:
            return self._empty(
                reason="No candidates were supplied."
            )

        # ---- 1) Index activities by compound ---------------
        activities_by_cid: Dict[
            str, List[ActivityRecord]
        ] = {}
        for r in activities:
            activities_by_cid.setdefault(
                r.compound_chembl_id, []
            ).append(r)

        # ---- 2) Index chains by candidate -------------------
        chains_by_cid: Dict[
            str, MechanismOfActionChain
        ] = {
            c.candidate_id: c for c in chains
        }

        # ---- 3) Build comparisons ---------------------------
        all_comparisons: List[CandidateComparison] = []

        measured_count = 0
        qualitative_count = 0
        no_activity_count = 0

        direct_count = 0
        two_hop_count = 0
        indirect_count = 0

        for candidate in candidates:
            cid = candidate.compound_id

            activity_quality = self._activity_quality(
                activities_by_cid.get(cid, [])
            )

            chain = chains_by_cid.get(cid)
            link_strength = self._link_strength(chain)
            diversity = self._evidence_diversity(chain)
            gaps = (
                len(chain.unresolved_links) if chain else 0
            )

            comparison = CandidateComparison(
                candidate_id=cid,
                activity_quality=activity_quality,
                mechanism_link_strength=link_strength,
                evidence_diversity=diversity,
                data_gaps=gaps,
                notes=self._build_notes(
                    activity_quality=activity_quality,
                    link_strength=link_strength,
                    gaps=gaps,
                ),
                metadata={
                    "candidate_name": candidate.name,
                    "chain_present": chain is not None,
                },
            )

            all_comparisons.append(comparison)

            if activity_quality == "measured":
                measured_count += 1
            elif activity_quality == "qualitative":
                qualitative_count += 1
            else:
                no_activity_count += 1

            if link_strength == "direct":
                direct_count += 1
            elif link_strength == "two_hop":
                two_hop_count += 1
            else:
                indirect_count += 1

        # ---- 4) Sort ----------------------------------------
        all_comparisons.sort(
            key=lambda c: (
                _ACTIVITY_RANK.get(c.activity_quality, 99),
                _LINK_RANK.get(
                    c.mechanism_link_strength, 99
                ),
                -c.evidence_diversity,
                c.data_gaps,
                c.candidate_id,
            )
        )

        top = all_comparisons[:_MAX_COMPARISONS]

        return {
            "found": True,
            "comparisons": top,
            "all_comparisons": all_comparisons,
            "scores_by_candidate": {
                c.candidate_id: c
                for c in all_comparisons
            },
            "reason": None,
            "metadata": {
                "total_candidates": len(candidates),
                "measured": measured_count,
                "qualitative": qualitative_count,
                "no_activity": no_activity_count,
                "direct_links": direct_count,
                "two_hop_links": two_hop_count,
                "indirect_links": indirect_count,
                "capped_at": _MAX_COMPARISONS,
            },
        }

    # ------------------------------------------------------------------
    # Dimension computations
    # ------------------------------------------------------------------

    @staticmethod
    def _activity_quality(
        records: List[ActivityRecord],
    ) -> str:
        if not records:
            return "none"

        has_measured = False
        has_qualitative = False

        for r in records:
            classification = (r.metadata or {}).get(
                "classification"
            )
            if classification in {
                "measured_potency",
                "out_of_range",
            }:
                has_measured = True
            elif classification == "qualitative_activity":
                has_qualitative = True

        if has_measured:
            return "measured"
        if has_qualitative:
            return "qualitative"
        return "none"

    @staticmethod
    def _link_strength(
        chain: Optional[MechanismOfActionChain],
    ) -> str:
        if chain is None:
            return "indirect"

        node_ids = chain.node_ids

        reaches_target = any(
            nid.startswith("target:") for nid in node_ids
        )
        reaches_pathway = any(
            nid.startswith("pathway:") for nid in node_ids
        )
        reaches_disease = any(
            nid.startswith("disease:") for nid in node_ids
        )

        if reaches_target and reaches_pathway and reaches_disease:
            return "direct"

        if reaches_target and (
            reaches_pathway or reaches_disease
        ):
            return "two_hop"

        return "indirect"

    @staticmethod
    def _evidence_diversity(
        chain: Optional[MechanismOfActionChain],
    ) -> int:
        if chain is None:
            return 0

        sources: Set[str] = set()

        for edge in chain.edges:
            meta = getattr(edge, "metadata", None) or {}
            if isinstance(meta, dict):
                source = meta.get("source")
                if isinstance(source, str) and source:
                    sources.add(source)

        return len(sources)

    @staticmethod
    def _build_notes(
        activity_quality: str,
        link_strength: str,
        gaps: int,
    ) -> List[str]:
        notes: List[str] = []

        if activity_quality == "none":
            notes.append(
                "No experimental activity records were found "
                "for this compound."
            )
        elif activity_quality == "qualitative":
            notes.append(
                "Only qualitative activity was reported. No "
                "numeric potency is available."
            )

        if link_strength == "indirect":
            notes.append(
                "The compound reaches its target, but no "
                "supported chain to the mechanism's pathway "
                "or the disease is available."
            )
        elif link_strength == "two_hop":
            notes.append(
                "The chain reaches the pathway or the disease "
                "but not both."
            )

        if gaps > 0:
            notes.append(
                f"{gaps} link(s) in this candidate's chain "
                "could not be established from the sources "
                "consulted."
            )

        return notes

    # ------------------------------------------------------------------
    # Empty path
    # ------------------------------------------------------------------

    @staticmethod
    def _empty(reason: str) -> Dict[str, Any]:
        return {
            "found": False,
            "comparisons": [],
            "all_comparisons": [],
            "scores_by_candidate": {},
            "reason": reason,
            "metadata": {
                "total_candidates": 0,
                "measured": 0,
                "qualitative": 0,
                "no_activity": 0,
                "direct_links": 0,
                "two_hop_links": 0,
                "indirect_links": 0,
                "capped_at": _MAX_COMPARISONS,
            },
        }


# ---------------------------------------------------------------------------
# Convenience
# ---------------------------------------------------------------------------


def evaluate_candidates(
    candidates: List[CandidateCompound],
    activities: List[ActivityRecord],
    chains: List[MechanismOfActionChain],
) -> Dict[str, Any]:
    """
    One-shot entry point.
    """
    return CandidateEvaluator().evaluate(
        candidates=candidates,
        activities=activities,
        chains=chains,
    )
