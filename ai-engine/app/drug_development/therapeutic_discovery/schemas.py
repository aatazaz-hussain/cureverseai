"""
CureVerseAI — Drug Development
Workflow 03 — Therapeutic Discovery
Result schemas.

This module defines the top-level result produced by the
Therapeutic Discovery workflow, plus the small dataclasses
that give its distinct concepts a typed identity.

Design
------

Workflow 03 has its own result contract. It does NOT
subclass W02's ReverseDiseaseResult and does NOT wrap it.
The two workflows share only the underlying graph
primitives (ImpactNodeSet, RelationshipSet,
EvidenceCollection) and the DiseaseIdentity type.

The in-process dataclass (TherapeuticDiscoveryResult) holds
those shared primitives directly. The wire format (a plain
dict matching the response contract in the W03 spec) is
produced by a serializer in service.py, mirroring W02's
pattern.

Sub-dataclass policy
--------------------

Six W03 concepts deserve named dataclasses because they
encode decisions that would otherwise be implicit in
dict keys:

    - SelectedMechanism: what the user is investigating
    - TargetSummary: a target + its two relevance signals
    - CandidateCompound: a compound + its source identifiers
    - ActivityRecord: an assay measurement + its full context
    - MechanismOfActionChain: the compound -> target ->
      pathway -> disease path, per candidate
    - CandidateComparison: 4-dimension evaluation, no
      composite score, per candidate

Everything else that is collection-like stays as plain
dicts or lists of dicts, matching W02's convention.

Scientific constraints encoded here
-----------------------------------

- No composite ranking score exists anywhere in this file.
  Candidates are compared on separate dimensions only.
- Activity records preserve the original value, units, and
  relation from the source. pchembl_value, when present,
  is ChEMBL's own normalization and is labeled as such.
- Support classification of every edge is preserved
  verbatim. An "experimentally_measured" edge carries an
  assay identifier; a "predicted" edge carries the method
  name. They are never conflated.

No external libraries are imported here. These are pure
data structures.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from app.drug_development.schemas.disease import (
    DiseaseIdentity,
)
from app.drug_development.schemas.evidence import (
    EvidenceCollection,
)
from app.drug_development.schemas.impact import ImpactNodeSet
from app.drug_development.schemas.relationships import (
    RelationshipSet,
)


# ---------------------------------------------------------------------------
# Selected mechanism
# ---------------------------------------------------------------------------


@dataclass
class SelectedMechanism:
    """
    The biological mechanism the user is investigating.

    May be supplied by the user (via a W02 handoff) or
    discovered by mechanism_resolver from the disease.

    `source` values:
        - "w02_handoff"  : came from a W02 node identifier
        - "discovered"   : derived from the disease by W03
        - "user_supplied": explicit identifier in the request
    """

    mechanism_id: str
    label: Optional[str] = None
    source: str = "discovered"
    identifier: Optional[str] = None
    description: Optional[str] = None
    evidence_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Target
# ---------------------------------------------------------------------------


@dataclass
class TargetSummary:
    """
    A candidate biological target.

    Two relevance signals are preserved separately:

        - mechanism_membership: bool — does the target
          participate in the selected mechanism?
        - open_targets_score: Optional[float] — the
          disease-association score from Open Targets, when
          available.

    Neither is combined into a single target score.
    """

    target_id: str
    label: str
    gene_symbol: Optional[str] = None
    uniprot_id: Optional[str] = None
    ensembl_id: Optional[str] = None
    chembl_target_id: Optional[str] = None

    mechanism_membership: bool = False
    open_targets_score: Optional[float] = None

    evidence_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Candidate compound
# ---------------------------------------------------------------------------


@dataclass
class CandidateCompound:
    """
    A compound retrieved from ChEMBL or another compatible
    source.

    Every identifier is preserved. No name is invented. A
    compound with no measured activity is a valid candidate
    with an empty activity list — it is not filtered out.
    """

    compound_id: str
    source: str = "ChEMBL"
    name: Optional[str] = None
    parent_chembl_id: Optional[str] = None
    canonical_smiles: Optional[str] = None
    identifiers: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Activity record
# ---------------------------------------------------------------------------


@dataclass
class ActivityRecord:
    """
    One assay measurement attached to a compound-target
    relationship.

    The original scientific value is preserved exactly as
    the source reported it. Fields:

        standard_type        e.g. "IC50", "Ki", "Kd", "EC50"
        standard_value       the numeric value, as a string
        standard_units       e.g. "nM"
        standard_relation    "=", "<", ">", "<=", ">="
        pchembl_value        ChEMBL's own normalized value,
                             when the source provides one. This
                             is NOT computed by CureVerseAI; it
                             is ChEMBL's normalization, labeled
                             as such in metadata.

    `evidence_level` mirrors ChEMBL's classification:

        quantitative   a numeric standard_value exists
        qualitative    only standard_text_value exists
        observational  neither value is present

    `assay_type` is ChEMBL's single-letter code:

        B   binding
        F   functional
        A   ADME
        T   toxicity
        P   physicochemical

    W03 keeps only B and F records at the compound_discovery
    layer. This dataclass is source-shape faithful.
    """

    activity_id: str
    target_chembl_id: str
    compound_chembl_id: str

    evidence_level: str = "observational"

    standard_type: Optional[str] = None
    standard_value: Optional[str] = None
    standard_units: Optional[str] = None
    standard_relation: Optional[str] = None
    standard_text_value: Optional[str] = None
    pchembl_value: Optional[str] = None

    assay_id: Optional[str] = None
    assay_type: Optional[str] = None
    assay_description: Optional[str] = None

    publication_year: Optional[int] = None
    publication_journal: Optional[str] = None

    source: str = "ChEMBL"
    source_record_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Mechanism-of-action chain
# ---------------------------------------------------------------------------


@dataclass
class MechanismOfActionChain:
    """
    The proposed chain for one candidate compound:

        compound -> target -> downstream pathway -> mechanism

    Every link in the chain is labeled by its support class.
    Missing links are recorded as `unresolved_links` rather
    than omitted.

    `edges` holds Relationship dataclass instances. The
    serialized form uses the standard Relationship shape so
    the frontend can render them like any other edge.
    """

    candidate_id: str
    target_id: str

    edges: List[Any] = field(default_factory=list)
    node_ids: List[str] = field(default_factory=list)

    unresolved_links: List[Dict[str, Any]] = field(
        default_factory=list
    )
    evidence_ids: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Candidate comparison
# ---------------------------------------------------------------------------


@dataclass
class CandidateComparison:
    """
    Four orthogonal evidence dimensions for one candidate.
    No composite score.

        activity_quality       "measured" | "qualitative" |
                               "none"
        mechanism_link_strength "direct" | "two_hop" |
                                "indirect"
        evidence_diversity     count of distinct sources
                               contributing evidence
        data_gaps              count of unresolved links in
                               the MoA chain

    The frontend may sort or filter by any single dimension.
    No combined metric exists.
    """

    candidate_id: str
    activity_quality: str = "none"
    mechanism_link_strength: str = "indirect"
    evidence_diversity: int = 0
    data_gaps: int = 0
    notes: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Reasoning
# ---------------------------------------------------------------------------


@dataclass
class ReasoningBlock:
    """
    Structured reasoning payload.

    `supported_findings` : statements with experimental or
                           database support
    `hypotheses`         : inferred connections and
                           plausibility statements
    `conflicts`          : contradictory evidence preserved
                           side-by-side
    `evidence_gaps`      : explicit missing links
    """

    supported_findings: List[Dict[str, Any]] = field(
        default_factory=list
    )
    hypotheses: List[Dict[str, Any]] = field(
        default_factory=list
    )
    conflicts: List[Dict[str, Any]] = field(
        default_factory=list
    )
    evidence_gaps: List[Dict[str, Any]] = field(
        default_factory=list
    )


# ---------------------------------------------------------------------------
# Provenance
# ---------------------------------------------------------------------------


@dataclass
class ProvenanceBlock:
    """
    Provenance for a single W03 run.

    Same shape as W02's ProvenanceRecord for consistency.
    """

    sources_queried: List[str] = field(default_factory=list)
    source_failures: List[Dict[str, Any]] = field(
        default_factory=list
    )
    records_retrieved: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Narration
# ---------------------------------------------------------------------------


@dataclass
class NarrationSegment:
    """
    One narration segment tied to a specific graph element.

    Mirrors W02's Explanation dataclass. Separate type here
    so the W03 result is self-contained.
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
class TherapeuticDiscoveryResult:
    """
    Complete, structured output of the Therapeutic Discovery
    workflow for a single query.

    The in-process contract. The wire contract is produced
    by serialize_therapeutic_discovery_result() in service.py.

    Shared graph primitives
    -----------------------

    `nodes`         ImpactNodeSet        (from W01's schemas)
    `relationships` RelationshipSet      (from W01's schemas)
    `evidence`      EvidenceCollection   (from W01's schemas)

    W03-specific containers
    -----------------------

    `targets`              [TargetSummary]
    `candidates`           [CandidateCompound]
    `activities`           [ActivityRecord]
    `moa_chains`           [MechanismOfActionChain]
    `candidate_comparisons [CandidateComparison]

    Result states
    -------------

    `resolution_status` values:

        "resolved"      : disease resolved, targets or
                          candidates returned
        "no_candidates" : disease resolved but no compounds
                          were found for the targets
        "partial"       : disease resolved but a source
                          failed mid-pipeline
        "unresolved"    : disease could not be resolved
        "invalid_input" : a supplied mechanism or target ID
                          could not be parsed

    `failure_reason` is populated for the last three states.
    """

    query: str

    disease: Optional[DiseaseIdentity] = None
    resolution_status: str = "unresolved"
    failure_reason: Optional[str] = None

    selected_mechanism: Optional[SelectedMechanism] = None

    targets: List[TargetSummary] = field(default_factory=list)
    candidates: List[CandidateCompound] = field(
        default_factory=list
    )
    activities: List[ActivityRecord] = field(
        default_factory=list
    )
    moa_chains: List[MechanismOfActionChain] = field(
        default_factory=list
    )
    candidate_comparisons: List[CandidateComparison] = field(
        default_factory=list
    )

    # Shared graph containers (W01 primitives)
    nodes: ImpactNodeSet = field(default_factory=ImpactNodeSet)
    relationships: RelationshipSet = field(
        default_factory=RelationshipSet
    )
    evidence: EvidenceCollection = field(
        default_factory=EvidenceCollection
    )

    reasoning: ReasoningBlock = field(
        default_factory=ReasoningBlock
    )
    provenance: ProvenanceBlock = field(
        default_factory=ProvenanceBlock
    )
    narration: List[NarrationSegment] = field(
        default_factory=list
    )

    metadata: Dict[str, Any] = field(default_factory=dict)
