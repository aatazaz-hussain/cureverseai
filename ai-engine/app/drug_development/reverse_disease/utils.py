"""
CureVerseAI — Drug Development
Workflow 02 — Reverse Disease Engineering
Shared helpers.

Why this module exists
----------------------

The W01 disease resolver normalizes every disease identifier
to COLON form for consistency across the codebase:

    "MONDO_0004979"  ->  "MONDO:0004979"

That is correct for most of W02 — colon form is the
canonical representation used in node IDs, evidence records,
and cross-references.

But Open Targets' GraphQL `disease(efoId:)` argument
requires UNDERSCORE form. A colon-form ID returns
`{"data":{"disease":null}}` with HTTP 200 — a silent null.

Verified by direct curl on 2026-10-10:

    MONDO_0004979  ->  {"disease":{"id":"MONDO_0004979", ...}}
    MONDO:0004979  ->  {"disease":null}

Every W02 module that queries Open Targets by disease ID
must convert colon form to underscore form first. Rather
than duplicate the conversion in phenotype_retriever.py,
mechanism_retriever.py, gene_variant_mapper.py, and any
future module, the conversion lives here once.

The reverse direction (underscore -> colon) is provided by
W01's _normalize_identifier in
app/drug_development/disease/resolver.py, but that helper
is not exported as a public API. This module therefore
provides both directions as public, testable helpers.
"""

from __future__ import annotations


def to_opentargets_id(colon_form: str) -> str:
    """
    Convert a colon-form identifier to Open Targets'
    underscore form.

        "MONDO:0004979"  ->  "MONDO_0004979"
        "EFO:0000270"    ->  "EFO_0000270"
        "MONDO_0004979"  ->  "MONDO_0004979"   (already)
        ""               ->  ""

    Any input without a colon is returned unchanged.
    """
    if not colon_form:
        return ""

    raw = colon_form.strip()

    if ":" not in raw:
        return raw

    # Replace the FIRST colon only. Multi-colon IDs are not
    # expected, but if they ever appear, only the prefix
    # separator is what Open Targets cares about.
    return raw.replace(":", "_", 1)


def to_colon_form(underscore_form: str) -> str:
    """
    Convert an Open Targets identifier to colon form.

        "MONDO_0004979"  ->  "MONDO:0004979"
        "MONDO:0004979"  ->  "MONDO:0004979"   (already)
        ""               ->  ""

    Any input without an underscore is returned unchanged.
    Uses rpartition so a prefix that itself contains an
    underscore is preserved.
    """
    if not underscore_form:
        return ""

    raw = underscore_form.strip()

    if ":" in raw:
        return raw

    if "_" in raw:
        prefix, _, suffix = raw.rpartition("_")
        if prefix and suffix:
            return f"{prefix}:{suffix}"

    return raw
