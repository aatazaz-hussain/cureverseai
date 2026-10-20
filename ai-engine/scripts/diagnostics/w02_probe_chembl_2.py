"""
W02 Phase 1 — ChEMBL follow-up (read-only).

Probes a target that HAS activities in ChEMBL so we
see the populated shape of:
    - get_activities()
    - get_validated_activities()
    - get_bioactivity_evidence()
    - get_target_evidence_bundle()

ADORA1 (adenosine A1 receptor) — GPCR, asthma-associated
in Open Targets, reviewed UniProt P30542, rich small-
molecule ChEMBL activity history.
"""

import json
import sys
from pathlib import Path

AI_ENGINE_ROOT = Path("/home/aatazazhussain/projects/cureverseai/ai-engine")
sys.path.insert(0, str(AI_ENGINE_ROOT))

from app.drug_development.sources.chembl import ChEMBLClient  # noqa: E402
from app.drug_development.sources.chembl_evidence import (  # noqa: E402
    ChEMBLEvidenceService,
)


SEP = "=" * 78


def section(title):
    print()
    print(SEP)
    print(title)
    print(SEP)


def safe(label, fn, *args, **kwargs):
    print(f"\n--- {label} ---")
    try:
        result = fn(*args, **kwargs)
    except Exception as exc:
        print(f"FAILED: {type(exc).__name__}: {exc}")
        return None
    print(json.dumps(result, indent=2, default=str)[:8000])
    return result


def main():
    gene_symbol = "ADORA1"
    uniprot_id = "P30542"
    preferred_name = "Adenosine receptor A1"

    with ChEMBLClient() as client:
        # ------------------------------------------------------------------
        # 1) Validated target resolution
        # ------------------------------------------------------------------
        section(f"1) find_human_protein_target for {gene_symbol}")
        target = safe(
            (
                f"find_human_protein_target(gene_symbol='{gene_symbol}', "
                f"required_uniprot='{uniprot_id}', "
                f"preferred_name='{preferred_name}')"
            ),
            client.find_human_protein_target,
            gene_symbol=gene_symbol,
            required_uniprot=uniprot_id,
            preferred_name=preferred_name,
        )

        if not target:
            print("\nCannot continue.")
            return

        target_chembl_id = target.get("target_chembl_id")
        print(f"\nResolved target_chembl_id = {target_chembl_id}")

        # ------------------------------------------------------------------
        # 2) Raw activity (no filter) — see shape
        # ------------------------------------------------------------------
        section("2) get_activities — raw, first 3 records, unfiltered")
        raw = safe(
            f"get_activities(target_chembl_id='{target_chembl_id}', limit=3)",
            client.get_activities,
            target_chembl_id=target_chembl_id,
            limit=3,
        )
        if raw:
            print(
                f"\nTotal count reported by server: "
                f"{(raw.get('page_meta') or {}).get('total_count')}"
            )

        # ------------------------------------------------------------------
        # 3) Filtered activity (standard types)
        # ------------------------------------------------------------------
        section("3) get_activities — filtered (IC50/EC50/Ki/Kd/AC50), 3 records")
        filtered = safe(
            (
                f"get_activities(target_chembl_id='{target_chembl_id}', "
                f"standard_types=['IC50','EC50','Ki','Kd','AC50'], limit=3)"
            ),
            client.get_activities,
            target_chembl_id=target_chembl_id,
            standard_types=["IC50", "EC50", "Ki", "Kd", "AC50"],
            limit=3,
        )
        if filtered:
            print(
                f"\nTotal count reported by server: "
                f"{(filtered.get('page_meta') or {}).get('total_count')}"
            )

        # ------------------------------------------------------------------
        # 4) Validated activities (normalized) — 3 records
        # ------------------------------------------------------------------
        section("4) get_validated_activities — 3 records")
        validated = safe(
            (
                f"get_validated_activities(target_chembl_id='{target_chembl_id}', "
                f"target_name='{preferred_name}', limit=3)"
            ),
            client.get_validated_activities,
            target_chembl_id=target_chembl_id,
            target_name=preferred_name,
            limit=3,
        )
        if validated is not None:
            print(f"\nvalidated count: {len(validated)}")

    # ------------------------------------------------------------------
    # 5) Full evidence bundle
    # ------------------------------------------------------------------
    section("5) ChEMBLEvidenceService.get_target_evidence_bundle")
    with ChEMBLEvidenceService() as service:
        bundle = safe(
            (
                f"get_target_evidence_bundle(gene_symbol='{gene_symbol}', "
                f"uniprot_id='{uniprot_id}', preferred_name='{preferred_name}', "
                f"limit=5)"
            ),
            service.get_target_evidence_bundle,
            gene_symbol=gene_symbol,
            uniprot_id=uniprot_id,
            preferred_name=preferred_name,
            limit=5,
        )

        if bundle is not None:
            section("5a) bundle.summary()")
            try:
                print(json.dumps(bundle.summary(), indent=2, default=str))
            except Exception as exc:
                print(f"FAILED: {type(exc).__name__}: {exc}")

            section("5b) bundle.provenance")
            try:
                print(json.dumps(bundle.provenance, indent=2, default=str))
            except Exception as exc:
                print(f"FAILED: {type(exc).__name__}: {exc}")

            section("5c) First compound (if any)")
            try:
                if bundle.compounds:
                    first = bundle.compounds[0]
                    print(json.dumps(
                        {
                            "compound_id": getattr(first, "compound_id", None),
                            "name": getattr(first, "name", None),
                            "smiles": (getattr(first, "smiles", None) or "")[:80] + "...",
                            "source": getattr(first, "source", None),
                            "evidence_type": getattr(first, "evidence_type", None),
                            "identifiers": getattr(first, "identifiers", None),
                        },
                        indent=2, default=str,
                    ))
                else:
                    print("no compounds")
            except Exception as exc:
                print(f"FAILED: {type(exc).__name__}: {exc}")

            section("5d) First relationship (if any)")
            try:
                if bundle.relationships:
                    first = bundle.relationships[0]
                    print(json.dumps(
                        {
                            "target": getattr(first, "target", None),
                            "compound": getattr(first, "compound", None),
                            "relationship_type": getattr(first, "relationship_type", None),
                            "evidence_level": getattr(first, "evidence_level", None),
                            "description": getattr(first, "description", None),
                            "identifiers": getattr(first, "identifiers", None),
                            "metadata": getattr(first, "metadata", None),
                        },
                        indent=2, default=str,
                    )[:6000])
                else:
                    print("no relationships")
            except Exception as exc:
                print(f"FAILED: {type(exc).__name__}: {exc}")

    print()
    print(SEP)
    print("DONE — ChEMBL follow-up complete.")
    print(SEP)


if __name__ == "__main__":
    main()
