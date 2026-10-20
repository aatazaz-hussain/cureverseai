"""
CureVerseAI — Drug Development
Disease Resolver.

Resolves a free-text disease query into a canonical
DiseaseIdentity, using:

    PRIMARY  : Open Targets Platform (disease search)
    FALLBACK : EBI OLS4 (MONDO + DOID)

The resolver never fabricates a disease. If it cannot
confidently resolve a query, it returns status="partial"
(or "unresolved" when no candidate exists at all) and
preserves every candidate it retrieved.

Design contract
---------------

Every call returns a DiseaseResolutionResult (defined in
app/drug_development/schemas/disease.py).

status is one of:

    "resolved"   : a canonical disease was selected with
                   sufficient confidence to proceed downstream
    "partial"    : candidates exist but the query is too
                   ambiguous (or too short) to auto-select
    "unresolved" : no candidate was retrieved from any source

When status is "partial" or "unresolved", `disease` is None.
Callers must handle that case explicitly. The failure states
specified for the workflow (DISEASE RESOLVED / DISEASE NOT
FOUND / partial resolution) map directly onto this field.

Confidence rule
---------------

A candidate may only be auto-selected as `disease` when:

    1. The query, after normalization, is at least 3
       characters long, AND

    2. The candidate's label contains the query as a
       whole-word sequence (case-insensitive, punctuation-
       stripped).

This rejects noisy short queries like "ad" or "ca" while
accepting "Alzheimer", "TB", "ALS", and specific phrases
like "type 2 diabetes".

Source-of-truth rule
--------------------

Open Targets is primary. OLS4 is fallback. OLS4 may only
produce a `resolved` result when Open Targets returned zero
rows. When Open Targets returned rows but failed the
confidence rule, the result stays `partial` and OLS rows
are added as additional candidates for caller inspection.

Provenance rule
---------------

Identifiers from both sources are preserved. Open Targets
uses underscore form ("MONDO_0004975"); OLS uses colon form
("MONDO:0004975"). The resolver normalizes to colon form
and deduplicates by string value. Each identifier records
which source(s) produced it.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from app.drug_development.disease.sources.ols import OLSClient
from app.drug_development.schemas.disease import (
    DiseaseIdentifier,
    DiseaseIdentity,
    DiseaseResolutionResult,
)
from app.drug_development.sources.open_targets import (
    OpenTargetsClient,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

#: Minimum query CHARACTER length for auto-selection.
#: Measured against the raw query string, not token count.
#: Prevents auto-resolving extremely short queries like
#: "ad", "ca", "tb" while still allowing legitimate short
#: disease abbreviations such as "TB", "ALS", "MS".
MIN_QUERY_LENGTH = 3

#: Number of results to request from each source.
DEFAULT_SEARCH_SIZE = 10

#: How many top-ranked rows from a source may be scanned when
#: looking for the first row that satisfies the confidence
#: rule. Rank 1 is not always the right answer: for a query
#: like "Parkinson", Open Targets ranks "parkinsonian
#: disorder" first and "Parkinson disease" second. Scanning
#: a small fixed window lets the resolver pick the obvious
#: answer without exposing it to rank-4+ noise. Increasing
#: this raises recall at the cost of precision.
SELECTION_SCAN_DEPTH = 3


# ---------------------------------------------------------------------------
# Text helpers
# ---------------------------------------------------------------------------


_WORD_RE = re.compile(r"[a-z0-9]+")


def _tokenize(text: str) -> List[str]:
    """
    Lowercase and split on non-alphanumeric characters.

    Used for whole-word containment checks. Punctuation and
    case are discarded; word boundaries are preserved.

    Possessive 's is stripped BEFORE tokenization so that
    common English disease names match their non-possessive
    canonical forms:

        "Alzheimer's disease"  -> ["alzheimer", "disease"]
        "Parkinson's disease"  -> ["parkinson", "disease"]
        "Crohn's disease"      -> ["crohn", "disease"]

    Without this normalization, the "'s" would tokenize as a
    separate token and break whole-word containment against
    labels like "Alzheimer disease".
    """

    if not text:
        return []

    # Strip possessive 's and its common Unicode variants.
    # Order matters: curly apostrophe variants must be handled
    # before the plain ASCII apostrophe.
    cleaned = (
        text.replace("\u2019s", "")
            .replace("\u2018s", "")
            .replace("'s", "")
    )

    return _WORD_RE.findall(cleaned.lower())


def _contains_whole_words(
    query_tokens: List[str],
    label_tokens: List[str],
) -> bool:
    """
    True if the query's tokens appear as a contiguous
    subsequence of the label's tokens.

    Examples (all True):
        ["alzheimer"] in ["alzheimer", "disease"]
        ["parkinson"] in ["parkinson", "disease"]
        ["type", "2", "diabetes"] in
            ["type", "2", "diabetes", "mellitus"]

    Examples (all False):
        ["alz"] in ["alzheimer", "disease"]      (partial word)
        ["diab"] in ["type", "2", "diabetes"]    (partial word)
        ["breast"] in ["lung", "cancer"]         (not present)
    """

    if not query_tokens or not label_tokens:
        return False

    qn = len(query_tokens)

    if qn > len(label_tokens):
        return False

    for i in range(len(label_tokens) - qn + 1):
        if label_tokens[i : i + qn] == query_tokens:
            return True

    return False


def _normalize_identifier(raw: str) -> str:
    """
    Normalize an ontology identifier to colon form.

    Open Targets returns "MONDO_0004975".
    OLS returns        "MONDO:0004975".

    Both normalize to "MONDO:0004975".

    Identifiers without an underscore or colon (rare) are
    returned unchanged.
    """

    if not raw:
        return raw

    if ":" in raw:
        return raw

    if "_" in raw:
        prefix, _, suffix = raw.rpartition("_")
        if prefix and suffix:
            return f"{prefix}:{suffix}"

    return raw


# ---------------------------------------------------------------------------
# Resolver
# ---------------------------------------------------------------------------


#: Prefixes in Open Targets disease IDs that are not actual
#: diseases (measurement / phenotype-lab entities).
_OT_DENY_PREFIXES = (
    "OBA:",
)

#: Substrings that mark an Open Targets result as a lab /
#: measurement entity rather than a disease. Applied to the
#: label after lowercasing.
_OT_DENY_LABEL_SUBSTRINGS = (
    "measurement",
    "level of ",
    "biomarker",
)


def _should_filter_ot_row(row: Dict[str, Any]) -> bool:
    """
    Return True when an Open Targets row is NOT a disease
    entity and should be dropped from resolver output.

    This is a HEURISTIC noise filter, not a scientific
    classifier. It removes obvious non-disease entities
    (OBA lab measurements, "level of X" biomarkers) from
    Open Targets disease search results, which occasionally
    surface through the disease entity surface.

    The filter is conservative: it only drops rows that
    clearly match a measurement pattern. Anything ambiguous
    is kept so the user can still see it as a candidate.
    """

    raw_id = str(row.get("id") or "").strip()

    for prefix in _OT_DENY_PREFIXES:
        if raw_id.startswith(prefix):
            return True

    label = str(row.get("name") or "").strip().lower()

    if not label:
        return False

    for needle in _OT_DENY_LABEL_SUBSTRINGS:
        if needle in label:
            return True

    return False


def _select_matching_row(
    rows: List[Dict[str, Any]],
    query_tokens: List[str],
    raw_query: str,
) -> Optional[int]:
    """
    Scan the top SELECTION_SCAN_DEPTH rows and return the
    index of the first row whose label satisfies the
    confidence rule.

    Returns None if no row in the scan window passes.

    Callers use the returned index to build the resolved
    DiseaseIdentity from the correct row, rather than always
    assuming row 0. Rows that do not match remain in the
    candidate list untouched.
    """

    if len(raw_query) < MIN_QUERY_LENGTH:
        return None

    if not query_tokens:
        return None

    limit = min(SELECTION_SCAN_DEPTH, len(rows))

    for index in range(limit):
        row = rows[index]
        label = str(row.get("name") or "")
        tokens = _tokenize(label)

        if _contains_whole_words(query_tokens, tokens):
            return index

    return None


class DiseaseResolver:
    """
    Resolves free-text disease queries into DiseaseIdentity
    objects with candidates preserved.
    """

    def __init__(
        self,
        open_targets_client: Optional[OpenTargetsClient] = None,
        ols_client: Optional[OLSClient] = None,
    ):
        self.open_targets = (
            open_targets_client or OpenTargetsClient()
        )
        self.ols = ols_client or OLSClient()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def resolve(
        self,
        query: str,
        size: int = DEFAULT_SEARCH_SIZE,
    ) -> DiseaseResolutionResult:
        """
        Resolve a disease query.

        Never raises for a blank or unresolvable query. Any
        source-level RuntimeError propagates so callers can
        surface "biological intelligence service unavailable"
        distinctly from "disease not found".
        """

        raw_query = (query or "").strip()

        if not raw_query:
            return DiseaseResolutionResult(
                query="",
                status="unresolved",
                disease=None,
                candidates=[],
                message="Disease query cannot be empty.",
            )

        query_tokens = _tokenize(raw_query)

        # ---- Primary: Open Targets -------------------------------

        try:
            ot_result = self.open_targets.search_disease(
                raw_query,
                size=size,
            )
        except RuntimeError:
            # Transport failure on the primary source is NOT a
            # "disease not found". Let it propagate.
            raise

        ot_rows = [
            row for row in (ot_result.get("rows") or [])
            if not _should_filter_ot_row(row)
        ]

        if ot_rows:
            return self._resolve_from_primary(
                raw_query=raw_query,
                query_tokens=query_tokens,
                ot_rows=ot_rows,
                size=size,
            )

        # ---- Fallback: OLS --------------------------------------

        ols_result = self.ols.search_disease(
            raw_query,
            size=size,
        )

        ols_rows = list(ols_result.get("rows") or [])

        if not ols_rows:
            return DiseaseResolutionResult(
                query=raw_query,
                status="unresolved",
                disease=None,
                candidates=[],
                message=(
                    "No disease record was found in Open Targets "
                    "or in MONDO/DOID."
                ),
            )

        return self._resolve_from_fallback(
            raw_query=raw_query,
            query_tokens=query_tokens,
            ols_rows=ols_rows,
        )

    # ------------------------------------------------------------------
    # Internal resolution paths
    # ------------------------------------------------------------------

    def _resolve_from_primary(
        self,
        raw_query: str,
        query_tokens: List[str],
        ot_rows: List[Dict[str, Any]],
        size: int,
    ) -> DiseaseResolutionResult:
        """
        Open Targets returned rows. Scan the top
        SELECTION_SCAN_DEPTH rows for the first row whose
        label satisfies the confidence rule.

        If a match is found, auto-select that row. If none
        of the scanned rows match, enrich candidates with
        OLS and return partial.
        """

        ot_candidates = self._build_ot_candidates(ot_rows)

        match_index = _select_matching_row(
            ot_rows, query_tokens, raw_query
        )

        if match_index is not None:
            selected = ot_rows[match_index]
            selected_label = str(
                selected.get("name") or ""
            )

            disease = self._build_disease_identity(
                query=raw_query,
                canonical_name=selected_label,
                identifiers=self._ot_identifiers(
                    selected
                ),
                description=selected.get("description"),
                source="Open Targets",
            )

            # Every other Open Targets hit becomes a
            # candidate, in original server order.
            extra_candidates = [
                c
                for i, c in enumerate(ot_candidates)
                if i != match_index
            ]

            return DiseaseResolutionResult(
                query=raw_query,
                status="resolved",
                disease=disease,
                candidates=extra_candidates,
                message=(
                    f"Resolved to '{selected_label}' via "
                    f"Open Targets (rank {match_index + 1} "
                    f"of top {SELECTION_SCAN_DEPTH})."
                ),
            )

        # No row in the scan window matched. Try OLS to
        # enrich candidates, but keep the status partial.
        ols_candidates: List[DiseaseIdentity] = []

        try:
            ols_result = self.ols.search_disease(
                raw_query,
                size=size,
            )
            ols_rows = list(
                ols_result.get("rows") or []
            )
            ols_candidates = self._build_ols_candidates(
                ols_rows
            )
        except RuntimeError:
            # OLS failure during a partial result must not
            # destroy the partial result we already have.
            ols_candidates = []

        return DiseaseResolutionResult(
            query=raw_query,
            status="partial",
            disease=None,
            candidates=ot_candidates + ols_candidates,
            message=(
                "Query is ambiguous: multiple disease "
                "candidates were retrieved from Open Targets. "
                "No canonical match could be auto-selected."
            ),
        )

    def _resolve_from_fallback(
        self,
        raw_query: str,
        query_tokens: List[str],
        ols_rows: List[Dict[str, Any]],
    ) -> DiseaseResolutionResult:
        """
        Open Targets returned nothing. OLS is authoritative.

        Re-rank OLS rows, then scan the top
        SELECTION_SCAN_DEPTH rows for the first one whose
        label satisfies the confidence rule.
        """

        ranked = self._rank_ols_rows(
            ols_rows, query_tokens
        )

        candidates = self._build_ols_candidates(ranked)

        match_index = _select_matching_row(
            ranked, query_tokens, raw_query
        )

        if match_index is not None:
            selected = ranked[match_index]
            selected_label = str(
                selected.get("name") or ""
            )

            ontology = str(
                selected.get("ontology") or ""
            ).upper()

            disease = self._build_disease_identity(
                query=raw_query,
                canonical_name=selected_label,
                identifiers=self._ols_identifiers(
                    selected
                ),
                description=selected.get("description"),
                source=ontology or "OLS",
            )

            extra_candidates = [
                c
                for i, c in enumerate(candidates)
                if i != match_index
            ]

            return DiseaseResolutionResult(
                query=raw_query,
                status="resolved",
                disease=disease,
                candidates=extra_candidates,
                message=(
                    f"Resolved to '{selected_label}' via OLS "
                    f"({ontology}, rank {match_index + 1} of "
                    f"top {SELECTION_SCAN_DEPTH})."
                ),
            )

        return DiseaseResolutionResult(
            query=raw_query,
            status="partial",
            disease=None,
            candidates=candidates,
            message=(
                "Query is ambiguous: multiple MONDO/DOID "
                "candidates were retrieved. No canonical "
                "match could be auto-selected."
            ),
        )

    # ------------------------------------------------------------------
    # Ranking
    # ------------------------------------------------------------------

    @staticmethod
    def _rank_ols_rows(
        rows: List[Dict[str, Any]],
        query_tokens: List[str],
    ) -> List[Dict[str, Any]]:
        """
        Re-rank OLS rows for fallback resolution.

        OLS returns subtype variants before canonical terms
        (e.g. "Alzheimer disease 3" before "Alzheimer
        disease"). We re-rank to prefer:

            1. Exact whole-word match on the shortest label
            2. Shorter labels over longer ones
            3. MONDO over DOID
            4. Server order as the final tiebreaker
        """

        def sort_key(row: Dict[str, Any]) -> Tuple[int, int, int, int]:
            label = str(row.get("name") or "")
            tokens = _tokenize(label)

            exact = (
                0
                if query_tokens
                and tokens == query_tokens
                else 1
            )
            word_count = len(tokens)
            ontology_rank = (
                0 if row.get("ontology") == "mondo" else 1
            )

            # row index in the original list — must be stable
            original_index = rows.index(row)

            return (
                exact,
                word_count,
                ontology_rank,
                original_index,
            )

        return sorted(rows, key=sort_key)

    # ------------------------------------------------------------------
    # Builders
    # ------------------------------------------------------------------

    @staticmethod
    def _build_ot_candidates(
        rows: List[Dict[str, Any]],
    ) -> List[DiseaseIdentity]:
        candidates: List[DiseaseIdentity] = []

        for row in rows:
            label = row.get("name")
            if not label:
                continue

            candidates.append(
                DiseaseIdentity(
                    query=str(label),
                    canonical_name=str(label),
                    identifiers=DiseaseResolver._ot_identifiers(
                        row
                    ),
                    description=row.get("description"),
                    sources=["Open Targets"],
                    resolution_status="partial",
                )
            )

        return candidates

    @staticmethod
    def _build_ols_candidates(
        rows: List[Dict[str, Any]],
    ) -> List[DiseaseIdentity]:
        candidates: List[DiseaseIdentity] = []

        for row in rows:
            label = row.get("name")
            if not label:
                continue

            ontology = str(
                row.get("ontology") or ""
            ).upper()

            candidates.append(
                DiseaseIdentity(
                    query=str(label),
                    canonical_name=str(label),
                    identifiers=DiseaseResolver._ols_identifiers(
                        row
                    ),
                    description=row.get("description"),
                    sources=[ontology] if ontology else [],
                    resolution_status="partial",
                )
            )

        return candidates

    @staticmethod
    def _build_disease_identity(
        query: str,
        canonical_name: str,
        identifiers: List[DiseaseIdentifier],
        description: Optional[str],
        source: str,
    ) -> DiseaseIdentity:
        return DiseaseIdentity(
            query=query,
            canonical_name=canonical_name,
            synonyms=[],
            identifiers=identifiers,
            category=None,
            description=description,
            sources=[source],
            resolution_status="resolved",
        )

    # ------------------------------------------------------------------
    # Identifier builders (Decision 3: option i)
    # ------------------------------------------------------------------

    @staticmethod
    def _ot_identifiers(
        row: Dict[str, Any],
    ) -> List[DiseaseIdentifier]:
        """
        Build a normalized identifier list from an Open
        Targets row. Open Targets returns a single ID per
        row, in underscore form.
        """

        raw = row.get("id")
        if not raw:
            return []

        return [
            DiseaseIdentifier(
                source="Open Targets",
                identifier=_normalize_identifier(str(raw)),
                metadata={"raw_id": str(raw)},
            )
        ]

    @staticmethod
    def _ols_identifiers(
        row: Dict[str, Any],
    ) -> List[DiseaseIdentifier]:
        """
        Build a normalized identifier list from an OLS row.
        OLS returns both obo_id (colon form) and short_form
        (underscore form) for the same term.
        """

        identifiers: List[DiseaseIdentifier] = []
        seen: set[str] = set()

        obo_id = row.get("obo_id")
        short_form = row.get("short_form")

        for raw in (obo_id, short_form):
            if not raw:
                continue

            normalized = _normalize_identifier(str(raw))

            if normalized in seen:
                continue

            seen.add(normalized)

            identifiers.append(
                DiseaseIdentifier(
                    source=str(
                        row.get("ontology") or "OLS"
                    ).upper(),
                    identifier=normalized,
                    metadata={"raw_id": str(raw)},
                )
            )

        return identifiers
