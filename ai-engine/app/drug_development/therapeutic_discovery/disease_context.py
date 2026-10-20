"""
CureVerseAI — Drug Development
Workflow 03 — Therapeutic Discovery
Disease Context.

Resolves the disease under investigation and records any
incoming mechanism or target identifier from a Workflow 02
handoff.

Responsibilities
----------------

    1. Accept either a free-text disease query or a
       pre-resolved disease identifier.
    2. Resolve the disease via W02's shared resolver.
    3. Validate and classify any incoming mechanism_id or
       target_id so downstream modules know how to expand
       them.
    4. Return a plain dict, not a dataclass, matching the
       layer-module convention used across W02 and W03.

Mechanism-kind inference
------------------------

The `mechanism_id` string arrives with a namespace prefix
that tells us how to expand it:

    pathway:R-HSA-*       -> a named biological process
                             from Reactome
    gene:SYMBOL           -> a gene
    protein:ACCESSION     -> a protein
    mechanism:evidence:*  -> a W02 evidence-category node
                             (not a biological mechanism)
    compound:CHEMBL*      -> a compound (unusual entry)
    <no prefix>           -> unknown, caller decides

The classification is a pure string operation. It does not
call any source.

What this module does NOT do
----------------------------

    - It does not expand the mechanism. That is the job of
      mechanism_resolver.py.
    - It does not fetch targets or compounds.
    - It does not catch transport errors from the resolver.
      Those propagate to the service layer, which records
      them in provenance.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.drug_development.reverse_disease.disease_resolver import (
    W02DiseaseResolver,
)
from app.drug_development.schemas.disease import (
    DiseaseIdentity,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


SOURCE_NAME = "Open Targets + OLS4 (via W02 resolver)"


# ---------------------------------------------------------------------------
# Helper — mechanism-kind inference
# ---------------------------------------------------------------------------


def classify_mechanism_id(mechanism_id: Optional[str]) -> Optional[str]:
    """
    Return the kind of a mechanism identifier, or None when
    no identifier was supplied.

    Kinds:
        "pathway"           pathway:R-HSA-XXXX
        "gene"              gene:SYMBOL
        "protein"           protein:ACCESSION
        "compound"          compound:CHEMBL*
        "evidence_category" mechanism:evidence:*
        "unknown"           anything else

    The function is case-sensitive on the prefix because the
    W02 vocabulary uses lowercase prefixes consistently.
    """
    if not mechanism_id:
        return None

    s = str(mechanism_id).strip()
    if not s:
        return None

    if s.startswith("pathway:"):
        return "pathway"
    if s.startswith("gene:"):
        return "gene"
    if s.startswith("protein:"):
        return "protein"
    if s.startswith("compound:"):
        return "compound"
    if s.startswith("mechanism:evidence:"):
        return "evidence_category"

    return "unknown"


# ---------------------------------------------------------------------------
# Context resolver
# ---------------------------------------------------------------------------


class DiseaseContextResolver:
    """
    W03's disease-context step.

    Delegates disease resolution to W02's resolver, keeps
    the W03-specific classification of mechanism/target
    identifiers, and returns a plain dict.
    """

    def __init__(
        self,
        resolver: Optional[W02DiseaseResolver] = None,
    ):
        self._resolver = resolver or W02DiseaseResolver()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def resolve(
        self,
        disease_query: str,
        mechanism_id: Optional[str] = None,
        target_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Resolve the disease and classify optional handoff IDs.

        Never raises for a blank query or an unresolvable
        disease. RuntimeError from the shared resolver
        propagates to the caller.
        """

        raw_query = (disease_query or "").strip()

        # If the caller supplied only a mechanism or target
        # and no disease, we still need a disease context.
        # W03 requires a disease anchor.
        if not raw_query and not mechanism_id and not target_id:
            return self._empty_result(
                query="",
                reason=(
                    "At least one of `disease`, `mechanism_id`, "
                    "or `target_id` must be provided."
                ),
                mechanism_id=mechanism_id,
                target_id=target_id,
            )

        if not raw_query:
            return self._empty_result(
                query="",
                reason=(
                    "A disease query is required. A mechanism "
                    "or target identifier alone does not "
                    "establish the disease context."
                ),
                mechanism_id=mechanism_id,
                target_id=target_id,
            )

        # ---- Resolve the disease via W02 --------------------------
        resolution = self._resolver.resolve(raw_query)

        if resolution.disease is None:
            return {
                "found": False,
                "query": raw_query,
                "resolution_status": resolution.status,
                "failure_reason": (
                    resolution.message
                    or "Disease could not be resolved."
                ),
                "disease": None,
                "candidates": list(
                    resolution.candidates or []
                ),
                "sources_queried": list(
                    W02DiseaseResolver.to_layer_dict(
                        resolution
                    ).get("sources_queried", [])
                ),
                "mechanism_id": mechanism_id,
                "mechanism_kind": classify_mechanism_id(
                    mechanism_id
                ),
                "target_id": target_id,
                "target_kind": classify_mechanism_id(
                    target_id
                ),
            }

        disease: DiseaseIdentity = resolution.disease

        return {
            "found": True,
            "query": raw_query,
            "resolution_status": disease.resolution_status,
            "failure_reason": None,
            "disease": disease,
            "candidates": [],
            "sources_queried": list(
                W02DiseaseResolver.to_layer_dict(
                    resolution
                ).get("sources_queried", [])
            ),
            "mechanism_id": mechanism_id,
            "mechanism_kind": classify_mechanism_id(
                mechanism_id
            ),
            "target_id": target_id,
            "target_kind": classify_mechanism_id(
                target_id
            ),
        }

    # ------------------------------------------------------------------
    # Empty / error path
    # ------------------------------------------------------------------

    @staticmethod
    def _empty_result(
        query: str,
        reason: str,
        mechanism_id: Optional[str] = None,
        target_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        return {
            "found": False,
            "query": query,
            "resolution_status": "unresolved",
            "failure_reason": reason,
            "disease": None,
            "candidates": [],
            "sources_queried": [],
            "mechanism_id": mechanism_id,
            "mechanism_kind": classify_mechanism_id(
                mechanism_id
            ),
            "target_id": target_id,
            "target_kind": classify_mechanism_id(target_id),
        }


# ---------------------------------------------------------------------------
# Convenience
# ---------------------------------------------------------------------------


def resolve_disease_context(
    disease_query: str,
    mechanism_id: Optional[str] = None,
    target_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    One-shot entry point.
    """
    return DiseaseContextResolver().resolve(
        disease_query=disease_query,
        mechanism_id=mechanism_id,
        target_id=target_id,
    )
