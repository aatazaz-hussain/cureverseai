"""
CureVerseAI — Drug Development
EBI OLS4 (Ontology Lookup Service) client.

This client is used as a FALLBACK disease resolution source
when the primary source (Open Targets) does not return a
usable match.

Scope
-----

Only two disease ontologies are queried from OLS by design:

    - MONDO  (Mondo Disease Ontology)
    - DOID   (Disease Ontology)

These two cover the vast majority of named human diseases
while remaining canonical and non-overlapping enough to rank
without ambiguity. Broader cross-ontology search is
deliberately NOT performed here; adding more ontologies is a
schema-level decision made elsewhere, not an ad-hoc one
buried in this client.

API generation
--------------

This client targets OLS4:
    https://www.ebi.ac.uk/ols4/api

The endpoint used is the OLS4 search surface:

    GET /search?q=...&ontology=...&type=class&rows=N

IMPORTANT — endpoint correctness note:

    An earlier version of this client used

        GET /ontologies/{ontology}/terms?search=...

    which is NOT a full-text search surface in OLS4. It
    returns arbitrary ontology members (including genes in
    MONDO and chemicals in DOID) and produces scientifically
    invalid disease candidates. That endpoint must not be
    used for disease resolution.

    The correct surface is /search with type=class, which
    restricts results to ontology classes (the category that
    disease terms belong to).

Conventions
-----------

- httpx only, matching the existing OpenTargetsClient and
  EnsemblClient in this codebase.
- No external libraries beyond httpx.
- Errors raised as RuntimeError for transport/HTTP failures,
  consistent with the rest of the codebase.
- The client returns RAW candidates. It does not rank, does
  not decide canonicality, and does not filter by name
  similarity. Ranking is a resolver concern.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx


class OLSClient:
    """
    Minimal EBI OLS4 client for disease term resolution.

    Only the /search surface is exposed. If a downstream
    phase needs full term metadata (cross-references,
    ancestors, xrefs), add a dedicated method here rather
    than expanding search_term's return shape.
    """

    BASE_URL = "https://www.ebi.ac.uk/ols4/api"

    SUPPORTED_ONTOLOGIES = ("mondo", "doid")

    #: Anatomy ontologies used by the System -> Organ -> Tissue
    #: mapping in Phase 03. These are deliberately kept SEPARATE
    #: from SUPPORTED_ONTOLOGIES so that disease resolution can
    #: never accidentally return an anatomy term. Only the
    #: dedicated anatomy methods below use this tuple.
    ANATOMY_ONTOLOGIES = ("uberon",)

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Perform a GET against OLS4 and return the parsed JSON.

        A 404 returns None so callers can distinguish "not
        found" from a transport failure. Other non-2xx
        responses raise RuntimeError.
        """

        url = f"{self.BASE_URL}{path}"

        try:
            with httpx.Client(
                timeout=httpx.Timeout(
                    connect=10.0,
                    read=self.timeout,
                    write=10.0,
                    pool=10.0,
                ),
                follow_redirects=True,
            ) as client:
                response = client.get(
                    url,
                    params=params or {},
                    headers={
                        "Accept": "application/json",
                        "User-Agent": "CureVerseAI/1.0",
                    },
                )

        except httpx.TimeoutException as exc:
            raise RuntimeError(
                f"OLS request timed out: {url}"
            ) from exc

        except httpx.RequestError as exc:
            raise RuntimeError(
                f"Unable to reach OLS: {exc}"
            ) from exc

        if response.status_code == 404:
            return None

        if response.status_code >= 400:
            raise RuntimeError(
                f"OLS returned HTTP {response.status_code} "
                f"for {url}"
            )

        return response.json()

    @staticmethod
    def _normalize_ontology(ontology: str) -> str:
        ontology = (ontology or "").strip().lower()

        if ontology not in OLSClient.SUPPORTED_ONTOLOGIES:
            raise ValueError(
                f"Unsupported ontology '{ontology}'. "
                f"Supported: {list(OLSClient.SUPPORTED_ONTOLOGIES)}"
            )

        return ontology

    @staticmethod
    def _extract_description(doc: Dict[str, Any]) -> Optional[str]:
        """
        OLS4 returns `description` as a list of strings or as
        a list of dicts with a "value" key, depending on the
        ontology. Return the first usable string, or None.
        """

        descriptions = doc.get("description")

        if not isinstance(descriptions, list) or not descriptions:
            return None

        first = descriptions[0]

        if isinstance(first, str):
            return first

        if isinstance(first, dict):
            value = first.get("value")
            if isinstance(value, str):
                return value

        return None

    @staticmethod
    def _normalize_doc(
        doc: Dict[str, Any],
        expected_ontology: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Convert a single OLS4 search doc into the resolver-
        facing row shape.

        Returns None if the doc is not a class term, is not
        from the expected ontology, or is missing an
        identifier or label.
        """

        if not isinstance(doc, dict):
            return None

        # Restrict to ontology classes. This is the same
        # filter we sent on the wire, but re-checked here in
        # case the server ever returns mixed types.
        if doc.get("type") != "class":
            return None

        ontology_name = doc.get("ontology_name")

        if ontology_name != expected_ontology:
            return None

        obo_id = doc.get("obo_id")
        short_form = doc.get("short_form")
        label = doc.get("label")

        if not label:
            return None

        if not obo_id and not short_form:
            return None

        return {
            "id": obo_id or short_form,
            "short_form": short_form,
            "obo_id": obo_id,
            "name": label,
            "description": OLSClient._extract_description(doc),
            "iri": doc.get("iri"),
            "ontology": ontology_name,
            "ontology_prefix": doc.get("ontology_prefix"),
        }

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def search_term(
        self,
        query: str,
        ontology: str = "mondo",
        size: int = 10,
    ) -> Dict[str, Any]:
        """
        Search a single disease ontology for class terms
        matching a free-text query.

        Returns a normalized dictionary:

            {
                "query":      <original query>,
                "ontology":   <lowercased ontology name>,
                "count":      <number of rows returned>,
                "total":      <server-reported total matches>,
                "rows": [
                    {
                        "id":              <obo_id or short_form>,
                        "short_form":      <short_form or None>,
                        "obo_id":          <obo_id or None>,
                        "name":            <label>,
                        "description":     <first description or None>,
                        "iri":             <IRI or None>,
                        "ontology":        <ontology name>,
                        "ontology_prefix": <prefix or None>,
                    },
                    ...
                ],
            }

        A query that finds nothing returns count=0 and an empty
        rows list. This is a valid outcome, not an error.

        Results are in server-returned order and are NOT
        ranked. Ranking is a resolver concern.
        """

        query = query.strip()

        if not query:
            raise ValueError(
                "OLS search query cannot be empty."
            )

        ontology = self._normalize_ontology(ontology)

        if size < 1:
            size = 1

        payload = self._get(
            "/search",
            params={
                "q": query,
                "ontology": ontology,
                "type": "class",
                "rows": size,
            },
        )

        if not payload:
            return {
                "query": query,
                "ontology": ontology,
                "count": 0,
                "total": 0,
                "rows": [],
            }

        response = payload.get("response") or {}
        docs = response.get("docs") or []
        total = response.get("numFound", 0)

        rows: List[Dict[str, Any]] = []

        for doc in docs:
            row = self._normalize_doc(doc, ontology)
            if row is not None:
                rows.append(row)

        return {
            "query": query,
            "ontology": ontology,
            "count": len(rows),
            "total": total,
            "rows": rows,
        }

    def search_disease(
        self,
        query: str,
        size: int = 10,
    ) -> Dict[str, Any]:
        """
        Search BOTH supported disease ontologies (MONDO and
        DOID) and return a single merged candidate set.

        Rows are returned in the order:

            1. All MONDO hits, in server-returned order
            2. Then all DOID hits, in server-returned order

        This ordering is deterministic but is NOT a ranking.
        Ranking is the resolver's responsibility.
        """

        query = query.strip()

        if not query:
            raise ValueError(
                "OLS search query cannot be empty."
            )

        all_rows: List[Dict[str, Any]] = []
        counts_by_ontology: Dict[str, int] = {}
        totals_by_ontology: Dict[str, int] = {}

        for ontology in self.SUPPORTED_ONTOLOGIES:
            result = self.search_term(
                query=query,
                ontology=ontology,
                size=size,
            )
            counts_by_ontology[ontology] = result["count"]
            totals_by_ontology[ontology] = result["total"]
            all_rows.extend(result["rows"])

        return {
            "query": query,
            "count": len(all_rows),
            "counts_by_ontology": counts_by_ontology,
            "totals_by_ontology": totals_by_ontology,
            "rows": all_rows,
        }

    # ------------------------------------------------------------------
    # Anatomy ontology surface (System / Organ / Tissue mapping)
    # ------------------------------------------------------------------

    @staticmethod
    def _normalize_anatomy_ontology(ontology: str) -> str:
        ontology = (ontology or "").strip().lower()

        if ontology not in OLSClient.ANATOMY_ONTOLOGIES:
            raise ValueError(
                f"Unsupported anatomy ontology '{ontology}'. "
                f"Supported: {list(OLSClient.ANATOMY_ONTOLOGIES)}"
            )

        return ontology

    def search_anatomy_term(
        self,
        query: str,
        ontology: str = "uberon",
        size: int = 10,
    ) -> Dict[str, Any]:
        """
        Search an anatomy ontology (default Uberon) for class
        terms matching a free-text query.

        Return shape is IDENTICAL to search_term(), so
        downstream code can share the same normalizers. The
        only difference is which ontology tuple is validated.

        This method does NOT touch the disease resolution path.
        """

        query = query.strip()

        if not query:
            raise ValueError(
                "Anatomy search query cannot be empty."
            )

        ontology = self._normalize_anatomy_ontology(ontology)

        if size < 1:
            size = 1

        payload = self._get(
            "/search",
            params={
                "q": query,
                "ontology": ontology,
                "type": "class",
                "rows": size,
            },
        )

        if not payload:
            return {
                "query": query,
                "ontology": ontology,
                "count": 0,
                "total": 0,
                "rows": [],
            }

        response = payload.get("response") or {}
        docs = response.get("docs") or []
        total = response.get("numFound", 0)

        rows: List[Dict[str, Any]] = []

        for doc in docs:
            row = self._normalize_doc(doc, ontology)
            if row is not None:
                rows.append(row)

        return {
            "query": query,
            "ontology": ontology,
            "count": len(rows),
            "total": total,
            "rows": rows,
        }

    def get_anatomy_term(
        self,
        iri: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve a single anatomy term by IRI from OLS4.

        Returns None on 404 / not found.

        Used when we already know the term IRI (e.g. from a
        cross-reference) and want the full label, description,
        and parent relationships.
        """

        if not iri or not iri.strip():
            raise ValueError(
                "Anatomy term IRI cannot be empty."
            )

        iri = iri.strip()

        # OLS4 double-URL-encodes the IRI in the path.
        import urllib.parse
        encoded = urllib.parse.quote(
            urllib.parse.quote(iri, safe=""),
            safe="",
        )

        payload = self._get(
            f"/ontologies/uberon/terms/{encoded}"
        )

        if not payload:
            return None

        return {
            "iri": payload.get("iri"),
            "label": payload.get("label"),
            "obo_id": payload.get("obo_id"),
            "short_form": payload.get("short_form"),
            "description": payload.get("description"),
            "ontology": payload.get("ontology_name"),
            "is_obsolete": payload.get("is_obsolete"),
            "has_children": payload.get("has_children"),
            "parents": payload.get("_links", {}).get("parents"),
            "ancestors": payload.get("_links", {}).get("ancestors"),
            "source": "OLS4",
        }

