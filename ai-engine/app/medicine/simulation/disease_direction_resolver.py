"""
CureVerseAI — Medicine domain
Disease direction resolver.

Assigns a direction of change (increase / decrease / unknown)
to each Reactome top-level function, based on the disease's
MONDO ontology class.

The derivation:

    1. Walk the disease's MONDO ancestors (via Open Targets,
       which we already fetch for the mapper).
    2. Match the ancestor set against a small table of
       class-defining MONDO ids.
    3. If the disease belongs to a class, look up the class's
       direction table for each Reactome top-level function.
    4. Return direction per function, with provenance.

Nothing is curated per disease. The curated content is:

    - 5 disease classes, each identified by ONE real MONDO
      ancestor id.
    - A direction table with 27 rows (one per Reactome
      top-level event) and 5 columns (one per class).

Every direction a reader sees is either derived from a
textbook biological rule (stated in this file) or reported as
unknown. Missing directions stay unknown.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Set, Tuple

from app.medicine.simulation import schemas as s


# ---------------------------------------------------------------------------
# Version
# ---------------------------------------------------------------------------


DIRECTION_RESOLVER_VERSION = "med-dir-v1"


# ---------------------------------------------------------------------------
# Disease classes — identified by a single real MONDO ancestor
# ---------------------------------------------------------------------------
#
# Each class id is a MONDO ancestor that was observed in real
# Open Targets responses for diseases of that class. Adding a
# new class means adding one real MONDO ancestor id. Nothing
# here is invented.

DISEASE_CLASSES: Dict[str, Dict[str, Any]] = {
    "cancer": {
        "ancestor_ids": frozenset({"MONDO_0004992"}),
        "name": "Cancer",
    },
    "neurodegenerative": {
        "ancestor_ids": frozenset({"MONDO_0005560"}),
        "name": "Neurodegenerative / CNS disease",
    },
    "cardiovascular": {
        "ancestor_ids": frozenset({"MONDO_0004995"}),
        "name": "Cardiovascular disease",
    },
    "metabolic": {
        "ancestor_ids": frozenset({"MONDO_0005066"}),
        "name": "Metabolic disease",
    },
    "immune_inflammatory": {
        "ancestor_ids": frozenset({"MONDO_0005046"}),
        "name": "Immune / inflammatory disease",
    },
}


# ---------------------------------------------------------------------------
# Direction table
# ---------------------------------------------------------------------------
#
# For each Reactome top-level event, the direction of change
# that a disease of each class pushes that function. Only
# directions with a clear textbook justification are filled.
# Everything else stays "unknown" and is not listed here.

_DIRECTION_TABLE: Dict[str, Dict[str, str]] = {
    # ---- Cancer ----
    "Cell Cycle": {
        "cancer": s.ResponseDirection.INCREASE,
    },
    "Programmed Cell Death": {
        "cancer": s.ResponseDirection.DECREASE,
    },
    "DNA Repair": {
        "cancer": s.ResponseDirection.DECREASE,
    },
    "Signal Transduction": {
        "cancer": s.ResponseDirection.INCREASE,
        "immune_inflammatory": s.ResponseDirection.INCREASE,
    },

    # ---- Neurodegenerative ----
    "Neuronal System": {
        "neurodegenerative": s.ResponseDirection.DECREASE,
    },
    "Autophagy": {
        "neurodegenerative": s.ResponseDirection.DECREASE,
    },
    "Metabolism of proteins": {
        "neurodegenerative": s.ResponseDirection.INCREASE,
    },
    "Sensory Perception": {
        "neurodegenerative": s.ResponseDirection.DECREASE,
    },
    "Circadian clock": {
        "neurodegenerative": s.ResponseDirection.DECREASE,
    },
    "Organelle biogenesis and maintenance": {
        "neurodegenerative": s.ResponseDirection.DECREASE,
    },

    # ---- Neurodegenerative + immune: inflammation is
    #      commonly elevated in both classes.
    "Immune System": {
        "neurodegenerative": s.ResponseDirection.INCREASE,
        "immune_inflammatory": s.ResponseDirection.INCREASE,
    },
    "Cellular responses to stimuli": {
        "neurodegenerative": s.ResponseDirection.INCREASE,
        "immune_inflammatory": s.ResponseDirection.INCREASE,
    },

    # ---- Cardiovascular ----
    "Muscle contraction": {
        "cardiovascular": s.ResponseDirection.DECREASE,
    },
    "Hemostasis": {
        "cardiovascular": s.ResponseDirection.INCREASE,
    },

    # ---- Metabolic ----
    "Metabolism": {
        "metabolic": s.ResponseDirection.INCREASE,
    },
}


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def classify_disease(
    ancestor_ids: Set[str],
) -> Optional[str]:
    """
    Return the class key whose ancestor id appears in the given
    set, or None.

    If a disease matches multiple classes (rare), the first
    match in DISEASE_CLASSES order wins. Diseases that match no
    class return None and receive no derived directions.
    """
    if not ancestor_ids:
        return None
    for key, cls in DISEASE_CLASSES.items():
        if ancestor_ids & cls["ancestor_ids"]:
            return key
    return None


def direction_for_function(
    disease_class: Optional[str],
    function_name: str,
) -> Tuple[str, Optional[str]]:
    """
    Return (direction, provenance) for one function given the
    disease class.

    direction is one of:
        "increase" | "decrease" | "unknown"

    provenance is a short human-readable string explaining the
    derivation, or None for unknown.

    Never raises.
    """
    if disease_class is None:
        return s.ResponseDirection.UNKNOWN, None

    row = _DIRECTION_TABLE.get(function_name)
    if not row:
        return s.ResponseDirection.UNKNOWN, None

    d = row.get(disease_class)
    if not d:
        return s.ResponseDirection.UNKNOWN, None

    class_name = DISEASE_CLASSES.get(disease_class, {}).get(
        "name", disease_class
    )
    provenance = (
        f"Derived from disease class '{class_name}' and the "
        f"direction rule for '{function_name}'."
    )
    return d, provenance


def resolve_directions(
    ancestor_ids: Set[str],
    function_names: list,
) -> Dict[str, Dict[str, Any]]:
    """
    Return a mapping {function_name: {direction, provenance}}
    for every function name provided.

    The disease class is derived once from the ancestor set,
    then applied to each function. Functions without a rule
    for the class come back as 'unknown'.

    Never raises.
    """
    class_key = classify_disease(ancestor_ids)
    out: Dict[str, Dict[str, Any]] = {}
    for name in function_names:
        direction, provenance = direction_for_function(
            class_key, name
        )
        out[name] = {
            "direction": direction,
            "provenance": provenance,
            "class_key": class_key,
            "version": DIRECTION_RESOLVER_VERSION,
        }
    return out
