"""
CureVerseAI — Medicine domain
Evidence integrator.

Retrieves the external evidence that grounds the Medicine
functional indicators. Two responsibilities:

    1. fetch_disease_targets
           Query Open Targets for the top associated targets
           of a resolved disease. Used by the cell_state_builder
           to ground each functional indicator in the disease's
           top associated targets and the evidence categories
           that support them.

    2. fetch_pathway_metadata
           Retrieve Reactome pathway metadata for the curated
           pathway stable ids that the function_vocabulary
           attaches to each indicator. Used so the frontend can
           display a pathway by name, species, and GO process
           instead of a bare stable id.

Design constraints (from the Medicine specification):

    - Never fabricate a value. Where a source returns nothing
      or the request fails, the returned payload is empty and
      the SourceStatus records the outcome.

    - Never raise for a source failure. The workflow must be
      able to proceed with the evidence it did retrieve and
      to surface the failure in ``source_status`` so the
      frontend can distinguish "returned 0" from
      "unreachable".

    - Do not use Open Targets' numeric ``score`` as a
      scientific claim. It is an internal ranking signal.
      The evidence CATEGORIES (datatypeScores[].id, e.g.
      ``literature``, ``genetic_association``, ``clinical``,
      ``animal_model``) are what the Medicine layers use to
      label how a link was established.

    - No new external dependencies. This module uses the
      existing OpenTargetsClient and ReactomeClient.

    - No caching here. The clients decide their own caching.
      ReactomeClient caches pathway metadata; the Open
      Targets client is not cached by design in the existing
      codebase.
"""

from __future__ import annotations

from typing import Any, Dict, List, Tuple

from app.medicine.simulation import schemas as s


# ---------------------------------------------------------------------------
# Open Targets — disease -> associated targets
# ---------------------------------------------------------------------------


#: GraphQL query used to fetch the top associated targets
#: for a disease. Field names are the ones confirmed by the
#: Phase 3 diagnostic:
#:
#:     disease(efoId: ...)  — the argument is ``efoId`` even
#:                            when the value is a MONDO id.
#:     associatedTargets(page: {index, size})
#:         rows[].target.id                Ensembl gene id
#:         rows[].target.approvedSymbol    gene symbol
#:         rows[].target.approvedName      gene name
#:         rows[].score                    OT association score
#:         rows[].datatypeScores[].id      evidence category
#:         rows[].datatypeScores[].score   per-category score
_DISEASE_TARGETS_QUERY = """
query MedicineDiseaseTargets($efoId: String!, $size: Int!) {
  disease(efoId: $efoId) {
    id
    name
    description
    associatedTargets(page: {index: 0, size: $size}) {
      count
      rows {
        target { id approvedSymbol approvedName }
        score
        datatypeScores { id score }
      }
    }
  }
}
"""


def fetch_disease_targets(
    disease_ref: s.DiseaseRef,
    size: int = 20,
) -> Tuple[Dict[str, Any], s.SourceStatus]:
    """
    Fetch the top associated targets for a resolved disease.

    Returns
    -------
    payload : dict
        On success::

            {
                "disease_id":   "MONDO_0004979",
                "disease_name": "asthma",
                "count":        7772,
                "rows": [
                    {
                        "target_id":       "ENSG00000143631",
                        "approved_symbol": "FLG",
                        "approved_name":   "filaggrin",
                        "score":           0.7491...,
                        "datatype_scores": [
                            {"id": "literature",         "score": 0.4089...},
                            {"id": "genetic_association","score": 0.9785...},
                        ],
                    },
                    ...
                ],
            }

        On failure or empty resolution: ``{"rows": [], "count": 0}``
        with the disease id preserved when available.

    source_status : SourceStatus
        reachable=False and error set when the transport failed;
        reachable=True with returned_records=count otherwise.

    Never raises.
    """
    empty_payload: Dict[str, Any] = {
        "disease_id": None,
        "disease_name": disease_ref.name if disease_ref else None,
        "count": 0,
        "rows": [],
    }

    if disease_ref is None or not disease_ref.id:
        return empty_payload, s.SourceStatus(
            source="Open Targets",
            reachable=True,
            returned_records=0,
            error=None,
            metadata={"note": "no resolved disease id"},
        )

    # Lazy import — OpenTargetsClient pulls in httpx and the
    # existing graphql helper. Keep the import local so a
    # failure in the Open Targets client cannot break the
    # Medicine package import.
    try:
        from app.drug_development.sources.open_targets import (
            OpenTargetsClient,
        )
        from app.drug_development.reverse_disease.utils import (
            to_opentargets_id,
        )
    except Exception as exc:
        return empty_payload, s.SourceStatus(
            source="Open Targets",
            reachable=False,
            returned_records=0,
            error=f"import failed: {exc}",
        )

    ot_id = to_opentargets_id(disease_ref.id)
    empty_payload["disease_id"] = ot_id

    try:
        client = OpenTargetsClient()
        raw = client.query(
            _DISEASE_TARGETS_QUERY,
            {"efoId": ot_id, "size": int(size)},
        )
    except Exception as exc:
        return empty_payload, s.SourceStatus(
            source="Open Targets",
            reachable=False,
            returned_records=0,
            error=str(exc),
        )

    disease_block = (raw or {}).get("disease") or {}

    if not disease_block:
        # OT answered but did not return a disease block.
        # This is not a transport failure: reachable=True,
        # records=0.
        return empty_payload, s.SourceStatus(
            source="Open Targets",
            reachable=True,
            returned_records=0,
            error=None,
            metadata={"note": "no disease block in response"},
        )

    at = disease_block.get("associatedTargets") or {}
    raw_rows = at.get("rows") or []
    count = int(at.get("count") or len(raw_rows))

    rows: List[Dict[str, Any]] = []
    for row in raw_rows:
        if not isinstance(row, dict):
            continue

        target = row.get("target") or {}
        target_id = target.get("id")
        symbol = target.get("approvedSymbol")
        if not target_id or not symbol:
            continue

        dt_scores = []
        for d in row.get("datatypeScores") or []:
            if isinstance(d, dict) and d.get("id"):
                dt_scores.append({
                    "id": d.get("id"),
                    "score": d.get("score"),
                })

        rows.append({
            "target_id": target_id,
            "approved_symbol": symbol,
            "approved_name": target.get("approvedName"),
            "score": row.get("score"),
            "datatype_scores": dt_scores,
        })

    payload = {
        "disease_id": disease_block.get("id") or ot_id,
        "disease_name": (
            disease_block.get("name") or disease_ref.name
        ),
        "count": count,
        "rows": rows,
    }

    return payload, s.SourceStatus(
        source="Open Targets",
        reachable=True,
        returned_records=len(rows),
        error=None,
        metadata={"total_available": count},
    )


# ---------------------------------------------------------------------------
# Reactome — pathway metadata by stable id
# ---------------------------------------------------------------------------


def fetch_pathway_metadata(
    st_ids: List[str],
) -> Tuple[Dict[str, Dict[str, Any]], s.SourceStatus]:
    """
    Fetch Reactome pathway metadata for a list of stable ids.

    Returns
    -------
    payload : dict
        Mapping ``st_id -> pathway_metadata`` for every id
        that resolved to a real pathway. Ids that 404 or that
        failed to fetch are simply absent from the mapping.

    source_status : SourceStatus
        reachable=True when at least one fetch completed
        (with or without data). reachable=False only when
        every fetch raised a transport error.

    Never raises.

    The metadata for each id is exactly what
    ``ReactomeClient.get_pathway_by_id`` returns: display
    name, species, GO process, cross references, literature
    count, review status, release dates.
    """
    clean_ids: List[str] = []
    seen = set()
    for raw in st_ids or []:
        sid = (raw or "").strip()
        if sid and sid not in seen:
            seen.add(sid)
            clean_ids.append(sid)

    if not clean_ids:
        return {}, s.SourceStatus(
            source="Reactome",
            reachable=True,
            returned_records=0,
            error=None,
            metadata={"note": "no stable ids requested"},
        )

    try:
        from app.data.sources.reactome import ReactomeClient
    except Exception as exc:
        return {}, s.SourceStatus(
            source="Reactome",
            reachable=False,
            returned_records=0,
            error=f"import failed: {exc}",
        )

    try:
        client = ReactomeClient()
    except Exception as exc:
        return {}, s.SourceStatus(
            source="Reactome",
            reachable=False,
            returned_records=0,
            error=f"client init failed: {exc}",
        )

    found: Dict[str, Dict[str, Any]] = {}
    errors: List[str] = []
    success_count = 0

    for st_id in clean_ids:
        try:
            result = client.get_pathway_by_id(st_id)
        except Exception as exc:
            errors.append(f"{st_id}: {exc}")
            continue

        success_count += 1

        if isinstance(result, dict) and result.get("found"):
            found[st_id] = result

    reachable = success_count > 0
    error_msg = "; ".join(errors) if errors and not reachable else None

    return found, s.SourceStatus(
        source="Reactome",
        reachable=reachable,
        returned_records=len(found),
        error=error_msg,
        metadata={
            "requested": len(clean_ids),
            "resolved": len(found),
            "per_id_errors": errors if errors else [],
        },
    )


# ---------------------------------------------------------------------------
# Evidence-category helpers
# ---------------------------------------------------------------------------


#: Open Targets datatype ids that Medicine recognises as
#: distinct evidence categories. The id strings come directly
#: from Open Targets and are the ones the frontend will show.
OT_DATATYPE_LABELS: Dict[str, str] = {
    "literature": "Literature",
    "genetic_association": "Genetic association",
    "somatic_mutation": "Somatic mutation",
    "known_drug": "Known drug",
    "affected_pathway": "Affected pathway",
    "animal_model": "Animal model",
    "rna_expression": "RNA expression",
    "clinical": "Clinical",
    "expression_atlas": "Expression atlas",
}


def summarise_datatype_scores(
    rows: List[Dict[str, Any]],
) -> Dict[str, int]:
    """
    Return counts of how many rows in ``rows`` carry each
    Open Targets datatype category.

    This is a CATEGORY count, never a score. It lets the
    frontend say "12 targets have genetic association
    evidence" without ever showing a numeric confidence.

    Rows without datatype_scores are counted under the empty
    string key and are excluded from the summary.
    """
    counts: Dict[str, int] = {}

    for row in rows or []:
        for dt in row.get("datatype_scores") or []:
            key = (dt.get("id") or "").strip()
            if not key:
                continue
            counts[key] = counts.get(key, 0) + 1

    return counts
