"""
CureVerseAI — Drug Development
Workflow 03 — Therapeutic Discovery
Target Discovery.

Given a SelectedMechanism and the disease, produce a list
of candidate therapeutic targets.

Sources
-------

1. Mechanism members
   The mechanism carries a list of member identifiers
   (either gene symbols or `uniprot:ACCESSION` strings).
   Each member is enriched via Ensembl + UniProt to
   obtain a gene symbol, Ensembl ID, and UniProt
   accession when available.

2. Open Targets top targets
   The disease's top associated targets from Open Targets.
   These carry an `open_targets_score`.

Union rule
----------

A target appears in the output if it is present in EITHER
source. Two metadata signals are recorded separately:

    mechanism_membership : bool
    open_targets_score   : float | None

Sorting:
    1. mechanism_membership descending (True first)
    2. open_targets_score descending (higher first)
    3. label ascending (alphabetical tiebreak)

No composite target score is produced.

Parallelism
-----------

Member enrichment runs with a 10-worker pool. Each worker
performs one Ensembl lookup and one UniProt resolution
(both cache-backed).

Caps
----

    _MAX_MEMBERS = 30    enrich at most this many members
    _MAX_OT_TARGETS = 20 top Open Targets targets

Rationale: beyond 30 members, the enrichment cost grows
without adding meaningful candidate diversity to a demo
investigation.
"""

from __future__ import annotations

from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed,
)
from typing import Any, Dict, List, Optional

from app.data.sources.ensembl import EnsemblClient
from app.drug_development.reverse_disease.utils import (
    to_opentargets_id,
)
from app.drug_development.schemas.disease import DiseaseIdentity
from app.drug_development.sources.open_targets import (
    OpenTargetsClient,
)
from app.drug_development.therapeutic_discovery.schemas import (
    SelectedMechanism,
    TargetSummary,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


SOURCE_OPEN_TARGETS = "Open Targets"
SOURCE_ENSEMBL = "Ensembl"
SOURCE_UNIPROT = "UniProt"

_MAX_MEMBERS = 30
_MAX_OT_TARGETS = 20
_MAX_WORKERS = 10


# ---------------------------------------------------------------------------
# Target discovery
# ---------------------------------------------------------------------------


class TargetDiscovery:
    """
    Build the W03 candidate-target list from a mechanism and
    a disease.
    """

    def __init__(
        self,
        open_targets_client: Optional[OpenTargetsClient] = None,
        ensembl_client: Optional[EnsemblClient] = None,
    ):
        self.open_targets = (
            open_targets_client or OpenTargetsClient()
        )
        self.ensembl = ensembl_client or EnsemblClient()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def discover(
        self,
        disease: DiseaseIdentity,
        mechanism: SelectedMechanism,
        mechanism_context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Build the target list.

        `mechanism_context` is the dict returned by
        mechanism_resolver.resolve(). Its `member_genes`
        field drives member enrichment.
        """

        member_ids = list(
            mechanism_context.get("member_genes") or []
        )[:_MAX_MEMBERS]

        # ---- 1) Enrich mechanism members in parallel -------
        enriched_members = self._enrich_members_parallel(
            member_ids
        )

        # ---- 2) Fetch disease's Open Targets targets ------
        ot_targets = self._fetch_open_targets_targets(
            disease
        )

        # ---- 3) Union ---------------------------------------
        by_id: Dict[str, TargetSummary] = {}

        # First, members (so we can flag them).
        for entry in enriched_members:
            if not entry:
                continue
            target_id = entry["target_id"]
            by_id[target_id] = TargetSummary(
                target_id=target_id,
                label=entry["label"],
                gene_symbol=entry.get("gene_symbol"),
                uniprot_id=entry.get("uniprot_id"),
                ensembl_id=entry.get("ensembl_id"),
                chembl_target_id=None,
                mechanism_membership=True,
                open_targets_score=None,
                evidence_ids=[],
                metadata={
                    "source": "mechanism_member",
                    "origin_id": entry.get("origin_id"),
                },
            )

        # Then, Open Targets. Merge into existing or add new.
        for ot in ot_targets:
            target_id = ot["target_id"]
            existing = by_id.get(target_id)

            if existing:
                existing.open_targets_score = ot.get(
                    "score"
                )
                existing.ensembl_id = (
                    existing.ensembl_id
                    or ot.get("ensembl_id")
                )
                existing.metadata["ot_symbol"] = ot.get(
                    "symbol"
                )
            else:
                by_id[target_id] = TargetSummary(
                    target_id=target_id,
                    label=ot["symbol"],
                    gene_symbol=ot["symbol"],
                    uniprot_id=None,
                    ensembl_id=ot.get("ensembl_id"),
                    chembl_target_id=None,
                    mechanism_membership=False,
                    open_targets_score=ot.get("score"),
                    evidence_ids=[],
                    metadata={
                        "source": "open_targets",
                    },
                )

        # ---- 4) Sort ----------------------------------------
        targets = list(by_id.values())
        targets.sort(
            key=lambda t: (
                not t.mechanism_membership,
                -(t.open_targets_score or 0.0),
                t.label.lower(),
            )
        )

        both_signals = sum(
            1
            for t in targets
            if t.mechanism_membership
            and t.open_targets_score is not None
        )

        if not targets:
            return {
                "found": False,
                "targets": [],
                "sources_queried": [
                    SOURCE_OPEN_TARGETS,
                    SOURCE_ENSEMBL,
                    SOURCE_UNIPROT,
                ],
                "reason": (
                    "No candidate targets were found from "
                    "either the mechanism or Open Targets."
                ),
                "metadata": {},
            }

        return {
            "found": True,
            "targets": targets,
            "sources_queried": [
                SOURCE_OPEN_TARGETS,
                SOURCE_ENSEMBL,
                SOURCE_UNIPROT,
            ],
            "reason": None,
            "metadata": {
                "mechanism_member_count": len(
                    enriched_members
                ),
                "open_targets_count": len(ot_targets),
                "union_count": len(targets),
                "targets_with_both_signals": both_signals,
                "enriched_count": sum(
                    1
                    for e in enriched_members
                    if e and e.get("uniprot_id")
                ),
            },
        }

    # ------------------------------------------------------------------
    # Member enrichment (parallel)
    # ------------------------------------------------------------------

    def _enrich_members_parallel(
        self,
        member_ids: List[str],
    ) -> List[Optional[Dict[str, Any]]]:
        results: List[Optional[Dict[str, Any]]] = (
            [None] * len(member_ids)
        )

        with ThreadPoolExecutor(
            max_workers=_MAX_WORKERS
        ) as pool:
            futures = {
                pool.submit(self._enrich_member, mid): i
                for i, mid in enumerate(member_ids)
            }

            for future in as_completed(futures):
                i = futures[future]
                try:
                    results[i] = future.result()
                except Exception:
                    results[i] = None

        return results

    def _enrich_member(
        self,
        member_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Resolve one mechanism member to a gene symbol,
        Ensembl ID, and UniProt accession.

        `member_id` is one of:
            SYMBOL              (e.g. IL4R)
            uniprot:ACCESSION   (e.g. uniprot:P24394)
        """

        symbol: Optional[str] = None
        uniprot: Optional[str] = None
        ensembl_id: Optional[str] = None

        # ---- Uniprot-prefixed member --------------------------
        if member_id.startswith("uniprot:"):
            accession = member_id.replace(
                "uniprot:", "", 1
            ).strip()

            # We do not have a UniProt -> gene symbol reverse
            # lookup in the current client. Use the accession
            # as a stable identifier for now and let Ensembl
            # resolve downstream if a symbol is needed.
            uniprot = accession
            target_id = f"target:{accession}"
            label = accession
        else:
            # Assume it's a gene symbol.
            symbol = member_id.strip().upper()
            if not symbol:
                return None

            try:
                gene_record = self.ensembl.lookup_gene(
                    symbol
                )
            except Exception:
                gene_record = None

            if isinstance(gene_record, dict):
                ensembl_id = gene_record.get("id")

            if ensembl_id:
                try:
                    resolved = (
                        self.ensembl
                        .resolve_reviewed_uniprot_accession(
                            ensembl_id
                        )
                    )
                except Exception:
                    resolved = None

                if isinstance(resolved, dict):
                    uniprot = resolved.get("accession")

            target_id = f"target:{symbol}"
            label = symbol

        return {
            "target_id": target_id,
            "label": label,
            "gene_symbol": symbol,
            "uniprot_id": uniprot,
            "ensembl_id": ensembl_id,
            "origin_id": member_id,
        }

    # ------------------------------------------------------------------
    # Open Targets fetch
    # ------------------------------------------------------------------

    def _fetch_open_targets_targets(
        self,
        disease: DiseaseIdentity,
    ) -> List[Dict[str, Any]]:
        ot_disease_id = self._pick_ot_disease_id(disease)
        if not ot_disease_id:
            return []

        query = """
        query W03TargetDiscovery($id: String!, $size: Int!) {
          disease(efoId: $id) {
            id
            associatedTargets(
              page: { index: 0, size: $size }
            ) {
              rows {
                target {
                  id
                  approvedSymbol
                }
                score
              }
            }
          }
        }
        """

        try:
            data = self.open_targets.query(
                query,
                {
                    "id": ot_disease_id,
                    "size": _MAX_OT_TARGETS,
                },
            )
        except Exception:
            return []

        if not isinstance(data, dict):
            return []

        disease_block = data.get("disease") or {}
        associated = (
            disease_block.get("associatedTargets") or {}
        )
        rows = associated.get("rows") or []

        out: List[Dict[str, Any]] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            target = row.get("target") or {}
            symbol = target.get("approvedSymbol")
            ensembl_id = target.get("id")
            if not symbol:
                continue

            out.append(
                {
                    "target_id": f"target:{symbol}",
                    "symbol": str(symbol),
                    "ensembl_id": (
                        str(ensembl_id) if ensembl_id else None
                    ),
                    "score": row.get("score"),
                }
            )

        return out

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _pick_ot_disease_id(
        disease: DiseaseIdentity,
    ) -> Optional[str]:
        identifiers = disease.identifiers or []

        for prefix in ("MONDO:", "EFO:", "Orphanet:"):
            for ident in identifiers:
                value = (ident.identifier or "").strip()
                if value.startswith(prefix):
                    return to_opentargets_id(value)

        return None


# ---------------------------------------------------------------------------
# Convenience
# ---------------------------------------------------------------------------


def discover_targets(
    disease: DiseaseIdentity,
    mechanism: SelectedMechanism,
    mechanism_context: Dict[str, Any],
) -> Dict[str, Any]:
    """
    One-shot entry point.
    """
    return TargetDiscovery().discover(
        disease=disease,
        mechanism=mechanism,
        mechanism_context=mechanism_context,
    )
