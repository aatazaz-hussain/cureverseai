"""
CureVerseAI — Drug Development
Biological Impact Graph schema.

This module defines the top-level result produced by the
Disease -> Biological Impact workflow.

Graph model
-----------

The impact graph is modeled as:

    - a set of typed NODES (ImpactNode), each carrying a
      node_type such as "system", "organ", "tissue", "cell",
      "gene", "protein", "molecule", "pathway", "mechanism",
      "effect"

    - a set of typed EDGES (Relationship, from relationships.py)
      connecting nodes by ID

    - a set of evidence records (ImpactEvidence, from
      evidence.py) referenced by ID from edges

Entity types are represented by ONE generic ImpactNode
dataclass with a discriminating `node_type` field, not by a
separate dataclass per entity type. This is a deliberate
design choice:

    - the graph semantics live on relationships, not on nodes
    - the frontend renders nodes by type, not by class
    - adding a new entity type is a new node_type constant,
      not a new file
    - serialization is uniform

If a downstream stage needs per-type fields, they go in the
node's `metadata` dict under a named key, never as a
new top-level field on ImpactNode.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.drug_development.schemas.disease import DiseaseIdentity
from app.drug_development.schemas.evidence import EvidenceCollection
from app.drug_development.schemas.relationships import RelationshipSet


# ---------------------------------------------------------------------------
# Node type vocabulary
# ---------------------------------------------------------------------------


class NodeType:
    """
    Controlled vocabulary for ImpactNode node_type.

    The set is small on purpose. Adding a new type is a
    schema-level decision, not an ad-hoc one.
    """

    DISEASE = "disease"
    BIOLOGICAL_SYSTEM = "system"
    ORGAN = "organ"
    TISSUE = "tissue"
    CELL_TYPE = "cell"
    GENE = "gene"
    PROTEIN = "protein"
    MOLECULE = "molecule"
    PATHWAY = "pathway"
    MECHANISM = "mechanism"
    BIOLOGICAL_EFFECT = "effect"

    # ------------------------------------------------------------------
    # Workflow 02 (Reverse Disease Engineering) — additive extensions.
    # These do not change any existing value and do not affect W01.
    # ------------------------------------------------------------------
    PHENOTYPE = "phenotype"
    VARIANT = "variant"
    MANIFESTATION = "manifestation"
    CONTRIBUTING_FACTOR = "factor"

    # ------------------------------------------------------------------
    # Workflow 03 (Therapeutic Discovery) — additive extensions.
    # ------------------------------------------------------------------
    #: A small molecule, biologic, or intervention retrieved
    #: from ChEMBL or another compound source. Distinct from
    #: MOLECULE, which is used for endogenous or generic
    #: chemical entities.
    COMPOUND = "compound"

    #: The specific interaction between a compound and a
    #: target — e.g. binding, inhibition, activation.
    MOLECULAR_ACTION = "molecular_action"

    #: A downstream biological consequence of a molecular
    #: action (e.g. reduced cytokine release).
    BIOLOGICAL_RESPONSE = "biological_response"

    ALL = (
        DISEASE,
        BIOLOGICAL_SYSTEM,
        ORGAN,
        TISSUE,
        CELL_TYPE,
        GENE,
        PROTEIN,
        MOLECULE,
        PATHWAY,
        MECHANISM,
        BIOLOGICAL_EFFECT,
        # --- W02 additions (see comment above) ---
        PHENOTYPE,
        VARIANT,
        MANIFESTATION,
        CONTRIBUTING_FACTOR,
        # --- W03 additions (therapeutic_discovery) ---
        COMPOUND,
        MOLECULAR_ACTION,
        BIOLOGICAL_RESPONSE,
    )


# ---------------------------------------------------------------------------
# Impact node
# ---------------------------------------------------------------------------


@dataclass
class ImpactNode:
    """
    A single typed entity in the Biological Impact Graph.

    `node_id` is the stable identifier referenced by
    Relationship.source_id and Relationship.target_id. It must
    be unique within a single BiologicalImpactResult.

    `node_type` must be one of NodeType.ALL.

    `identifier` is an external identifier when one exists
    (for example an Ensembl gene ID, UniProt accession, or
    ontology term). It is optional because some nodes --
    particularly mechanisms and effects -- may be internal
    constructs without an external ID.

    `evidence_ids` mirrors Relationship.evidence_ids for
    evidence that supports the EXISTENCE or IDENTITY of the
    node itself, as opposed to evidence about its
    relationships. An empty list is a valid state.

    `metadata` is an open bag for type-specific fields. It is
    deliberately a dict, not a union of typed subclasses, so
    the node stays serializable and the frontend can index
    into it by key without needing per-type schemas.
    """

    node_id: str
    node_type: str
    name: str
    identifier: Optional[str] = None
    description: Optional[str] = None
    evidence_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Impact node collection
# ---------------------------------------------------------------------------


@dataclass
class ImpactNodeSet:
    """
    An indexed collection of ImpactNode records.

    Lookup is by node_id. Nodes are never deduplicated by
    name, because two nodes with the same display name but
    different identifiers (for example two genes with the
    same symbol on different chromosomes) are distinct
    entities.

    Duplicate node_ids are a data-integrity error and are
    preserved as-is so the error is visible rather than
    silently resolved.
    """

    nodes: List[ImpactNode] = field(default_factory=list)
    by_id: Dict[str, int] = field(default_factory=dict)
    by_type: Dict[str, List[int]] = field(default_factory=dict)

    def add(self, node: ImpactNode) -> int:
        index = len(self.nodes)
        self.nodes.append(node)

        if node.node_id not in self.by_id:
            self.by_id[node.node_id] = index

        self.by_type.setdefault(node.node_type, []).append(index)

        return index

    def get(self, node_id: str) -> Optional[ImpactNode]:
        index = self.by_id.get(node_id)
        if index is None:
            return None
        return self.nodes[index]

    def of_type(self, node_type: str) -> List[ImpactNode]:
        return [
            self.nodes[i]
            for i in self.by_type.get(node_type, [])
        ]


# ---------------------------------------------------------------------------
# Reasoning payload
# ---------------------------------------------------------------------------


@dataclass
class ImpactReasoning:
    """
    Structured reasoning payload for the impact result.

    `summary` is a short human-readable statement. It must be
    generated FROM the structured evidence and relationships,
    not invented independently.

    `findings` is a list of structured finding records. The
    shape of each record is intentionally open; downstream
    consumers must key into named fields, not positional
    indices.

    `limitations` is a list of explicit caveats. It must not
    be empty when evidence is partial or missing.

    This dataclass is a container only. It performs no
    reasoning itself. The reasoning is produced by the
    existing EvidenceReasoningEngine and mapped into this
    structure by the impact builder.
    """

    summary: Optional[str] = None
    findings: List[Dict[str, Any]] = field(default_factory=list)
    limitations: List[str] = field(default_factory=list)
    sources: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Top-level result
# ---------------------------------------------------------------------------


@dataclass
class BiologicalImpactResult:
    """
    The complete, structured output of the
    Disease -> Biological Impact workflow.

    This is the contract that:

        - the AI Engine returns
        - the backend forwards (possibly normalized)
        - the frontend consumes

    All entity layers are stored as ONE ImpactNodeSet rather
    than as separate lists per type. Per-type access is
    available via ImpactNodeSet.of_type(...). This keeps the
    result serializable as a single graph and avoids parallel
    lists that can drift out of sync.

    `resolution_status` mirrors the value on DiseaseIdentity
    so callers can branch on it without digging into the
    disease object.

    `failure_reason` is populated when resolution_status is
    "partial" or "unresolved" AND the builder chose not to
    proceed. It is None on a fully successful result.

    `metadata` carries builder-level provenance such as
    source-list, timing, and version info. It must not carry
    scientific claims.
    """

    query: str
    disease: Optional[DiseaseIdentity] = None
    resolution_status: str = "unresolved"
    nodes: ImpactNodeSet = field(default_factory=ImpactNodeSet)
    relationships: RelationshipSet = field(default_factory=RelationshipSet)
    evidence: EvidenceCollection = field(default_factory=EvidenceCollection)
    reasoning: ImpactReasoning = field(default_factory=ImpactReasoning)
    failure_reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
