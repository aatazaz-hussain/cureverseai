"""
CureVerseAI — Drug Development
Pathway mapper.

Given a resolved DiseaseIdentity, produce the pathway
layer of the Biological Impact Graph:

    Disease  --alters-->         Pathway
    Protein  --participates_in--> Pathway

Data flow
---------

    Disease
      |
      v
    Open Targets: disease -> top-N targets
      |
      v
    Ensembl + UniProt: gene -> protein (reuses Phase 05
                                  resolution, cache warm)
      |
      v
    Reactome: protein -> pathways
      |
      v
    Top N pathways per protein
      |
      v
    Deduplicate across proteins
      |
      v
    ImpactNodes + Relationships + Evidence

Design decisions (locked)
-------------------------

R4     Pathways only. No synthesized mechanism nodes.
R-B(b) Top 5 pathways per protein.
R-C    protein --participates_in--> pathway.
R-D    disease --alters--> pathway.
R-E    10 parallel workers; Reactome responses are
       cached on disk with a 30-day TTL.

Evidence semantics
------------------

Each pathway carries two relationships:

    disease --alters--> pathway     (evidence: Reactome)
    protein --participates_in--> pathway  (evidence: Reactome)

The disease -> pathway relationship is asserted because
the disease has associated proteins that participate in
that pathway. It is not a direct experimental claim; its
evidence_level is ASSOCIATION.

The protein -> pathway relationship is a direct Reactome
annotation; its evidence_level is DIRECT.

What this module does NOT do
----------------------------

- It does not synthesize "mechanism" nodes. Per R4,
  pathways ARE the mechanism layer. Disease mechanisms
  are visible through pathway names and descriptions.
- It does not call ChEMBL, GTEx, HPA, or Monarch.
- It does not weight or score pathways. Rank is preserved
  from Reactome's ordering, which is by depth from root.

Conventions
-----------

- Dataclasses from Phase 01 schemas are used directly.
- Reuses OpenTargetsClient, EnsemblClient, and
  ReactomeClient. No new external libraries.
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
from app.data.sources.reactome import ReactomeClient
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
SOURCE_REACTOME = "Reactome"

PATHWAY_NODE_PREFIX = "pathway:"
PROTEIN_NODE_PREFIX = "protein:"
DISEASE_NODE_PREFIX = "disease:"

#: Same cap as Phases 03, 04, 05.
MAX_TARGETS = 10

#: Parallel workers for per-protein Reactome queries.
MAX_WORKERS = 10

#: Reactome returns up to ~50 pathways per protein, ordered
#: by depth. We keep the most specific ones (deepest) as
#: they are more likely to describe a mechanism rather than
#: a broad biological process.
TOP_PATHWAYS_PER_PROTEIN = 5


# ---------------------------------------------------------------------------
# Mapper
# ---------------------------------------------------------------------------


class PathwayMapper:
    """
    Maps a DiseaseIdentity to pathway ImpactNodes and
    Relationships using Open Targets + Ensembl + Reactome.
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

    def map_disease_to_pathways(
        self,
        disease: DiseaseIdentity,
    ) -> Dict[str, Any]:
        """
        Build the pathway layer for one disease.
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

        try:
            ot_targets = self._fetch_top_targets(
                ot_disease_id, MAX_TARGETS
            )
        except RuntimeError as exc:
            return self._empty(
                disease_node_id=disease_node_id,
                reason=f"Open Targets request failed: {exc}",
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

        # ---- Parallel per-protein pathway lookup ----------------
        per_target = self._process_targets_parallel(
            ot_targets,
            disease,
            disease_node_id,
        )

        nodes: List[ImpactNode] = []
        relationships: List[Relationship] = []
        evidence_records: List[ImpactEvidence] = []

        # Deduplicate pathway nodes by st_id
        pathway_nodes_by_id: Dict[str, ImpactNode] = {}
        # Track which proteins point at each pathway
        pathway_to_proteins: Dict[str, List[str]] = {}

        # Track protein nodes Phase 06 emits so they can be
        # merged into the graph alongside pathway nodes.
        protein_nodes_by_id: Dict[str, ImpactNode] = {}

        for result in per_target:
            if result is None:
                continue

            for node in result.get("protein_nodes") or []:
                if node.node_id not in protein_nodes_by_id:
                    protein_nodes_by_id[node.node_id] = node

            for node in result["pathway_nodes"]:
                # Only add node once
                if node.node_id not in pathway_nodes_by_id:
                    pathway_nodes_by_id[node.node_id] = node

            for pid, protein in result["protein_to_pathway"]:
                pathway_to_proteins.setdefault(pid, [])
                if protein not in pathway_to_proteins[pid]:
                    pathway_to_proteins[pid].append(protein)

            for rel in result["participates_relationships"]:
                relationships.append(rel)

            for ev in result["evidence_records"]:
                # Only add evidence once per unique id
                if not any(
                    e.evidence_id == ev.evidence_id
                    for e in evidence_records
                ):
                    evidence_records.append(ev)

        nodes.extend(protein_nodes_by_id.values())
        nodes.extend(pathway_nodes_by_id.values())

        if not pathway_nodes_by_id:
            return self._empty(
                disease_node_id=disease_node_id,
                reason=(
                    "No Reactome pathway could be mapped for "
                    "any associated target."
                ),
                extra_metadata={
                    "disease_id": ot_disease_id,
                    "targets_queried": len(ot_targets),
                },
            )

        # ---- Disease -> pathway relationships -------------------
        # Emitted here (not per-target) because they need
        # access to the full deduplicated node set.
        for pid, proteins in pathway_to_proteins.items():
            evidence_id = f"ev:reactome:pathway:{pid}"

            # Evidence already exists if any protein added it;
            # but the disease -> pathway evidence is its own.
            if not any(
                e.evidence_id == evidence_id
                for e in evidence_records
            ):
                node = pathway_nodes_by_id.get(
                    f"{PATHWAY_NODE_PREFIX}{pid}"
                )
                display = (
                    node.name if node else pid
                )

                evidence_records.append(
                    ImpactEvidence(
                        evidence_id=evidence_id,
                        source=SOURCE_REACTOME,
                        relationship_description=(
                            f"{disease.canonical_name or disease.query} "
                            f"alters pathway {display} "
                            f"({pid}) via {len(proteins)} "
                            f"associated protein(s)."
                        ),
                        evidence_level=EvidenceLevel.ASSOCIATION,
                        reference=EvidenceReference(
                            source=SOURCE_REACTOME,
                            source_id=pid,
                            source_type="database",
                            url=(
                                "https://reactome.org/content/detail/"
                                f"{pid}"
                            ),
                            metadata={},
                        ),
                        identifiers={
                            "reactome_id": pid,
                        },
                        metadata={
                            "supporting_proteins": proteins,
                            "supporting_protein_count": len(proteins),
                        },
                    )
                )

            relationships.append(
                Relationship(
                    source_id=disease_node_id,
                    target_id=f"{PATHWAY_NODE_PREFIX}{pid}",
                    relationship_type=RelationshipType.ALTERS,
                    evidence_ids=[evidence_id],
                    evidence_level=EvidenceLevel.ASSOCIATION,
                    description=(
                        f"{disease.canonical_name or disease.query} "
                        f"alters Reactome pathway {pid}."
                    ),
                    metadata={
                        "reactome_id": pid,
                        "supporting_protein_count": len(proteins),
                        "source": SOURCE_REACTOME,
                    },
                )
            )

        return {
            "disease_node_id": disease_node_id,
            "nodes": [asdict(n) for n in nodes],
            "relationships": [asdict(r) for r in relationships],
            "evidence": [asdict(e) for e in evidence_records],
            "sources": [
                SOURCE_OT,
                SOURCE_ENSEMBL,
                SOURCE_UNIPROT,
                SOURCE_REACTOME,
            ],
            "found": True,
            "metadata": {
                "disease_id": ot_disease_id,
                "targets_queried": len(ot_targets),
                "pathways_kept": len(pathway_nodes_by_id),
                "top_pathways_per_protein": TOP_PATHWAYS_PER_PROTEIN,
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
                ): i
                for i, target in enumerate(ot_targets)
            }

            for future in as_completed(futures):
                i = futures[future]
                try:
                    results[i] = future.result()
                except Exception:
                    results[i] = None

        return results

    def _process_target(
        self,
        target: Dict[str, Any],
        disease: DiseaseIdentity,
        disease_node_id: str,
    ) -> Optional[Dict[str, Any]]:
        """
        For one gene: resolve its protein, fetch Reactome
        pathways, build pathway nodes and participates_in
        relationships.

        Returns None if the target cannot be resolved to a
        protein.
        """

        symbol = target.get("symbol")
        if not symbol:
            return None

        # ---- Resolve Ensembl -> UniProt (cache-warm) -----------
        ensembl_id = None
        try:
            ensembl_record = self.ensembl.lookup_gene(symbol)
            if isinstance(ensembl_record, dict):
                ensembl_id = ensembl_record.get("id")
        except Exception:
            return None

        if not ensembl_id:
            return None

        uniprot_resolution = None
        try:
            uniprot_resolution = (
                self.ensembl.resolve_reviewed_uniprot_accession(
                    ensembl_id
                )
            )
        except Exception:
            return None

        if not uniprot_resolution:
            return None

        accession = uniprot_resolution.get("accession")
        if not accession:
            return None

        # ---- Fetch pathways from Reactome ----------------------
        try:
            pathways_result = (
                self.reactome.get_pathways_for_protein(accession)
            )
        except RuntimeError:
            return None

        if not pathways_result.get("found"):
            return None

        pathways = pathways_result["pathways"][
            :TOP_PATHWAYS_PER_PROTEIN
        ]

        pathway_nodes: List[ImpactNode] = []
        protein_nodes: List[ImpactNode] = []
        participates_relationships: List[Relationship] = []
        evidence_records: List[ImpactEvidence] = []
        protein_to_pathway: List[tuple] = []

        protein_node_id = f"{PROTEIN_NODE_PREFIX}{accession}"

        # Emit the protein node here too, so the participates_in
        # relationships have a matching node in the final graph.
        # If Phase 05 (molecular) already emitted an identical
        # protein node, Phase 08's dedup will keep Phase 05's
        # version because "molecular" precedes "pathways" in
        # LAYER_ORDER. Either way, integrity holds.
        protein_nodes.append(
            ImpactNode(
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
                    "emitted_by": "pathway_mapping",
                },
            )
        )

        for pw in pathways:
            st_id = pw["st_id"]
            display = pw["display_name"]

            pathway_node_id = f"{PATHWAY_NODE_PREFIX}{st_id}"

            node = ImpactNode(
                node_id=pathway_node_id,
                node_type=NodeType.PATHWAY,
                name=display,
                identifier=st_id,
                description=None,
                evidence_ids=[],
                metadata={
                    "reactome_id": st_id,
                    "reactome_db_id": pw.get("db_id"),
                    "display_name": display,
                    "species": pw.get("species_name"),
                    "is_in_disease": pw.get("is_in_disease"),
                    "is_inferred": pw.get("is_inferred"),
                    "has_diagram": pw.get("has_diagram"),
                    "has_ehld": pw.get("has_ehld"),
                    "release_date": pw.get("release_date"),
                    "last_updated_date": pw.get("last_updated_date"),
                    "schema_class": pw.get("schema_class"),
                    "source": SOURCE_REACTOME,
                },
            )
            pathway_nodes.append(node)

            # Protein -> pathway evidence + relationship
            ev_id = (
                f"ev:reactome:participates:{accession}:{st_id}"
            )

            evidence_records.append(
                ImpactEvidence(
                    evidence_id=ev_id,
                    source=SOURCE_REACTOME,
                    relationship_description=(
                        f"{symbol} ({accession}) participates in "
                        f"Reactome pathway {display} ({st_id})."
                    ),
                    evidence_level=EvidenceLevel.DIRECT,
                    reference=EvidenceReference(
                        source=SOURCE_REACTOME,
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
                        "uniprot_accession": accession,
                        "gene_symbol": symbol,
                    },
                    metadata={
                        "display_name": display,
                        "species": pw.get("species_name"),
                        "is_in_disease": pw.get("is_in_disease"),
                    },
                )
            )

            participates_relationships.append(
                Relationship(
                    source_id=protein_node_id,
                    target_id=pathway_node_id,
                    relationship_type=(
                        RelationshipType.PARTICIPATES_IN
                    ),
                    evidence_ids=[ev_id],
                    evidence_level=EvidenceLevel.DIRECT,
                    description=(
                        f"{accession} participates in "
                        f"{display} ({st_id})."
                    ),
                    metadata={
                        "reactome_id": st_id,
                        "uniprot_accession": accession,
                        "source": SOURCE_REACTOME,
                    },
                )
            )

            protein_to_pathway.append((st_id, accession))

        return {
            "pathway_nodes": pathway_nodes,
            "protein_nodes": protein_nodes,
            "participates_relationships": participates_relationships,
            "evidence_records": evidence_records,
            "protein_to_pathway": protein_to_pathway,
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
              rows {
                target { id approvedSymbol }
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
        rows = (
            disease.get("associatedTargets") or {}
        ).get("rows") or []

        out: List[Dict[str, Any]] = []
        for row in rows:
            t = row.get("target") or {}
            symbol = t.get("approvedSymbol")
            tid = t.get("id")
            if not symbol or not tid:
                continue
            out.append(
                {"id": tid, "symbol": symbol,
                 "score": row.get("score")}
            )
        return out

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
            "sources": [
                SOURCE_OT, SOURCE_ENSEMBL,
                SOURCE_UNIPROT, SOURCE_REACTOME,
            ],
            "found": False,
            "metadata": extra_metadata or {},
            "reason": reason,
        }
