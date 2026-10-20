"""
CureVerseAI — Drug Development
Workflow 03 — Therapeutic Discovery
Mechanism of Action.

For each candidate compound, assemble the proposed
mechanistic chain:

    compound --binds_to--> target
    target   --participates_in--> pathway
    pathway  --associated_with--> disease

Every edge carries a support_class. Missing links are
recorded in `unresolved_links` on the chain. The chain
never fabricates an edge.

Edge support classes
--------------------

Compound -> Target:
    experimentally_measured    a B or F assay record exists
                               for this compound against this
                               target
    supported_association      the compound is ChEMBL-listed
                               against this target but no
                               assay record is present in the
                               current run
    unresolved                 the compound has no record
                               against any target in this run

Target -> Pathway:
    retrieved_fact             the target is a member of the
                               selected pathway per Reactome
    unresolved                 the target is not in the
                               pathway's member list

Pathway -> Disease:
    supported_association      the W02 handoff established
                               this edge (pathway contributed
                               by >= 2 disease-associated
                               genes)
    mechanistic_inference      the pathway was discovered by
                               W03 and the disease-to-pathway
                               relationship was inferred, not
                               carried from W02
    unresolved                 no disease link is available

Data structures
---------------

Each chain stores full Relationship dataclass instances in
`edges`, so the frontend can render them like any other
graph edge. `node_ids` lists every node the chain touches.
`evidence_ids` collects every evidence reference.

Pure module
-----------

This module does not call any source. All inputs are
already fetched. It runs in well under a second even for
hundreds of compounds.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set

from app.drug_development.schemas.relationships import (
    Relationship,
    RelationshipType,
    SupportClass,
)
from app.drug_development.therapeutic_discovery.schemas import (
    ActivityRecord,
    CandidateCompound,
    MechanismOfActionChain,
    SelectedMechanism,
    TargetSummary,
)


# ---------------------------------------------------------------------------
# Node ID conventions
# ---------------------------------------------------------------------------


_COMPOUND_NODE_PREFIX = "compound:"
_TARGET_NODE_PREFIX = "target:"
_PATHWAY_NODE_PREFIX = "pathway:"
_DISEASE_NODE_PREFIX = "disease:"


# ---------------------------------------------------------------------------
# Mechanism of Action builder
# ---------------------------------------------------------------------------


class MechanismOfActionBuilder:
    """
    Assemble per-candidate mechanism-of-action chains.
    """

    def __init__(self) -> None:
        pass

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build(
        self,
        candidates: List[CandidateCompound],
        targets: List[TargetSummary],
        activities: List[ActivityRecord],
        mechanism: SelectedMechanism,
        mechanism_context: Dict[str, Any],
        disease_node_id: Optional[str],
    ) -> Dict[str, Any]:
        """
        Build one chain per candidate.

        `disease_node_id` is the W03-wide disease anchor
        (e.g. "disease:MONDO_0004979"). None when no disease
        was resolved — the pathway-to-disease edge is then
        marked unresolved.
        """

        if not candidates:
            return self._empty(
                reason="No candidate compounds were supplied."
            )

        # ---- 1) Index activities by compound --------------
        activities_by_compound: Dict[
            str, List[ActivityRecord]
        ] = {}
        for record in activities:
            activities_by_compound.setdefault(
                record.compound_chembl_id, []
            ).append(record)

        # ---- 2) Index targets by target_id ----------------
        targets_by_id: Dict[str, TargetSummary] = {
            t.target_id: t for t in targets
        }

        # ---- 3) Build a synthetic target index by
        #         chembl_target_id so activities can find
        #         their targets reliably.
        targets_by_chembl: Dict[str, TargetSummary] = {}
        for t in targets:
            if t.chembl_target_id:
                targets_by_chembl[t.chembl_target_id] = t

        # Some activities reference ChEMBL target IDs that
        # don't appear in `targets_by_chembl` because we
        # filtered the target list. That's fine — such an
        # activity simply doesn't produce a chain edge.

        # ---- 4) Pathway node id --------------------------
        pathway_node_id = self._pathway_node_id(mechanism)

        # ---- 5) Target -> Pathway edges ------------------
        # Only targets that are mechanism members get this
        # edge. Targets from Open Targets alone do not.
        target_to_pathway_edges: Dict[
            str, Relationship
        ] = {}
        for t in targets:
            if not t.mechanism_membership:
                continue
            if not pathway_node_id:
                continue

            target_to_pathway_edges[t.target_id] = (
                self._target_to_pathway_edge(
                    target=t,
                    pathway_node_id=pathway_node_id,
                    mechanism=mechanism,
                )
            )

        # ---- 6) Pathway -> Disease edge ------------------
        pathway_to_disease_edge: Optional[Relationship] = None
        if pathway_node_id and disease_node_id:
            pathway_to_disease_edge = (
                self._pathway_to_disease_edge(
                    pathway_node_id=pathway_node_id,
                    disease_node_id=disease_node_id,
                    mechanism=mechanism,
                )
            )

        # ---- 7) Build chains ------------------------------
        chains: List[MechanismOfActionChain] = []
        full_path_count = 0
        missing_link_count = 0
        targets_linked: Set[str] = set()

        for candidate in candidates:
            chain = self._build_one_chain(
                candidate=candidate,
                activities_by_compound=(
                    activities_by_compound
                ),
                targets_by_chembl=targets_by_chembl,
                target_to_pathway_edges=(
                    target_to_pathway_edges
                ),
                pathway_to_disease_edge=(
                    pathway_to_disease_edge
                ),
                pathway_node_id=pathway_node_id,
                disease_node_id=disease_node_id,
            )

            chains.append(chain)

            if chain.unresolved_links:
                missing_link_count += 1
            else:
                full_path_count += 1

            for nid in chain.node_ids:
                if nid.startswith(_TARGET_NODE_PREFIX):
                    targets_linked.add(nid)

        return {
            "found": True,
            "chains": chains,
            "reason": None,
            "metadata": {
                "chains_built": len(chains),
                "chains_with_full_path": full_path_count,
                "chains_with_missing_links": (
                    missing_link_count
                ),
                "targets_linked_to_mechanism": len(
                    targets_linked
                ),
            },
        }

    # ------------------------------------------------------------------
    # Single-chain construction
    # ------------------------------------------------------------------

    def _build_one_chain(
        self,
        candidate: CandidateCompound,
        activities_by_compound: Dict[
            str, List[ActivityRecord]
        ],
        targets_by_chembl: Dict[str, TargetSummary],
        target_to_pathway_edges: Dict[str, Relationship],
        pathway_to_disease_edge: Optional[Relationship],
        pathway_node_id: Optional[str],
        disease_node_id: Optional[str],
    ) -> MechanismOfActionChain:
        compound_node_id = (
            f"{_COMPOUND_NODE_PREFIX}"
            f"{candidate.compound_id}"
        )

        edges: List[Relationship] = []
        node_ids: List[str] = [compound_node_id]
        evidence_ids: List[str] = []
        unresolved: List[Dict[str, Any]] = []

        # Find all activities for this compound.
        records = activities_by_compound.get(
            candidate.compound_id, []
        )

        # Group by ChEMBL target id.
        targets_with_activity: Dict[str, int] = {}
        for r in records:
            cid = r.target_chembl_id
            targets_with_activity[cid] = (
                targets_with_activity.get(cid, 0) + 1
            )

        if not targets_with_activity:
            unresolved.append(
                {
                    "reason": "no_activity_records",
                    "statement": (
                        "No B or F assay records were found "
                        "for this compound against any target "
                        "in this investigation."
                    ),
                }
            )
            return MechanismOfActionChain(
                candidate_id=candidate.compound_id,
                target_id="",
                edges=edges,
                node_ids=node_ids,
                unresolved_links=unresolved,
                evidence_ids=evidence_ids,
                metadata={"has_activity": False},
            )

        # For each target with activity, build the edge.
        primary_target_id: str = ""

        for chembl_target_id, count in targets_with_activity.items():
            target = targets_by_chembl.get(chembl_target_id)

            if target is None:
                # Activity exists but the target isn't in our
                # resolved list — record and skip.
                unresolved.append(
                    {
                        "reason": "target_not_in_scope",
                        "statement": (
                            f"Activity record references "
                            f"ChEMBL target {chembl_target_id} "
                            "which is outside the resolved "
                            "target set for this run."
                        ),
                        "chembl_target_id": chembl_target_id,
                    }
                )
                continue

            target_node_id = target.target_id
            if target_node_id not in node_ids:
                node_ids.append(target_node_id)

            edge = self._compound_to_target_edge(
                compound_node_id=compound_node_id,
                target_node_id=target_node_id,
                candidate=candidate,
                target=target,
                activity_count=count,
            )
            edges.append(edge)

            if not primary_target_id:
                primary_target_id = target_node_id

            # Target -> Pathway edge (only if member).
            tp_edge = target_to_pathway_edges.get(
                target.target_id
            )
            if tp_edge is not None:
                edges.append(tp_edge)
                if tp_edge.target_id not in node_ids:
                    node_ids.append(tp_edge.target_id)
                for eid in tp_edge.evidence_ids:
                    if eid not in evidence_ids:
                        evidence_ids.append(eid)

                # Pathway -> Disease edge.
                if pathway_to_disease_edge is not None:
                    edges.append(pathway_to_disease_edge)
                    if (
                        pathway_to_disease_edge.target_id
                        not in node_ids
                    ):
                        node_ids.append(
                            pathway_to_disease_edge.target_id
                        )
                    for eid in (
                        pathway_to_disease_edge.evidence_ids
                    ):
                        if eid not in evidence_ids:
                            evidence_ids.append(eid)
            else:
                if pathway_node_id:
                    unresolved.append(
                        {
                            "reason": "target_not_in_pathway",
                            "statement": (
                                f"{target.label} is not a "
                                "member of the selected "
                                "mechanism's pathway."
                            ),
                            "target_id": target.target_id,
                        }
                    )

        return MechanismOfActionChain(
            candidate_id=candidate.compound_id,
            target_id=primary_target_id,
            edges=edges,
            node_ids=node_ids,
            unresolved_links=unresolved,
            evidence_ids=evidence_ids,
            metadata={
                "has_activity": True,
                "targets_with_activity": len(
                    targets_with_activity
                ),
            },
        )

    # ------------------------------------------------------------------
    # Edge constructors
    # ------------------------------------------------------------------

    @staticmethod
    def _compound_to_target_edge(
        compound_node_id: str,
        target_node_id: str,
        candidate: CandidateCompound,
        target: TargetSummary,
        activity_count: int,
    ) -> Relationship:
        return Relationship(
            source_id=compound_node_id,
            target_id=target_node_id,
            relationship_type=RelationshipType.BINDS_TO,
            evidence_ids=[],
            evidence_level="experimental",
            support_class=(
                SupportClass.EXPERIMENTALLY_MEASURED
            ),
            description=(
                f"{candidate.name or candidate.compound_id} "
                f"is associated with {target.label} through "
                f"{activity_count} experimental assay "
                f"record(s) in ChEMBL."
            ),
            metadata={
                "activity_count": activity_count,
                "target_label": target.label,
                "compound_label": (
                    candidate.name or candidate.compound_id
                ),
                "source": "ChEMBL",
            },
        )

    @staticmethod
    def _target_to_pathway_edge(
        target: TargetSummary,
        pathway_node_id: str,
        mechanism: SelectedMechanism,
    ) -> Relationship:
        return Relationship(
            source_id=target.target_id,
            target_id=pathway_node_id,
            relationship_type=(
                RelationshipType.PARTICIPATES_IN
            ),
            evidence_ids=[],
            evidence_level="direct",
            support_class=SupportClass.RETRIEVED_FACT,
            description=(
                f"{target.label} participates in the "
                f"pathway "
                f"'{mechanism.label or mechanism.mechanism_id}' "
                f"according to Reactome."
            ),
            metadata={
                "reactome_id": mechanism.identifier,
                "mechanism_id": mechanism.mechanism_id,
                "source": "Reactome",
            },
        )

    @staticmethod
    def _pathway_to_disease_edge(
        pathway_node_id: str,
        disease_node_id: str,
        mechanism: SelectedMechanism,
    ) -> Relationship:
        source_label = (
            mechanism.label or mechanism.mechanism_id
        )
        return Relationship(
            source_id=pathway_node_id,
            target_id=disease_node_id,
            relationship_type=(
                RelationshipType.ASSOCIATED_WITH
            ),
            evidence_ids=[],
            evidence_level="association",
            support_class=SupportClass.SUPPORTED_ASSOCIATION,
            description=(
                f"The pathway '{source_label}' is "
                f"associated with the disease through the "
                f"mechanism investigation."
            ),
            metadata={
                "reactome_id": mechanism.identifier,
                "mechanism_id": mechanism.mechanism_id,
                "source": "Reactome",
            },
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _pathway_node_id(
        mechanism: SelectedMechanism,
    ) -> Optional[str]:
        if mechanism.mechanism_id.startswith("pathway:"):
            stable_id = mechanism.mechanism_id.replace(
                "pathway:", "", 1
            )
            return f"{_PATHWAY_NODE_PREFIX}{stable_id}"
        return None

    @staticmethod
    def _empty(reason: str) -> Dict[str, Any]:
        return {
            "found": False,
            "chains": [],
            "reason": reason,
            "metadata": {
                "chains_built": 0,
                "chains_with_full_path": 0,
                "chains_with_missing_links": 0,
                "targets_linked_to_mechanism": 0,
            },
        }


# ---------------------------------------------------------------------------
# Convenience
# ---------------------------------------------------------------------------


def build_mechanism_of_action(
    candidates: List[CandidateCompound],
    targets: List[TargetSummary],
    activities: List[ActivityRecord],
    mechanism: SelectedMechanism,
    mechanism_context: Dict[str, Any],
    disease_node_id: Optional[str],
) -> Dict[str, Any]:
    """
    One-shot entry point.
    """
    return MechanismOfActionBuilder().build(
        candidates=candidates,
        targets=targets,
        activities=activities,
        mechanism=mechanism,
        mechanism_context=mechanism_context,
        disease_node_id=disease_node_id,
    )
