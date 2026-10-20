"""
W02 Phase 1 — HPO type introspection (read-only).

Closes the last Open Targets uncertainty: the sub-field
names of the HPO object reached through
disease.phenotypes.rows.phenotypeHPO.

Also runs the correct query on asthma so we see the real
populated shape.
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
    # 1) Introspect HPO type
    # ------------------------------------------------------------------
    section("1) Introspect HPO type")
    safe_query(
        client,
        "__type(name='HPO') { fields }",
        """
        query IntrospectHPO {
          __type(name: "HPO") {
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
    # 2) Real query: disease -> phenotypes -> phenotypeHPO
    # ------------------------------------------------------------------
    section("2) disease(efoId='MONDO_0004979').phenotypes.rows.phenotypeHPO")
    safe_query(
        client,
        f"disease(efoId='{disease_id}').phenotypes (correct field path)",
        """
        query DiseasePhenotypeRows($efoId: String!) {
          disease(efoId: $efoId) {
            id
            name
            phenotypes {
              count
              rows {
                phenotypeHPO {
                  id
                  name
                  description
                }
                phenotypeEFO {
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
    # 3) Also introspect the evidence sub-structure
    # ------------------------------------------------------------------
    section("3) Introspect DiseaseHPOEvidence type (the evidence field)")
    safe_query(
        client,
        "__type(name='DiseaseHPOEvidence') { fields }",
        """
        query IntrospectEvidence {
          __type(name: "DiseaseHPOEvidence") {
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

    print()
    print(SEP)
    print("DONE — HPO type diagnostic complete.")
    print(SEP)


if __name__ == "__main__":
    main()
