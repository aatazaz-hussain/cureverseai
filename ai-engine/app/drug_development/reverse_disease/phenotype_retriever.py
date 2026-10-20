"""
CureVerseAI — Drug Development
Workflow 02 — Reverse Disease Engineering
Phenotype Retriever (layer module).

Given a resolved DiseaseIdentity, retrieve the
disease-associated phenotypes and emit the first W02 graph
layer:

    disease  --associated_with-->  phenotype

Data sources
------------

Primary   : Open Targets (disease.phenotypes.rows.phenotypeHPO)
Enrichment: EBI OLS4 HPO (only when Open Targets omits a
            description for a specific HPO term)

Both are already wired and verified at the W02 source layer:

    app.drug_development.sources.open_targets.OpenTargetsClient
    app.drug_development.reverse_disease.sources.hpo.HPOClient

Row filtering rules (per W02 Phase 1 diagnostic, File 8a)
---------------------------------------------------------

Open Targets' disease.phenotypes.rows can contain rows where:

    phenotypeHPO is null and phenotypeEFO is set

This produces a self-loop if naively emitted (e.g. asthma
appearing as its own phenotype). Those rows are dropped.

Inheritance-mode terms (e.g. HP:0000006 "Autosomal dominant
inheritance", HP:0001426 "Non-Mendelian inheritance") are
NOT clinical manifestations in the W02 sense, but the spec
requires that no retrieved record be silently dropped. They
are therefore kept as phenotype nodes, tagged via node
metadata (`inheritance_like: True`) so downstream layers can
choose how to treat them. The tag is derived from HPO's own
`namespace` list — never invented.

Output shape
------------

Mirrors W01's layer modules exactly (see
drug_development/disease/biological_systems.py):

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

Downstream code (graph builder, evidence integrator) expects
this shape from every layer module.

No fabrication
--------------

A disease with zero Open Targets phenotypes returns
found=False and an empty graph layer with a clear `reason`.
Nothing is invented to fill the layer.

Transport failures propagate. A RuntimeError from Open
Targets or OLS4 is NOT caught here — the service layer
records it in provenance.source_failures.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, List, Optional

from app.drug_development.reverse_disease.sources.hpo import (
    HPOClient,
    normalize_hp_id,
)
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


SOURCE_NAME = "Open Targets"
ENRICHMENT_SOURCE = "OLS4"

DISEASE_NODE_PREFIX = "disease:"
PHENOTYPE_NODE_PREFIX = "phenotype:"

#: Cap on how many phenotypes we request from Open Targets.
#: Open Targets' phenotype layer is small (asthma: 5 rows);
#: a 50-row ceiling is comfortable headroom.
_MAX_PHENOTYPE_ROWS = 50

#: Prefix of the HPO namespace value that marks inheritance
#: terms. OLS4 has been observed to label HP:0000006 and
#: HP:0001426 with namespace values like "inheritance".
_INHERITANCE_NAMESPACE_HINT = "inherit"


# ---------------------------------------------------------------------------
# Retriever
# ---------------------------------------------------------------------------


class PhenotypeRetriever:
    """
    Retrieves disease-associated phenotypes from Open Targets
    and emits a W02 phenotype layer.
    """

    def __init__(
        self,
        open_targets_client: Optional[OpenTargetsClient] = None,
        hpo_client: Optional[HPOClient] = None,
    ):
        self.open_targets = (
            open_targets_client or OpenTargetsClient()
        )
        self.hpo = hpo_client or HPOClient()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def retrieve(
        self,
        disease: DiseaseIdentity,
    ) -> Dict[str, Any]:
        """
        Build the phenotype layer for one disease.

        Never raises for a disease with no retrievable
        phenotypes. RuntimeError from a source propagates.
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
                    "No Open Targets-compatible disease "
                    "identifier available for phenotype "
                    "lookup."
                ),
            )

        # ---- Query Open Targets -------------------------------
        rows = self._fetch_open_targets_rows(ot_disease_id)

        if not rows:
            return self._empty_result(
                disease_node_id=disease_node_id,
                reason=(
                    "Open Targets returned no phenotype rows "
                    f"for {ot_disease_id}."
                ),
                extra_metadata={
                    "open_targets_disease_id": ot_disease_id,
                    "rows_returned": 0,
                },
            )

        # ---- Build the layer ----------------------------------
        nodes: List[ImpactNode] = []
        relationships: List[Relationship] = []
        evidence_records: List[ImpactEvidence] = []

        dropped_self_loop = 0
        dropped_malformed = 0
        enriched_count = 0
        inheritance_like_count = 0

        for row in rows:
            hpo = row.get("phenotypeHPO")

            if not hpo or not isinstance(hpo, dict):
                # phenotypeHPO is null: this row refers to the
                # disease itself (phenotypeEFO). Drop.
                dropped_self_loop += 1
                continue

            raw_hp_id = hpo.get("id")
            name = hpo.get("name")
            description = hpo.get("description")
            namespace = hpo.get("namespace")

            if not raw_hp_id or not name:
                dropped_malformed += 1
                continue

            hp_id = normalize_hp_id(str(raw_hp_id))

            if not hp_id.startswith("HP:"):
                dropped_malformed += 1
                continue

            node_id = self._phenotype_node_id(hp_id)

            # ---- Optional enrichment via OLS4 ----------------
            # Per Decision 8D-B: only when Open Targets omits
            # a description. When that happens we ask OLS4 for
            # the HPO term's own definition. This is a
            # fallback and may itself return None — some HPO
            # terms have no recorded definition.
            enriched = False
            description_source = (
                "open_targets" if description else "unavailable"
            )
            synonyms: list = []

            if not description:
                term = self.hpo.get_term(hp_id)
                if term.get("found"):
                    term_desc = term.get("description")
                    if term_desc:
                        description = term_desc
                        description_source = "ols4"
                        enriched = True
                        enriched_count += 1
                    if not namespace:
                        namespace = term.get("namespace")
                    syns = term.get("synonyms")
                    if isinstance(syns, list):
                        synonyms = [
                            str(s) for s in syns if s
                        ]

            inheritance_like = self._is_inheritance_like(
                namespace
            )
            if inheritance_like:
                inheritance_like_count += 1

            # ---- Phenotype node ------------------------------
            node = ImpactNode(
                node_id=node_id,
                node_type=NodeType.PHENOTYPE,
                name=str(name),
                identifier=hp_id,
                description=description,
                evidence_ids=[],
                metadata={
                    "hpo_id": hp_id,
                    "raw_hpo_id": str(raw_hp_id),
                    "namespace": list(namespace or []),
                    "inheritance_like": inheritance_like,
                    "enriched_via_ols4": enriched,
                    "description_source": description_source,
                    "synonyms": list(synonyms),
                    "source": SOURCE_NAME,
                },
            )
            nodes.append(node)

            # ---- Evidence record -----------------------------
            evidence_id = f"ev:ot:phenotype:{hp_id}"

            evidence = ImpactEvidence(
                evidence_id=evidence_id,
                source=SOURCE_NAME,
                relationship_description=(
                    f"{disease.canonical_name or disease.query} "
                    f"is associated with the phenotype "
                    f"'{name}' ({hp_id}) in Open Targets."
                ),
                evidence_level=EvidenceLevel.ASSOCIATION,
                reference=EvidenceReference(
                    source=SOURCE_NAME,
                    source_id=ot_disease_id,
                    source_type="database",
                    url=None,
                    metadata={
                        "hpo_id": hp_id,
                        "hpo_name": str(name),
                    },
                ),
                identifiers={
                    "open_targets_disease_id": ot_disease_id,
                    "hpo_id": hp_id,
                },
                metadata={
                    "namespace": list(namespace or []),
                    "inheritance_like": inheritance_like,
                },
            )
            evidence_records.append(evidence)

            # ---- Relationship ---------------------------------
            relationship = Relationship(
                source_id=disease_node_id,
                target_id=node_id,
                relationship_type=RelationshipType.ASSOCIATED_WITH,
                evidence_ids=[evidence_id],
                evidence_level=EvidenceLevel.ASSOCIATION,
                support_class=SupportClass.SUPPORTED_ASSOCIATION,
                description=(
                    f"{disease.canonical_name or disease.query} "
                    f"is associated with '{name}'."
                ),
                metadata={
                    "hpo_id": hp_id,
                    "inheritance_like": inheritance_like,
                    "source": SOURCE_NAME,
                },
            )
            relationships.append(relationship)

        # ---- Zero useful rows after filtering -----------------
        if not nodes:
            return self._empty_result(
                disease_node_id=disease_node_id,
                reason=(
                    "Open Targets returned phenotype rows, but "
                    "none carried a usable phenotypeHPO record."
                ),
                extra_metadata={
                    "open_targets_disease_id": ot_disease_id,
                    "rows_returned": len(rows),
                    "dropped_self_loop": dropped_self_loop,
                    "dropped_malformed": dropped_malformed,
                },
            )

        # ---- Assemble result ----------------------------------
        return {
            "disease_node_id": disease_node_id,
            "nodes": [asdict(n) for n in nodes],
            "relationships": [asdict(r) for r in relationships],
            "evidence": [asdict(e) for e in evidence_records],
            "sources": [SOURCE_NAME, ENRICHMENT_SOURCE],
            "found": True,
            "metadata": {
                "open_targets_disease_id": ot_disease_id,
                "rows_returned": len(rows),
                "phenotypes_kept": len(nodes),
                "dropped_self_loop": dropped_self_loop,
                "dropped_malformed": dropped_malformed,
                "enriched_via_ols4": enriched_count,
                "inheritance_like": inheritance_like_count,
            },
            "reason": None,
        }

    # ------------------------------------------------------------------
    # Open Targets fetch
    # ------------------------------------------------------------------

    def _fetch_open_targets_rows(
        self,
        ot_disease_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Query Open Targets for disease.phenotypes.rows with
        the HPO sub-selection.

        Returns the raw `rows` list, or [] when the disease
        has no phenotypes.

        Uses the shared OpenTargetsClient. The GraphQL query
        is defined here because it is W02-specific; the
        client only handles transport.
        """
        graphql_query = """
        query W02Phenotypes($efoId: String!) {
          disease(efoId: $efoId) {
            id
            name
            phenotypes {
              count
              rows {
                phenotypeHPO {
                  id
                  name
                  description
                }
              }
            }
          }
        }
        """

        data = self.open_targets.query(
            graphql_query,
            {"efoId": ot_disease_id},
        )

        # Detect silent GraphQL failures. Open Targets'
        # GraphQL surface can return HTTP 200 with a partial
        # response when a sub-selection is invalid, in which
        # case `disease` is null. That is NOT an empty
        # phenotype list — it is a query error. Distinguish
        # the two, otherwise the layer reports a false
        # "no phenotypes" reason.
        if data is None:
            raise RuntimeError(
                "Open Targets returned no data for phenotype "
                f"query on {ot_disease_id}."
            )

        disease = data.get("disease")

        if disease is None:
            raise RuntimeError(
                "Open Targets returned no disease object for "
                f"phenotype query on {ot_disease_id}. "
                "This usually indicates a rejected GraphQL "
                "sub-selection, not a missing disease."
            )

        phenotypes = disease.get("phenotypes")

        if phenotypes is None:
            # Disease exists but has no phenotypes block.
            # That is a legitimate empty result, not an
            # error.
            return []

        rows = phenotypes.get("rows") or []

        if not isinstance(rows, list):
            return []

        return rows[:_MAX_PHENOTYPE_ROWS]

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _disease_node_id(
        disease: DiseaseIdentity,
    ) -> Optional[str]:
        """
        Deterministic disease node ID, mirroring W01's
        BiologicalSystemsMapper._disease_node_id.

        Colons in the identifier are replaced with
        underscores so the node ID is visually clean:
        "MONDO:0004979" -> "disease:MONDO_0004979".
        The original identifier remains on the node's
        `identifier` field elsewhere.
        """
        if not disease.identifiers:
            return None

        primary = disease.identifiers[0]
        ident = (primary.identifier or "").strip()

        if not ident:
            return None

        sanitized = ident.replace(":", "_")
        return f"{DISEASE_NODE_PREFIX}{sanitized}"

    @staticmethod
    def _phenotype_node_id(hp_id: str) -> str:
        """
        Node ID for a phenotype node.

        "HP:0032933" -> "phenotype:HP_0032933"
        """
        sanitized = hp_id.replace(":", "_")
        return f"{PHENOTYPE_NODE_PREFIX}{sanitized}"

    @staticmethod
    def _pick_open_targets_disease_id(
        disease: DiseaseIdentity,
    ) -> Optional[str]:
        """
        Pick the best identifier for an Open Targets
        disease lookup.

        Preference order:
            1. First MONDO identifier
            2. First EFO identifier
            3. First Orphanet identifier

        IMPORTANT: Open Targets' GraphQL `disease(efoId:)`
        argument requires UNDERSCORE form ("MONDO_0004979").
        Colon form returns {"disease": null} with HTTP 200 —
        a silent failure.

        The resolver normalizes identifiers to colon form
        for consistency. This method converts to underscore
        form for the Open Targets call only; downstream
        node IDs, evidence, and cross-references continue
        to use colon form.

        See app.drug_development.reverse_disease.utils.

        Returns None if no supported identifier is available.
        """
        identifiers = disease.identifiers or []

        for prefix in ("MONDO:", "EFO:", "Orphanet:"):
            for ident in identifiers:
                value = (ident.identifier or "").strip()
                if value.startswith(prefix):
                    return to_opentargets_id(value)

        return None

    @staticmethod
    def _is_inheritance_like(
        namespace: Optional[List[Any]],
    ) -> bool:
        """
        True when any namespace entry contains the
        substring "inherit" (case-insensitive).

        This is a HEURISTIC over the source-provided
        namespace list. It is used ONLY to set a metadata
        flag on the node — it never removes the node or
        weakens its relationship.
        """
        if not namespace:
            return False

        for entry in namespace:
            if not isinstance(entry, str):
                continue
            if _INHERITANCE_NAMESPACE_HINT in entry.lower():
                return True

        return False

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
            "sources": [SOURCE_NAME, ENRICHMENT_SOURCE],
            "found": False,
            "metadata": extra_metadata or {},
            "reason": reason,
        }
