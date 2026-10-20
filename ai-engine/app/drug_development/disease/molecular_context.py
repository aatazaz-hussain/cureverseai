"""
CureVerseAI — Drug Development
Molecular Context mapper.

Given a resolved DiseaseIdentity, produce the molecular
layer of the Biological Impact Graph:

    Disease  --associated_with-->  Gene
    Disease  --associated_with-->  Protein
    Gene     --encodes-->          Protein

Data flow
---------

    Disease
      |
      v
    Open Targets: disease -> top-N associated targets
      |
      v
    Ensembl: gene symbol -> Ensembl gene record
      |
      v
    Ensembl xrefs + UniProt: reviewed Swiss-Prot accession
      |
      v
    ImpactNodes (gene, protein)
    + Relationships (disease->gene, disease->protein, gene->protein)
    + Evidence (Open Targets, Ensembl, UniProt)

Parallelism
-----------

Targets are resolved concurrently with a
ThreadPoolExecutor of size MAX_WORKERS. This is safe
because each target's work is independent. Combined
with the DiskCache layer in EnsemblClient, a cold
request drops from ~3 minutes to ~20-30 seconds, and a
warm request completes in under a second.

Result ordering is preserved: nodes, relationships, and
evidence appear in the same order they would have
appeared in the sequential version.

Design decisions (locked)
-------------------------

M1(b)  Emit BOTH gene nodes and protein nodes.
M2(b)  Minimal fields: symbol, Ensembl ID, UniProt accession.
M3(a)  RelationshipType.ENCODES added to Phase 01.
M4(a)  disease -> gene and disease -> protein use
       RelationshipType.ASSOCIATED_WITH.
M5(a)  No ChEMBL in Phase 05.
M6(a)  Emit the gene node even if UniProt resolution
       fails; skip only the protein node. Record the skip
       in metadata.
M7(a)  Top 10 Open Targets targets.

P-F(a) Parallelize with 10 workers.
P-G(b) Do not cache Open Targets.

What this module does NOT do
----------------------------

- It does not call ChEMBL.
- It does not call GTEx, HPA, or Monarch.
- It does not attach pathway or mechanism nodes.
- It does not run protein or molecule feature
  extraction (ESM-2, ChemBERTa).
- It does not run EvidenceReasoningEngine.

Conventions
-----------

- Dataclasses from Phase 01 schemas are used directly.
- Reuses OpenTargetsClient and EnsemblClient.
- No new external libraries. `concurrent.futures` is stdlib.
- All returned structures are serializable plain dicts.
"""

from __future__ import annotations

from concurrent.futures import (
    ThreadPoolExecutor,
    as_completed,
)
from dataclasses import asdict
from typing import Any, Dict, List, Optional

from app.data.sources.ensembl import EnsemblClient
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
)
from app.drug_development.sources.open_targets import (
    OpenTargetsClient,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SOURCE_OT = "Open Targets"
SOURCE_ENSEMBL = "Ensembl"
SOURCE_UNIPROT = "UniProt"

GENE_NODE_PREFIX = "gene:"
PROTEIN_NODE_PREFIX = "protein:"
DISEASE_NODE_PREFIX = "disease:"

#: Same cap as Phase 03 and Phase 04.
MAX_TARGETS = 10

#: Number of targets resolved concurrently.
MAX_WORKERS = 10


# ---------------------------------------------------------------------------
# Mapper
# ---------------------------------------------------------------------------


class MolecularContextMapper:
    """
    Maps a DiseaseIdentity to gene and protein ImpactNodes
    and Relationships.
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

    def map_disease_to_molecular_entities(
        self,
        disease: DiseaseIdentity,
    ) -> Dict[str, Any]:
        """
        Build the molecular layer for one disease.
        """

        disease_node_id = self._disease_node_id(disease)

        if disease_node_id is None:
            return self._empty(
                reason=(
                    "Disease has no identifiers; cannot build "
                    "a disease node."
                )
            )

        ot_disease_id = self._pick_ot_disease_id(disease)

        if ot_disease_id is None:
            return self._empty(
                disease_node_id=disease_node_id,
                reason=(
                    "No Open Targets-compatible identifier "
                    "available for this disease."
                ),
            )

        # ---- Query Open Targets ----------------------------------
        try:
            ot_targets = self._fetch_top_targets(
                ot_disease_id, MAX_TARGETS
            )
        except RuntimeError as exc:
            return self._empty(
                disease_node_id=disease_node_id,
                reason=(
                    "Open Targets request failed: "
                    f"{exc}"
                ),
            )

        if not ot_targets:
            return self._empty(
                disease_node_id=disease_node_id,
                reason=(
                    f"Open Targets returned no associated "
                    f"targets for {ot_disease_id}."
                ),
                extra_metadata={
                    "disease_id": ot_disease_id,
                    "targets_queried": 0,
                },
            )

        # ---- Parallel per-target processing ----------------------
        per_target = self._process_targets_parallel(
            ot_targets,
            disease,
            disease_node_id,
        )

        nodes: List[ImpactNode] = []
        relationships: List[Relationship] = []
        evidence_records: List[ImpactEvidence] = []
        unresolved_genes: List[str] = []

        for result in per_target:
            if result is None:
                continue

            nodes.extend(result["nodes"])
            relationships.extend(result["relationships"])
            evidence_records.extend(result["evidence"])

            if result.get("unresolved_gene"):
                unresolved_genes.append(result["unresolved_gene"])

        if not nodes:
            return self._empty(
                disease_node_id=disease_node_id,
                reason=(
                    "No molecular entity could be produced "
                    "for this disease."
                ),
                extra_metadata={
                    "disease_id": ot_disease_id,
                    "targets_queried": len(ot_targets),
                },
            )

        gene_count = sum(
            1 for n in nodes
            if n.node_type == NodeType.GENE
        )
        protein_count = sum(
            1 for n in nodes
            if n.node_type == NodeType.PROTEIN
        )

        return {
            "disease_node_id": disease_node_id,
            "nodes": [asdict(n) for n in nodes],
            "relationships": [asdict(r) for r in relationships],
            "evidence": [asdict(e) for e in evidence_records],
            "sources": [SOURCE_OT, SOURCE_ENSEMBL, SOURCE_UNIPROT],
            "found": True,
            "metadata": {
                "disease_id": ot_disease_id,
                "targets_queried": len(ot_targets),
                "genes_emitted": gene_count,
                "proteins_emitted": protein_count,
                "unresolved_genes": unresolved_genes,
            },
            "reason": None,
        }

    # ------------------------------------------------------------------
    # Parallel orchestration
    # ------------------------------------------------------------------

    def _process_targets_parallel(
        self,
        ot_targets: List[Dict[str, Any]],
        disease: DiseaseIdentity,
        disease_node_id: str,
    ) -> List[Optional[Dict[str, Any]]]:
        """
        Run _process_target on every target concurrently.

        Returns a list of the same length as ot_targets, in
        the original order. Entries are None for malformed
        targets or targets whose processing raised.
        """

        results: List[Optional[Dict[str, Any]]] = (
            [None] * len(ot_targets)
        )

        with ThreadPoolExecutor(
            max_workers=MAX_WORKERS
        ) as pool:
            futures = {
                pool.submit(
                    self._process_target,
                    target,
                    disease,
                    disease_node_id,
                ): index
                for index, target in enumerate(ot_targets)
            }

            for future in as_completed(futures):
                index = futures[future]
                try:
                    results[index] = future.result()
                except Exception:
                    results[index] = None

        return results

    def _process_target(
        self,
        target: Dict[str, Any],
        disease: DiseaseIdentity,
        disease_node_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Process a single Open Targets target into gene and
        (optionally) protein entities plus their
        relationships and evidence.

        Never raises: any failure is contained so one bad
        target does not abort the whole request.
        """

        symbol = target.get("symbol")
        ot_target_id = target.get("id")
        ot_score = target.get("score")

        if not symbol or not ot_target_id:
            return None

        nodes: List[ImpactNode] = []
        relationships: List[Relationship] = []
        evidence_records: List[ImpactEvidence] = []
        unresolved_gene: Optional[str] = None

        # ---- Enrich via Ensembl ---------------------------------
        ensembl_record = None
        try:
            ensembl_record = self.ensembl.lookup_gene(symbol)
        except Exception:
            ensembl_record = None

        ensembl_id = None
        gene_name = symbol

        if isinstance(ensembl_record, dict):
            ensembl_id = ensembl_record.get("id")
            gene_name = (
                ensembl_record.get("display_name") or symbol
            )

        gene_node_id = f"{GENE_NODE_PREFIX}{symbol}"

        gene_node = ImpactNode(
            node_id=gene_node_id,
            node_type=NodeType.GENE,
            name=symbol,
            identifier=ensembl_id or ot_target_id,
            description=(
                gene_name if gene_name != symbol else None
            ),
            evidence_ids=[],
            metadata={
                "gene_symbol": symbol,
                "ensembl_id": ensembl_id,
                "open_targets_id": ot_target_id,
                "open_targets_score": ot_score,
                "source": SOURCE_OT,
            },
        )
        nodes.append(gene_node)

        # ---- Disease -> gene evidence ----------------------------
        gene_ev_id = f"ev:ot:gene:{symbol}"

        gene_evidence = ImpactEvidence(
            evidence_id=gene_ev_id,
            source=SOURCE_OT,
            relationship_description=(
                f"Open Targets reports {symbol} as an "
                f"associated target of "
                f"{disease.canonical_name or disease.query}."
            ),
            evidence_level=EvidenceLevel.ASSOCIATION,
            reference=EvidenceReference(
                source=SOURCE_OT,
                source_id=ot_target_id,
                source_type="database",
                url=None,
                metadata={
                    "open_targets_score": ot_score,
                },
            ),
            identifiers={
                "gene_symbol": symbol,
                "ensembl_id": ensembl_id or "",
                "open_targets_id": ot_target_id,
            },
            metadata={
                "open_targets_score": ot_score,
            },
        )
        evidence_records.append(gene_evidence)

        relationships.append(
            Relationship(
                source_id=disease_node_id,
                target_id=gene_node_id,
                relationship_type=(
                    RelationshipType.ASSOCIATED_WITH
                ),
                evidence_ids=[gene_ev_id],
                evidence_level=EvidenceLevel.ASSOCIATION,
                description=(
                    f"{disease.canonical_name or disease.query} "
                    f"is associated with {symbol} "
                    f"(Open Targets)."
                ),
                metadata={
                    "open_targets_id": ot_target_id,
                    "open_targets_score": ot_score,
                    "source": SOURCE_OT,
                },
            )
        )

        # ---- Resolve UniProt protein -----------------------------
        if not ensembl_id:
            unresolved_gene = symbol
            return {
                "nodes": nodes,
                "relationships": relationships,
                "evidence": evidence_records,
                "unresolved_gene": unresolved_gene,
            }

        uniprot_resolution = None
        try:
            uniprot_resolution = (
                self.ensembl.resolve_reviewed_uniprot_accession(
                    ensembl_id
                )
            )
        except Exception:
            uniprot_resolution = None

        if not uniprot_resolution:
            unresolved_gene = symbol
            return {
                "nodes": nodes,
                "relationships": relationships,
                "evidence": evidence_records,
                "unresolved_gene": unresolved_gene,
            }

        accession = uniprot_resolution.get("accession")
        if not accession:
            unresolved_gene = symbol
            return {
                "nodes": nodes,
                "relationships": relationships,
                "evidence": evidence_records,
                "unresolved_gene": unresolved_gene,
            }

        protein_node_id = f"{PROTEIN_NODE_PREFIX}{accession}"

        protein_node = ImpactNode(
            node_id=protein_node_id,
            node_type=NodeType.PROTEIN,
            name=accession,
            identifier=accession,
            description=uniprot_resolution.get("protein_name"),
            evidence_ids=[],
            metadata={
                "uniprot_accession": accession,
                "uniprot_id": uniprot_resolution.get("uniprot_id"),
                "organism": uniprot_resolution.get("organism"),
                "entry_type": uniprot_resolution.get("entry_type"),
                "reviewed": uniprot_resolution.get("reviewed"),
                "gene_symbol": symbol,
                "ensembl_id": ensembl_id,
                "source": SOURCE_UNIPROT,
            },
        )
        nodes.append(protein_node)

        # ---- Disease -> protein evidence ------------------------
        protein_ev_id = f"ev:uniprot:protein:{accession}"

        protein_evidence = ImpactEvidence(
            evidence_id=protein_ev_id,
            source=SOURCE_UNIPROT,
            relationship_description=(
                f"{symbol} resolves to the reviewed UniProt "
                f"entry {accession} "
                f"({uniprot_resolution.get('protein_name') or 'protein name unavailable'})."
            ),
            evidence_level=EvidenceLevel.DIRECT,
            reference=EvidenceReference(
                source=SOURCE_UNIPROT,
                source_id=accession,
                source_type="database",
                url=(
                    "https://www.uniprot.org/uniprotkb/"
                    f"{accession}"
                ),
                metadata={
                    "reviewed": uniprot_resolution.get("reviewed"),
                    "organism": uniprot_resolution.get("organism"),
                },
            ),
            identifiers={
                "uniprot_accession": accession,
                "ensembl_id": ensembl_id,
                "gene_symbol": symbol,
            },
            metadata={
                "protein_name": uniprot_resolution.get("protein_name"),
                "entry_type": uniprot_resolution.get("entry_type"),
                "reviewed": uniprot_resolution.get("reviewed"),
                "organism": uniprot_resolution.get("organism"),
            },
        )
        evidence_records.append(protein_evidence)

        relationships.append(
            Relationship(
                source_id=disease_node_id,
                target_id=protein_node_id,
                relationship_type=(
                    RelationshipType.ASSOCIATED_WITH
                ),
                evidence_ids=[protein_ev_id],
                evidence_level=EvidenceLevel.DIRECT,
                description=(
                    f"{disease.canonical_name or disease.query} "
                    f"is associated with protein {accession} "
                    f"via gene {symbol}."
                ),
                metadata={
                    "gene_symbol": symbol,
                    "uniprot_accession": accession,
                    "source": SOURCE_UNIPROT,
                },
            )
        )

        # ---- Gene -> protein (ENCODES) --------------------------
        relationships.append(
            Relationship(
                source_id=gene_node_id,
                target_id=protein_node_id,
                relationship_type=RelationshipType.ENCODES,
                evidence_ids=[protein_ev_id],
                evidence_level=EvidenceLevel.DIRECT,
                description=f"{symbol} encodes {accession}.",
                metadata={
                    "gene_symbol": symbol,
                    "uniprot_accession": accession,
                    "source": SOURCE_UNIPROT,
                },
            )
        )

        return {
            "nodes": nodes,
            "relationships": relationships,
            "evidence": evidence_records,
            "unresolved_gene": unresolved_gene,
        }

    # ------------------------------------------------------------------
    # Open Targets helpers
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
                    return value

        return None

    def _fetch_top_targets(
        self,
        ot_disease_id: str,
        size: int,
    ) -> List[Dict[str, Any]]:
        graphql_query = """
        query DiseaseTargets($id: String!, $size: Int!) {
          disease(efoId: $id) {
            id
            name
            associatedTargets(
              page: {index: 0, size: $size}
            ) {
              count
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

        ot_id_arg = ot_disease_id.replace(":", "_")

        data = self.open_targets.query(
            graphql_query,
            {"id": ot_id_arg, "size": size},
        )

        disease = data.get("disease") or {}
        associations = (
            disease.get("associatedTargets") or {}
        )
        rows = associations.get("rows") or []

        targets: List[Dict[str, Any]] = []

        for row in rows:
            target = row.get("target") or {}
            symbol = target.get("approvedSymbol")
            target_id = target.get("id")

            if not symbol or not target_id:
                continue

            targets.append(
                {
                    "id": target_id,
                    "symbol": symbol,
                    "score": row.get("score"),
                }
            )

        return targets

    # ------------------------------------------------------------------
    # Node helpers
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
    def _empty(
        disease_node_id: Optional[str] = None,
        reason: Optional[str] = None,
        extra_metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        return {
            "disease_node_id": disease_node_id,
            "nodes": [],
            "relationships": [],
            "evidence": [],
            "sources": [SOURCE_OT, SOURCE_ENSEMBL, SOURCE_UNIPROT],
            "found": False,
            "metadata": extra_metadata or {},
            "reason": reason,
        }
