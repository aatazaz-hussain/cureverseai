"""
W02 Phase 1 — Open Targets diagnostic (read-only).

Probes the current Open Targets GraphQL API for the fields
Workflow 02 will need:

    1. disease search (already used by W01's resolver)
    2. disease -> associatedTargets (candidate mechanism layer)
    3. disease -> phenotypes (HPO)
    4. disease -> known drugs / mechanisms of action
    5. target -> associated variants (variant layer source)

Prints raw shapes. Writes nothing. Modifies nothing.
"""

import json
import sys
from pathlib import Path

# Ensure ai-engine is on the import path
AI_ENGINE_ROOT = Path("/home/aatazazhussain/projects/cureverseai/ai-engine")
sys.path.insert(0, str(AI_ENGINE_ROOT))

from app.drug_development.sources.open_targets import OpenTargetsClient  # noqa: E402


SEP = "=" * 78


def section(title: str) -> None:
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
    print(json.dumps(data, indent=2)[:6000])
    return data


def main():
    client = OpenTargetsClient(timeout=60.0)

    # ------------------------------------------------------------------
    # 1) Disease search — confirm the shape W01's resolver uses.
    # ------------------------------------------------------------------
    section("1) Disease search — asthma")
    search = safe_query(
        client,
        "search(queryString='asthma', entityNames=['disease'])",
        """
        query SearchDisease($query: String!, $size: Int!) {
          search(
            queryString: $query,
            entityNames: ["disease"],
            page: { index: 0, size: $size }
          ) {
            total
            hits {
              id
              name
              entity
              description
            }
          }
        }
        """,
        {"query": "asthma", "size": 5},
    )

    if not search:
        print("\nCannot continue — disease search failed.")
        return

    hits = (search.get("search") or {}).get("hits") or []
    if not hits:
        print("\nNo hits — cannot continue.")
        return

    disease_id = hits[0].get("id")
    disease_name = hits[0].get("name")
    print(f"\nUsing disease_id={disease_id}  name={disease_name}")

    # ------------------------------------------------------------------
    # 2) disease -> associatedTargets (candidate mechanism layer)
    # ------------------------------------------------------------------
    section("2) disease -> associatedTargets (top 5 rows, with datasource scores)")
    safe_query(
        client,
        f"disease(efoId='{disease_id}').associatedTargets",
        """
        query DiseaseTargets($efoId: String!, $size: Int!) {
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
        """,
        {"efoId": disease_id, "size": 5},
    )

    # ------------------------------------------------------------------
    # 3) disease -> phenotypes (HPO terms)
    # ------------------------------------------------------------------
    section("3) disease -> phenotypes (HPO)")
    safe_query(
        client,
        f"disease(efoId='{disease_id}').phenotypes",
        """
        query DiseasePhenotypes($efoId: String!) {
          disease(efoId: $efoId) {
            id
            name
            phenotypes {
              phenotype
              numberOfDatasources
              numberOfRows
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
        """,
        {"efoId": disease_id},
    )

    # ------------------------------------------------------------------
    # 4) disease -> known drugs / mechanism of action
    # ------------------------------------------------------------------
    section("4) disease -> knownDrugs (top 3)")
    safe_query(
        client,
        f"disease(efoId='{disease_id}').knownDrugs",
        """
        query DiseaseKnownDrugs($efoId: String!, $size: Int!) {
          disease(efoId: $efoId) {
            id
            name
            knownDrugs(page: { index: 0, size: $size }) {
              count
              rows {
                phase
                status
                drugId
                drug {
                  id
                  name
                  maximumClinicalTrialPhase
                  mechanismsOfAction {
                    rows {
                      mechanismOfAction
                      targets {
                        id
                        approvedSymbol
                      }
                    }
                  }
                }
                disease {
                  id
                  name
                }
              }
            }
          }
        }
        """,
        {"efoId": disease_id, "size": 3},
    )

    # ------------------------------------------------------------------
    # 5) target -> associated variants (variant layer source)
    # ------------------------------------------------------------------
    # Pick a target from the disease associations we just queried.
    section("5) target -> associated variants")
    target_query = safe_query(
        client,
        f"disease(efoId='{disease_id}').associatedTargets (target only)",
        """
        query DiseaseTargetsMinimal($efoId: String!, $size: Int!) {
          disease(efoId: $efoId) {
            associatedTargets(page: { index: 0, size: $size }) {
              rows {
                target {
                  id
                  approvedSymbol
                }
              }
            }
          }
        }
        """,
        {"efoId": disease_id, "size": 1},
    )

    if target_query:
        rows = (
            (target_query.get("disease") or {})
            .get("associatedTargets", {})
            .get("rows", [])
        )
        if rows:
            target_id = rows[0]["target"]["id"]
            target_symbol = rows[0]["target"]["approvedSymbol"]
            print(f"\nUsing target_id={target_id}  symbol={target_symbol}")

            section("5a) target.variants (attempt)")
            safe_query(
                client,
                f"target(ensemblId='{target_id}').variants",
                """
                query TargetVariants($id: String!) {
                  target(ensemblId: $id) {
                    id
                    approvedSymbol
                    variants {
                      id
                      variantId
                      rsIds
                      mostSevereConsequence {
                        id
                        label
                      }
                    }
                  }
                }
                """,
                {"id": target_id},
            )

    # ------------------------------------------------------------------
    # 6) disease class / therapeutic area (context for contributing factors)
    # ------------------------------------------------------------------
    section("6) disease core fields")
    safe_query(
        client,
        f"disease(efoId='{disease_id}') core",
        """
        query DiseaseCore($efoId: String!) {
          disease(efoId: $efoId) {
            id
            name
            description
            therapeuticAreas {
              id
              name
            }
            dbXRefs
            parents {
              id
              name
            }
          }
        }
        """,
        {"efoId": disease_id},
    )

    print()
    print(SEP)
    print("DONE — Open Targets diagnostic complete.")
    print(SEP)


if __name__ == "__main__":
    main()
