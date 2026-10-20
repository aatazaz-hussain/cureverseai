"""
W02 Phase 1 — mechanism layer diagnostic (read-only).

Probes disease.associatedTargets on Open Targets for asthma,
with the full datatypeScores and datasourceScores structure,
so File 9's design is grounded in real data.

Two views:
    1. Top 20 targets with full score breakdown
    2. Distribution of datatypes and datasources across
       the top 50 targets
"""

import sys
from collections import Counter, defaultdict
from pathlib import Path

AI_ENGINE_ROOT = Path("/home/aatazazhussain/projects/cureverseai/ai-engine")
sys.path.insert(0, str(AI_ENGINE_ROOT))

from app.drug_development.sources.open_targets import OpenTargetsClient  # noqa: E402
from app.drug_development.reverse_disease.utils import to_opentargets_id  # noqa: E402


SEP = "=" * 78


def section(title):
    print()
    print(SEP)
    print(title)
    print(SEP)


def main():
    client = OpenTargetsClient(timeout=60.0)

    # File 8 lesson: Open Targets requires underscore form
    disease_id = to_opentargets_id("MONDO:0004979")  # asthma

    # ------------------------------------------------------------------
    # Query 1: top 20 targets with full breakdown
    # ------------------------------------------------------------------
    section("1) Top 20 targets with datatype + datasource scores")

    query_top = """
    query W02MechanismTop($efoId: String!, $size: Int!) {
      disease(efoId: $efoId) {
        id
        name
        associatedTargets(page: { index: 0, size: $size }) {
          count
          rows {
            score
            target {
              id
              approvedSymbol
              approvedName
              biotype
            }
            datatypeScores {
              id
              score
            }
            datasourceScores {
              id
              score
            }
          }
        }
      }
    }
    """

    data = client.query(query_top, {"efoId": disease_id, "size": 20})

    disease = (data or {}).get("disease") or {}
    if not disease:
        print("FAILED: no disease returned.")
        return

    print(f"disease: {disease.get('name')}  (id: {disease.get('id')})")

    associated = disease.get("associatedTargets") or {}
    print(f"total associated targets: {associated.get('count')}")
    rows = associated.get("rows") or []
    print(f"rows returned: {len(rows)}")
    print()

    for i, row in enumerate(rows, 1):
        target = row.get("target") or {}
        print(f"  {i:2}. {target.get('approvedSymbol'):<12} | "
              f"score={row.get('score'):.3f} | "
              f"{target.get('approvedName')}")

        datatypes = row.get("datatypeScores") or []
        datasources = row.get("datasourceScores") or []

        if datatypes:
            dt_str = ", ".join(
                f"{d.get('id')}={d.get('score'):.3f}"
                for d in datatypes
                if isinstance(d, dict)
            )
            print(f"       datatypes:   {dt_str}")

        if datasources:
            ds_str = ", ".join(
                f"{d.get('id')}={d.get('score'):.3f}"
                for d in datasources
                if isinstance(d, dict)
            )
            print(f"       datasources: {ds_str}")

        print()

    # ------------------------------------------------------------------
    # Query 2: distribution across top 50
    # ------------------------------------------------------------------
    section("2) Distribution of datatypes + datasources across top 50")

    data2 = client.query(query_top, {"efoId": disease_id, "size": 50})
    rows2 = (
        ((data2 or {}).get("disease") or {})
        .get("associatedTargets", {})
        .get("rows", [])
    )

    datatype_counts = Counter()
    datasource_counts = Counter()
    datatype_scores_sum = defaultdict(float)
    datasource_scores_sum = defaultdict(float)

    for row in rows2:
        for d in row.get("datatypeScores") or []:
            if not isinstance(d, dict):
                continue
            dt = d.get("id")
            if dt:
                datatype_counts[dt] += 1
                datatype_scores_sum[dt] += float(d.get("score") or 0)

        for d in row.get("datasourceScores") or []:
            if not isinstance(d, dict):
                continue
            ds = d.get("id")
            if ds:
                datasource_counts[ds] += 1
                datasource_scores_sum[ds] += float(d.get("score") or 0)

    print(f"\ntargets analyzed: {len(rows2)}")
    print()

    print("--- datatypeScores distribution ---")
    for dt, count in datatype_counts.most_common():
        avg = datatype_scores_sum[dt] / count
        print(f"  {dt:<25} appears in {count:>2}/{len(rows2)} targets  | "
              f"avg_score={avg:.3f}")

    print()
    print("--- datasourceScores distribution ---")
    for ds, count in datasource_counts.most_common():
        avg = datasource_scores_sum[ds] / count
        print(f"  {ds:<25} appears in {count:>2}/{len(rows2)} targets  | "
              f"avg_score={avg:.3f}")

    # ------------------------------------------------------------------
    # Query 3: does Open Targets have 'mechanisms of action'?
    # ------------------------------------------------------------------
    section("3) Probe: disease.knownDrugs / drugs / mechanismsOfAction shape")

    # Known drugs was removed per File 1b. Try alternate names.
    for probe_name, probe_query in [
        (
            "disease.associatedTargets.rows.target.knownDrugs",
            """
            query T($efoId: String!) {
              disease(efoId: $efoId) {
                associatedTargets(page: {index: 0, size: 1}) {
                  rows {
                    target {
                      id
                      approvedSymbol
                      knownDrugs { count }
                    }
                  }
                }
              }
            }
            """,
        ),
        (
            "disease.parents (HDO terms)",
            """
            query T($efoId: String!) {
              disease(efoId: $efoId) {
                parents {
                  id
                  name
                }
              }
            }
            """,
        ),
    ]:
        print(f"\n--- {probe_name} ---")
        try:
            d = client.query(probe_query, {"efoId": disease_id})
            import json
            print(json.dumps(d, indent=2)[:3000])
        except Exception as e:
            print(f"FAILED: {type(e).__name__}: {str(e)[:400]}")

    print()
    print(SEP)
    print("DONE — mechanism diagnostic complete.")
    print(SEP)


if __name__ == "__main__":
    main()
