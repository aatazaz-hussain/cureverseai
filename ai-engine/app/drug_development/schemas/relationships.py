"""
CureVerseAI — Drug Development
Relationship schemas.

A Relationship is a directed edge in the Biological Impact Graph.
Entities (disease, system, organ, tissue, cell, gene, protein,
molecule, pathway, mechanism, effect) live in their own schemas.
Relationships are the connective tissue between them.

Design notes:
- Relationships are directed: source_id -> target_id.
- Relationship verbs are constrained by a small, explicit set so
  the frontend and downstream reasoning layer can rely on them.
- Evidence is attached to each relationship by reference
  (evidence_id / evidence_refs), not embedded. This keeps the
  graph traversal cheap and lets a single evidence record back
  multiple relationships.
- No entity definitions are imported here. Only string IDs.
  This avoids circular imports as the schema package grows.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Relationship type vocabulary
# ---------------------------------------------------------------------------


class RelationshipType:
    """
    Controlled vocabulary for relationship verbs used in the
    Biological Impact Graph.

    Kept as string constants (not an Enum) so relationships can
    be serialized, persisted, and compared as plain strings
    without conversion overhead.

    The set is intentionally small. Adding a new verb is a
    deliberate schema decision, not an ad-hoc one.
    """

    AFFECTS = "affects"                       # disease -> system / organ
    CONTAINS = "contains"                     # system -> organ, organ -> tissue, tissue -> cell
    ASSOCIATED_WITH = "associated_with"       # disease -> gene / protein / mechanism
    INVOLVES = "involves"                     # disease / cell -> molecular entity
    ALTERS = "alters"                         # disease / molecule -> pathway
    PARTICIPATES_IN = "participates_in"       # protein -> pathway
    PRODUCES = "produces"                     # pathway / mechanism -> effect
    INTERACTS_WITH = "interacts_with"         # protein -> protein, molecule -> molecule
    ENCODES = "encodes"                       # gene -> protein

    # ------------------------------------------------------------------
    # Workflow 02 (Reverse Disease Engineering) — additive extensions.
    # These do not change any existing value and do not affect W01.
    #
    # These verbs describe mechanism-layer relationships that W02
    # needs, distinct from W01's impact-relationship vocabulary.
    # ------------------------------------------------------------------
    ACTIVATES = "activates"
    MODULATES = "modulates"
    CONTRIBUTES_TO = "contributes_to"
    CAUSES = "causes"

    # ------------------------------------------------------------------
    # Workflow 03 (Therapeutic Discovery) — additive extensions.
    # ------------------------------------------------------------------
    #: Compound -> Target. A compound is physically associated
    #: with a biological target (measured binding, predicted
    #: binding, or database-recorded interaction).
    BINDS_TO = "binds_to"

    #: Compound -> Target. The compound reduces or blocks the
    #: target's activity. Evidence must be experimental or
    #: clearly labeled as predicted.
    INHIBITS = "inhibits"

    #: Compound or intervention -> Mechanism. The intervention
    #: changes the mechanism's behaviour.
    MODIFIES = "modifies"

    ALL = (
        AFFECTS,
        CONTAINS,
        ASSOCIATED_WITH,
        INVOLVES,
        ALTERS,
        PARTICIPATES_IN,
        PRODUCES,
        INTERACTS_WITH,
        ENCODES,
        # --- W02 additions (see comment above) ---
        ACTIVATES,
        MODULATES,
        CONTRIBUTES_TO,
        CAUSES,
        # --- W03 additions (therapeutic_discovery) ---
        BINDS_TO,
        INHIBITS,
        MODIFIES,
    )


# ---------------------------------------------------------------------------
# Support class vocabulary (Workflow 02)
# ---------------------------------------------------------------------------


class SupportClass:
    """
    W02's four-class support model, per the Reverse Disease
    Engineering specification.

    This is a SEPARATE axis from EvidenceLevel:

        - EvidenceLevel classifies ONE evidence record's nature
          (direct, association, experimental, ...).

        - SupportClass classifies how strongly a WHOLE relationship
          is supported when all of its evidence records are
          considered together.

    A relationship whose evidence contains a `direct` record may
    still be classed as `supported_association` if the source does
    not establish causation. The two axes are orthogonal.

    These are semantic labels, not probabilities. They must not be
    converted into numeric confidence scores.
    """

    RETRIEVED_FACT = "retrieved_fact"
    SUPPORTED_ASSOCIATION = "supported_association"
    MECHANISTIC_INFERENCE = "mechanistic_inference"
    UNKNOWN = "unknown"

    # ------------------------------------------------------------------
    # Workflow 03 (Therapeutic Discovery) — additive extensions.
    # ------------------------------------------------------------------
    #: A compound-target relationship backed by an actual
    #: assay record. The measurement exists and was reported
    #: by a source; potency or effect is not extrapolated.
    EXPERIMENTALLY_MEASURED = "experimentally_measured"

    #: A compound-target relationship produced by a
    #: computational prediction (docking, ML model, or
    #: similarity inference). NOT an observation.
    PREDICTED = "predicted"

    #: A link that the workflow attempted to establish but
    #: could not. A first-class state: the graph shows the
    #: gap explicitly rather than silently omitting the edge.
    UNRESOLVED = "unresolved"

    ALL = (
        RETRIEVED_FACT,
        SUPPORTED_ASSOCIATION,
        MECHANISTIC_INFERENCE,
        UNKNOWN,
        # --- W03 additions (therapeutic_discovery) ---
        EXPERIMENTALLY_MEASURED,
        PREDICTED,
        UNRESOLVED,
    )


# ---------------------------------------------------------------------------
# Relationship
# ---------------------------------------------------------------------------


@dataclass
class Relationship:
    """
    A single directed edge in the Biological Impact Graph.

    `source_id` and `target_id` are stable entity identifiers
    assigned by the impact builder (see impact.py). They are
    strings, not object references, so the graph can be
    serialized, cached, and traversed without holding the
    entire entity graph in memory.

    `relationship_type` must be one of RelationshipType.ALL.
    Validation is a downstream concern; the schema does not
    enforce it, to keep construction cheap during graph
    assembly.

    `evidence_ids` references records in the evidence layer
    (see evidence.py, file 3 of this package). An empty list
    means no evidence has been attached yet, which is a valid
    intermediate state during graph construction but must be
    surfaced to the user as "insufficient evidence" rather
    than silently collapsed.

    `evidence_level` is a coarse category mirror for fast
    filtering before evidence lookup. It must never be the
    sole basis for a scientific claim; the full evidence
    record is authoritative.

    `confidence` is intentionally NOT a numeric probability.
    If a downstream stage produces a numeric score it lives in
    `metadata` under a named key, so it can never be mistaken
    for a clinical probability.
    """

    source_id: str
    target_id: str
    relationship_type: str
    evidence_ids: List[str] = field(default_factory=list)
    evidence_level: Optional[str] = None

    # ------------------------------------------------------------------
    # Workflow 02 — four-class support model. Optional and additive:
    # W01 relationships leave this as None and are unaffected.
    #
    # Must be one of SupportClass.ALL when set.
    # ------------------------------------------------------------------
    support_class: Optional[str] = None

    description: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Relationship collection
# ---------------------------------------------------------------------------


@dataclass
class RelationshipSet:
    """
    A collection of relationships plus lightweight indexes.

    The indexes are built lazily by the impact builder, not by
    this schema. This class is a plain container so that
    relationships can be passed around before indexing is
    required.
    """

    relationships: List[Relationship] = field(default_factory=list)
    by_source: Dict[str, List[int]] = field(default_factory=dict)
    by_target: Dict[str, List[int]] = field(default_factory=dict)
    by_type: Dict[str, List[int]] = field(default_factory=dict)

    def add(self, relationship: Relationship) -> int:
        """
        Append a relationship and return its index.

        Indexes are NOT updated here. Call build_indexes()
        when the set is complete.
        """
        self.relationships.append(relationship)
        return len(self.relationships) - 1

    def build_indexes(self) -> None:
        """
        Rebuild source / target / type indexes from the
        current relationship list. Safe to call repeatedly.
        """
        self.by_source.clear()
        self.by_target.clear()
        self.by_type.clear()

        for index, relationship in enumerate(self.relationships):
            self.by_source.setdefault(
                relationship.source_id, []
            ).append(index)

            self.by_target.setdefault(
                relationship.target_id, []
            ).append(index)

            self.by_type.setdefault(
                relationship.relationship_type, []
            ).append(index)
