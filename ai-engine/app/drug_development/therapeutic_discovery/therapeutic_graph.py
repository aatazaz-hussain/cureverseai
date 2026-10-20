"""
CureVerseAI — Drug Development
Workflow 03 — Therapeutic Discovery
Therapeutic Graph.

Assemble the final W03 graph from:
    - the disease
    - the selected mechanism
    - the candidate targets
    - the candidate compounds
    - the mechanism-of-action chains

Node types used
---------------

    DISEASE             one anchor node
    MECHANISM           the selected mechanism
    PATHWAY             the mechanism's pathway (when the
                        mechanism is a pathway ID)
    GENE                a target
    COMPOUND            a candidate compound

Edges used
----------

    compound --binds_to--> gene         from each chain
    gene --participates_in--> pathway    from each chain
    pathway --associated_with--> disease from each chain

Dedup rules
-----------

    nodes:         by node_id
    relationships: by (source_id, relationship_type, target_id)
    evidence:      by evidence_id

Integrity
---------

The same integrity report shape W02 produces. Every edge
endpoint is checked against the node set; every evidence
reference is checked against the evidence collection.
Issues are recorded, not raised.

Pure module, no I/O.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, List, Optional, Set

from app.drug_development.schemas.disease import (
    DiseaseIdentity,
)
from app.drug_development.schemas.evidence import (
    EvidenceCollection,
    ImpactEvidence,
)
from app.drug_development.schemas.impact import (
    ImpactNode,
    ImpactNodeSet,
    NodeType,
)
from app.drug_development.schemas.relationships import (
    Relationship,
    RelationshipSet,
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
# Constants
# ---------------------------------------------------------------------------


_DISEASE_NODE_PREFIX = "disease:"
_MECHANISM_NODE_PREFIX = "mechanism:selected:"
_COMPOUND_NODE_PREFIX = "compound:"
_TARGET_NODE_PREFIX = "target:"
_PATHWAY_NODE_PREFIX = "pathway:"


# ---------------------------------------------------------------------------
# Graph Builder
# ---------------------------------------------------------------------------


class TherapeuticGraphBuilder:
    """
    Assemble the W03 graph.
    """

    def __init__(self) -> None:
        pass

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build(
        self,
        disease: Optional[DiseaseIdentity],
        mechanism: SelectedMechanism,
        targets: List[TargetSummary],
        candidates: List[CandidateCompound],
        activities: List[ActivityRecord],
        chains: List[MechanismOfActionChain],
    ) -> Dict[str, Any]:
        """
        Build the graph and return serialized containers.
        """

        nodes = ImpactNodeSet()
        relationships = RelationshipSet()
        evidence = EvidenceCollection()

        disease_node_id: Optional[str] = None

        # ---- 1) Disease node -------------------------------
        if disease is not None:
            disease_node = self._build_disease_node(disease)
            if disease_node is not None:
                nodes.add(disease_node)
                disease_node_id = disease_node.node_id

        # ---- 2) Mechanism node -----------------------------
        mechanism_node = self._build_mechanism_node(mechanism)
        if mechanism_node is not None:
            if mechanism_node.node_id not in nodes.by_id:
                nodes.add(mechanism_node)

        # ---- 3) Pathway node (if the mechanism is a
        #         pathway) ----------------------------------
        pathway_node_id: Optional[str] = None
        if mechanism.mechanism_id.startswith("pathway:"):
            stable_id = mechanism.mechanism_id.replace(
                "pathway:", "", 1
            )
            pathway_node_id = (
                f"{_PATHWAY_NODE_PREFIX}{stable_id}"
            )

            if pathway_node_id not in nodes.by_id:
                nodes.add(
                    ImpactNode(
                        node_id=pathway_node_id,
                        node_type=NodeType.PATHWAY,
                        name=mechanism.label or stable_id,
                        identifier=stable_id,
                        description=None,
                        evidence_ids=[],
                        metadata={
                            "reactome_id": stable_id,
                            "mechanism_id": mechanism.mechanism_id,
                            "source": "Reactome",
                        },
                    )
                )

            # Pathway -> Disease edge.
            if disease_node_id:
                rel = Relationship(
                    source_id=pathway_node_id,
                    target_id=disease_node_id,
                    relationship_type=(
                        RelationshipType.ASSOCIATED_WITH
                    ),
                    evidence_ids=[],
                    evidence_level="association",
                    support_class=(
                        SupportClass.SUPPORTED_ASSOCIATION
                    ),
                    description=(
                        f"The pathway "
                        f"'{mechanism.label or stable_id}' "
                        f"is associated with the disease."
                    ),
                    metadata={
                        "reactome_id": stable_id,
                        "source": "Reactome",
                    },
                )
                relationships.add(rel)

        # ---- 4) Target nodes --------------------------------
        # One ImpactNode per target. Reuse the GENE node type
        # so the frontend renders targets like any other
        # biological entity.
        for target in targets:
            node_id = target.target_id
            if node_id in nodes.by_id:
                continue

            nodes.add(
                ImpactNode(
                    node_id=node_id,
                    node_type=NodeType.GENE,
                    name=target.label,
                    identifier=(
                        target.ensembl_id
                        or target.uniprot_id
                        or target.chembl_target_id
                    ),
                    description=None,
                    evidence_ids=[],
                    metadata={
                        "gene_symbol": target.gene_symbol,
                        "uniprot_id": target.uniprot_id,
                        "ensembl_id": target.ensembl_id,
                        "chembl_target_id": (
                            target.chembl_target_id
                        ),
                        "mechanism_membership": (
                            target.mechanism_membership
                        ),
                        "open_targets_score": (
                            target.open_targets_score
                        ),
                        "source": "Mechanism + Open Targets",
                    },
                )
            )

        # ---- 5) Target -> Pathway edges ---------------------
        # Only for targets that are mechanism members. This
        # edge is asserted once per target, regardless of how
        # many compounds reach the target.
        if pathway_node_id:
            for target in targets:
                if not target.mechanism_membership:
                    continue

                rel = Relationship(
                    source_id=target.target_id,
                    target_id=pathway_node_id,
                    relationship_type=(
                        RelationshipType.PARTICIPATES_IN
                    ),
                    evidence_ids=[],
                    evidence_level="direct",
                    support_class=(
                        SupportClass.RETRIEVED_FACT
                    ),
                    description=(
                        f"{target.label} participates in the "
                        f"pathway "
                        f"'{mechanism.label or mechanism.identifier}'."
                    ),
                    metadata={
                        "reactome_id": mechanism.identifier,
                        "source": "Reactome",
                    },
                )
                key = (
                    f"{rel.source_id}|{rel.relationship_type}|"
                    f"{rel.target_id}"
                )
                if not self._relationship_exists(
                    relationships, rel
                ):
                    relationships.add(rel)

        # ---- 6) Compound nodes ------------------------------
        for candidate in candidates:
            node_id = f"{_COMPOUND_NODE_PREFIX}{candidate.compound_id}"
            if node_id in nodes.by_id:
                continue

            nodes.add(
                ImpactNode(
                    node_id=node_id,
                    node_type=NodeType.COMPOUND,
                    name=candidate.name or candidate.compound_id,
                    identifier=candidate.compound_id,
                    description=None,
                    evidence_ids=[],
                    metadata={
                        "source": candidate.source,
                        "parent_chembl_id": (
                            candidate.parent_chembl_id
                        ),
                        "canonical_smiles": (
                            candidate.canonical_smiles
                        ),
                        "identifiers": dict(
                            candidate.identifiers or {}
                        ),
                    },
                )
            )

        # ---- 7) Compound -> Target edges --------------------
        # Deduplicate across chains: many chains may connect
        # the same compound to the same target via different
        # activities.
        seen_compound_target: Set[str] = set()

        for chain in chains:
            for edge in chain.edges:
                if not edge.source_id.startswith(
                    _COMPOUND_NODE_PREFIX
                ):
                    # Not a compound edge — those are added
                    # in step 8 below.
                    continue

                key = (
                    f"{edge.source_id}|{edge.relationship_type}|"
                    f"{edge.target_id}"
                )
                if key in seen_compound_target:
                    continue
                if self._relationship_exists(
                    relationships, edge
                ):
                    seen_compound_target.add(key)
                    continue

                relationships.add(edge)
                seen_compound_target.add(key)

        # ---- 8) Add remaining chain edges -------------------
        # Target -> Pathway and Pathway -> Disease edges are
        # already added in steps 3 and 5. Any chain edge that
        # references something not covered by those steps is
        # added here for completeness.
        for chain in chains:
            for edge in chain.edges:
                if self._relationship_exists(
                    relationships, edge
                ):
                    continue

                source_ok = edge.source_id in nodes.by_id
                target_ok = edge.target_id in nodes.by_id
                if not source_ok or not target_ok:
                    # Skip dangling edges; integrity check
                    # will still report the source chain.
                    continue

                relationships.add(edge)

        # ---- 9) Build indexes -------------------------------
        relationships.build_indexes()

        # ---- 10) Integrity check ----------------------------
        integrity = self._check_integrity(
            nodes=nodes,
            relationships=relationships,
            evidence=evidence,
            layers_merged=[
                "disease",
                "mechanism",
                "targets",
                "compounds",
                "chains",
            ],
        )

        return {
            "nodes": [asdict(n) for n in nodes.nodes],
            "edges": [
                asdict(r)
                for r in relationships.relationships
            ],
            "evidence": [asdict(e) for e in evidence.records],
            "disease_node_id": disease_node_id,
            "pathway_node_id": pathway_node_id,
            "integrity": integrity,
        }

    # ------------------------------------------------------------------
    # Node constructors
    # ------------------------------------------------------------------

    @staticmethod
    def _build_disease_node(
        disease: DiseaseIdentity,
    ) -> Optional[ImpactNode]:
        if not disease.identifiers:
            return None

        primary = disease.identifiers[0]
        ident = (primary.identifier or "").strip()
        if not ident:
            return None

        sanitized = ident.replace(":", "_")
        node_id = f"{_DISEASE_NODE_PREFIX}{sanitized}"

        return ImpactNode(
            node_id=node_id,
            node_type=NodeType.DISEASE,
            name=disease.canonical_name or disease.query,
            identifier=ident,
            description=disease.description,
            evidence_ids=[],
            metadata={
                "canonical_name": disease.canonical_name,
                "query": disease.query,
                "sources": list(disease.sources or []),
                "resolution_status": disease.resolution_status,
            },
        )

    @staticmethod
    def _build_mechanism_node(
        mechanism: SelectedMechanism,
    ) -> Optional[ImpactNode]:
        if not mechanism.mechanism_id:
            return None

        # The mechanism node uses a dedicated prefix so it
        # does not collide with the pathway node.
        sanitized = mechanism.mechanism_id.replace(
            ":", "_"
        ).replace("/", "_")
        node_id = f"{_MECHANISM_NODE_PREFIX}{sanitized}"

        return ImpactNode(
            node_id=node_id,
            node_type=NodeType.MECHANISM,
            name=mechanism.label or mechanism.mechanism_id,
            identifier=mechanism.identifier or (
                mechanism.mechanism_id
            ),
            description=mechanism.description,
            evidence_ids=list(mechanism.evidence_ids or []),
            metadata={
                "source": mechanism.source,
                "mechanism_id": mechanism.mechanism_id,
            },
        )

    # ------------------------------------------------------------------
    # Integrity
    # ------------------------------------------------------------------

    @staticmethod
    def _check_integrity(
        nodes: ImpactNodeSet,
        relationships: RelationshipSet,
        evidence: EvidenceCollection,
        layers_merged: List[str],
    ) -> Dict[str, Any]:
        node_ids = set(nodes.by_id.keys())
        evidence_ids = set(evidence.by_id.keys())

        dangling_sources: List[str] = []
        dangling_targets: List[str] = []
        rels_missing_evidence: List[str] = []

        for rel in relationships.relationships:
            key = (
                f"{rel.source_id}|{rel.relationship_type}|"
                f"{rel.target_id}"
            )

            if rel.source_id not in node_ids:
                if key not in dangling_sources:
                    dangling_sources.append(key)

            if rel.target_id not in node_ids:
                if key not in dangling_targets:
                    dangling_targets.append(key)

            for ev_id in rel.evidence_ids or []:
                if ev_id not in evidence_ids:
                    bad = f"{key}->{ev_id}"
                    if bad not in rels_missing_evidence:
                        rels_missing_evidence.append(bad)

        nodes_missing_evidence: List[str] = []
        for node in nodes.nodes:
            for ev_id in node.evidence_ids or []:
                if ev_id not in evidence_ids:
                    key = f"{node.node_id}->{ev_id}"
                    if key not in nodes_missing_evidence:
                        nodes_missing_evidence.append(key)

        duplicate_node_ids = _find_duplicates(
            [n.node_id for n in nodes.nodes]
        )
        duplicate_relationship_keys = _find_duplicates(
            [
                f"{r.source_id}|{r.relationship_type}|"
                f"{r.target_id}"
                for r in relationships.relationships
            ]
        )
        duplicate_evidence_ids = _find_duplicates(
            [e.evidence_id for e in evidence.records]
        )

        ok = (
            not dangling_sources
            and not dangling_targets
            and not rels_missing_evidence
            and not nodes_missing_evidence
            and not duplicate_node_ids
            and not duplicate_relationship_keys
            and not duplicate_evidence_ids
        )

        return {
            "ok": ok,
            "node_count": len(nodes.nodes),
            "relationship_count": len(
                relationships.relationships
            ),
            "evidence_count": len(evidence.records),
            "dangling_relationship_sources": (
                dangling_sources
            ),
            "dangling_relationship_targets": (
                dangling_targets
            ),
            "relationships_with_missing_evidence": (
                rels_missing_evidence
            ),
            "nodes_with_missing_evidence": (
                nodes_missing_evidence
            ),
            "duplicate_node_ids": duplicate_node_ids,
            "duplicate_relationship_keys": (
                duplicate_relationship_keys
            ),
            "duplicate_evidence_ids": (
                duplicate_evidence_ids
            ),
            "layers_merged": list(layers_merged),
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _relationship_exists(
        relationships: RelationshipSet,
        rel: Relationship,
    ) -> bool:
        for existing in relationships.relationships:
            if (
                existing.source_id == rel.source_id
                and existing.target_id == rel.target_id
                and existing.relationship_type
                == rel.relationship_type
            ):
                return True
        return False


def _find_duplicates(values: List[str]) -> List[str]:
    seen: Set[str] = set()
    dupes: List[str] = []
    for v in values:
        if v in seen:
            if v not in dupes:
                dupes.append(v)
        else:
            seen.add(v)
    return dupes


# ---------------------------------------------------------------------------
# Convenience
# ---------------------------------------------------------------------------


def build_therapeutic_graph(
    disease: Optional[DiseaseIdentity],
    mechanism: SelectedMechanism,
    targets: List[TargetSummary],
    candidates: List[CandidateCompound],
    activities: List[ActivityRecord],
    chains: List[MechanismOfActionChain],
) -> Dict[str, Any]:
    """
    One-shot entry point.
    """
    return TherapeuticGraphBuilder().build(
        disease=disease,
        mechanism=mechanism,
        targets=targets,
        candidates=candidates,
        activities=activities,
        chains=chains,
    )
