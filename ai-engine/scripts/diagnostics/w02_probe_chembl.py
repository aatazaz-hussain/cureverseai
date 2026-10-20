"""
W02 Phase 1 — ChEMBL diagnostic (read-only).

Probes the existing ChEMBL client surface for the
gene -> target -> compound -> bioactivity flow that
Workflow 02 will attach as supporting experimental
evidence for a mechanism.

Uses the existing clients:
    - app.drug_development.sources.chembl.ChEMBLClient
    - app.drug_development.sources.chembl_evidence.ChEMBLEvidenceService

Writes nothing. Modifies nothing.
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
    # IL4R is a real asthma-associated gene from the Open Targets probe.
    # The UniProt accession for reviewed human IL4R is P24394.
    # The preferred protein name is "Interleukin-4 receptor subunit alpha".
    gene_symbol = "IL4R"
    uniprot_id = "P24394"
    preferred_name = "Interleukin-4 receptor subunit alpha"

    # ------------------------------------------------------------------
    # 1) Raw target search
    # ------------------------------------------------------------------
    section(f"1) ChEMBLClient.search_targets(query='{gene_symbol}')")
    with ChEMBLClient() as client:
        raw_search = safe(
            f"search_targets(query='{gene_symbol}', limit=10)",
            client.search_targets,
            query=gene_symbol,
            limit=10,
        )

        if not raw_search:
            print("\nCannot continue — target search failed.")
            return

        # ------------------------------------------------------------------
        # 2) find_human_protein_target with validation
        # ------------------------------------------------------------------
        section("2) ChEMBLClient.find_human_protein_target — validated resolution")
        resolved_target = safe(
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

        if not resolved_target:
            print("\nCannot continue — validated target resolution failed.")
            return

        target_chembl_id = resolved_target.get("target_chembl_id")
        print(f"\nResolved target_chembl_id = {target_chembl_id}")

        # ------------------------------------------------------------------
        # 3) Raw activity probe (no standard_types filter)
        # ------------------------------------------------------------------
        section("3) ChEMBLClient.get_activities — raw (limit=5, no filter)")
        raw_activities = safe(
            f"get_activities(target_chembl_id='{target_chembl_id}', limit=5)",
            client.get_activities,
            target_chembl_id=target_chembl_id,
            limit=5,
        )

        # ------------------------------------------------------------------
        # 4) Filtered activity probe (standard_types only)
        # ------------------------------------------------------------------
        section(
            "4) ChEMBLClient.get_activities — filtered "
            "(IC50/EC50/Ki/Kd/AC50, limit=5)"
        )
        filtered_activities = safe(
            (
                f"get_activities(target_chembl_id='{target_chembl_id}', "
                f"standard_types=['IC50','EC50','Ki','Kd','AC50'], limit=5)"
            ),
            client.get_activities,
            target_chembl_id=target_chembl_id,
            standard_types=["IC50", "EC50", "Ki", "Kd", "AC50"],
            limit=5,
        )

        # ------------------------------------------------------------------
        # 5) get_validated_activities — full validation + normalization
        # ------------------------------------------------------------------
        section("5) ChEMBLClient.get_validated_activities (limit=3)")
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

    # ------------------------------------------------------------------
    # 6) ChEMBLEvidenceService.get_target_evidence_bundle — the wrapper
    # ------------------------------------------------------------------
    section("6) ChEMBLEvidenceService.get_target_evidence_bundle")
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
            section("6a) bundle.summary()")
            try:
                summary = bundle.summary()
                print(json.dumps(summary, indent=2, default=str)[:4000])
            except Exception as exc:
                print(f"FAILED: {type(exc).__name__}: {exc}")

            section("6b) bundle.provenance")
            try:
                print(
                    json.dumps(
                        bundle.provenance,
                        indent=2,
                        default=str,
                    )[:4000]
                )
            except Exception as exc:
                print(f"FAILED: {type(exc).__name__}: {exc}")

            section("6c) ChEMBLEvidenceService.summarize(bundle)")
            try:
                summary2 = ChEMBLEvidenceService.summarize(bundle)
                print(json.dumps(summary2, indent=2, default=str)[:4000])
            except Exception as exc:
                print(f"FAILED: {type(exc).__name__}: {exc}")

    print()
    print(SEP)
    print("DONE — ChEMBL diagnostic complete.")
    print(SEP)


if __name__ == "__main__":
    main()
