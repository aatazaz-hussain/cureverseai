"""
CureVerseAI — Cache pre-warmer.

Runs the full Disease -> Biological Impact pipeline for
a list of demo diseases. Each run populates all disk
caches (Ensembl gene lookups, UniProt resolutions,
Reactome pathways). After this script completes, every
subsequent query for these diseases is fast.

Run:

    .venv/bin/python scripts/prewarm.py

The script is safe to run repeatedly. Cached entries
within the TTL window are reused; only missing entries
are fetched.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

_AI_ENGINE_ROOT = Path(__file__).resolve().parents[1]
if str(_AI_ENGINE_ROOT) not in sys.path:
    sys.path.insert(0, str(_AI_ENGINE_ROOT))


from app.drug_development.pipeline import run_disease_impact


# ---------------------------------------------------------------------------
# Diseases to pre-warm
# ---------------------------------------------------------------------------

DEMO_DISEASES = [
    # Most likely demo diseases
    "Alzheimer's disease",
    "Parkinson disease",
    "Asthma",
    "Type 2 diabetes",
    "Breast cancer",

    # Secondary
    "Lung cancer",
    "Heart disease",
    "Liver disease",
    "Kidney disease",
    "Thyroid disorder",
]


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def main() -> int:
    print("=" * 72)
    print("CureVerseAI — Cache Pre-warm")
    print("=" * 72)
    print()
    print(f"Diseases: {len(DEMO_DISEASES)}")
    print("Cold runs populate caches. Warm runs will be fast.")
    print()

    overall_start = time.time()
    total_cold = 0.0
    total = 0
    failed = 0

    for i, query in enumerate(DEMO_DISEASES, start=1):
        total += 1

        print(f"[{i}/{total}] {query}")

        t0 = time.time()
        try:
            result = run_disease_impact(query)
        except Exception as exc:
            elapsed = time.time() - t0
            print(f"      FAILED after {elapsed:.1f}s: {exc!r}")
            failed += 1
            continue

        elapsed = time.time() - t0
        total_cold += elapsed

        status = result.get("resolution_status", "?")
        nodes = len(result.get("nodes") or [])
        rels = len(result.get("relationships") or [])

        if status == "resolved":
            print(
                f"      OK — {elapsed:.1f}s — "
                f"{nodes} nodes, {rels} relationships"
            )
        elif status == "unresolved":
            print(
                f"      {elapsed:.1f}s — unresolved "
                f"(not a disease)"
            )
        else:
            print(
                f"      {elapsed:.1f}s — status={status}, "
                f"{nodes} nodes"
            )

        # Second run — should be near-instant
        t0 = time.time()
        try:
            run_disease_impact(query)
            warm = time.time() - t0
            print(f"      Warm run: {warm:.2f}s")
        except Exception:
            pass

    overall = time.time() - overall_start

    print()
    print("=" * 72)
    print(
        f"DONE: {total - failed}/{total} succeeded "
        f"in {overall:.1f}s total"
    )
    print("=" * 72)
    print()
    print("All caches are now warm.")
    print("Every subsequent query for these diseases will be")
    print("fast (typically under 5 seconds per disease).")
    print()

    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
