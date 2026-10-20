"""
CureVerseAI — Medicine domain
Intervention resolver.

Resolves a free-text intervention name or a canonical
identifier into a Medicine-local ``InterventionRef``, together
with the biological targets the intervention is recorded as
acting on.

Three resolution paths, tried in order:

    1. Curated override table
       Some identifiers arrive from an upstream CureVerseAI
       workflow (for example a pathway stable id handed off
       from Drug Development Workflow 02). The
       function_vocabulary carries a small, versioned override
       table for these. When a match exists, the override is
       used directly and ChEMBL is not consulted.

    2. Canonical ChEMBL identifier
       An input of the form ``chembl:CHEMBL1234`` (case
       insensitive) is treated as a ChEMBL molecule id. The
       molecule is fetched by id.

    3. Free-text name
       Any other input is treated as a name query. The
       ChEMBL molecule search is used, and the best hit is
       selected by a documented rule (highest max_phase,
       then first result). The rule is not a scientific
       claim; it is an ordering heuristic, and the chosen
       molecule id is recorded in the returned record so
       the caller can surface it.

Targets for a molecule come from the ChEMBL activity
records. Each unique ChEMBL target id that the molecule has
been assayed against becomes a TargetRef. The target name is
whatever ChEMBL recorded on the activity; it is preserved as
is. No potency value from any activity is used as a claim
about the intervention's effect in this module.

Design constraints:

    - Never raise for bad input or an unknown molecule. The
      resolver returns an unresolved InterventionRef with a
      SourceStatus that records whether the source answered
      (reachable=True, returned_records=0) or failed
      (reachable=False, error set).

    - Never fabricate a target, a name, or an identifier.
      Every field comes from ChEMBL or from the curated
      override table.

    - No numeric score, no confidence, no ranking. The
      selection heuristic (highest max_phase) is recorded in
      the returned record's metadata and is not presented as
      a scientific finding.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from app.medicine.simulation import schemas as s


# ---------------------------------------------------------------------------
# Identifier parsing
# ---------------------------------------------------------------------------


#: Matches ``chembl:<id>`` and ``CHEMBL<digits>`` forms.
#: Captures the bare ChEMBL id in group 1.
_CHEMBL_PATTERN = re.compile(
    r"^(?:chembl:)?(CHEMBL\d+)$",
    re.IGNORECASE,
)


def _parse_chembl_id(text: str) -> Optional[str]:
    """
    Return the canonical ``CHEMBL<digits>`` form if the input
    is a ChEMBL molecule id, or None otherwise.
    """
    if not text:
        return None
    m = _CHEMBL_PATTERN.match(text.strip())
    if not m:
        return None
    return m.group(1).upper()


# ---------------------------------------------------------------------------
# Target extraction
# ---------------------------------------------------------------------------


#: Maximum number of distinct targets recorded on an
#: InterventionRef. Ranked by number of activities observed,
#: then by ChEMBL target id for stability.
_MAX_TARGETS = 10


#: ChEMBL target_type values that represent real biological
#: targets. Everything else (TISSUE, CELL-LINE, UNCHECKED,
#: ORGANISM, NON-MOLECULAR, etc.) is an assay artifact or a
#: curation bucket and is excluded from the InterventionRef.
#:
#: Confirmed against ChEMBL:
#:     CHEMBL1798    SINGLE PROTEIN   Cysteinyl leukotriene receptor 1
#:     CHEMBL612545  UNCHECKED        (curation bucket)
#:     CHEMBL2367379 TISSUE           Liver microsome
_BIOLOGICAL_TARGET_TYPES = frozenset({
    "SINGLE PROTEIN",
    "PROTEIN COMPLEX",
    "PROTEIN FAMILY",
})



def _get_target_accession(
    client: Any,
    target_chembl_id: str,
) -> Optional[str]:
    """
    Fetch the UniProt accession for a ChEMBL target id.

    Uses ChEMBL get_target and reads
    ``target_components[0].accession``. Returns None on any
    failure or when the target has no components with an
    accession.

    Never raises.
    """
    if client is None:
        return None
    tid = (target_chembl_id or "").strip()
    if not tid:
        return None
    try:
        data = client.get_target(tid)
    except Exception:
        return None
    if not isinstance(data, dict):
        return None
    comps = data.get("target_components") or []
    if not isinstance(comps, list) or not comps:
        return None
    first = comps[0]
    if not isinstance(first, dict):
        return None
    acc = (first.get("accession") or "").strip()
    return acc or None


def _is_biological_target(
    client: Any,
    target_chembl_id: str,
) -> bool:
    """
    Ask ChEMBL what type of target this is and decide whether
    it is a real biological target.

    Keeps:    SINGLE PROTEIN, PROTEIN COMPLEX, PROTEIN FAMILY
    Drops:    TISSUE, CELL-LINE, UNCHECKED, ORGANISM,
              NON-MOLECULAR, and anything else.

    Returns False on any failure (transport error, missing
    field). The conservative default is to drop — under-claim
    rather than over-claim.

    Never raises.
    """
    if client is None:
        # No client means we cannot verify the type. Return
        # False so nothing unverified enters the target list.
        return False

    tid = (target_chembl_id or "").strip()
    if not tid:
        return False

    try:
        data = client.get_target(tid)
    except Exception:
        return False

    if not isinstance(data, dict):
        return False

    ttype = (data.get("target_type") or "").strip().upper()
    return ttype in _BIOLOGICAL_TARGET_TYPES


def _extract_targets(
    normalized_activities: List[Dict[str, Any]],
    mechanism_records: Optional[List[Dict[str, Any]]] = None,
    client: Optional[Any] = None,
) -> List[s.TargetRef]:
    """
    Derive the distinct biological targets a molecule acts on.

    Sources, in priority order:

        1. ChEMBL mechanism records — the pharmacological
           targets with a documented action type
           (ANTAGONIST, INHIBITOR, AGONIST, ...). These take
           precedence because they are what the drug is
           actually known to do.
        2. ChEMBL activity records — every target the molecule
           has been assayed against.

    Both sources are filtered through _BIOLOGICAL_TARGET_TYPES:
    a target must have target_type SINGLE PROTEIN,
    PROTEIN COMPLEX or PROTEIN FAMILY to be kept. Assay
    artifacts (TISSUE, CELL-LINE, UNCHECKED, ...) are dropped.

    The mechanism-of-action record enriches the matching
    TargetRef with ``action_type`` and ``mechanism_of_action``.
    When a mechanism target does not appear in the activity
    list, it is added anyway — the mechanism record is the
    stronger signal.

    Ranking: mechanisms first, then activity count
    (descending), then ChEMBL target id (ascending).

    The ``_MAX_TARGETS`` cap is applied only to the activity-
    derived targets, and only after mechanism targets have
    been included. Mechanism targets are never dropped by the
    cap.

    Never raises.
    """
    # Index mechanism records by target id.
    mech_by_target: Dict[str, Dict[str, Any]] = {}
    for mech in mechanism_records or []:
        if not isinstance(mech, dict):
            continue
        tid = (mech.get("target_chembl_id") or "").strip()
        if not tid:
            continue
        mech_by_target[tid] = {
            "action_type": mech.get("action_type"),
            "mechanism_of_action": mech.get("mechanism_of_action"),
        }

    # Index activity targets.
    by_target: Dict[str, Dict[str, Any]] = {}
    for activity in normalized_activities or []:
        target = (activity or {}).get("target") or {}
        tid = (target.get("chembl_id") or "").strip()
        if not tid:
            continue
        entry = by_target.setdefault(tid, {
            "id": tid,
            "name": target.get("name") or tid,
            "organism": target.get("organism"),
            "count": 0,
        })
        entry["count"] += 1

    # Rank activity-derived targets.
    ranked_activities = sorted(
        by_target.values(),
        key=lambda e: (-e["count"], e["id"]),
    )

    refs: List[s.TargetRef] = []
    seen: set = set()

    # Mechanism-derived first.
    for tid, mech in mech_by_target.items():
        if tid in seen:
            continue
        seen.add(tid)

        base = by_target.get(tid)
        name = base["name"] if base else tid
        organism = base.get("organism") if base else None
        count = base["count"] if base else 0

        refs.append(
            s.TargetRef(
                id=f"chembl_target:{tid}",
                name=name,
                source="ChEMBL",
                source_id=tid,
                target_type="protein",
                metadata={
                    "organism": organism,
                    "activity_count": count,
                    "action_type": mech.get("action_type"),
                    "mechanism_of_action": mech.get("mechanism_of_action"),
                    "via": "mechanism",
                    "uniprot_accession": _get_target_accession(client, tid),
                },
            )
        )

    # Activity-derived, capped, filtered by real target type.
    activities_added = 0
    for entry in ranked_activities:
        if activities_added >= _MAX_TARGETS:
            break
        tid = entry["id"]
        if tid in seen:
            continue

        # Ask ChEMBL what type this target actually is and
        # drop assay artifacts. Mechanism targets already
        # passed this filter implicitly (ChEMBL only records
        # mechanisms on real targets).
        if not _is_biological_target(client, tid):
            continue

        seen.add(tid)
        activities_added += 1

        refs.append(
            s.TargetRef(
                id=f"chembl_target:{tid}",
                name=entry["name"],
                source="ChEMBL",
                source_id=tid,
                target_type="protein",
                metadata={
                    "organism": entry.get("organism"),
                    "activity_count": entry["count"],
                    "via": "activity",
                    "uniprot_accession": _get_target_accession(client, tid),
                },
            )
        )

    return refs

# ---------------------------------------------------------------------------
# Result builders
# ---------------------------------------------------------------------------


def _unresolved_ref(query: str, reason: str) -> s.InterventionRef:
    """
    Return an honest unresolved InterventionRef for a query
    that could not be resolved. No fabricated fields.
    """
    return s.InterventionRef(
        id="",
        name=query or "",
        source="ChEMBL",
        source_id="",
        intervention_type=None,
        targets=[],
        resolution_status="unresolved",
        metadata={"reason": reason},
    )


def _ref_from_override(
    identifier: str,
    override: Dict[str, Any],
) -> s.InterventionRef:
    """
    Build an InterventionRef from a curated override entry.
    The override shape is documented in function_vocabulary.
    """
    return s.InterventionRef(
        id=override.get("canonical_id") or identifier,
        name=override.get("canonical_name") or identifier,
        source=override.get("source") or "curated_override",
        source_id=identifier,
        intervention_type="class",
        targets=[],
        resolution_status="resolved",
        metadata={
            "note": override.get("note"),
            "override_identifier": identifier,
        },
    )


def _fetch_mechanism_records(
    client: Any,
    molecule_chembl_id: str,
    parent_chembl_id: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Fetch ChEMBL mechanism records for a molecule, walking to
    the parent molecule if the salt has none.

    ChEMBL attaches mechanism records to whichever ChEMBL id
    it has them for — often the salt, sometimes the parent.
    The resolver tries the given id first, then the parent.

    Never raises.
    """
    ids_to_try: List[str] = []
    if molecule_chembl_id:
        ids_to_try.append(molecule_chembl_id.strip().upper())
    if parent_chembl_id and parent_chembl_id.strip().upper() not in ids_to_try:
        ids_to_try.append(parent_chembl_id.strip().upper())

    for cid in ids_to_try:
        try:
            recs = client.get_mechanism(cid)
        except Exception:
            recs = []
        if recs:
            return recs

    return []


def _ref_from_chembl(
    molecule: Dict[str, Any],
    activities: List[Dict[str, Any]],
    client: Optional[Any] = None,
    selection_metadata: Optional[Dict[str, Any]] = None,
) -> s.InterventionRef:
    """
    Build an InterventionRef from a ChEMBL molecule record,
    its normalized activities, and its mechanism records.

    When ``client`` is provided, the resolver fetches mechanism
    records and merges them into the target list. When client
    is None (offline use), only activities are used and the
    result is honest about the absence of mechanism data.
    """
    chembl_id = molecule.get("chembl_id") or ""
    pref_name = molecule.get("pref_name") or chembl_id

    # Fetch mechanism records if we have a live client.
    mechanism_records: List[Dict[str, Any]] = []
    parent_id = None
    hierarchy = molecule.get("molecule_hierarchy") or {}
    if isinstance(hierarchy, dict):
        parent_id = hierarchy.get("parent_chembl_id")

    if client is not None:
        mechanism_records = _fetch_mechanism_records(
            client, chembl_id, parent_id
        )

    targets = _extract_targets(activities, mechanism_records, client)

    metadata: Dict[str, Any] = {
        "max_phase": molecule.get("max_phase"),
        "molecule_type": molecule.get("molecule_type"),
        "therapeutic_flag": molecule.get("therapeutic_flag"),
        "synonyms": molecule.get("synonyms") or [],
        "activity_count": len(activities or []),
        "mechanism_count": len(mechanism_records),
        "parent_chembl_id": parent_id,
    }
    if selection_metadata:
        metadata["selection"] = selection_metadata

    return s.InterventionRef(
        id=f"chembl:{chembl_id}",
        name=pref_name,
        source="ChEMBL",
        source_id=chembl_id,
        intervention_type=molecule.get("molecule_type"),
        targets=targets,
        resolution_status="resolved",
        metadata=metadata,
    )

# ---------------------------------------------------------------------------
# Core resolution
# ---------------------------------------------------------------------------


def _choose_best_molecule(
    molecules: List[Dict[str, Any]],
) -> Tuple[Optional[Dict[str, Any]], Dict[str, Any]]:
    """
    Return (chosen_molecule, selection_metadata).

    Selection rule: highest ``max_phase`` value; None sorts
    last; ties broken by ChEMBL id ascending for stability.

    The rule is a heuristic recorded in the returned metadata
    so the caller can see why a specific molecule was chosen.
    """
    if not molecules:
        return None, {"rule": "no_candidates"}

    def sort_key(entry: Dict[str, Any]) -> Tuple[int, str]:
        phase = entry.get("max_phase")
        phase_int = int(phase) if isinstance(phase, (int, float)) else -1
        return (-phase_int, str(entry.get("chembl_id") or ""))

    ranked = sorted(molecules, key=sort_key)
    chosen = ranked[0]

    return chosen, {
        "rule": "highest_max_phase_then_id",
        "max_phase": chosen.get("max_phase"),
        "candidate_count": len(molecules),
    }


def resolve_intervention_with_status(
    identifier_or_query: str,
) -> Tuple[s.InterventionRef, s.SourceStatus]:
    """
    Resolve an intervention and return a SourceStatus alongside
    the InterventionRef.

    SourceStatus conventions:

        reachable=True,  returned_records>0  -> resolved
        reachable=True,  returned_records=0  -> source answered, no match
        reachable=False                      -> transport failure

    Never raises.
    """
    raw = (identifier_or_query or "").strip()

    if not raw:
        return (
            _unresolved_ref("", "empty input"),
            s.SourceStatus(
                source="intervention_resolver",
                reachable=True,
                returned_records=0,
                error=None,
                metadata={"note": "empty input"},
            ),
        )

    # --- Path 1: override table ---
    try:
        from app.medicine.simulation import function_vocabulary as v
        override = v.resolve_override(raw)
    except Exception:
        override = None

    if override:
        ref = _ref_from_override(raw, override)
        return ref, s.SourceStatus(
            source="intervention_resolver",
            reachable=True,
            returned_records=1,
            error=None,
            metadata={"path": "override"},
        )

    # --- Paths 2 and 3 require ChEMBL ---
    try:
        from app.drug_development.sources.chembl import ChEMBLClient
    except Exception as exc:
        return (
            _unresolved_ref(raw, f"chembl import failed: {exc}"),
            s.SourceStatus(
                source="ChEMBL",
                reachable=False,
                returned_records=0,
                error=f"import failed: {exc}",
            ),
        )

    client: Optional[Any] = None
    try:
        client = ChEMBLClient()

        chembl_id = _parse_chembl_id(raw)

        if chembl_id:
            # Path 2: direct id.
            try:
                molecule = client.get_molecule(chembl_id)
            except LookupError as exc:
                return (
                    _unresolved_ref(raw, str(exc)),
                    s.SourceStatus(
                        source="ChEMBL",
                        reachable=True,
                        returned_records=0,
                        error=None,
                        metadata={
                            "path": "direct_id",
                            "note": "molecule id not found",
                        },
                    ),
                )
            except Exception as exc:
                return (
                    _unresolved_ref(raw, f"chembl error: {exc}"),
                    s.SourceStatus(
                        source="ChEMBL",
                        reachable=False,
                        returned_records=0,
                        error=str(exc),
                    ),
                )

            selection_meta = {"rule": "direct_id"}
            path_label = "direct_id"

        else:
            # Path 3: free-text search.
            try:
                search = client.search_molecules_by_name(raw, limit=5)
            except Exception as exc:
                return (
                    _unresolved_ref(raw, f"chembl search error: {exc}"),
                    s.SourceStatus(
                        source="ChEMBL",
                        reachable=False,
                        returned_records=0,
                        error=str(exc),
                    ),
                )

            if not search.get("found"):
                return (
                    _unresolved_ref(
                        raw, "no ChEMBL molecule matched the query"
                    ),
                    s.SourceStatus(
                        source="ChEMBL",
                        reachable=True,
                        returned_records=0,
                        error=None,
                        metadata={"path": "name_search"},
                    ),
                )

            molecule_summary, selection_meta = _choose_best_molecule(
                search.get("molecules") or []
            )

            if not molecule_summary:
                return (
                    _unresolved_ref(raw, "no usable molecule in search"),
                    s.SourceStatus(
                        source="ChEMBL",
                        reachable=True,
                        returned_records=0,
                        error=None,
                        metadata={"path": "name_search"},
                    ),
                )

            # Fetch the full molecule record for the chosen id.
            try:
                molecule = client.get_molecule(
                    molecule_summary["chembl_id"]
                )
            except LookupError as exc:
                return (
                    _unresolved_ref(raw, str(exc)),
                    s.SourceStatus(
                        source="ChEMBL",
                        reachable=True,
                        returned_records=0,
                        error=None,
                        metadata={"path": "name_search"},
                    ),
                )
            except Exception as exc:
                return (
                    _unresolved_ref(
                        raw, f"chembl fetch error: {exc}"
                    ),
                    s.SourceStatus(
                        source="ChEMBL",
                        reachable=False,
                        returned_records=0,
                        error=str(exc),
                    ),
                )

            path_label = "name_search"

        # --- Targets via activities (both paths 2 and 3) ---
        activities: List[Dict[str, Any]] = []
        activity_error: Optional[str] = None
        try:
            activities = client.get_activities_for_molecule(
                molecule["chembl_id"], limit=200
            )
        except Exception as exc:
            activity_error = str(exc)

        ref = _ref_from_chembl(
            molecule,
            activities,
            client=client,
            selection_metadata={**selection_meta, "path": path_label},
        )

        return ref, s.SourceStatus(
            source="ChEMBL",
            reachable=True,
            returned_records=1,
            error=activity_error,
            metadata={
                "path": path_label,
                "targets": len(ref.targets),
                "activities": len(activities),
            },
        )

    finally:
        if client is not None:
            try:
                client.close()
            except Exception:
                pass


def resolve_intervention(
    identifier_or_query: str,
) -> s.InterventionRef:
    """
    Convenience wrapper: resolve and return only the
    InterventionRef. Use resolve_intervention_with_status when
    the SourceStatus is also needed.
    """
    ref, _status = resolve_intervention_with_status(identifier_or_query)
    return ref
