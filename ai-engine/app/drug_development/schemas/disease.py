"""
CureVerseAI — Drug Development
Disease domain schemas.

These schemas represent the internal disease identity model used
by the Disease -> Biological Impact workflow.

Design notes:
- Dataclasses are used here to match the internal-model convention
  already established in app/data/schemas.py and
  app/drug_development/evidence.py.
- Pydantic is reserved for API request/response boundaries.
- No external services or clients are imported. These are pure
  data structures only.
- A disease may fail to resolve cleanly. Partial and unresolved
  states are first-class outcomes, not exceptions.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Identifier
# ---------------------------------------------------------------------------


@dataclass
class DiseaseIdentifier:
    """
    A single external identifier for a disease.

    `source` names the authority that issued the identifier
    (for example an ontology or knowledge base). `identifier`
    is the identifier value as issued by that source.

    No source is assumed to be more authoritative than another
    at the schema level. Ranking is a downstream concern.
    """

    source: str
    identifier: str
    url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Disease identity
# ---------------------------------------------------------------------------


@dataclass
class DiseaseIdentity:
    """
    Canonical internal representation of a disease.

    This is the root node of the Disease -> Biological Impact
    workflow. Every downstream mapping (system, organ, tissue,
    cell, molecular, pathway, mechanism) is anchored to a
    DiseaseIdentity instance.

    `resolution_status` values:
        - "resolved"   : one confident canonical disease
        - "partial"    : disease recognized, but identity data
                         is incomplete or ambiguous
        - "unresolved" : disease could not be grounded
    """

    query: str
    canonical_name: Optional[str] = None
    synonyms: List[str] = field(default_factory=list)
    identifiers: List[DiseaseIdentifier] = field(default_factory=list)
    category: Optional[str] = None
    description: Optional[str] = None
    sources: List[str] = field(default_factory=list)
    resolution_status: str = "unresolved"
    metadata: Dict[str, Any] = field(default_factory=dict)


# ---------------------------------------------------------------------------
# Resolution result
# ---------------------------------------------------------------------------


@dataclass
class DiseaseResolutionResult:
    """
    Outcome of attempting to resolve a raw user query into a
    DiseaseIdentity.

    `candidates` preserves all plausible diseases when the
    resolver cannot confidently pick one. `disease` is only
    populated when the resolver has selected a canonical
    identity. Callers must be prepared for `disease is None`.

    `message` is intended for human-readable diagnostics and
    must not be treated as structured data.
    """

    query: str
    status: str
    disease: Optional[DiseaseIdentity] = None
    candidates: List[DiseaseIdentity] = field(default_factory=list)
    message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
