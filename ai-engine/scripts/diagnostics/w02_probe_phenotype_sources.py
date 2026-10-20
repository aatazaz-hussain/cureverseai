"""
W02 Phase 1 — phenotype source diagnostic (read-only).

Three probes:
    1. Introspect DiseaseHPO type (the row type inside
       DiseaseHPOs.rows) — completing File 1b's deferred
       introspection.
    2. Query disease(efoId='MONDO:0004979').phenotypes.rows
       with the discovered fields, for asthma.
    3. Probe OLS4 /search with ontology=hp directly —
       see if HPO class terms are retrievable.
"""

import json
import sys
from pathlib import Path

import httpx

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
    # 1) Introspect DiseaseHPO type
    # ------------------------------------------------------------------
    section("1) Introspect DiseaseHPO type (the row type)")
    safe_query(
        client,
        "__type(name='DiseaseHPO') { fields }",
        """
        query IntrospectDiseaseHPO {
          __type(name: "DiseaseHPO") {
            name
            fields {
              name
              type {
                name
                kind
                ofType {
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
        }
        """,
        {},
    )

    # ------------------------------------------------------------------
    # 2) Query disease.phenotypes.rows with guessed fields
    # ------------------------------------------------------------------
    section("2) disease(efoId='MONDO_0004979').phenotypes.rows")
    safe_query(
        client,
        f"disease(efoId='{disease_id}').phenotypes.rows",
        """
        query DiseasePhenotypeRows($efoId: String!) {
          disease(efoId: $efoId) {
            id
            name
            phenotypes {
              count
              rows {
                id
                name
                description
                numberOfDatasources
              }
            }
          }
        }
        """,
        {"efoId": disease_id},
    )

    # ------------------------------------------------------------------
    # 3) Probe OLS4 /search with ontology=hp
    # ------------------------------------------------------------------
    section("3) OLS4 /search?ontology=hp&type=class — 'inflammation'")
    url = "https://www.ebi.ac.uk/ols4/api/search"
    params = {
        "q": "inflammation",
        "ontology": "hp",
        "type": "class",
        "rows": 5,
    }

    try:
        with httpx.Client(timeout=30.0, follow_redirects=True) as hc:
            response = hc.get(
                url,
                params=params,
                headers={
                    "Accept": "application/json",
                    "User-Agent": "CureVerseAI/1.0",
                },
            )
        print(f"HTTP {response.status_code}")
        if response.status_code < 400:
            payload = response.json()
            response_block = payload.get("response") or {}
            docs = response_block.get("docs") or []
            total = response_block.get("numFound", 0)

            print(f"numFound: {total}")
            print(f"docs returned: {len(docs)}")
            print()
            print("First 5 docs (raw):")
            print(json.dumps(docs[:5], indent=2)[:6000])
        else:
            print(response.text[:2000])
    except Exception as exc:
        print(f"FAILED: {type(exc).__name__}: {exc}")

    # ------------------------------------------------------------------
    # 4) OLS4 HP term lookup by specific ID (sanity check)
    # ------------------------------------------------------------------
    section("4) OLS4 HP direct term lookup — HP:0002099 (asthma)")
    url4 = "https://www.ebi.ac.uk/ols4/api/ontologies/hp/terms"
    params4 = {
        "obo_id": "HP:0002099",
    }
    try:
        with httpx.Client(timeout=30.0, follow_redirects=True) as hc:
            response = hc.get(
                url4,
                params=params4,
                headers={
                    "Accept": "application/json",
                    "User-Agent": "CureVerseAI/1.0",
                },
            )
        print(f"HTTP {response.status_code}")
        if response.status_code < 400:
            print(json.dumps(response.json(), indent=2)[:5000])
        else:
            print(response.text[:2000])
    except Exception as exc:
        print(f"FAILED: {type(exc).__name__}: {exc}")

    print()
    print(SEP)
    print("DONE — phenotype source diagnostic complete.")
    print(SEP)


if __name__ == "__main__":
    main()
