"""
CureVerseAI — Drug Development
Workflow 03 — Therapeutic Discovery
Mechanism Resolver.

Given the W03 disease context (see disease_context.py),
produce a SelectedMechanism that downstream modules can
use to discover therapeutic targets.

Three entry cases
-----------------

Case 1 — pathway handoff (mechanism_kind == "pathway")
    The user arrived from a W02 pathway node.
    The mechanism is already a named biological process.
    We accept it and fetch its member genes from Reactome.

Case 2 — gene / protein / evidence_category handoff
    The user arrived from a W02 gene, protein, or
    evidence-category node. These are not biological
    mechanisms, so we expand them:
        - gene / protein -> Reactome pathways containing
          that gene, intersected with the disease's
          Open Targets targets
        - evidence_category -> the disease's Open Targets
          targets, used to discover a pathway
    The best-scoring pathway becomes the mechanism.

Case 3 — no mechanism supplied
    The user entered a disease directly. We discover a
    mechanism by:
        1. Fetching the disease's top associated targets
           from Open Targets.
        2. Fetching Reactome pathways for each target's
           UniProt accession in parallel.
        3. Counting how many disease targets participate
           in each pathway.
        4. Choosing the pathway with the highest count.

Every case returns the same shape. Missing data is
recorded in `reason`, never fabricated.

Parallelism
-----------

Case 3 performs the Reactome pathway lookups for all top
targets concurrently with a 10-worker pool. This is the
single biggest cost in W03's mechanism step.

Sources used
------------

    Open Targets     disease.associatedTargets
    Ensembl          gene lookup + UniProt accession resolution
    Reactome         protein -> pathways, pathway members

All are already wired in the codebase and cache-backed.
"""

from __future__ import annotations

from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed,
)
from typing import Any, Dict, List, Optional

from app.data.sources.ensembl import EnsemblClient
from app.data.sources.reactome import ReactomeClient
from app.drug_development.reverse_disease.utils import (
    to_opentargets_id,
)
from app.drug_development.schemas.disease import DiseaseIdentity
from app.drug_development.sources.open_targets import (
    OpenTargetsClient,
)
from app.drug_development.therapeutic_discovery.schemas import (
    SelectedMechanism,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


SOURCE_OPEN_TARGETS = "Open Targets"
SOURCE_REACTOME = "Reactome"
SOURCE_ENSEMBL = "Ensembl"

#: How many top disease-associated genes to scan during
#: mechanism discovery. Matches W02's _TOP_GENES.
_TOP_GENES = 20

#: How many parallel Reactome lookups.
_MAX_WORKERS = 10

#: A pathway must have at least this many disease targets
#: to be considered the primary mechanism.
_MIN_TARGETS_FOR_MECHANISM = 2


# ---------------------------------------------------------------------------
# Resolver
# ---------------------------------------------------------------------------


class MechanismResolver:
    """
    Resolve or discover the mechanism under study.
    """

    def __init__(
        self,
        open_targets_client: Optional[OpenTargetsClient] = None,
        ensembl_client: Optional[EnsemblClient] = None,
        reactome_client: Optional[ReactomeClient] = None,
    ):
        self.open_targets = (
            open_targets_client or OpenTargetsClient()
        )
        self.ensembl = ensembl_client or EnsemblClient()
        self.reactome = reactome_client or ReactomeClient()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def resolve(
        self,
        disease: DiseaseIdentity,
        context: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Produce a SelectedMechanism for downstream modules.

        `context` is the dict returned by disease_context.py.
        Its `mechanism_id` and `mechanism_kind` fields drive
        the three cases above.
        """

        mechanism_id = context.get("mechanism_id")
        mechanism_kind = context.get("mechanism_kind")

        # ---- Case 1: pathway handoff ---------------------------
        if mechanism_kind == "pathway":
            return self._from_pathway_id(
                mechanism_id=mechanism_id,
                disease=disease,
            )

        # ---- Case 2: gene / protein / evidence_category --------
        if mechanism_kind in {
            "gene",
            "protein",
            "evidence_category",
        }:
            return self._from_non_pathway_handoff(
                mechanism_id=mechanism_id,
                mechanism_kind=mechanism_kind,
                disease=disease,
            )

        # ---- Case 3: discovery ---------------------------------
        return self._discover_from_disease(disease)

    # ------------------------------------------------------------------
    # Case 1 — pathway handoff
    # ------------------------------------------------------------------

    def _from_pathway_id(
        self,
        mechanism_id: str,
        disease: DiseaseIdentity,
    ) -> Dict[str, Any]:
        """
        Accept a Reactome pathway ID and fetch its member
        proteins.
        """

        reactome_stable_id = mechanism_id.replace(
            "pathway:", "", 1
        )

        try:
            members = self._fetch_pathway_members(
                reactome_stable_id
            )
        except Exception as exc:
            return self._empty(
                reason=(
                    f"Reactome pathway lookup failed for "
                    f"{reactome_stable_id}: "
                    f"{type(exc).__name__}"
                ),
                source_failures=[
                    {
                        "source": SOURCE_REACTOME,
                        "reason": str(exc)[:200],
                    }
                ],
            )

        if not members:
            return self._empty(
                reason=(
                    f"Reactome returned no members for "
                    f"pathway {reactome_stable_id}."
                ),
            )

        # Fetch display name from search (single call,
        # cache-backed) or fall back to the ID.
        display_name = self._fetch_pathway_name(
            reactome_stable_id
        )

        mechanism = SelectedMechanism(
            mechanism_id=mechanism_id,
            label=display_name,
            source="w02_handoff",
            identifier=reactome_stable_id,
            description=None,
            evidence_ids=[],
            metadata={
                "reactome_stable_id": reactome_stable_id,
                "member_count": len(members),
            },
        )

        return {
            "found": True,
            "mechanism": mechanism,
            "candidate_mechanisms": [mechanism],
            "member_genes": self._member_symbols(members),
            "member_target_ensembl_ids": [],
            "pathway_reactome_id": reactome_stable_id,
            "sources_queried": [SOURCE_REACTOME],
            "reason": None,
            "metadata": {
                "case": "pathway_handoff",
                "member_count": len(members),
            },
        }

    # ------------------------------------------------------------------
    # Case 2 — non-pathway handoff
    # ------------------------------------------------------------------

    def _from_non_pathway_handoff(
        self,
        mechanism_id: str,
        mechanism_kind: str,
        disease: DiseaseIdentity,
    ) -> Dict[str, Any]:
        """
        Expand a gene, protein, or evidence-category ID
        into a pathway.
        """

        # For gene / protein handoffs, extract the identifier
        # and look up its pathways.
        gene_symbol: Optional[str] = None
        if mechanism_kind == "gene":
            gene_symbol = mechanism_id.replace(
                "gene:", "", 1
            ).strip()
        elif mechanism_kind == "protein":
            # Protein accession — resolve to gene symbol via
            # Ensembl.
            accession = mechanism_id.replace(
                "protein:", "", 1
            ).strip()
            gene_symbol = self._gene_for_uniprot(accession)

        # Evidence-category handoff falls through to discovery.
        if not gene_symbol:
            discovered = self._discover_from_disease(disease)
            # Annotate the case without changing the result.
            discovered["metadata"]["case"] = (
                f"{mechanism_kind}_to_discovery"
            )
            return discovered

        # Find pathways for this gene, then intersect with the
        # disease's Open Targets targets to pick the best.
        gene_pathways = self._pathways_for_gene(gene_symbol)
        if not gene_pathways:
            discovered = self._discover_from_disease(disease)
            discovered["metadata"]["case"] = (
                f"{mechanism_kind}_no_pathways_fallback"
            )
            return discovered

        # Pick the first pathway (Reactome returns them
        # ordered by depth from root — the deepest is most
        # specific).
        top = gene_pathways[0]
        st_id = top.get("st_id") or top.get("reactome_id")
        label = top.get("display_name") or st_id

        if not st_id:
            discovered = self._discover_from_disease(disease)
            discovered["metadata"]["case"] = (
                f"{mechanism_kind}_missing_stid_fallback"
            )
            return discovered

        mechanism = SelectedMechanism(
            mechanism_id=f"pathway:{st_id}",
            label=label,
            source="w02_handoff",
            identifier=st_id,
            metadata={
                "expanded_from": mechanism_id,
                "expansion_kind": mechanism_kind,
            },
        )

        members = self._fetch_pathway_members(st_id)

        return {
            "found": True,
            "mechanism": mechanism,
            "candidate_mechanisms": [mechanism],
            "member_genes": self._member_symbols(members),
            "member_target_ensembl_ids": [],
            "pathway_reactome_id": st_id,
            "sources_queried": [
                SOURCE_ENSEMBL,
                SOURCE_REACTOME,
            ],
            "reason": None,
            "metadata": {
                "case": f"{mechanism_kind}_expanded",
                "expanded_from": mechanism_id,
            },
        }

    # ------------------------------------------------------------------
    # Case 3 — discovery from the disease
    # ------------------------------------------------------------------

    def _discover_from_disease(
        self,
        disease: DiseaseIdentity,
    ) -> Dict[str, Any]:
        """
        Discover a mechanism by intersecting Open Targets
        targets with Reactome pathways.
        """

        ot_disease_id = self._pick_ot_disease_id(disease)
        if not ot_disease_id:
            return self._empty(
                reason=(
                    "No Open Targets-compatible disease "
                    "identifier available for mechanism "
                    "discovery."
                ),
            )

        targets = self._fetch_top_targets(ot_disease_id)
        if not targets:
            return self._empty(
                reason=(
                    f"Open Targets returned no associated "
                    f"targets for {ot_disease_id}."
                ),
            )

        # Parallel Reactome lookups (10 workers).
        per_target = self._pathways_per_target_parallel(targets)

        # Count genes per pathway.
        pathway_members: Dict[str, Dict[str, Any]] = {}

        for result in per_target:
            if not result:
                continue

            gene_symbol = result["gene_symbol"]

            for pw in result["pathways"]:
                st_id = pw.get("st_id")
                if not st_id:
                    continue

                entry = pathway_members.setdefault(
                    st_id,
                    {
                        "st_id": st_id,
                        "display_name": pw.get(
                            "display_name"
                        )
                        or st_id,
                        "genes": [],
                    },
                )

                if gene_symbol not in entry["genes"]:
                    entry["genes"].append(gene_symbol)

        # Filter by threshold and sort by gene count.
        eligible = [
            e
            for e in pathway_members.values()
            if len(e["genes"]) >= _MIN_TARGETS_FOR_MECHANISM
        ]
        eligible.sort(key=lambda e: -len(e["genes"]))

        if not eligible:
            return self._empty(
                reason=(
                    "No Reactome pathway contained at least "
                    f"{_MIN_TARGETS_FOR_MECHANISM} of the "
                    "disease's top associated targets."
                ),
                source_failures=[],
            )

        top = eligible[0]
        st_id = top["st_id"]

        mechanism = SelectedMechanism(
            mechanism_id=f"pathway:{st_id}",
            label=top["display_name"],
            source="discovered",
            identifier=st_id,
            metadata={
                "supporting_genes": list(top["genes"]),
                "supporting_gene_count": len(top["genes"]),
            },
        )

        candidates = [
            SelectedMechanism(
                mechanism_id=f"pathway:{e['st_id']}",
                label=e["display_name"],
                source="discovered",
                identifier=e["st_id"],
                metadata={
                    "supporting_genes": list(e["genes"]),
                    "supporting_gene_count": len(e["genes"]),
                },
            )
            for e in eligible[:10]
        ]

        return {
            "found": True,
            "mechanism": mechanism,
            "candidate_mechanisms": candidates,
            "member_genes": list(top["genes"]),
            "member_target_ensembl_ids": [],
            "pathway_reactome_id": st_id,
            "sources_queried": [
                SOURCE_OPEN_TARGETS,
                SOURCE_REACTOME,
            ],
            "reason": None,
            "metadata": {
                "case": "discovered",
                "pathways_seen": len(pathway_members),
                "pathways_eligible": len(eligible),
            },
        }

    # ------------------------------------------------------------------
    # Fetch helpers
    # ------------------------------------------------------------------

    def _fetch_top_targets(
        self,
        ot_disease_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Fetch top disease-associated genes from Open Targets.
        """

        query = """
        query W03MechanismTargets($id: String!, $size: Int!) {
          disease(efoId: $id) {
            id
            name
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

        data = self.open_targets.query(
            query,
            {"id": ot_disease_id, "size": _TOP_GENES},
        )

        if data is None:
            raise RuntimeError(
                "Open Targets returned no data for "
                f"mechanism discovery on {ot_disease_id}."
            )

        disease = data.get("disease")
        if disease is None:
            raise RuntimeError(
                "Open Targets returned no disease object for "
                f"mechanism discovery on {ot_disease_id}."
            )

        associated = disease.get("associatedTargets") or {}
        rows = associated.get("rows") or []

        out: List[Dict[str, Any]] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            target = row.get("target") or {}
            symbol = target.get("approvedSymbol")
            ensembl_id = target.get("id")
            if not symbol or not ensembl_id:
                continue
            out.append(
                {
                    "symbol": str(symbol),
                    "ensembl_id": str(ensembl_id),
                    "score": row.get("score"),
                }
            )

        return out

    def _pathways_per_target_parallel(
        self,
        targets: List[Dict[str, Any]],
    ) -> List[Optional[Dict[str, Any]]]:
        """
        Fetch Reactome pathways for each target concurrently.
        """

        results: List[Optional[Dict[str, Any]]] = (
            [None] * len(targets)
        )

        with ThreadPoolExecutor(
            max_workers=_MAX_WORKERS
        ) as pool:
            futures = {
                pool.submit(self._pathways_for_target, t): i
                for i, t in enumerate(targets)
            }

            for future in as_completed(futures):
                i = futures[future]
                try:
                    results[i] = future.result()
                except Exception:
                    results[i] = None

        return results

    def _pathways_for_target(
        self,
        target: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        For one target, resolve UniProt and fetch Reactome
        pathways.

        Returns None when the target cannot be resolved.
        """

        symbol = target.get("symbol")
        ensembl_id = target.get("ensembl_id")

        if not symbol or not ensembl_id:
            return None

        try:
            uniprot = (
                self.ensembl.resolve_reviewed_uniprot_accession(
                    ensembl_id
                )
            )
        except Exception:
            return None

        if not isinstance(uniprot, dict):
            return None

        accession = uniprot.get("accession")
        if not accession:
            return None

        try:
            pathways = self.reactome.get_pathways_for_protein(
                str(accession)
            )
        except Exception:
            return None

        if not pathways.get("found"):
            return None

        return {
            "gene_symbol": symbol,
            "ensembl_id": ensembl_id,
            "uniprot_accession": str(accession),
            "pathways": pathways.get("pathways") or [],
        }

    def _pathways_for_gene(
        self,
        gene_symbol: str,
    ) -> List[Dict[str, Any]]:
        """
        Fetch Reactome pathways for one gene symbol.
        """

        try:
            ensembl_record = self.ensembl.lookup_gene(
                gene_symbol
            )
        except Exception:
            return []

        if not isinstance(ensembl_record, dict):
            return []

        ensembl_id = ensembl_record.get("id")
        if not ensembl_id:
            return []

        try:
            uniprot = (
                self.ensembl.resolve_reviewed_uniprot_accession(
                    ensembl_id
                )
            )
        except Exception:
            return []

        if not isinstance(uniprot, dict):
            return []

        accession = uniprot.get("accession")
        if not accession:
            return []

        try:
            pathways = self.reactome.get_pathways_for_protein(
                str(accession)
            )
        except Exception:
            return []

        if not pathways.get("found"):
            return []

        return list(pathways.get("pathways") or [])

    def _fetch_pathway_members(
        self,
        reactome_stable_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Fetch member proteins of a Reactome pathway.

        The exact shape returned by Reactome depends on
        which endpoint is used. This method calls the
        ContentService participant endpoint and normalizes
        the response to a list of dicts with at least
        `uniprot_accession` and `gene_symbol` when available.
        """

        # Reactome ContentService endpoint for pathway
        # participants. Returns a JSON array.
        import httpx

        url = (
            "https://reactome.org/ContentService/data/"
            f"participants/{reactome_stable_id}"
        )

        try:
            with httpx.Client(
                timeout=httpx.Timeout(
                    connect=10.0,
                    read=30.0,
                    write=10.0,
                    pool=10.0,
                ),
                follow_redirects=True,
            ) as client:
                response = client.get(
                    url,
                    headers={
                        "Accept": "application/json",
                        "User-Agent": "CureVerseAI/1.0",
                    },
                )
        except Exception as exc:
            raise RuntimeError(
                f"Reactome participants request failed for "
                f"{reactome_stable_id}: {exc}"
            ) from exc

        if response.status_code == 404:
            return []

        response.raise_for_status()

        payload = response.json()
        if not isinstance(payload, list):
            return []

        members: List[Dict[str, Any]] = []
        for entry in payload:
            if not isinstance(entry, dict):
                continue
            ref = entry.get("refEntities") or []
            if not isinstance(ref, list):
                ref = []

            for r in ref:
                if not isinstance(r, dict):
                    continue
                identifier = r.get("identifier")
                display = r.get("displayName")
                if not identifier:
                    continue
                members.append(
                    {
                        "uniprot_accession": str(identifier),
                        "gene_symbol": None,
                        "display_name": str(display)
                        if display
                        else None,
                    }
                )

        return members

    def _fetch_pathway_name(
        self,
        reactome_stable_id: str,
    ) -> Optional[str]:
        """
        Fetch the display name of a Reactome pathway.
        """

        import httpx

        url = (
            "https://reactome.org/ContentService/data/"
            f"query/{reactome_stable_id}"
        )

        try:
            with httpx.Client(
                timeout=httpx.Timeout(
                    connect=10.0,
                    read=30.0,
                    write=10.0,
                    pool=10.0,
                ),
                follow_redirects=True,
            ) as client:
                response = client.get(
                    url,
                    headers={
                        "Accept": "application/json",
                        "User-Agent": "CureVerseAI/1.0",
                    },
                )
        except Exception:
            return None

        if response.status_code >= 400:
            return None

        try:
            payload = response.json()
        except ValueError:
            return None

        if isinstance(payload, dict):
            name = payload.get("displayName")
            if name:
                return str(name)

        return None

    def _gene_for_uniprot(
        self,
        accession: str,
    ) -> Optional[str]:
        """
        Resolve a UniProt accession to a gene symbol via
        Ensembl's reverse lookup.

        Ensembl's public REST API does not expose a direct
        UniProt -> gene-symbol reverse lookup in the version
        currently used by this project. As a fallback, this
        method returns None; the caller then falls through
        to discovery.

        A future iteration may add a dedicated reverse lookup.
        """

        return None

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

    @staticmethod
    def _member_symbols(
        members: List[Dict[str, Any]],
    ) -> List[str]:
        """
        Extract identifiers from member records.

        Prefers gene_symbol when Reactome provides one.
        Falls back to UniProt accession (prefixed as
        "uniprot:") so downstream modules can resolve
        the gene via Ensembl.
        """

        out: List[str] = []
        for m in members:
            symbol = m.get("gene_symbol")
            if symbol and symbol not in out:
                out.append(str(symbol))
                continue

            accession = m.get("uniprot_accession")
            if accession:
                prefixed = f"uniprot:{accession}"
                if prefixed not in out:
                    out.append(prefixed)

        return out

    @staticmethod
    def _empty(
        reason: str,
        source_failures: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        return {
            "found": False,
            "mechanism": None,
            "candidate_mechanisms": [],
            "member_genes": [],
            "member_target_ensembl_ids": [],
            "pathway_reactome_id": None,
            "sources_queried": [],
            "reason": reason,
            "metadata": {
                "source_failures": source_failures or [],
            },
        }


# ---------------------------------------------------------------------------
# Convenience
# ---------------------------------------------------------------------------


def resolve_mechanism(
    disease: DiseaseIdentity,
    context: Dict[str, Any],
) -> Dict[str, Any]:
    """
    One-shot entry point.
    """
    return MechanismResolver().resolve(disease, context)
