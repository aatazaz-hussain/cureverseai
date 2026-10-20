"""
CureVerseAI — Drug Development
Workflow 02 — Reverse Disease Engineering
Result schemas.

This module defines the top-level result produced by the
Reverse Disease Engineering workflow, plus the two
W02-specific small dataclasses it depends on.

Design
------

Workflow 02 has its own result contract. It is NOT a subclass
of W01's BiologicalImpactResult and it does NOT wrap it. The
two workflows share only the underlying graph primitives
(ImpactNodeSet, RelationshipSet, EvidenceCollection) and the
DiseaseIdentity type — they do not share a top-level result.

The in-process dataclass (ReverseDiseaseResult) holds those
shared primitives directly. The wire format (a plain dict
matching the response contract in the W02 spec) is produced
by a serializer in service.py, mirroring W01's pattern where
BiologicalImpactResult is serialized by
serialize_impact_result() in pipeline.py.

Sub-dataclass policy
--------------------

Two W02 concepts deserve named dataclasses:

    - ProvenanceRecord: source_failures is a first-class
      concept in W02, not an afterthought. A typed record
      prevents drift.

    - Explanation: narration segments reference a specific
      graph node or edge. Encoding the two-field address
      (target_kind + target_id) in a dataclass prevents the
      frontend from having to guess.

Everything else that is collection-like (the seven
mechanistic_investigation layers, uncertainties) stays as
plain dicts or lists of dicts, matching W01's layer-module
convention.

Field naming
------------

Field names on the result follow the W02 spec's response
contract exactly, EXCEPT for graph primitives (nodes,
relationships, evidence) which keep their W01 names.

No external libraries are imported here. These are pure
data structures.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.drug_development.schemas.disease import DiseaseIdentity
from app.drug_development.schemas.evidence import (
    EvidenceCollection,
)
from app.drug_development.schemas.impact import ImpactNodeSet
from app.drug_development.schemas.relationships import (
    RelationshipSet,
)


# ---------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------


@dataclass
class ProvenanceRecord:
    """
    Provenance for a single Reverse Disease Engineering run.

    `sources_queried` lists the source NAMES actually contacted
    during this run (e.g. "Open Targets", "Reactome", "ChEMBL").
    It is a set-like list; deduplication is the caller's job.

    `source_failures` is a list of structured failure records.
    Each record has at least:

        {
            "source": <str>,       # source name
            "reason": <str>,       # short human-readable cause
            "metadata": <dict>,    # optional, source-specific
        }

    A source that succeeded with zero records is NOT a failure.
    It appears in `sources_queried`, contributes nothing to
    `source_failures`, and its zero count is preserved in
    `metadata` if the caller wishes to record it there.

    `records_retrieved` is a total count across all sources —
    a count, not a score. It must never be interpreted as
    evidence strength.

    `metadata` is an open bag for per-source counts and
    timing. It must not carry scientific claims.
    """

    sources_queried: List[str] = field(default_factory=list)
    source_failures: List[Dict[str, Any]] = field(
        default_factory=list
    )
    records_retrieved: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Explanation
# ---------------------------------------------------------------------------


@dataclass
class Explanation:
    """
    A single narration segment tied to a specific graph element.

    `target_kind` is either "node" or "edge". The frontend uses
    this discriminator to decide how to highlight the graph when
    the segment plays.

    `target_id` identifies the graph element:

        - when target_kind == "node": target_id is a node_id
        - when target_kind == "edge": target_id is a stable
          edge key of the form
          "<source_id>|<relationship_type>|<target_id>"

    The edge key format is deliberately parseable and stable,
    so the frontend can locate the corresponding relationship
    in the serialized graph without a separate index.

    `support_class`, when set, must be one of SupportClass.ALL
    (from app.drug_development.schemas.relationships). It is
    populated when target_kind == "edge" and left None for
    node explanations.

    `evidence_ids` are the evidence records backing this
    explanation, when it discusses a specific relationship.
    Empty for explanations that describe a node.

    `text` is the human-readable explanation. It must be
    generated FROM the graph and its evidence, not invented
    independently. It must not upgrade an association into a
    causal claim.
    """

    explanation_id: str
    target_kind: str               # "node" | "edge"
    target_id: str
    text: str
    support_class: Optional[str] = None
    evidence_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Top-level result
# ---------------------------------------------------------------------------


@dataclass
class ReverseDiseaseResult:
    """
    Complete, structured output of the Reverse Disease
    Engineering workflow for a single query.

    This is the in-process contract. The wire contract is
    produced by serialize_reverse_disease_result() in
    service.py, which strips container indexes and converts
    the dataclass to a plain dict.

    Field summary
    -------------

    query
        The raw user query, preserved verbatim.

    disease
        The resolved DiseaseIdentity, or None when resolution
        failed or is ambiguous.

    resolution_status
        "resolved" | "partial" | "unresolved". Mirrors
        DiseaseIdentity.resolution_status but is stored at
        the top level so callers can branch without digging
        into `disease`.

    failure_reason
        Populated only when resolution_status is "partial"
        or "unresolved". None on a fully resolved run.

    nodes / relationships / evidence
        The shared Phase 01 containers. `nodes` is an
        ImpactNodeSet, `relationships` is a RelationshipSet,
        `evidence` is an EvidenceCollection. Serialization
        emits their primary lists (`.nodes`, `.relationships`,
        `.records`) and strips their index maps, mirroring
        W01.

    mechanistic_investigation
        A dict with the seven W02 layers:

            phenotypes
            contributing_factors
            mechanisms
            genes
            variants
            pathways
            manifestations

        Each value is itself a dict in the W01 layer-module
        shape:

            {
                "disease_node_id": <str or None>,
                "nodes":           [<serialized ImpactNode>...],
                "relationships":   [<serialized Relationship>...],
                "evidence":        [<serialized ImpactEvidence>...],
                "sources":         [<str>...],
                "found":           <bool>,
                "metadata":        {...},
                "reason":          <str or None>,
            }

        Layer entries that were not run in this pass are
        omitted from the dict entirely; they are not present
        as empty dicts. Callers must tolerate missing keys.

    explanations
        Ordered narration segments tied to graph elements.
        Order is meaningful; the frontend plays them in the
        order given.

    uncertainties
        A list of structured uncertainty notes. Each note is
        a dict with at least:

            {
                "type": <str>,        # e.g. "missing_variant_data"
                "statement": <str>,   # human-readable
                "related_ids": [<str>...],
            }

        `type` values are drawn from a controlled vocabulary
        defined in the uncertainty builder (not here), so
        the frontend can filter without parsing prose.

    provenance
        ProvenanceRecord. See above.

    metadata
        Open bag for build-level diagnostics (counts, timing,
        schema version). Must not carry scientific claims.
    """

    query: str
    disease: Optional[DiseaseIdentity] = None
    resolution_status: str = "unresolved"
    failure_reason: Optional[str] = None

    # In-process containers (Phase 01 dataclasses)
    nodes: ImpactNodeSet = field(default_factory=ImpactNodeSet)
    relationships: RelationshipSet = field(
        default_factory=RelationshipSet
    )
    evidence: EvidenceCollection = field(
        default_factory=EvidenceCollection
    )

    # Per-layer summaries (W01 layer-module shape)
    mechanistic_investigation: Dict[str, Any] = field(
        default_factory=dict
    )

    # W02-specific
    explanations: List[Explanation] = field(default_factory=list)
    uncertainties: List[Dict[str, Any]] = field(
        default_factory=list
    )
    provenance: ProvenanceRecord = field(
        default_factory=ProvenanceRecord
    )

    # Build-level metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
