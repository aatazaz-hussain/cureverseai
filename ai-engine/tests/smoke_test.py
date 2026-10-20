"""
CureVerseAI — AI Engine Smoke Test.

Runs the full Disease -> Biological Impact pipeline
against a fixed set of real diseases plus one nonsense
query, and verifies structural invariants on the
resulting BiologicalImpactResult.

Two modes:

    in-process (default)  Imports the pipeline directly.
                          No backend required.
    http                  POSTs to the backend at
                          http://localhost:8000 (override
                          with --backend-url).

CLI:

    python tests/smoke_test.py
    python tests/smoke_test.py --http
    python tests/smoke_test.py --both
    python tests/smoke_test.py --http --backend-url http://localhost:8000

Exit code 0 if all pass, 1 otherwise.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx

# Ensure the ai-engine root is on sys.path
_AI_ENGINE_ROOT = Path(__file__).resolve().parents[1]
if str(_AI_ENGINE_ROOT) not in sys.path:
    sys.path.insert(0, str(_AI_ENGINE_ROOT))


# ---------------------------------------------------------------------------
# Imports (shared by both modes)
# ---------------------------------------------------------------------------

from app.drug_development.disease.resolver import (
    DiseaseResolver,
)
from app.drug_development.disease.biological_systems import (
    BiologicalSystemsMapper,
)
from app.drug_development.disease.tissue_mapping import (
    TissueMapper,
)
from app.drug_development.disease.cellular_context import (
    CellularContextMapper,
)
from app.drug_development.disease.molecular_context import (
    MolecularContextMapper,
)
from app.drug_development.disease.pathway_mapping import (
    PathwayMapper,
)
from app.drug_development.disease.impact_evidence import (
    ImpactEvidenceIntegrator,
)
from app.drug_development.impact.impact_builder import (
    build_impact_result,
)
from app.drug_development.pipeline import (
    deserialize_impact_result,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

DEFAULT_BACKEND_URL = "http://localhost:8000"

#: HTTP read timeout. Matches the backend's own client
#: timeout against the AI Engine.
HTTP_TIMEOUT_SECONDS = 300.0

TEST_DISEASES: List[Tuple[str, str]] = [
    ("Alzheimer's disease", "resolved"),
    ("Breast cancer", "resolved"),
    ("Asthma", "resolved"),
    ("Type 2 diabetes", "resolved"),
    ("Parkinson disease", "resolved"),
    ("xyzzy not a real disease", "unresolved"),
]


# ---------------------------------------------------------------------------
# In-process runner
# ---------------------------------------------------------------------------


def run_pipeline(query: str) -> Dict[str, Any]:
    """
    Run the full pipeline in-process.

    Returns a dict with `resolution`, `layers`, `reasoning`,
    `impact`, `elapsed` — the same shape this module's
    assertions expect.
    """

    t0 = time.time()

    resolver = DiseaseResolver()
    resolution = resolver.resolve(query)

    result: Dict[str, Any] = {
        "query": query,
        "resolution": resolution,
        "disease": resolution.disease,
        "layers": {},
        "reasoning": None,
        "impact": None,
        "elapsed": 0.0,
    }

    if resolution.disease is None:
        result["elapsed"] = time.time() - t0
        return result

    d = resolution.disease

    systems = BiologicalSystemsMapper().map_disease_to_systems(d)
    tissues = TissueMapper().map_disease_to_tissues(d)
    cells = CellularContextMapper().map_disease_to_cell_types(d)
    molecular = MolecularContextMapper().map_disease_to_molecular_entities(d)
    pathways = PathwayMapper().map_disease_to_pathways(d)

    result["layers"] = {
        "systems": systems,
        "tissues": tissues,
        "cells": cells,
        "molecular": molecular,
        "pathways": pathways,
    }

    reasoning = ImpactEvidenceIntegrator().integrate(
        systems_result=systems,
        tissues_result=tissues,
        cells_result=cells,
        molecular_result=molecular,
        pathways_result=pathways,
    )
    result["reasoning"] = reasoning

    impact = build_impact_result(
        disease=d,
        raw_query=query,
        resolution_status=resolution.status,
        systems_result=systems,
        tissues_result=tissues,
        cells_result=cells,
        molecular_result=molecular,
        pathways_result=pathways,
        reasoning=reasoning,
    )
    result["impact"] = impact

    result["elapsed"] = time.time() - t0
    return result


# ---------------------------------------------------------------------------
# HTTP runner
# ---------------------------------------------------------------------------


class HTTPModeError(Exception):
    """Backend not reachable or returned an unexpected shape."""


def run_pipeline_http(
    query: str,
    backend_url: str,
) -> Dict[str, Any]:
    """
    Run the full pipeline via the backend HTTP endpoint.

    Returns a dict in the same shape as run_pipeline so the
    same assertions can be applied.
    """

    url = f"{backend_url.rstrip('/')}/api/v1/analyze"

    payload = {
        "domain": "drug_development",
        "task": "disease_biological_impact",
        "input": {"disease": query},
    }

    t0 = time.time()

    try:
        with httpx.Client(
            timeout=httpx.Timeout(
                connect=10.0,
                read=HTTP_TIMEOUT_SECONDS,
                write=30.0,
                pool=30.0,
            ),
        ) as client:
            response = client.post(url, json=payload)
    except httpx.RequestError as exc:
        raise HTTPModeError(
            f"Backend not reachable at {backend_url}: {exc}"
        ) from exc

    if response.status_code >= 400:
        raise HTTPModeError(
            f"Backend returned HTTP {response.status_code}: "
            f"{response.text[:200]}"
        )

    try:
        body = response.json()
    except ValueError as exc:
        raise HTTPModeError(
            f"Backend returned non-JSON: {response.text[:200]}"
        ) from exc

    if not body.get("success"):
        raise HTTPModeError(
            f"Backend reported success=False: {body}"
        )

    inner = body.get("data") or {}
    result_dict = inner.get("result")

    if not isinstance(result_dict, dict):
        raise HTTPModeError(
            f"Backend response missing data.result: "
            f"{json.dumps(body)[:200]}"
        )

    # Rebuild dataclasses from serialized form
    impact = deserialize_impact_result(result_dict)

    # Reconstruct the shape assert_structure expects
    resolution = _Namespace(
        status=result_dict.get("resolution_status", "unresolved"),
        disease=impact.disease,
        message=result_dict.get("failure_reason"),
    )

    return {
        "query": result_dict.get("query", query),
        "resolution": resolution,
        "disease": impact.disease,
        "layers": {},  # HTTP response is fully assembled
        "reasoning": result_dict.get("reasoning"),
        "impact": impact,
        "elapsed": time.time() - t0,
    }


class _Namespace:
    """Trivial attribute-bag for shims."""

    def __init__(self, **kwargs):
        self.__dict__.update(kwargs)


# ---------------------------------------------------------------------------
# Assertions
# ---------------------------------------------------------------------------


def assert_structure(
    result: Dict[str, Any],
    expected_status: str,
    mode: str = "inproc",
) -> List[str]:
    """
    Verify structural invariants. Returns a list of
    failure messages (empty if all pass).
    """

    failures: List[str] = []

    query = result["query"]
    resolution = result["resolution"]
    impact = result["impact"]
    layers = result["layers"]

    # Nonsense query path
    if expected_status == "unresolved":
        if resolution.disease is not None:
            failures.append(
                f"nonsense query unexpectedly resolved to "
                f"'{resolution.disease.canonical_name}'"
            )
        if resolution.status != "unresolved":
            failures.append(
                f"nonsense query status is "
                f"'{resolution.status}', expected 'unresolved'"
            )
        if impact is not None and mode == "inproc":
            # In-process: unresolved short-circuits before
            # any impact is built. HTTP mode always
            # receives an impact-shaped body (with zero
            # nodes), which is fine.
            failures.append(
                "nonsense query produced a non-None impact"
            )
        return failures

    # Real disease path
    if resolution.disease is None:
        failures.append(
            f"resolution returned no disease for '{query}'"
        )
        return failures

    if resolution.status not in ("resolved", "partial"):
        failures.append(
            f"resolution.status is '{resolution.status}', "
            f"expected 'resolved' or 'partial'"
        )

    if impact is None:
        failures.append("impact result is None")
        return failures

    # Disease node must exist
    disease_node_ids = [
        node.node_id
        for node in impact.nodes.nodes
        if node.node_type == "disease"
    ]
    if not disease_node_ids:
        failures.append("no disease node emitted")
    elif len(disease_node_ids) > 1:
        failures.append(
            f"expected exactly 1 disease node, got "
            f"{len(disease_node_ids)}"
        )

    # Integrity must be OK
    integrity = impact.metadata.get("integrity") or {}
    if not integrity.get("ok"):
        failures.append(
            f"integrity.ok is False: "
            f"dangling_sources="
            f"{len(integrity.get('dangling_relationship_sources', []))}, "
            f"dangling_targets="
            f"{len(integrity.get('dangling_relationship_targets', []))}, "
            f"missing_evidence="
            f"{len(integrity.get('relationships_with_missing_evidence', []))}"
        )

    # In-process mode checks layers; HTTP mode does not
    # receive per-layer dicts, so skip that check in HTTP.
    if mode == "inproc":
        layers_found = 0
        for layer_name in (
            "systems", "tissues", "cells", "molecular", "pathways"
        ):
            layer = layers.get(layer_name)
            if layer and layer.get("found"):
                layers_found += 1

        if layers_found < 3:
            failures.append(
                f"only {layers_found}/5 layers contributed nodes"
            )

        def _layer_node_count(name: str) -> int:
            layer = layers.get(name) or {}
            return len(layer.get("nodes") or [])

        if _layer_node_count("systems") < 1:
            failures.append("no system nodes")
        if _layer_node_count("molecular") < 3:
            failures.append("fewer than 3 molecular nodes")
        if _layer_node_count("pathways") < 3:
            failures.append("fewer than 3 pathway nodes")

    # Every relationship endpoint resolves to a real node
    node_ids = set(impact.nodes.by_id.keys())
    for rel in impact.relationships.relationships:
        if rel.source_id not in node_ids:
            failures.append(
                f"relationship source {rel.source_id} not in nodes"
            )
            break
        if rel.target_id not in node_ids:
            failures.append(
                f"relationship target {rel.target_id} not in nodes"
            )
            break

    # Reasoning must be present
    if impact.reasoning is None:
        failures.append("reasoning is None")
    else:
        if not impact.reasoning.summary:
            failures.append("reasoning.summary is empty")
        if not impact.reasoning.limitations:
            failures.append("reasoning.limitations is empty")

    return failures


# ---------------------------------------------------------------------------
# Reporting
# ---------------------------------------------------------------------------


def _format_pass(result: Dict[str, Any], prefix: str) -> str:
    impact = result["impact"]
    if impact is None:
        return (
            f"{prefix}[PASS] {result['query']!r} — "
            f"unresolved (no impact)"
        )

    n = len(impact.nodes.nodes)
    r = len(impact.relationships.relationships)
    e = len(impact.evidence.records)
    t = result["elapsed"]

    return (
        f"{prefix}[PASS] {result['query']!r} — "
        f"{n} nodes, {r} relationships, {e} evidence, "
        f"{t:.1f}s"
    )


def _format_fail(
    result: Dict[str, Any],
    failures: List[str],
    prefix: str,
) -> str:
    lines = [f"{prefix}[FAIL] {result['query']!r}"]
    for f in failures:
        lines.append(f"{prefix}         - {f}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Mode runners
# ---------------------------------------------------------------------------


def run_inproc_mode() -> Tuple[int, int]:
    """
    Run all tests in-process.
    Returns (passed, total).
    """

    passed = 0
    total = 0

    for query, expected in TEST_DISEASES:
        total += 1

        try:
            result = run_pipeline(query)
        except Exception as exc:
            print(f"[FAIL] {query!r}")
            print(f"         - pipeline raised: {exc!r}")
            continue

        failures = assert_structure(
            result, expected, mode="inproc"
        )

        if failures:
            print(_format_fail(result, failures, prefix=""))
        else:
            passed += 1
            print(_format_pass(result, prefix=""))

    return passed, total


def run_http_mode(
    backend_url: str,
) -> Tuple[int, int]:
    """
    Run all tests via the backend HTTP endpoint.
    Returns (passed, total).
    """

    # Preflight: is the backend reachable?
    try:
        with httpx.Client(timeout=5.0) as client:
            ping = client.get(f"{backend_url.rstrip('/')}/")
        if ping.status_code >= 400:
            print(
                f"ERROR: Backend at {backend_url} responded "
                f"with HTTP {ping.status_code}"
            )
            return 0, 0
    except httpx.RequestError as exc:
        print(
            f"ERROR: Backend not reachable at {backend_url}: "
            f"{exc}"
        )
        return 0, 0

    passed = 0
    total = 0

    for query, expected in TEST_DISEASES:
        total += 1

        try:
            result = run_pipeline_http(query, backend_url)
        except HTTPModeError as exc:
            print(f"[HTTP][FAIL] {query!r}")
            print(f"[HTTP]         - {exc}")
            continue
        except Exception as exc:
            print(f"[HTTP][FAIL] {query!r}")
            print(f"[HTTP]         - unexpected: {exc!r}")
            continue

        # HTTP mode: structural assertions only
        failures = assert_structure(
            result, expected, mode="http"
        )

        if failures:
            print(_format_fail(result, failures, prefix="[HTTP] "))
        else:
            passed += 1
            print(_format_pass(result, prefix="[HTTP] "))

    return passed, total


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _parse_args(argv: Optional[List[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "CureVerseAI AI Engine smoke test "
            "(in-process and/or HTTP mode)."
        ),
    )

    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--http",
        action="store_true",
        help="Run tests against the backend HTTP API.",
    )
    mode.add_argument(
        "--both",
        action="store_true",
        help="Run both in-process and HTTP tests.",
    )

    parser.add_argument(
        "--backend-url",
        default=os.getenv(
            "CUREVERSEAI_BACKEND_URL", DEFAULT_BACKEND_URL
        ),
        help=(
            "Backend URL for HTTP mode "
            f"(default: {DEFAULT_BACKEND_URL})."
        ),
    )

    return parser.parse_args(argv)


def main(argv: Optional[List[str]] = None) -> int:
    args = _parse_args(argv)

    print("=" * 70)
    print("CureVerseAI — AI Engine Smoke Test")
    print("=" * 70)
    print()
    print(f"Cases: {len(TEST_DISEASES)}  (real sources)")
    print(
        f"Mode:  "
        f"{'http' if args.http else 'both' if args.both else 'inproc'}"
    )
    if args.http or args.both:
        print(f"Backend: {args.backend_url}")
    print()

    start = time.time()

    total = 0
    passed = 0

    if not args.http:
        p, t = run_inproc_mode()
        passed += p
        total += t

    if args.both:
        print()

    if args.http or args.both:
        p, t = run_http_mode(args.backend_url)
        passed += p
        total += t

    elapsed = time.time() - start

    print()
    print("=" * 70)
    print(
        f"RESULTS: {passed}/{total} passed in {elapsed:.1f}s"
    )
    print("=" * 70)

    return 0 if passed == total and total > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
