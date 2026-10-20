"""
W02 Phase 1 — Open Targets follow-up diagnostic (read-only).

Two probes:
    1. Introspect the real fields on DiseaseHPOs type
    2. Probe Disease.phenotypes with a minimal valid query
    3. Try the current variant field name on Target
"""

import json
import sys
from pathlib import Path

AI_ENGINE_ROOT = Path("/home/aatazazhussain/projects/cureverseai/ai-engine")
sys.path.insert(0, str(AI_ENGINE_ROOT))

from app.drug_development.sources.open_targets import OpenTargetsClient  # noqa: E402


SEP = "=" * 78


def section(title):
    print()
    print(SEP)
    print(title)
    print(SEP)


def safe_query(client, label, query, variables):
    print(f"\n--- {label} ---")
    try:
        data = client.query(query, variables)
    except Exception as exc:
        print(f"FAILED: {type(exc).__name__}: {exc}")
        return None
    print(json.dumps(data, indent=2)[:8000])
    return data


def main():
    client = OpenTargetsClient(timeout=60.0)
    disease_id = "MONDO_0004979"  # asthma

    # ------------------------------------------------------------------
    # 1) Introspect DiseaseHPOs type — see real field names
    # ------------------------------------------------------------------
    section("1) Introspect DiseaseHPOs type")
    safe_query(
        client,
        "__type(name='DiseaseHPOs') { fields }",
        """
        query IntrospectDiseaseHPOs {
          __type(name: "DiseaseHPOs") {
            name
            fields {
              name
              type {
                name
                kind
                ofType {
                  name
                  kind
                }
              }
            }
          }
        }
        """,
        {},
    )

    # ------------------------------------------------------------------
    # 2) Try disease.phenotypes with a minimal valid selection
    # ------------------------------------------------------------------
    section("2) disease.phenotypes minimal probe")
    safe_query(
        client,
        f"disease(efoId='{disease_id}').phenotypes (minimal)",
        """
        query MinimalPhenotypes($efoId: String!) {
          disease(efoId: $efoId) {
            id
            name
            phenotypes {
              edges {
                node {
                  id
                  name
                }
              }
            }
          }
        }
        """,
        {"efoId": disease_id},
    )

    # ------------------------------------------------------------------
    # 3) Introspect Target type — what variant-ish fields exist?
    # ------------------------------------------------------------------
    section("3) Introspect Target type (looking for variant fields)")
    safe_query(
        client,
        "__type(name='Target') { fields }",
        """
        query IntrospectTarget {
          __type(name: "Target") {
            name
            fields {
              name
            }
          }
        }
        """,
        {},
    )

    # ------------------------------------------------------------------
    # 4) Try disease.drugs (potential rename of knownDrugs)
    # ------------------------------------------------------------------
    section("4) disease.drugs probe (potential knownDrugs rename)")
    safe_query(
        client,
        f"disease(efoId='{disease_id}').drugs",
        """
        query DiseaseDrugs($efoId: String!, $size: Int!) {
          disease(efoId: $efoId) {
            id
            name
            drugs(page: { index: 0, size: $size }) {
              count
              rows {
                phase
                status
                drugId
                drug {
                  id
                  name
                  maximumClinicalTrialPhase
                }
              }
            }
          }
        }
        """,
        {"efoId": disease_id, "size": 3},
    )

    print()
    print(SEP)
    print("DONE — follow-up diagnostic complete.")
    print(SEP)


if __name__ == "__main__":
    main()
