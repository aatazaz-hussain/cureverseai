"""
CureVerseAI — Drug Development
Impact evidence schemas.

This module defines the evidence record used by the
Biological Impact Graph (Disease -> Biological Impact).

IMPORTANT — coexistence with app/drug_development/evidence.py:

    app/drug_development/evidence.py already exists and defines
    TargetEvidence, CompoundEvidence, DrugTargetEvidence and
    EvidenceBundle for the ChEMBL / Open Targets flows.

    This file does NOT import from it, does NOT replace it, and
    does NOT redefine any of its names. It defines a separate,
    impact-graph-specific evidence type. The existing module is
    the authoritative source for bioactivity evidence records.

DESIGN CONSTRAINTS (from the specification):

    1. Evidence categories must not be collapsed into a single
       score. Therefore this schema has NO numeric confidence
       field, NO composite score, and NO ranking number.

    2. Uncertainty is explicit. Every record carries an
       evidence_level drawn from a fixed vocabulary.

    3. Provenance is preserved. Every record names its source,
       a source-specific identifier where available, and an
       optional URL.

    4. A record may legitimately lack detail. Missing detail
       is represented by absent optional fields, NOT by
       fabricated placeholder values.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Evidence level vocabulary
# ---------------------------------------------------------------------------


class EvidenceLevel:
    """
    Controlled vocabulary for how strongly a relationship is
    supported, per the specification's uncertainty model.

    These levels are semantic labels, not probabilities. They
    describe the NATURE of the supporting information, not a
    numeric strength.

    DIRECT         : the source states the relationship directly.
    ASSOCIATION    : the source reports a statistical / curated
                     association, not a direct causal statement.
    EXPERIMENTAL   : an experimental observation (for example a
                     measured assay result).
    COMPUTATIONAL  : a relationship produced by inference or
                     computation, not directly observed.
    CONTEXTUAL     : surrounding biological context that does
                     not by itself establish the relationship.
    LIMITED        : evidence exists but is sparse or narrow.
    INSUFFICIENT   : no supporting evidence was retrieved.
    """

    DIRECT = "direct"
    ASSOCIATION = "association"
    EXPERIMENTAL = "experimental"
    COMPUTATIONAL = "computational"
    CONTEXTUAL = "contextual"
    LIMITED = "limited"
    INSUFFICIENT = "insufficient"

    ALL = (
        DIRECT,
        ASSOCIATION,
        EXPERIMENTAL,
        COMPUTATIONAL,
        CONTEXTUAL,
        LIMITED,
        INSUFFICIENT,
    )


# ---------------------------------------------------------------------------
# Evidence reference
# ---------------------------------------------------------------------------


@dataclass
class EvidenceReference:
    """
    A pointer to the source-of-truth record behind an evidence
    entry.

    For example, for an Open Targets disease-association record,
    `source="Open Targets"`, `source_id="ENSG000001..."` (the
    target ID), and `url` points to the Open Targets page.

    `source_type` is a coarse label such as "database",
    "ontology", "literature", "internal_model" so callers can
    filter without parsing the source name.
    """

    source: str
    source_id: Optional[str] = None
    source_type: Optional[str] = None
    url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Impact evidence
# ---------------------------------------------------------------------------


@dataclass
class ImpactEvidence:
    """
    A single evidence record attached to a Relationship in the
    Biological Impact Graph.

    One ImpactEvidence instance may back multiple relationships
    (for example, a single Open Targets record can support both
    "disease -> gene" and "disease -> pathway" edges). That is
    why evidence is referenced by ID from Relationship, not
    embedded inside it.

    `relationship_description` is a human-readable statement of
    WHAT this record supports. It is not a claim of causality
    and must not be paraphrased into stronger language
    downstream.

    `evidence_level` must be one of EvidenceLevel.ALL. No
    numeric strength is stored on the record. If a downstream
    stage needs to rank evidence, it does so by grouping and
    counting categories, not by scoring individual records.
    """

    evidence_id: str
    source: str
    relationship_description: str
    evidence_level: str = EvidenceLevel.INSUFFICIENT
    reference: Optional[EvidenceReference] = None
    identifiers: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_sufficient(self) -> bool:
        """
        Convenience predicate: does this record provide any
        supporting information?

        A record at INSUFFICIENT is a legitimate placeholder
        that must be surfaced to the user as missing evidence,
        not hidden.
        """
        return self.evidence_level != EvidenceLevel.INSUFFICIENT


# ---------------------------------------------------------------------------
# Evidence collection
# ---------------------------------------------------------------------------


@dataclass
class EvidenceCollection:
    """
    An indexed collection of ImpactEvidence records.

    Lookup is by evidence_id. The collection is deliberately
    non-destructive: records are never silently merged or
    deduplicated by content, because two sources reporting
    similar content are two pieces of evidence, not one.

    Use group_by_level() for a category count without
    collapsing the underlying records.
    """

    records: List[ImpactEvidence] = field(default_factory=list)
    by_id: Dict[str, int] = field(default_factory=dict)

    def add(self, evidence: ImpactEvidence) -> int:
        """
        Append an evidence record and index it by evidence_id.

        If the evidence_id already exists, the existing index
        is preserved and the duplicate is appended. Duplicate
        IDs are a data-integrity issue that must be caught
        upstream, not silently resolved here.
        """
        index = len(self.records)
        self.records.append(evidence)

        if evidence.evidence_id not in self.by_id:
            self.by_id[evidence.evidence_id] = index

        return index

    def get(self, evidence_id: str) -> Optional[ImpactEvidence]:
        index = self.by_id.get(evidence_id)
        if index is None:
            return None
        return self.records[index]

    def group_by_level(self) -> Dict[str, int]:
        """
        Return counts per evidence_level.

        This is a CATEGORY count, not a score. It must not be
        reduced to a single number downstream.
        """
        counts: Dict[str, int] = {level: 0 for level in EvidenceLevel.ALL}

        for record in self.records:
            if record.evidence_level in counts:
                counts[record.evidence_level] += 1

        return counts
