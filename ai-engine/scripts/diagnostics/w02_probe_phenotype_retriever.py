"""
W02 Phase 1 — phenotype retriever diagnostic.

Runs five GraphQL variants against Open Targets to pinpoint
exactly which sub-selection is being rejected.
"""

import sys
from pathlib import Path

AI_ENGINE_ROOT = Path("/home/aatazazhussain/projects/cureverseai/ai-engine")
sys.path.insert(0, str(AI_ENGINE_ROOT))

from app.drug_development.sources.open_targets import OpenTargetsClient  # noqa: E402


def run(label, query):
    print(f"\n=== {label} ===")
    client = OpenTargetsClient(timeout=60.0)
    try:
        data = client.query(query, {"efoId": "MONDO:0004979"})
    except Exception as e:
        print(f"FAILED: {type(e).__name__}: {str(e)[:600]}")
        return
    d = (data or {}).get("disease")
    if d is None:
        print("SUCCESS but disease is None")
        print("  raw data:", str(data)[:300])
        return
    print("SUCCESS")
    print("  disease name:", d.get("name"))
    ph = d.get("phenotypes") or {}
    print("  count:", ph.get("count"))
    print("  rows:", len(ph.get("rows") or []))


# Query A: minimal
run("A — just count", """
query TA($efoId: String!) {
  disease(efoId: $efoId) {
    id
    phenotypes {
      count
    }
  }
}
""")

# Query B: phenotypeHPO only
run("B — phenotypeHPO { id name description } only", """
query TB($efoId: String!) {
  disease(efoId: $efoId) {
    id
    name
    phenotypes {
      count
      rows {
        phenotypeHPO { id name description }
      }
    }
  }
}
""")

# Query C: exactly what worked in File 8a
run("C — phenotypeHPO + phenotypeEFO (the File 8a query)", """
query DiseasePhenotypeRows($efoId: String!) {
  disease(efoId: $efoId) {
    id
    name
    phenotypes {
      count
      rows {
        phenotypeHPO { id name description }
        phenotypeEFO { id name }
      }
    }
  }
}
""")

# Query D: what the retriever currently sends
run("D — retriever's current query", """
query W02Phenotypes($efoId: String!) {
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
      }
    }
  }
}
""")

# Query E: with namespace (original retriever guess)
run("E — with namespace (original retriever guess)", """
query TE($efoId: String!) {
  disease(efoId: $efoId) {
    id
    name
    phenotypes {
      count
      rows {
        phenotypeHPO { id name description namespace }
      }
    }
  }
}
""")
