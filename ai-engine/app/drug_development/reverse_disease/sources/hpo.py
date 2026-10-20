"""
CureVerseAI — Drug Development
Workflow 02 — Reverse Disease Engineering
HPO ontology client (EBI OLS4).

Purpose
-------

Workflow 02 needs two operations against the Human Phenotype
Ontology:

    get_term(obo_id)    -> enrichment of a known HP ID with
                           label, description, synonyms,
                           namespace, obsoletion flag

    search_terms(query) -> free-text lookup that returns HPO
                           class terms matching a phrase

Both operations are exposed by EBI OLS4.

Why a W02-local client instead of the existing OLSClient
--------------------------------------------------------

The existing OLSClient in
app/drug_development/disease/sources/ols.py has locked
supported-ontology tuples:

    SUPPORTED_ONTOLOGIES = ("mondo", "doid")
    ANATOMY_ONTOLOGIES   = ("uberon",)

HP is deliberately not in either tuple. Its docstring is
explicit that adding ontologies is a schema-level decision
made elsewhere, not an ad-hoc one buried in that client.

W02 therefore ships its own thin HPO client. It does NOT
modify OLSClient and it does NOT add HP to any of its tuples.

Conventions
-----------

- httpx only, matching every other client in this codebase.
- Cached with the shared DiskCache (SHA256 keys, 30 day TTL).
- Every method returns a plain dict with a `found: bool` key,
  matching the W01 convention.
- 404 returns found=False, not an exception.
- Other non-2xx responses raise RuntimeError.
- No numeric scores, no ranking, no fabrication.

HPO identifiers are normalized to colon form
("HP:0002099") on input and output. OLS4 returns both
underscore short_form and colon obo_id; callers get colon
form.

Public API
----------

    HPOClient(timeout=30.0, cache_dir=None, cache_ttl=None)

    .get_term(obo_id: str) -> dict
    .search_terms(query: str, size: int = 10) -> dict
"""

from __future__ import annotations

from pathlib import Path as _Path
from typing import Any, Dict, List, Optional

import httpx

from app.data.cache import DiskCache


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


OLS4_BASE_URL = "https://www.ebi.ac.uk/ols4/api"

#: W02-local cache directory. Kept separate from the W01
#: Ensembl and Reactome caches so failures are isolated.
_DEFAULT_CACHE_DIR = (
    _Path(__file__).resolve().parents[4]
    / "data" / "cache" / "w02_hpo"
)

#: HPO terms change slowly; 30 days is a reasonable TTL.
_DEFAULT_CACHE_TTL = 30 * 24 * 3600

#: The OLS4 ontology name for HPO.
_HPO_ONTOLOGY = "hp"

#: Max synonyms captured per term. Terms can have dozens of
#: narrow/related synonyms; we keep the first N and record
#: the truncation in metadata.
_MAX_SYNONYMS = 25


# ---------------------------------------------------------------------------
# Normalization helpers
# ---------------------------------------------------------------------------


def normalize_hp_id(raw: str) -> str:
    """
    Normalize an HPO identifier to colon form.

        "HP_0002099" -> "HP:0002099"
        "HP:0002099" -> "HP:0002099"

    Any input that already contains a colon is returned
    unchanged. Input without either separator is returned
    unchanged.
    """
    if not raw:
        return ""

    raw = raw.strip()

    if ":" in raw:
        return raw

    if "_" in raw:
        prefix, _, suffix = raw.rpartition("_")
        if prefix and suffix:
            return f"{prefix}:{suffix}"

    return raw


def _underscore_form(colon_form: str) -> str:
    """
    Convert "HP:0002099" to "HP_0002099" for OLS4 lookups
    that accept the underscore short_form.
    """
    if not colon_form:
        return ""
    return colon_form.replace(":", "_")


# ---------------------------------------------------------------------------
# Client
# ---------------------------------------------------------------------------


class HPOClient:
    """
    Minimal OLS4 client for HPO term lookup and search.

    Cache-backed. Non-blocking on 404. Raises RuntimeError
    only on transport-level failure or unexpected HTTP status.
    """

    def __init__(
        self,
        timeout: float = 30.0,
        cache_dir: Optional[str] = None,
        cache_ttl: int = _DEFAULT_CACHE_TTL,
    ):
        self.timeout = timeout
        self.cache = DiskCache(
            cache_dir or _DEFAULT_CACHE_DIR,
            ttl_seconds=cache_ttl,
        )

    # ------------------------------------------------------------------
    # Internal HTTP
    # ------------------------------------------------------------------

    def _get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Perform a GET against OLS4.

        A 404 returns None. Other non-2xx responses raise
        RuntimeError. Transport errors raise RuntimeError.
        """
        url = f"{OLS4_BASE_URL}{path}"

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
                f"OLS4 request timed out: {url}"
            ) from exc
        except httpx.RequestError as exc:
            raise RuntimeError(
                f"Unable to reach OLS4: {exc}"
            ) from exc

        if response.status_code == 404:
            return None

        if response.status_code >= 400:
            raise RuntimeError(
                f"OLS4 returned HTTP {response.status_code} "
                f"for {url}"
            )

        try:
            return response.json()
        except ValueError as exc:
            raise RuntimeError(
                f"OLS4 returned invalid JSON for {url}"
            ) from exc

    # ------------------------------------------------------------------
    # get_term
    # ------------------------------------------------------------------

    def get_term(self, obo_id: str) -> Dict[str, Any]:
        """
        Retrieve an HPO term by identifier.

        Accepts "HP:0002099" or "HP_0002099". Returns a
        normalized dict:

            {
                "found":       <bool>,
                "id":          "HP:0002099",
                "short_form":  "HP_0002099",
                "iri":         <str or None>,
                "name":        <str or None>,
                "description": <str or None>,
                "synonyms":    [<str>, ...],
                "namespace":   [<str>, ...],
                "is_obsolete": <bool>,
                "source":      "OLS4",
            }

        A term that OLS4 does not know returns found=False
        with the id echoed back and all other fields None
        or empty.
        """
        normalized = normalize_hp_id(obo_id)

        if not normalized:
            raise ValueError(
                "HPO identifier cannot be empty."
            )

        cache_key = DiskCache.make_key(
            "w02_hpo:get_term",
            normalized,
        )
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached.get("data")

        result = self._get_term_uncached(normalized)
        self.cache.set(cache_key, {"data": result})
        return result

    def _get_term_uncached(
        self,
        normalized_id: str,
    ) -> Dict[str, Any]:
        """
        Network path for get_term. No cache reads or writes.
        """

        empty = {
            "found": False,
            "id": normalized_id,
            "short_form": _underscore_form(normalized_id),
            "iri": None,
            "name": None,
            "description": None,
            "synonyms": [],
            "namespace": [],
            "is_obsolete": False,
            "source": "OLS4",
        }

        payload = self._get(
            f"/ontologies/{_HPO_ONTOLOGY}/terms",
            params={"obo_id": normalized_id},
        )

        if not payload:
            return empty

        embedded = payload.get("_embedded") or {}
        terms = embedded.get("terms") or []

        if not terms:
            return empty

        # OLS4 returns a single term for an obo_id filter.
        # If it ever returns multiple, we take the first and
        # record the extra count in metadata at the caller.
        term = terms[0]

        if not isinstance(term, dict):
            return empty

        raw_description = term.get("description")
        description = self._first_string(raw_description)

        synonyms = self._collect_synonyms(term)

        namespace = term.get("in_subset")
        if not isinstance(namespace, list):
            namespace = []

        return {
            "found": True,
            "id": normalize_hp_id(
                term.get("obo_id") or normalized_id
            ),
            "short_form": term.get("short_form")
            or _underscore_form(normalized_id),
            "iri": term.get("iri"),
            "name": term.get("label"),
            "description": description,
            "synonyms": synonyms,
            "namespace": [
                str(n) for n in namespace if n is not None
            ],
            "is_obsolete": bool(term.get("is_obsolete")),
            "source": "OLS4",
        }

    # ------------------------------------------------------------------
    # search_terms
    # ------------------------------------------------------------------

    def search_terms(
        self,
        query: str,
        size: int = 10,
    ) -> Dict[str, Any]:
        """
        Search HPO class terms by free text.

        Returns a normalized dict:

            {
                "query": <str>,
                "count": <int>,
                "rows": [
                    {
                        "id":          "HP:0002099",
                        "short_form":  "HP_0002099",
                        "name":        "Asthma",
                        "description": <str or None>,
                        "iri":         <str or None>,
                        "ontology":    "hp",
                    },
                    ...
                ],
                "source": "OLS4",
            }

        Rows are in server-returned order and are NOT ranked.
        Ontology filtering is re-applied client-side because
        OLS4's ontology parameter is not strictly enforced on
        the search endpoint.
        """
        query = (query or "").strip()

        if not query:
            raise ValueError(
                "HPO search query cannot be empty."
            )

        if size < 1:
            size = 1

        cache_key = DiskCache.make_key(
            "w02_hpo:search_terms",
            f"{query}|{size}",
        )
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached.get("data")

        result = self._search_terms_uncached(query, size)
        self.cache.set(cache_key, {"data": result})
        return result

    def _search_terms_uncached(
        self,
        query: str,
        size: int,
    ) -> Dict[str, Any]:
        payload = self._get(
            "/search",
            params={
                "q": query,
                "ontology": _HPO_ONTOLOGY,
                "type": "class",
                "rows": size,
            },
        )

        empty = {
            "query": query,
            "count": 0,
            "rows": [],
            "source": "OLS4",
        }

        if not payload:
            return empty

        response = payload.get("response") or {}
        docs = response.get("docs") or []

        rows: List[Dict[str, Any]] = []

        for doc in docs:
            if not isinstance(doc, dict):
                continue

            # Strict client-side filter.
            #
            # Root cause (W02 Phase 1 diagnostic, File 8c):
            # OLS4's `ontology_name` field reports "hp" even
            # for MPATH terms. The `ontology=hp` request
            # parameter is also not strictly enforced. The
            # `obo_id` prefix is the only reliable signal.
            #
            # Additionally, drop non-class documents even if
            # the server claims otherwise.
            if doc.get("type") != "class":
                continue

            obo_id = normalize_hp_id(
                doc.get("obo_id") or doc.get("short_form") or ""
            )

            if not obo_id.startswith("HP:"):
                continue

            rows.append(
                {
                    "id": obo_id,
                    "short_form": doc.get("short_form"),
                    "name": doc.get("label"),
                    "description": self._first_string(
                        doc.get("description")
                    ),
                    "iri": doc.get("iri"),
                    "ontology": doc.get("ontology_name"),
                }
            )

        return {
            "query": query,
            "count": len(rows),
            "rows": rows,
            "source": "OLS4",
        }

    # ------------------------------------------------------------------
    # Small helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _first_string(raw: Any) -> Optional[str]:
        """
        OLS4 returns `description` as a list whose first
        element is either a string or a dict with a "value"
        key. Return the first usable string, or None.
        """
        if isinstance(raw, str):
            return raw or None

        if isinstance(raw, list) and raw:
            first = raw[0]
            if isinstance(first, str):
                return first or None
            if isinstance(first, dict):
                value = first.get("value")
                if isinstance(value, str):
                    return value or None

        return None

    @staticmethod
    def _collect_synonyms(term: Dict[str, Any]) -> List[str]:
        """
        Collect unique synonym strings across the two OLS4
        synonym fields (`exact_synonyms`, `related_synonyms`)
        and the obo_synonym list.
        """
        seen: set[str] = set()
        out: List[str] = []

        def push(value: Any) -> None:
            if not isinstance(value, str):
                return
            value = value.strip()
            if not value or value in seen:
                return
            seen.add(value)
            if len(out) < _MAX_SYNONYMS:
                out.append(value)

        for key in ("exact_synonyms", "related_synonyms"):
            values = term.get(key)
            if isinstance(values, list):
                for v in values:
                    push(v)

        obo_syn = term.get("obo_synonym")
        if isinstance(obo_syn, list):
            for entry in obo_syn:
                if isinstance(entry, dict):
                    push(entry.get("name"))

        return out
