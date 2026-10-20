"""
CureVerseAI — Drug Development
Workflow 03 — Therapeutic Discovery
Compound Discovery.

Given the target list from target_discovery.py, query
ChEMBL for candidate compounds and their experimental
activity records.

Algorithm
---------

For each target that can be resolved to a ChEMBL target
ID:

    1. Resolve the target to a ChEMBL ID (via UniProt when
       available, via gene symbol as fallback).
    2. Fetch bioactivity evidence via ChEMBLEvidenceService
       (already wired, cache-friendly, validated).
    3. Filter activities to assay types B (binding) and F
       (functional). ADME (A) and toxicity (T) records are
       excluded — they are not direct measures against the
       target.
    4. Cap the number of compounds per target at
       _MAX_COMPOUNDS_PER_TARGET.
    5. Convert ChEMBL's EvidenceBundle into the W03 typed
       containers (CandidateCompound, ActivityRecord).

Parallelism
-----------

Targets are queried with an 8-worker pool. This is the
single biggest speed lever in W03 — ChEMBL returns
activity data slowly on cold cache.

What this module does NOT do
----------------------------

    - It does not rank compounds by potency. Measured
      activity is preserved as raw values in ActivityRecord.
    - It does not invent compounds when ChEMBL returns
      none. A target with no compounds is recorded in
      provenance and skipped.
    - It does not filter by "good" activity values. Even a
      single qualitative record is preserved.

Data provenance
---------------

Every compound retains its ChEMBL identifier. Every
activity retains its assay identifier, publication
reference, and standard metadata. Values are stored as
strings to preserve exact source form.
"""

from __future__ import annotations

from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed,
)
from typing import Any, Dict, List, Optional, Set

from app.drug_development.sources.chembl import ChEMBLClient
from app.drug_development.sources.chembl_evidence import (
    ChEMBLEvidenceService,
)
from app.drug_development.therapeutic_discovery.schemas import (
    ActivityRecord,
    CandidateCompound,
    TargetSummary,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


SOURCE_CHEMBL = "ChEMBL"

#: ChEMBL assay types to keep. B = binding, F = functional.
#: ADME (A) and toxicity (T) are excluded.
_ALLOWED_ASSAY_TYPES = {"B", "F"}

#: ChEMBL activity type filter. These are the standard
#: measures. Records without a standard_type are also kept
#: if they have a text value.
_STANDARD_TYPES = ["IC50", "EC50", "Ki", "Kd", "AC50"]

#: Cap per target.
_MAX_COMPOUNDS_PER_TARGET = 25

#: Cap across the whole run.
_MAX_TOTAL_COMPOUNDS = 200

#: Parallel workers.
_MAX_WORKERS = 8


# ---------------------------------------------------------------------------
# Compound Discovery
# ---------------------------------------------------------------------------


class CompoundDiscovery:
    """
    Retrieve candidate compounds and their activity records
    from ChEMBL.
    """

    def __init__(
        self,
        chembl_client: Optional[ChEMBLClient] = None,
        chembl_service: Optional[ChEMBLEvidenceService] = None,
    ):
        self._client = chembl_client
        self._service = chembl_service

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def discover(
        self,
        targets: List[TargetSummary],
    ) -> Dict[str, Any]:
        """
        Retrieve compounds for each target.

        Never raises for a target that returns no compounds
        or cannot be resolved. RuntimeError from ChEMBL
        transport propagates only when it affects every
        target (unlikely); otherwise per-target failures are
        absorbed and recorded in metadata.targets_skipped.
        """

        if not targets:
            return self._empty(
                reason="No targets were supplied."
            )

        # Parallel per-target query.
        per_target = self._query_targets_parallel(targets)

        # Persist resolved ChEMBL target IDs back onto the
        # TargetSummary objects so downstream modules
        # (moa_builder, therapeutic_graph) can match
        # activities to targets.
        for target, result in zip(targets, per_target):
            if (
                result is not None
                and result.get("chembl_target_id")
                and not target.chembl_target_id
            ):
                target.chembl_target_id = result[
                    "chembl_target_id"
                ]

        # Aggregate.
        candidates_by_id: Dict[str, CandidateCompound] = {}
        activities: List[ActivityRecord] = []
        by_target: Dict[str, List[str]] = {}

        targets_with_chembl_id = 0
        targets_with_compounds = 0
        targets_without_compounds = 0
        targets_skipped: List[Dict[str, Any]] = []

        for target, result in zip(targets, per_target):
            if result is None:
                targets_skipped.append(
                    {
                        "target_id": target.target_id,
                        "reason": "unresolved",
                    }
                )
                continue

            if not result.get("chembl_target_id"):
                targets_skipped.append(
                    {
                        "target_id": target.target_id,
                        "reason": "no_chembl_target",
                    }
                )
                continue

            targets_with_chembl_id += 1

            if not result["compounds"]:
                targets_without_compounds += 1
                by_target[target.target_id] = []
                continue

            targets_with_compounds += 1

            target_compound_ids: List[str] = []

            for compound in result["compounds"]:
                cid = compound.compound_id
                if cid not in candidates_by_id:
                    candidates_by_id[cid] = compound
                if cid not in target_compound_ids:
                    target_compound_ids.append(cid)

            by_target[target.target_id] = target_compound_ids

            for activity in result["activities"]:
                activities.append(activity)

            # Cap total.
            if len(candidates_by_id) >= _MAX_TOTAL_COMPOUNDS:
                break

        candidates = list(candidates_by_id.values())[
            :_MAX_TOTAL_COMPOUNDS
        ]

        if not candidates:
            return {
                "found": False,
                "candidates": [],
                "activities": [],
                "by_target": by_target,
                "sources_queried": [SOURCE_CHEMBL],
                "reason": (
                    "ChEMBL returned no compounds for any of "
                    "the supplied targets."
                ),
                "metadata": {
                    "targets_queried": len(targets),
                    "targets_with_chembl_id": (
                        targets_with_chembl_id
                    ),
                    "targets_with_compounds": 0,
                    "targets_without_compounds": (
                        targets_without_compounds
                    ),
                    "total_compounds": 0,
                    "total_activities": 0,
                    "targets_skipped": targets_skipped,
                },
            }

        # Activity type breakdown.
        type_counts: Dict[str, int] = {}
        for a in activities:
            key = a.standard_type or a.evidence_level
            type_counts[key] = type_counts.get(key, 0) + 1

        return {
            "found": True,
            "candidates": candidates,
            "activities": activities,
            "by_target": by_target,
            "sources_queried": [SOURCE_CHEMBL],
            "reason": None,
            "metadata": {
                "targets_queried": len(targets),
                "targets_with_chembl_id": (
                    targets_with_chembl_id
                ),
                "targets_with_compounds": (
                    targets_with_compounds
                ),
                "targets_without_compounds": (
                    targets_without_compounds
                ),
                "total_compounds": len(candidates),
                "total_activities": len(activities),
                "activity_types": type_counts,
                "targets_skipped": targets_skipped,
            },
        }

    # ------------------------------------------------------------------
    # Parallel dispatch
    # ------------------------------------------------------------------

    def _query_targets_parallel(
        self,
        targets: List[TargetSummary],
    ) -> List[Optional[Dict[str, Any]]]:
        results: List[Optional[Dict[str, Any]]] = (
            [None] * len(targets)
        )

        with ThreadPoolExecutor(
            max_workers=_MAX_WORKERS
        ) as pool:
            futures = {
                pool.submit(self._query_one_target, t): i
                for i, t in enumerate(targets)
            }

            for future in as_completed(futures):
                i = futures[future]
                try:
                    results[i] = future.result()
                except Exception:
                    results[i] = None

        return results

    def _query_one_target(
        self,
        target: TargetSummary,
    ) -> Optional[Dict[str, Any]]:
        """
        Resolve a ChEMBL target and fetch its compounds.

        Returns None when the target cannot be resolved.
        Returns a dict with `chembl_target_id` and empty
        `compounds` / `activities` when ChEMBL has no data.
        """

        client = self._get_client()
        service = self._get_service()

        # ---- 1) Resolve to ChEMBL target ------------------
        chembl_target_id: Optional[str] = None

        if target.chembl_target_id:
            chembl_target_id = target.chembl_target_id
        else:
            symbol = target.gene_symbol or target.label
            if not symbol:
                return None

            try:
                resolved = client.find_human_protein_target(
                    gene_symbol=symbol,
                    required_uniprot=target.uniprot_id,
                    preferred_name=None,
                )
                chembl_target_id = resolved.get(
                    "target_chembl_id"
                )
            except LookupError:
                return None
            except Exception:
                return None

        if not chembl_target_id:
            return None

        # ---- 2) Fetch bioactivity -------------------------
        try:
            bundle = service.get_bioactivity_evidence(
                target_chembl_id=chembl_target_id,
                target_name=target.label,
                limit=200,
                standard_types=_STANDARD_TYPES,
            )
        except Exception:
            return {
                "chembl_target_id": chembl_target_id,
                "compounds": [],
                "activities": [],
            }

        # ---- 3) Filter and convert ------------------------
        compounds_out: List[CandidateCompound] = []
        activities_out: List[ActivityRecord] = []

        seen_compound_ids: Set[str] = set()

        for rel in bundle.relationships:
            meta = rel.metadata or {}
            assay = meta.get("assay") or {}
            measurement = meta.get("measurement") or {}

            assay_type = assay.get("type")
            if assay_type not in _ALLOWED_ASSAY_TYPES:
                continue

            compound_id = rel.compound
            if not compound_id:
                continue

            # Compound record — first time we see it.
            if compound_id not in seen_compound_ids:
                if (
                    len(seen_compound_ids)
                    >= _MAX_COMPOUNDS_PER_TARGET
                ):
                    continue

                compounds_out.append(
                    CandidateCompound(
                        compound_id=str(compound_id),
                        source=SOURCE_CHEMBL,
                        name=meta.get("compound_name"),
                        parent_chembl_id=None,
                        canonical_smiles=meta.get(
                            "canonical_smiles"
                        ),
                        identifiers={
                            "chembl_compound_id": str(
                                compound_id
                            ),
                        },
                        metadata={
                            "target_chembl_id": (
                                chembl_target_id
                            ),
                        },
                    )
                )
                seen_compound_ids.add(compound_id)

            # Activity record.
            pub = meta.get("publication") or {}

            try:
                year_value = pub.get("year")
                year = (
                    int(year_value)
                    if year_value is not None
                    else None
                )
            except (TypeError, ValueError):
                year = None

            activities_out.append(
                ActivityRecord(
                    activity_id=str(
                        rel.identifiers.get(
                            "chembl_activity_id", ""
                        )
                    ),
                    target_chembl_id=chembl_target_id,
                    compound_chembl_id=str(compound_id),
                    evidence_level=str(
                        rel.evidence_level
                        or "observational"
                    ),
                    standard_type=measurement.get(
                        "standard_type"
                    ),
                    standard_value=measurement.get(
                        "standard_value"
                    ),
                    standard_units=measurement.get(
                        "standard_units"
                    ),
                    standard_relation=measurement.get(
                        "standard_relation"
                    ),
                    standard_text_value=measurement.get(
                        "standard_text_value"
                    ),
                    pchembl_value=measurement.get(
                        "pchembl_value"
                    ),
                    assay_id=str(
                        rel.identifiers.get(
                            "chembl_assay_id", ""
                        )
                    )
                    or None,
                    assay_type=assay_type,
                    assay_description=assay.get(
                        "description"
                    ),
                    publication_year=year,
                    publication_journal=pub.get("journal"),
                    source=SOURCE_CHEMBL,
                    source_record_id=rel.identifiers.get(
                        "chembl_record_id"
                    ),
                    metadata={
                        "target_label": target.label,
                        "target_id": target.target_id,
                    },
                )
            )

        return {
            "chembl_target_id": chembl_target_id,
            "compounds": compounds_out,
            "activities": activities_out,
        }

    # ------------------------------------------------------------------
    # Lazy service construction
    # ------------------------------------------------------------------

    def _get_client(self) -> ChEMBLClient:
        if self._client is None:
            self._client = ChEMBLClient()
        return self._client

    def _get_service(self) -> ChEMBLEvidenceService:
        if self._service is None:
            self._service = ChEMBLEvidenceService(
                client=self._get_client()
            )
        return self._service

    # ------------------------------------------------------------------
    # Empty path
    # ------------------------------------------------------------------

    @staticmethod
    def _empty(reason: str) -> Dict[str, Any]:
        return {
            "found": False,
            "candidates": [],
            "activities": [],
            "by_target": {},
            "sources_queried": [SOURCE_CHEMBL],
            "reason": reason,
            "metadata": {},
        }


# ---------------------------------------------------------------------------
# Convenience
# ---------------------------------------------------------------------------


def discover_compounds(
    targets: List[TargetSummary],
) -> Dict[str, Any]:
    """
    One-shot entry point.
    """
    return CompoundDiscovery().discover(targets)
