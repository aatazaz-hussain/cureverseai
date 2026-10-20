"""
CureVerseAI — Journey Test.

Verifies that the AI Engine's full pipeline produces a
valid bubble journey for a set of real diseases.

For each disease:
  - runs the pipeline (through the pipeline module)
  - extracts the root system and tissue/cell/molecule counts
  - asserts the journey would render (at least 1 system,
    at least 1 tissue)

Also measures total runtime so we know how warm caches
help the demo.

Run:
    .venv/bin/python tests/journey_test.py
Exit code 0 if all pass, 1 otherwise.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Tuple

_AI_ENGINE_ROOT = Path(__file__).resolve().parents[1]
if str(_AI_ENGINE_ROOT) not in sys.path:
    sys.path.insert(0, str(_AI_ENGINE_ROOT))


from app.drug_development.pipeline import run_disease_impact
from app.drug_development.disease.bubble_journey_helpers import (
    summarize_journey,
)


# ---------------------------------------------------------------------------
# Test cases
# ---------------------------------------------------------------------------

TEST_DISEASES: List[str] = [
    "Asthma",
    "Alzheimer's disease",
    "Type 2 diabetes",
    "Breast cancer",
    "Parkinson disease",
]


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def run_one(query: str) -> Tuple[bool, List[str], Dict[str, Any]]:
    """Run the pipeline and summarize the journey."""

    failures: List[str] = []

    try:
        result = run_disease_impact(query)
    except Exception as exc:
        failures.append(f"pipeline raised: {exc!r}")
        return False, failures, {}

    if result.get("resolution_status") == "unresolved":
        failures.append("query did not resolve")
        return False, failures, {}

    summary = summarize_journey(result)

    # Structural assertions
    if summary["systems"] < 1:
        failures.append("no systems in result")

    if summary["tissues"] < 1:
        failures.append("no tissues in result")

    if summary["root_system"] is None:
        failures.append("no root system could be picked")

    if summary["journey_depth"] < 2:
        failures.append(
            f"journey depth is {summary['journey_depth']}, "
            f"expected at least 2"
        )

    return len(failures) == 0, failures, summary


# ---------------------------------------------------------------------------
# Entrypoint
# ---------------------------------------------------------------------------

def main() -> int:
    print("=" * 72)
    print("CureVerseAI — Journey Test")
    print("=" * 72)
    print()
    print(f"Diseases: {len(TEST_DISEASES)}")
    print("Each disease runs the full pipeline. Warm cache is fast.")
    print()

    total = 0
    passed = 0
    overall_start = time.time()

    for query in TEST_DISEASES:
        total += 1

        t0 = time.time()
        ok, failures, summary = run_one(query)
        elapsed = time.time() - t0

        if ok:
            passed += 1
            print(f"[PASS] {query!r} — {elapsed:.1f}s")
            print(
                f"       systems={summary['systems']}  "
                f"root={summary['root_system']!r}"
            )
            print(
                f"       tissues={summary['tissues']}  "
                f"cells={summary['cells']}  "
                f"molecules={summary['molecules']}"
            )
            print(
                f"       journey depth={summary['journey_depth']}"
            )
        else:
            print(f"[FAIL] {query!r} — {elapsed:.1f}s")
            for f in failures:
                print(f"         - {f}")

    overall = time.time() - overall_start

    print()
    print("=" * 72)
    print(
        f"RESULTS: {passed}/{total} passed in {overall:.1f}s"
    )
    print("=" * 72)

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
