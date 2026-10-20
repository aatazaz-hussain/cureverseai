"""
CureVerseAI — Medicine domain
Disease resolver.

This module is a thin, read-only wrapper around the existing
Drug Development disease resolver:

    app.drug_development.disease.resolver.DiseaseResolver

The wrapper exists so that:

    1. Medicine code depends on a Medicine-local shape
       (``DiseaseRef``) rather than on W01's ``DiseaseIdentity``.
       If W01's internal shape ever changes, only this file
       needs updating.

    2. Medicine can record the resolution outcome as a
       ``SourceStatus`` alongside the resolved ``DiseaseRef``,
       so the workflow can distinguish "resolved", "no match",
       and "source unreachable" without collapsing them.

Design constraints:

    - No new external HTTP calls. This module does not
      instantiate an Open Targets or OLS client itself; it uses
      the W01 resolver, which already encapsulates them.

    - No fabrication. If the resolver returns a result with
      ``status != "resolved"``, that status is passed through
      verbatim. Callers must surface it honestly, per the
      Medicine specification.

    - No raising on bad input. An empty query or a query that
      does not resolve returns a ``DiseaseRef`` with
      ``resolution_status="invalid_input"`` or ``"unresolved"``,
      plus a ``SourceStatus`` marking the outcome.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

from app.medicine.simulation import schemas as s


# ---------------------------------------------------------------------------
# Identifier preference
# ---------------------------------------------------------------------------
#
# When a resolved DiseaseIdentity carries multiple identifiers
# from multiple sources, Medicine needs ONE canonical id for the
# ``DiseaseRef``. Preference order below reflects the sources
# with the widest cross-reference coverage and the most stable
# identifier form.

_IDENTIFIER_PREFERENCE: Tuple[str, ...] = (
    "MONDO",
    "DOID",
    "EFO",
    "ORPHA",
    "OMIM",
)


def _pick_canonical_identifier(
    identifiers: List[Any],
) -> Tuple[Optional[str], Optional[str]]:
    """
    Return (identifier_value, source) for the best identifier
    available, or (None, None) if there is none.

    Preference is by source name prefix. If no preferred source
    is present, the first identifier in the list is used.
    """
    if not identifiers:
        return None, None

    by_source: Dict[str, str] = {}
    for ident in identifiers:
        source = getattr(ident, "source", None) or ""
        value = getattr(ident, "identifier", None) or ""
        if source and value and source not in by_source:
            by_source[source] = value

    for preferred in _IDENTIFIER_PREFERENCE:
        if preferred in by_source:
            return by_source[preferred], preferred

    # Fallback: any identifier at all.
    for source, value in by_source.items():
        return value, source

    return None, None


# ---------------------------------------------------------------------------
# Mapping
# ---------------------------------------------------------------------------


def _map_to_ref(
    query: str,
    result_status: str,
    identity: Optional[Any],
) -> s.DiseaseRef:
    """
    Map a W01 ``DiseaseIdentity`` (or None) into a Medicine-local
    ``DiseaseRef``.

    Never raises. If ``identity`` is None, returns a DiseaseRef
    carrying the original query and the resolution status, with
    empty identifiers and metadata.
    """
    if identity is None:
        return s.DiseaseRef(
            id=None,
            name=query,
            query=query,
            source="",
            resolution_status=result_status or "unresolved",
            identifiers={},
            metadata={},
        )

    canonical_id, _canonical_source = _pick_canonical_identifier(
        getattr(identity, "identifiers", []) or []
    )

    name = (
        getattr(identity, "canonical_name", None)
        or getattr(identity, "query", None)
        or query
    )

    identifiers: Dict[str, str] = {}
    for ident in getattr(identity, "identifiers", []) or []:
        src = getattr(ident, "source", None)
        val = getattr(ident, "identifier", None)
        if src and val and src not in identifiers:
            identifiers[src] = val

    sources_list = getattr(identity, "sources", []) or []
    source_str = ",".join(sources_list) if sources_list else ""

    meta: Dict[str, Any] = dict(getattr(identity, "metadata", {}) or {})
    synonyms = getattr(identity, "synonyms", None)
    if synonyms:
        meta["synonyms"] = list(synonyms)
    category = getattr(identity, "category", None)
    if category:
        meta["category"] = category
    description = getattr(identity, "description", None)
    if description:
        meta["description"] = description

    return s.DiseaseRef(
        id=canonical_id,
        name=name,
        query=query,
        source=source_str,
        resolution_status=result_status or "unresolved",
        identifiers=identifiers,
        metadata=meta,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def resolve_disease(query: str) -> s.DiseaseRef:
    """
    Resolve a free-text disease query into a Medicine-local
    ``DiseaseRef``.

    Empty or whitespace-only queries return a DiseaseRef with
    ``resolution_status="invalid_input"``. No external call is
    made in that case.

    Never raises. A resolver failure (transport error, unexpected
    shape) is caught and returned as an unresolved DiseaseRef
    with an explanatory note in ``metadata``.
    """
    ref, _status = resolve_disease_with_status(query)
    return ref


def resolve_disease_with_status(
    query: str,
) -> Tuple[s.DiseaseRef, s.SourceStatus]:
    """
    Resolve a disease query AND return a ``SourceStatus`` record
    describing the outcome.

    The SourceStatus uses a stable source name that the workflow
    can aggregate. It distinguishes:

        reachable=True,  returned_records>0  -> resolved or partial
        reachable=True,  returned_records=0  -> unresolved / no_candidates
        reachable=False                      -> resolver raised

    The SourceStatus is diagnostic. The DiseaseRef is
    authoritative for the scientific state.
    """
    clean = (query or "").strip()

    if not clean:
        ref = s.DiseaseRef(
            id=None,
            name="",
            query="",
            source="",
            resolution_status="invalid_input",
            identifiers={},
            metadata={},
        )
        return ref, s.SourceStatus(
            source="disease_resolver",
            reachable=True,
            returned_records=0,
            error=None,
            metadata={"note": "empty query"},
        )

    # Lazy import so the W01 pipeline is not pulled at module
    # import time of Medicine code.
    from app.drug_development.disease.resolver import DiseaseResolver

    try:
        resolver = DiseaseResolver()
        result = resolver.resolve(clean)
    except Exception as exc:
        ref = s.DiseaseRef(
            id=None,
            name=clean,
            query=clean,
            source="",
            resolution_status="unresolved",
            identifiers={},
            metadata={"resolver_error": str(exc)},
        )
        return ref, s.SourceStatus(
            source="disease_resolver",
            reachable=False,
            returned_records=0,
            error=str(exc),
        )

    status = getattr(result, "status", "unresolved") or "unresolved"
    identity = getattr(result, "disease", None)

    ref = _map_to_ref(clean, status, identity)

    returned = 1 if identity is not None else 0
    note = getattr(result, "message", None)

    source_status = s.SourceStatus(
        source="disease_resolver",
        reachable=True,
        returned_records=returned,
        error=None,
        metadata={
            "status": status,
            "message": note,
        },
    )

    return ref, source_status
