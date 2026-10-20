"""
CureVerseAI — Bubble journey helpers.

Server-side summary of what the frontend bubble journey
would look like for a result. Mirrors the tiered
hierarchy in the frontend's bubbleJourney.ts, so tests
can assert journey shape without running the browser.

The frontend owns the actual rendering; this module
only extracts counts and picks the root system.
"""

from __future__ import annotations

from typing import Any, Dict, Optional


def _nodes_of_type(
    result: Dict[str, Any],
    node_type: str,
) -> list:
    return [
        n
        for n in (result.get("nodes") or [])
        if n.get("node_type") == node_type
    ]


def _pick_root_system(
    result: Dict[str, Any],
) -> Optional[Dict[str, Any]]:
    """
    Choose the most affected system by hpo_annotation_count.
    Matches the frontend's pickRootSystem.
    """
    systems = _nodes_of_type(result, "system")
    if not systems:
        return None

    best = systems[0]
    best_count = -1

    for s in systems:
        md = s.get("metadata") or {}
        count = int(md.get("hpo_annotation_count", 0) or 0)
        if count > best_count:
            best_count = count
            best = s

    return best


def summarize_journey(
    result: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Return counts and derived shape of the journey that
    would be shown for this result.

    Fields:
        systems   — number of system nodes
        tissues   — number of tissue nodes
        cells     — number of cell nodes
        molecules — number of gene + protein nodes
        root_system — name of the chosen root system
        journey_depth — how many non-empty tiers
                        (0-4) starting from the system

    Journey depth is computed as:
        0 if no systems
        1 + (tissues > 0 ? 1 : 0)
          + (cells > 0 ? 1 : 0)
          + (molecules > 0 ? 1 : 0)
    """
    systems = _nodes_of_type(result, "system")
    tissues = _nodes_of_type(result, "tissue")
    cells = _nodes_of_type(result, "cell")
    genes = _nodes_of_type(result, "gene")
    proteins = _nodes_of_type(result, "protein")

    molecules = genes + proteins

    root = _pick_root_system(result)

    depth = 0
    if systems:
        depth = 1
        if tissues:
            depth += 1
        if cells:
            depth += 1
        if molecules:
            depth += 1

    return {
        "systems": len(systems),
        "tissues": len(tissues),
        "cells": len(cells),
        "molecules": len(molecules),
        "root_system": (
            root.get("name") if root else None
        ),
        "journey_depth": depth,
    }
