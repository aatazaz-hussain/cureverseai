"""
CureVerseAI — Drug Development
Workflow 02 — Reverse Disease Engineering
Disease Resolver (W02 adapter).

Thin adapter over the existing DiseaseResolver used by
Workflow 01.

Rationale
---------

The existing DiseaseResolver (in
app/drug_development/disease/resolver.py) already implements
everything W02's resolution step needs:

    - free-text -> DiseaseIdentity
    - Open Targets primary + OLS4 fallback
    - whole-word confidence rule with possessive normalization
    - "resolved" / "partial" / "unresolved" as first-class
      statuses
    - candidate preservation when the query is ambiguous
    - identifier normalization (underscore <-> colon form)
    - a noise filter for OBA measurement entities

W02's task is NOT to re-implement any of this. This module:

    1. delegates resolution to the shared resolver
    2. adds a to_layer_dict() helper that produces the
       W02-shaped dict the service layer needs for
       provenance and the disease block in the final
       result

The shared resolver's transport contract is preserved:
a RuntimeError from a source is NOT caught here. Transport
failures are surfaced to the service layer, which is where
provenance.source_failures lives.

Attribution
-----------

The shared resolver does not report which source produced
the resolution. This adapter infers it from the resolved
DiseaseIdentity's identifiers:

    - Open Targets produces identifiers with source
      "Open Targets"
    - OLS produces identifiers with source equal to the
      ontology name ("MONDO" or "DOID")

The inference is done from the resolved identity, not from
the raw response, because the resolver normalizes sources
before returning.

Public API
----------

    W02DiseaseResolver().resolve(query)
        -> DiseaseResolutionResult   (Phase 01 dataclass)

    W02DiseaseResolver.to_layer_dict(result)
        -> dict   (W02-shaped)

No other names are part of the public API.
"""

from __future__ import annotations

from typing import Any, Dict, List

from app.drug_development.disease.resolver import (
    DiseaseResolver,
)
from app.drug_development.schemas.disease import (
    DiseaseIdentifier,
    DiseaseIdentity,
    DiseaseResolutionResult,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


#: Canonical source names used in the W02 result. Kept here so
#: provenance and the disease block agree on strings.
SOURCE_OPEN_TARGETS = "Open Targets"
SOURCE_OLS = "OLS4"


# ---------------------------------------------------------------------------
# Adapter
# ---------------------------------------------------------------------------


class W02DiseaseResolver:
    """
    W02-facing disease resolver.

    Delegates to the shared DiseaseResolver and adds a
    W02-shaped layer dict.
    """

    def __init__(
        self,
        resolver: DiseaseResolver | None = None,
    ):
        self._resolver = resolver or DiseaseResolver()

    # ------------------------------------------------------------------
    # Resolution
    # ------------------------------------------------------------------

    def resolve(
        self,
        query: str,
    ) -> DiseaseResolutionResult:
        """
        Resolve a free-text disease query.

        Behavior is entirely delegated to the shared
        resolver. In particular:

            - blank query     -> status="unresolved"
            - ambiguous query -> status="partial"
            - clear match     -> status="resolved"
            - transport error -> RuntimeError propagates
        """
        return self._resolver.resolve(query)

    # ------------------------------------------------------------------
    # Layer dict
    # ------------------------------------------------------------------

    @staticmethod
    def to_layer_dict(
        result: DiseaseResolutionResult,
    ) -> Dict[str, Any]:
        """
        Produce a W02-shaped dict from a
        DiseaseResolutionResult.

        Shape:

            {
                "query":              <str>,
                "resolution_status":  "resolved" | "partial" | "unresolved",
                "resolved_name":      <str or None>,
                "identifiers":        [
                    {"source": <str>, "identifier": <str>, "url": <str or None>},
                    ...
                ],
                "candidates":         [
                    {
                        "canonical_name": <str>,
                        "identifiers":    [...],
                        "description":    <str or None>,
                        "sources":        [<str>, ...],
                    },
                    ...
                ],
                "message":            <str or None>,
                "sources_queried":    [<str>, ...],
            }

        `sources_queried` lists the sources that produced the
        result. When status is "unresolved" it is empty. When
        status is "resolved" it names the primary source.
        When status is "partial" it names every source whose
        candidates were preserved.

        No numeric scores are produced. Candidate order is
        preserved as the shared resolver returned it.
        """

        resolved_name = None
        identifiers: List[Dict[str, Any]] = []

        if result.disease is not None:
            resolved_name = result.disease.canonical_name
            identifiers = W02DiseaseResolver._identifiers_to_dicts(
                result.disease.identifiers
            )

        candidates = [
            W02DiseaseResolver._candidate_to_dict(c)
            for c in (result.candidates or [])
        ]

        sources_queried = W02DiseaseResolver._infer_sources(
            result
        )

        return {
            "query": result.query,
            "resolution_status": result.status,
            "resolved_name": resolved_name,
            "identifiers": identifiers,
            "candidates": candidates,
            "message": result.message,
            "sources_queried": sources_queried,
        }

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------

    @staticmethod
    def _identifiers_to_dicts(
        identifiers: List[DiseaseIdentifier],
    ) -> List[Dict[str, Any]]:
        out: List[Dict[str, Any]] = []

        for ident in identifiers or []:
            if not isinstance(ident, DiseaseIdentifier):
                continue

            out.append(
                {
                    "source": ident.source,
                    "identifier": ident.identifier,
                    "url": ident.url,
                }
            )

        return out

    @staticmethod
    def _candidate_to_dict(
        candidate: DiseaseIdentity,
    ) -> Dict[str, Any]:
        return {
            "canonical_name": candidate.canonical_name,
            "identifiers": W02DiseaseResolver._identifiers_to_dicts(
                candidate.identifiers
            ),
            "description": candidate.description,
            "sources": list(candidate.sources or []),
        }

    @staticmethod
    def _infer_sources(
        result: DiseaseResolutionResult,
    ) -> List[str]:
        """
        Infer which sources produced the resolution.

        The shared resolver does not report this directly.
        We infer from:

            - the resolved disease's identifiers (when
              status == "resolved")
            - the candidate sources (when status == "partial")

        Source names are normalized to the canonical strings
        used throughout W02.
        """

        collected: List[str] = []

        def push(name: str) -> None:
            if name and name not in collected:
                collected.append(name)

        # Resolved case
        if result.disease is not None:
            for ident in result.disease.identifiers or []:
                push(
                    W02DiseaseResolver._normalize_source(
                        ident.source
                    )
                )

        # Partial case — candidates may carry a mixture
        for candidate in result.candidates or []:
            for ident in candidate.identifiers or []:
                push(
                    W02DiseaseResolver._normalize_source(
                        ident.source
                    )
                )

        return collected

    @staticmethod
    def _normalize_source(raw: str) -> str:
        """
        Map a resolver-reported source name to the canonical
        W02 string.

        The shared resolver uses "Open Targets" for OT, and
        the ontology name (uppercase) for OLS rows, e.g.
        "MONDO", "DOID". Both of those come from OLS4.
        """
        if not raw:
            return ""

        if raw == SOURCE_OPEN_TARGETS:
            return SOURCE_OPEN_TARGETS

        # Anything that looks like an ontology name came
        # from OLS4.
        return SOURCE_OLS
