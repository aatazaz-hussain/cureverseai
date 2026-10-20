"""
CureVerseAI — Drug Development
Workflow 02 — Reverse Disease Engineering
Pathway Mapper (layer module).

Emits the fourth W02 graph layer:

    gene     --participates_in-->  pathway
    disease  --associated_with-->  pathway    (elevated only)

Why a W02-local module instead of reusing W01's PathwayMapper
------------------------------------------------------------

W01's PathwayMapper (drug_development/disease/pathway_mapping.py)
already does something close: it maps disease-associated
proteins to Reactome pathways and emits protein/pathway
nodes and participates_in relationships.

W02 differs from W01 in four ways that make reuse
impractical without duplicating work anyway:

    1. Target scope. W01 uses MAX_TARGETS = 10. W02's
       gene and mechanism layers use 20, so the pathway
       layer must cover the same 20 genes to keep the
       graph coherent.

    2. Relationship semantics. W01 emits
       `disease --alters--> pathway` for every pathway.
       W02 asserts a disease-to-pathway edge only when
       the pathway is supported by 2 or more associated
       genes — a weaker, evidence-conservative claim.

    3. Support classification. W02's four-class model
       requires `support_class` on every relationship.
       W01 does not set it.

    4. No protein nodes. W01 emits protein nodes as a
       side effect of pathway discovery. W02's gene layer
       (File 10) already emits gene nodes with the same
       Ensembl/UniProt metadata; a second protein layer
       would be redundant.

The underlying clients (OpenTargetsClient, EnsemblClient,
ReactomeClient) are shared and cache-shared. W02 does not
duplicate network logic; it duplicates only the
disease-specific aggregation policy.

Data flow
---------

    disease
      -> Open Targets top 20 targets (reused shape)
      -> per gene (parallel, 10 workers):
             Ensembl lookup_gene           (cached)
             Ensembl resolve_reviewed_uniprot_accession (cached)
             Reactome get_pathways_for_protein (cached)
      -> top 5 pathways per gene
      -> dedupe by Reactome st_id
      -> gene --participates_in--> pathway     (every pair)
      -> disease --associated_with--> pathway  (if >=2 genes)

Evidence semantics
------------------

    gene -> pathway: RETRIEVED_FACT
        Reactome directly records this protein->pathway
        participation. It is a database fact, not an
        inference.

    disease -> pathway: SUPPORTED_ASSOCIATION
        The disease association is INFERRED from the fact
        that >=2 disease-associated genes participate in
        the pathway. This is a statistical/curated
        association, not a causal claim.

Runtime
-------

First run:   ~30-60s (20 Reactome calls, mostly parallel,
             caches may be cold for genes not in W01's
             prewarm set)
Subsequent:  <5s (all cached)

Output shape
------------

Mirrors the other W02 layers:

    {
        "disease_node_id": <str or None>,
        "nodes":           [<ImpactNode as dict>, ...],
        "relationships":   [<Relationship as dict>, ...],
        "evidence":        [<ImpactEvidence as dict>, ...],
        "sources":         [<str>, ...],
        "found":           <bool>,
        "metadata":        {...},
        "reason":          <str or None>,
    }
"""

from __future__ import annotations

from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed,
)
from dataclasses import asdict
from typing import Any, Dict, List, Optional, Tuple

from app.data.sources.ensembl import EnsemblClient
from app.data.sources.reactome import ReactomeClient
from app.drug_development.reverse_disease.utils import (
    to_opentargets_id,
)
from app.drug_development.schemas.disease import (
    DiseaseIdentity,
)
from app.drug_development.schemas.evidence import (
    EvidenceLevel,
    EvidenceReference,
    ImpactEvidence,
)
from app.drug_development.schemas.impact import (
    ImpactNode,
    NodeType,
)
from app.drug_development.schemas.relationships import (
    Relationship,
    RelationshipType,
    SupportClass,
)
from app.drug_development.sources.open_targets import (
    OpenTargetsClient,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


SOURCE_NAME = "Reactome"
SOURCES_LIST = ["Open Targets", "Ensembl", "UniProt", "Reactome"]

DISEASE_NODE_PREFIX = "disease:"
GENE_NODE_PREFIX = "gene:"
PATHWAY_NODE_PREFIX = "pathway:"

#: Aligned with gene_variant_mapper._TOP_GENES and
#: mechanism_retriever._TOP_TARGETS so all three downstream
#: layers describe the same target set.
_TOP_GENES = 20

#: Reactome returns up to ~50 pathways per protein, ordered
#: by depth from root. Keep the most specific ones.
_TOP_PATHWAYS_PER_GENE = 5

#: Parallel workers for per-gene Reactome queries.
_MAX_WORKERS = 10

#: A pathway must be supported by at least this many
#: disease-associated genes before it earns a
#: disease --associated_with--> pathway edge. Pathways
#: supported by only one gene remain gene-level facts but
#: are not elevated to disease-level claims.
_MIN_GENES_FOR_DISEASE_EDGE = 2


# ---------------------------------------------------------------------------
# Mapper
# ---------------------------------------------------------------------------


class PathwayMapper:
    """
    Maps a DiseaseIdentity to Reactome pathway nodes,
    enriched with W02 support classification.
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

    def retrieve(
        self,
        disease: DiseaseIdentity,
    ) -> Dict[str, Any]:
        """
        Build the pathway layer for one disease.

        Never raises for a disease with no mappable pathways.
        Transport failures from Open Targets propagate;
        per-gene enrichment failures are absorbed.
        """

        disease_node_id = self._disease_node_id(disease)

        if disease_node_id is None:
            return self._empty_result(
                reason=(
                    "Disease has no identifiers; cannot build "
                    "a disease node."
                )
            )

        ot_disease_id = self._pick_open_targets_disease_id(
            disease
        )

        if ot_disease_id is None:
            return self._empty_result(
                disease_node_id=disease_node_id,
                reason=(
                    "No Open Targets-compatible identifier "
                    "available for this disease."
                ),
            )

        try:
            targets = self._fetch_top_targets(ot_disease_id)
        except RuntimeError as exc:
            return self._empty_result(
                disease_node_id=disease_node_id,
                reason=f"Open Targets request failed: {exc}",
            )

        if not targets:
            return self._empty_result(
                disease_node_id=disease_node_id,
                reason=(
                    "Open Targets returned no associated "
                    f"targets for {ot_disease_id}."
                ),
                extra_metadata={
                    "open_targets_disease_id": ot_disease_id,
                    "targets_queried": 0,
                },
            )

        # ---- Per-gene parallel pathway lookup ----------------
        per_gene_results = self._process_genes_parallel(targets)

        # ---- Aggregate ----------------------------------------
        pathway_nodes_by_id: Dict[str, ImpactNode] = {}
        pathway_to_gene_symbols: Dict[str, List[str]] = {}
        gene_to_pathways: Dict[str, List[str]] = {}

        participates_relationships: List[Relationship] = []
        evidence_records: List[ImpactEvidence] = []

        genes_with_pathways = 0
        genes_without_pathways = 0

        for result in per_gene_results:
            if result is None:
                genes_without_pathways += 1
                continue

            symbol = result["gene_symbol"]
            gene_node_id = result["gene_node_id"]

            if not result["pathway_nodes"]:
                genes_without_pathways += 1
                continue

            genes_with_pathways += 1

            for node in result["pathway_nodes"]:
                if node.node_id not in pathway_nodes_by_id:
                    pathway_nodes_by_id[node.node_id] = node

            for st_id in result["st_ids"]:
                pathway_to_gene_symbols.setdefault(
                    st_id, []
                )
                if symbol not in pathway_to_gene_symbols[st_id]:
                    pathway_to_gene_symbols[st_id].append(symbol)

                gene_to_pathways.setdefault(
                    symbol, []
                ).append(st_id)

            participates_relationships.extend(
                result["relationships"]
            )
            evidence_records.extend(result["evidence_records"])

        if not pathway_nodes_by_id:
            return self._empty_result(
                disease_node_id=disease_node_id,
                reason=(
                    "No Reactome pathway could be mapped for "
                    "any associated gene."
                ),
                extra_metadata={
                    "open_targets_disease_id": ot_disease_id,
                    "targets_queried": len(targets),
                },
            )

        # ---- Disease -> pathway edges (elevated only) --------
        disease_to_pathway_relationships: List[Relationship] = []

        elevated_count = 0
        single_gene_count = 0

        for st_id, symbols in pathway_to_gene_symbols.items():
            if len(symbols) < _MIN_GENES_FOR_DISEASE_EDGE:
                single_gene_count += 1
                continue

            elevated_count += 1

            pathway_node_id = f"{PATHWAY_NODE_PREFIX}{st_id}"
            node = pathway_nodes_by_id.get(pathway_node_id)
            display = node.name if node else st_id

            evidence_id = f"ev:reactome:disease_pathway:{st_id}"

            evidence_records.append(
                ImpactEvidence(
                    evidence_id=evidence_id,
                    source=SOURCE_NAME,
                    relationship_description=(
                        f"{disease.canonical_name or disease.query} "
                        f"is associated with pathway {display} "
                        f"({st_id}) via "
                        f"{len(symbols)} disease-associated "
                        f"gene(s)."
                    ),
                    evidence_level=EvidenceLevel.ASSOCIATION,
                    reference=EvidenceReference(
                        source=SOURCE_NAME,
                        source_id=st_id,
                        source_type="database",
                        url=(
                            "https://reactome.org/content/detail/"
                            f"{st_id}"
                        ),
                        metadata={
                            "supporting_genes": list(symbols),
                        },
                    ),
                    identifiers={
                        "reactome_id": st_id,
                    },
                    metadata={
                        "supporting_genes": list(symbols),
                        "supporting_gene_count": len(symbols),
                    },
                )
            )

            disease_to_pathway_relationships.append(
                Relationship(
                    source_id=disease_node_id,
                    target_id=pathway_node_id,
                    relationship_type=(
                        RelationshipType.ASSOCIATED_WITH
                    ),
                    evidence_ids=[evidence_id],
                    evidence_level=EvidenceLevel.ASSOCIATION,
                    support_class=(
                        SupportClass.SUPPORTED_ASSOCIATION
                    ),
                    description=(
                        f"{disease.canonical_name or disease.query} "
                        f"links to the biological process "
                        f"'{display}' ({st_id}) through "
                        f"{len(symbols)} associated genes."
                    ),
                    metadata={
                        "reactome_id": st_id,
                        "supporting_genes": list(symbols),
                        "supporting_gene_count": len(symbols),
                        "source": SOURCE_NAME,
                    },
                )
            )

        # ---- Assemble -----------------------------------------
        all_relationships = (
            participates_relationships
            + disease_to_pathway_relationships
        )

        return {
            "disease_node_id": disease_node_id,
            "nodes": [
                asdict(n)
                for n in pathway_nodes_by_id.values()
            ],
            "relationships": [
                asdict(r) for r in all_relationships
            ],
            "evidence": [asdict(e) for e in evidence_records],
            "sources": list(SOURCES_LIST),
            "found": True,
            "metadata": {
                "open_targets_disease_id": ot_disease_id,
                "targets_queried": len(targets),
                "genes_with_pathways": genes_with_pathways,
                "genes_without_pathways": (
                    genes_without_pathways
                ),
                "pathways_kept": len(pathway_nodes_by_id),
                "disease_pathways_elevated": elevated_count,
                "disease_pathways_single_gene": (
                    single_gene_count
                ),
                "min_genes_for_disease_edge": (
                    _MIN_GENES_FOR_DISEASE_EDGE
                ),
                "top_pathways_per_gene": (
                    _TOP_PATHWAYS_PER_GENE
                ),
            },
            "reason": None,
        }

    # ------------------------------------------------------------------
    # Open Targets fetch
    # ------------------------------------------------------------------

    def _fetch_top_targets(
        self,
        ot_disease_id: str,
    ) -> List[Dict[str, Any]]:
        graphql_query = """
        query W02PathwayTargets($id: String!, $size: Int!) {
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
            graphql_query,
            {"id": ot_disease_id, "size": _TOP_GENES},
        )

        if data is None:
            raise RuntimeError(
                "Open Targets returned no data for pathway "
                f"query on {ot_disease_id}."
            )

        disease = data.get("disease")
        if disease is None:
            raise RuntimeError(
                "Open Targets returned no disease object for "
                f"pathway query on {ot_disease_id}. This "
                "usually indicates a rejected GraphQL "
                "sub-selection."
            )

        associated = disease.get("associatedTargets") or {}
        rows = associated.get("rows") or []

        out: List[Dict[str, Any]] = []
        for row in rows:
            if not isinstance(row, dict):
                continue
            t = row.get("target") or {}
            symbol = t.get("approvedSymbol")
            ensembl_id = t.get("id")
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

    # ------------------------------------------------------------------
    # Parallel per-gene processing
    # ------------------------------------------------------------------

    def _process_genes_parallel(
        self,
        targets: List[Dict[str, Any]],
    ) -> List[Optional[Dict[str, Any]]]:
        results: List[Optional[Dict[str, Any]]] = (
            [None] * len(targets)
        )

        with ThreadPoolExecutor(
            max_workers=_MAX_WORKERS
        ) as pool:
            futures = {
                pool.submit(self._process_gene, t): i
                for i, t in enumerate(targets)
            }

            for future in as_completed(futures):
                i = futures[future]
                try:
                    results[i] = future.result()
                except Exception:
                    results[i] = None

        return results

    def _process_gene(
        self,
        target: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        For one gene, resolve the UniProt accession and fetch
        its Reactome pathways.

        Returns None if the gene cannot be resolved to a
        protein or has no Reactome pathways.
        """

        symbol = target.get("symbol")
        ensembl_id = target.get("ensembl_id")

        if not symbol or not ensembl_id:
            return None

        # ---- Resolve UniProt accession (cached) --------------
        try:
            uniprot_resolution = (
                self.ensembl.resolve_reviewed_uniprot_accession(
                    ensembl_id
                )
            )
        except Exception:
            return None

        if not isinstance(uniprot_resolution, dict):
            return None

        accession = uniprot_resolution.get("accession")
        if not accession:
            return None

        # ---- Fetch pathways (cached) --------------------------
        try:
            pathways_result = (
                self.reactome.get_pathways_for_protein(
                    str(accession)
                )
            )
        except RuntimeError:
            return None

        if not pathways_result.get("found"):
            return None

        pathways = (
            pathways_result.get("pathways") or []
        )[:_TOP_PATHWAYS_PER_GENE]

        if not pathways:
            return None

        gene_node_id = f"{GENE_NODE_PREFIX}{symbol.upper()}"

        pathway_nodes: List[ImpactNode] = []
        st_ids: List[str] = []
        relationships: List[Relationship] = []
        evidence_records: List[ImpactEvidence] = []

        for pw in pathways:
            st_id = pw.get("st_id")
            display_name = pw.get("display_name")

            if not st_id or not display_name:
                continue

            st_id = str(st_id)
            st_ids.append(st_id)

            pathway_node_id = f"{PATHWAY_NODE_PREFIX}{st_id}"

            node = ImpactNode(
                node_id=pathway_node_id,
                node_type=NodeType.PATHWAY,
                name=str(display_name),
                identifier=st_id,
                description=None,
                evidence_ids=[],
                metadata={
                    "reactome_id": st_id,
                    "reactome_st_id_version": pw.get(
                        "st_id_version"
                    ),
                    "reactome_db_id": pw.get("db_id"),
                    "species": pw.get("species_name"),
                    "is_in_disease": pw.get("is_in_disease"),
                    "is_inferred": pw.get("is_inferred"),
                    "has_diagram": pw.get("has_diagram"),
                    "has_ehld": pw.get("has_ehld"),
                    "release_date": pw.get("release_date"),
                    "last_updated_date": pw.get(
                        "last_updated_date"
                    ),
                    "schema_class": pw.get("schema_class"),
                    "source": SOURCE_NAME,
                },
            )
            pathway_nodes.append(node)

            # ---- gene -> pathway evidence + relationship -----
            ev_id = (
                f"ev:reactome:participates:"
                f"{symbol}:{st_id}"
            )

            evidence_records.append(
                ImpactEvidence(
                    evidence_id=ev_id,
                    source=SOURCE_NAME,
                    relationship_description=(
                        f"{symbol} (UniProt {accession}) "
                        f"participates in Reactome pathway "
                        f"{display_name} ({st_id})."
                    ),
                    evidence_level=EvidenceLevel.DIRECT,
                    reference=EvidenceReference(
                        source=SOURCE_NAME,
                        source_id=st_id,
                        source_type="database",
                        url=(
                            "https://reactome.org/content/detail/"
                            f"{st_id}"
                        ),
                        metadata={
                            "species": pw.get("species_name"),
                        },
                    ),
                    identifiers={
                        "reactome_id": st_id,
                        "uniprot_accession": str(accession),
                        "gene_symbol": symbol,
                    },
                    metadata={
                        "display_name": str(display_name),
                        "species": pw.get("species_name"),
                        "is_in_disease": pw.get("is_in_disease"),
                    },
                )
            )

            relationships.append(
                Relationship(
                    source_id=gene_node_id,
                    target_id=pathway_node_id,
                    relationship_type=(
                        RelationshipType.PARTICIPATES_IN
                    ),
                    evidence_ids=[ev_id],
                    evidence_level=EvidenceLevel.DIRECT,
                    support_class=SupportClass.RETRIEVED_FACT,
                    description=(
                        f"The gene {symbol} takes part in "
                        f"the biological process "
                        f"'{display_name}' ({st_id})."
                    ),
                    metadata={
                        "reactome_id": st_id,
                        "uniprot_accession": str(accession),
                        "source": SOURCE_NAME,
                    },
                )
            )

        if not pathway_nodes:
            return None

        return {
            "gene_symbol": symbol,
            "gene_node_id": gene_node_id,
            "uniprot_accession": str(accession),
            "pathway_nodes": pathway_nodes,
            "st_ids": st_ids,
            "relationships": relationships,
            "evidence_records": evidence_records,
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _disease_node_id(
        disease: DiseaseIdentity,
    ) -> Optional[str]:
        if not disease.identifiers:
            return None

        primary = disease.identifiers[0]
        ident = (primary.identifier or "").strip()

        if not ident:
            return None

        sanitized = ident.replace(":", "_")
        return f"{DISEASE_NODE_PREFIX}{sanitized}"

    @staticmethod
    def _pick_open_targets_disease_id(
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
    def _empty_result(
        disease_node_id: Optional[str] = None,
        reason: Optional[str] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return {
            "disease_node_id": disease_node_id,
            "nodes": [],
            "relationships": [],
            "evidence": [],
            "sources": list(SOURCES_LIST),
            "found": False,
            "metadata": extra_metadata or {},
            "reason": reason,
        }
