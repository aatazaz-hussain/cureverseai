"""
CureVerseAI — Medicine domain
Function mapper.

Derives a functional vocabulary for any resolved disease by
asking the real biomedical sources what that disease's biology
actually is.

This module exists because the earlier curated vocabulary
(``function_vocabulary.py``) supported only three diseases.
The mapper makes every disease Open Targets can resolve a
first-class citizen of the Medicine simulation.

Design constraints (locked):

    - No fabricated indicator. Every indicator carries the
      specific Reactome pathway stable ids that grounded it.

    - No fabricated direction. ``direction_of_benefit`` is
      set only where the Reactome top-level event has an
      unambiguous interpretation. Everything else defaults
      to ``qualitative_only``.

    - No numeric score. Open Targets' association ``score``
      is used only to decide which targets to sample. It is
      never copied into an indicator, a measurement, or a
      response.

    - No allowlist. Any resolved disease works. If Open
      Targets returns zero associated targets, the mapper
      returns None and records the honest fact.

The mapper's output shape matches
``function_vocabulary.get_pair`` exactly, so every module
downstream of the vocabulary keeps working unchanged.
"""

from __future__ import annotations

import re
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Tuple

from app.medicine.simulation import schemas as s


# ---------------------------------------------------------------------------
# Version
# ---------------------------------------------------------------------------


#: Version of the mapper's derivation rules. Feeds the run_id
#: computation alongside FUNCTION_MAPPER_VERSION.
MAPPER_VERSION = "med-mapper-v1"


# ---------------------------------------------------------------------------
# Reactome top-level event -> direction of benefit
# ---------------------------------------------------------------------------
#
# Every top-level Reactome event that has an unambiguous
# direction of benefit in a disease-modelling context is
# listed. Every other event defaults to ``qualitative_only``,
# which is the honest choice: we do not assert a direction we
# cannot justify.
#
# The keys are the exact top-level event display names from
# Reactome (see /data/eventsHierarchy/9606).

_DIRECTION_BY_TOP_LEVEL: Dict[str, str] = {
    # Unambiguous directions.
    "DNA Repair":            s.DirectionOfBenefit.HIGHER_BETTER,
    "DNA Replication":       s.DirectionOfBenefit.HIGHER_BETTER,
    "Protein localization":  s.DirectionOfBenefit.QUALITATIVE_ONLY,
    "Autophagy":             s.DirectionOfBenefit.QUALITATIVE_ONLY,

    # Everything else: direction is context-dependent.
    # Listed here for documentation, but all fall through to
    # qualitative_only via the default.
    "Signal Transduction":   s.DirectionOfBenefit.QUALITATIVE_ONLY,
    "Immune System":         s.DirectionOfBenefit.QUALITATIVE_ONLY,
    "Metabolism":            s.DirectionOfBenefit.QUALITATIVE_ONLY,
    "Metabolism of RNA":     s.DirectionOfBenefit.QUALITATIVE_ONLY,
    "Metabolism of proteins": s.DirectionOfBenefit.QUALITATIVE_ONLY,
    "Gene expression (Transcription)": s.DirectionOfBenefit.QUALITATIVE_ONLY,
    "Programmed Cell Death": s.DirectionOfBenefit.QUALITATIVE_ONLY,
    "Cell Cycle":            s.DirectionOfBenefit.QUALITATIVE_ONLY,
    "Cellular responses to stimuli": s.DirectionOfBenefit.QUALITATIVE_ONLY,
    "Cell-Cell communication": s.DirectionOfBenefit.QUALITATIVE_ONLY,
    "Extracellular matrix organization": s.DirectionOfBenefit.QUALITATIVE_ONLY,
    "Hemostasis":            s.DirectionOfBenefit.QUALITATIVE_ONLY,
    "Developmental Biology": s.DirectionOfBenefit.QUALITATIVE_ONLY,
    "Reproduction":          s.DirectionOfBenefit.QUALITATIVE_ONLY,
    "Muscle contraction":    s.DirectionOfBenefit.QUALITATIVE_ONLY,
    "Neuronal System":       s.DirectionOfBenefit.QUALITATIVE_ONLY,
    "Sensory Perception":    s.DirectionOfBenefit.QUALITATIVE_ONLY,
    "Circadian clock":       s.DirectionOfBenefit.QUALITATIVE_ONLY,
    "Chromatin organization": s.DirectionOfBenefit.QUALITATIVE_ONLY,
    "Organelle biogenesis and maintenance": s.DirectionOfBenefit.QUALITATIVE_ONLY,
    "Transport of small molecules": s.DirectionOfBenefit.QUALITATIVE_ONLY,
    "Vesicle-mediated transport": s.DirectionOfBenefit.QUALITATIVE_ONLY,
    "Digestion and absorption": s.DirectionOfBenefit.QUALITATIVE_ONLY,
    "Drug ADME":             s.DirectionOfBenefit.QUALITATIVE_ONLY,
    "Disease":               s.DirectionOfBenefit.QUALITATIVE_ONLY,
}


def _direction_for(top_level: str) -> str:
    """
    Return the direction_of_benefit for a Reactome top-level
    event. Defaults to ``qualitative_only`` for any event not
    in the table above.
    """
    return _DIRECTION_BY_TOP_LEVEL.get(
        (top_level or "").strip(),
        s.DirectionOfBenefit.QUALITATIVE_ONLY,
    )


# ---------------------------------------------------------------------------
# Indicator id slugification
# ---------------------------------------------------------------------------


_SLUG_STRIP = re.compile(r"[^a-z0-9]+")


def _slugify(text: str) -> str:
    s_ = _SLUG_STRIP.sub("_", (text or "").lower()).strip("_")
    return s_ or "unknown"


# ---------------------------------------------------------------------------
# Open Targets fetch
# ---------------------------------------------------------------------------


_OT_QUERY = """
query Mapper($efoId: String!, $size: Int!) {
  disease(efoId: $efoId) {
    id
    name
    associatedTargets(page: {index: 0, size: $size}) {
      count
      rows {
        target {
          id
          approvedSymbol
          approvedName
          proteinIds { id source }
        }
        score
        datatypeScores { id score }
      }
    }
  }
}
"""


def _fetch_ot_targets(
    disease_ref: s.DiseaseRef,
    size: int,
) -> Tuple[List[Dict[str, Any]], s.SourceStatus]:
    """
    Fetch the disease's top-associated targets from Open
    Targets and return the extracted rows plus a SourceStatus.

    Row shape returned:

        {
            "ensembl_id":    "ENSG...",
            "symbol":        "EGFR",
            "uniprot":       "P00533" | None,
            "score":         <float>,   # for ranking only
            "datatypes":     ["literature", "clinical", ...],
        }

    Never raises.
    """
    if not disease_ref or not disease_ref.id:
        return [], s.SourceStatus(
            source="Open Targets",
            reachable=True,
            returned_records=0,
            error=None,
            metadata={"note": "no resolved disease id"},
        )

    try:
        from app.drug_development.sources.open_targets import (
            OpenTargetsClient,
        )
        from app.drug_development.reverse_disease.utils import (
            to_opentargets_id,
        )
    except Exception as exc:
        return [], s.SourceStatus(
            source="Open Targets",
            reachable=False,
            returned_records=0,
            error=f"import failed: {exc}",
        )

    ot_id = to_opentargets_id(disease_ref.id)

    try:
        client = OpenTargetsClient()
        raw = client.query(_OT_QUERY, {"efoId": ot_id, "size": int(size)})
    except Exception as exc:
        return [], s.SourceStatus(
            source="Open Targets",
            reachable=False,
            returned_records=0,
            error=str(exc),
        )

    disease_block = (raw or {}).get("disease") or {}
    at = disease_block.get("associatedTargets") or {}
    raw_rows = at.get("rows") or []

    rows: List[Dict[str, Any]] = []
    for row in raw_rows:
        if not isinstance(row, dict):
            continue
        target = row.get("target") or {}
        ensembl_id = target.get("id")
        symbol = target.get("approvedSymbol")
        if not ensembl_id or not symbol:
            continue

        uniprot = None
        for pid in target.get("proteinIds") or []:
            if not isinstance(pid, dict):
                continue
            if pid.get("source") == "uniprot_swissprot":
                uniprot = pid.get("id")
                break

        datatypes = []
        for dt in row.get("datatypeScores") or []:
            if isinstance(dt, dict) and dt.get("id"):
                datatypes.append(dt["id"])

        rows.append({
            "ensembl_id": ensembl_id,
            "symbol": symbol,
            "uniprot": uniprot,
            "score": row.get("score"),
            "datatypes": datatypes,
        })

    return rows, s.SourceStatus(
        source="Open Targets",
        reachable=True,
        returned_records=len(rows),
        error=None,
        metadata={"total_available": int(at.get("count") or 0)},
    )


# ---------------------------------------------------------------------------
# Reactome pathway collection
# ---------------------------------------------------------------------------


def _fetch_pathways_for_accession(
    accession: str,
) -> Tuple[str, List[str]]:
    """
    Return (accession, [pathway_st_id, ...]).

    Never raises. On any failure, returns (accession, []).
    Uses the ReactomeClient's own cache and error handling.
    """
    try:
        from app.data.sources.reactome import ReactomeClient
        rc = ReactomeClient()
        r = rc.get_pathways_for_protein(accession)
    except Exception:
        return accession, []

    if not isinstance(r, dict) or not r.get("found"):
        return accession, []

    st_ids: List[str] = []
    for pw in r.get("pathways") or []:
        if isinstance(pw, dict):
            st_id = pw.get("st_id")
            if st_id:
                st_ids.append(str(st_id))

    return accession, st_ids


def _fetch_top_level_for_pathway(
    st_id: str,
) -> Tuple[str, Optional[str]]:
    """
    Return (st_id, top_level_display_name) where the second
    element is the display name of the top-level Reactome
    event that contains this pathway.

    Uses ReactomeClient.get_event_ancestors. Never raises.
    """
    try:
        from app.data.sources.reactome import ReactomeClient
        rc = ReactomeClient()
        chain = rc.get_event_ancestors(st_id)
    except Exception:
        return st_id, None

    if not chain:
        return st_id, None

    top = chain[-1]
    return st_id, top.get("display_name")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def derive_pair(
    disease_ref: s.DiseaseRef,
    cell_type: Optional[str] = None,
    target_sample_size: int = 25,
) -> Tuple[Optional[Dict[str, Any]], List[s.SourceStatus]]:
    """
    Derive a curated-pair-shaped vocabulary for any resolved
    disease.

    Returns (pair, source_statuses) where:

        pair is a dict with the same shape as
        ``function_vocabulary.get_pair`` produces, or None if
        the disease has no usable Open Targets association data.

        source_statuses is a list of SourceStatus records for
        the OT fetch and (aggregated) Reactome fetches.

    Never raises. A disease with zero associated targets or
    zero resolvable pathways returns (None, statuses).
    """
    statuses: List[s.SourceStatus] = []

    rows, ot_status = _fetch_ot_targets(disease_ref, target_sample_size)
    statuses.append(ot_status)

    if not rows:
        return None, statuses

    # Collect UniProt accessions from the rows. Missing ones
    # are simply skipped — no Ensembl fallback in v1, to keep
    # the derivation honest and bounded.
    accessions: List[str] = []
    for r in rows:
        acc = (r.get("uniprot") or "").strip()
        if acc and acc not in accessions:
            accessions.append(acc)

    if not accessions:
        statuses.append(s.SourceStatus(
            source="Reactome",
            reachable=True,
            returned_records=0,
            error=None,
            metadata={"note": "no reviewed UniProt accessions on OT rows"},
        ))
        return None, statuses

    # Fetch pathways for every accession in parallel.
    pathway_ids: List[str] = []
    accession_errors: List[str] = []
    fetch_success = 0

    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {
            pool.submit(_fetch_pathways_for_accession, acc): acc
            for acc in accessions
        }
        for fut in as_completed(futures):
            try:
                acc, st_ids = fut.result()
            except Exception as exc:
                accession_errors.append(str(exc))
                continue
            fetch_success += 1
            for st in st_ids:
                if st not in pathway_ids:
                    pathway_ids.append(st)

    statuses.append(s.SourceStatus(
        source="Reactome",
        reachable=fetch_success > 0,
        returned_records=len(pathway_ids),
        error="; ".join(accession_errors) if accession_errors and fetch_success == 0 else None,
        metadata={
            "accessions_queried": len(accessions),
            "accessions_succeeded": fetch_success,
            "unique_pathways": len(pathway_ids),
        },
    ))

    if not pathway_ids:
        return None, statuses

    # Resolve each unique pathway to its top-level event.
    pathway_to_top: Dict[str, str] = {}
    with ThreadPoolExecutor(max_workers=6) as pool:
        futures = {
            pool.submit(_fetch_top_level_for_pathway, st): st
            for st in pathway_ids
        }
        for fut in as_completed(futures):
            try:
                st, top = fut.result()
            except Exception:
                continue
            if top:
                pathway_to_top[st] = top

    if not pathway_to_top:
        return None, statuses

    # Group pathways by top-level event.
    grouped: Dict[str, List[str]] = {}
    for st, top in pathway_to_top.items():
        grouped.setdefault(top, []).append(st)

    # Build indicators, sorted by number of pathways desc so
    # the most-supported categories come first.
    indicators: List[Dict[str, Any]] = []
    for top, st_ids in sorted(
        grouped.items(),
        key=lambda kv: (-len(kv[1]), kv[0]),
    ):
        direction = _direction_for(top)
        indicators.append({
            "id": f"fn:reactome:{_slugify(top)}",
            "name": top,
            "direction_of_benefit": direction,
            "unit": None,
            "description": (
                f"Reactome top-level functional area '{top}' "
                f"derived from {len(st_ids)} pathway(s) linked "
                f"to {disease_ref.name}'s top associated targets."
            ),
            "evidence_level": "association",
            "source": "Reactome",
            "pathway_links": list(st_ids),
        })

    # Cell context: prefer a hint; otherwise use the disease's
    # own name as the context label. We do not fabricate a
    # specific cell type we cannot support.
    ctx_id = cell_type or f"context:{_slugify(disease_ref.name)}"
    ctx_name = cell_type or f"{disease_ref.name} (disease-affected tissue)"
    ctx_source = "Open Targets (disease association)"
    ctx_notes = (
        "This cell context was derived from the disease's own "
        "Open Targets associations. It is not a specific "
        "curated cell type. For curated cell types, use one of "
        "the reference pairs in function_vocabulary."
    )

    pair: Dict[str, Any] = {
        "disease_id": disease_ref.id,
        "disease_name": disease_ref.name,
        "cell_context_id": ctx_id,
        "cell_context_name": ctx_name,
        "cell_context_ontology": None,
        "cell_context_source": ctx_source,
        "context_notes": ctx_notes,
        "indicators": indicators,
        "derived": True,
        "mapper_version": MAPPER_VERSION,
    }

    return pair, statuses
