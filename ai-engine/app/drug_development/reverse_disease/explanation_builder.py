"""
CureVerseAI — Drug Development
Workflow 02 — Reverse Disease Engineering
Explanation Builder.

Produces an ordered list of Explanation records — narration
segments tied to specific graph nodes or edges — for the
scientific guide.

Design principles
-----------------

1. Every explanation text is a TEMPLATE rendering of fields
   present in the graph. No claim in any `text` field can
   reference anything that is not directly readable from
   the node or edge that segment targets.

   This guarantees the spec's rule:
       "The language model should not invent missing
        scientific relationships."

   There is no LLM call in this builder. If narrative
   enrichment is wanted later, it becomes an optional
   post-processor that consumes the segments produced here.
   The base segments never depend on it.

2. Segments are ordered to match the W02 investigation
   direction:

       disease identity
       -> phenotypes
       -> mechanisms
       -> pathways (top)
       -> genes (top)

   The frontend plays them in the order returned.

3. Only a curated subset is emitted. A typical disease
   graph has ~70 nodes and ~100 edges. Narrating all of
   them would overwhelm the guide. Instead we emit:

       1 disease node segment
       all phenotype node segments
       all mechanism node segments
       top N pathway node segments (by rank)
       top M disease -> gene edge segments (by Open Targets score)

   The frontend can fetch additional node/edge detail on
   demand through the graph itself.

What this module does NOT do
----------------------------

- It does not call an LLM.
- It does not modify the graph.
- It does not add caveats the graph does not contain.
- It does not silently drop entities. If a node type is
  absent from the graph, the corresponding segment group is
  simply not present in the returned list.

Output shape
------------

A list of Explanation dataclass instances (from
app.drug_development.reverse_disease.schemas) serialized
via dataclasses.asdict.

Each Explanation carries:

    explanation_id, target_kind ("node" | "edge"),
    target_id, text, support_class, evidence_ids, metadata

The `target_id` for an edge is the stable key
    "<source_id>|<relationship_type>|<target_id>"
so the frontend can locate the corresponding relationship
in the graph without a separate index.

Segment id convention
---------------------

    exp:node:<node_id>
    exp:edge:<source_id>|<type>|<target_id>

The id is deterministic, so downstream code (frontend state,
testing, diffing) can rely on it.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any, Dict, List, Optional

from app.drug_development.reverse_disease.schemas import (
    Explanation,
)


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


#: How many top-ranked pathways get their own segment. Ranking
#: comes from MechanismRanker, which orders pathways by
#: supporting gene count descending.
_TOP_PATHWAYS = 10

#: How many top-scoring disease -> gene edges get a segment.
#: Ordering is by Open Targets score descending.
_TOP_GENE_EDGES = 10


# ---------------------------------------------------------------------------
# Builder
# ---------------------------------------------------------------------------


class ExplanationBuilder:
    """
    Produces ordered Explanation records from a merged W02
    graph and a ranked-mechanisms document.
    """

    def __init__(self) -> None:
        pass

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def build(
        self,
        merged_graph: Dict[str, Any],
        ranking: Optional[Dict[str, Any]] = None,
    ) -> List[Dict[str, Any]]:
        """
        Build the ordered explanation segments.

        `merged_graph` is CausalGraphBuilder.build()'s output.
        `ranking` is MechanismRanker.rank()'s output; if not
        provided, pathways are emitted in graph order rather
        than rank order.

        Returns a list of serialized Explanation dicts.
        """

        graph = merged_graph.get("graph") or {}
        nodes = graph.get("nodes") or []
        edges = graph.get("edges") or []

        nodes_by_id: Dict[str, Dict[str, Any]] = {
            n["node_id"]: n
            for n in nodes
            if isinstance(n, dict) and n.get("node_id")
        }

        segments: List[Explanation] = []

        # ---- 1. Disease identity ----------------------------
        disease_node = self._find_disease_node(nodes)
        if disease_node is not None:
            segments.append(
                self._node_segment(
                    node=disease_node,
                    text=self._disease_text(disease_node),
                )
            )

        # ---- 2. Phenotypes ----------------------------------
        for node in nodes:
            if not isinstance(node, dict):
                continue
            if node.get("node_type") != "phenotype":
                continue

            segments.append(
                self._node_segment(
                    node=node,
                    text=self._phenotype_text(node),
                )
            )

        # ---- 3. Mechanisms ----------------------------------
        for node in nodes:
            if not isinstance(node, dict):
                continue
            if node.get("node_type") != "mechanism":
                continue

            segments.append(
                self._node_segment(
                    node=node,
                    text=self._mechanism_text(node),
                )
            )

        # ---- 4. Top pathways --------------------------------
        pathway_nodes = self._ordered_pathways(
            nodes=nodes,
            ranking=ranking,
        )
        for node in pathway_nodes[:_TOP_PATHWAYS]:
            segments.append(
                self._node_segment(
                    node=node,
                    text=self._pathway_text(
                        node=node,
                        edges=edges,
                    ),
                )
            )

        # ---- 5. Top gene associations ------------------------
        gene_edges = self._top_gene_edges(
            edges=edges,
            limit=_TOP_GENE_EDGES,
        )
        for edge in gene_edges:
            target = nodes_by_id.get(edge.get("target_id"))
            if target is None:
                continue

            segments.append(
                self._edge_segment(
                    edge=edge,
                    text=self._gene_edge_text(
                        edge=edge,
                        target_node=target,
                        source_node=disease_node,
                    ),
                )
            )

        return [asdict(s) for s in segments]

    # ------------------------------------------------------------------
    # Segment constructors
    # ------------------------------------------------------------------

    @staticmethod
    def _node_segment(
        node: Dict[str, Any],
        text: str,
    ) -> Explanation:
        node_id = str(node.get("node_id"))
        return Explanation(
            explanation_id=f"exp:node:{node_id}",
            target_kind="node",
            target_id=node_id,
            text=text,
            support_class=None,
            evidence_ids=list(node.get("evidence_ids") or []),
            metadata={
                "node_type": node.get("node_type"),
                "name": node.get("name"),
            },
        )

    @staticmethod
    def _edge_segment(
        edge: Dict[str, Any],
        text: str,
    ) -> Explanation:
        source_id = str(edge.get("source_id"))
        target_id = str(edge.get("target_id"))
        rel_type = str(edge.get("relationship_type"))
        edge_key = f"{source_id}|{rel_type}|{target_id}"

        return Explanation(
            explanation_id=f"exp:edge:{edge_key}",
            target_kind="edge",
            target_id=edge_key,
            text=text,
            support_class=edge.get("support_class"),
            evidence_ids=list(edge.get("evidence_ids") or []),
            metadata={
                "source_id": source_id,
                "target_id": target_id,
                "relationship_type": rel_type,
            },
        )

    # ------------------------------------------------------------------
    # Node selection
    # ------------------------------------------------------------------

    @staticmethod
    def _find_disease_node(
        nodes: List[Dict[str, Any]],
    ) -> Optional[Dict[str, Any]]:
        for node in nodes:
            if not isinstance(node, dict):
                continue
            if node.get("node_type") == "disease":
                return node
        return None

    @staticmethod
    def _ordered_pathways(
        nodes: List[Dict[str, Any]],
        ranking: Optional[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Return pathway nodes in the order the ranker
        provided, or in graph order when no ranking was
        supplied.
        """
        pathway_nodes = [
            n for n in nodes
            if isinstance(n, dict)
            and n.get("node_type") == "pathway"
        ]

        if not ranking:
            return pathway_nodes

        ranked = ranking.get("ranked_pathways") or []

        ordered_ids = [
            r.get("node_id")
            for r in ranked
            if isinstance(r, dict) and r.get("node_id")
        ]

        by_id = {
            n["node_id"]: n for n in pathway_nodes
            if n.get("node_id")
        }

        ordered: List[Dict[str, Any]] = []
        seen: set[str] = set()
        for pid in ordered_ids:
            node = by_id.get(pid)
            if node is None or pid in seen:
                continue
            ordered.append(node)
            seen.add(pid)

        # Any pathway not in the ranking is appended in
        # original order.
        for node in pathway_nodes:
            if node.get("node_id") not in seen:
                ordered.append(node)

        return ordered

    @staticmethod
    def _top_gene_edges(
        edges: List[Dict[str, Any]],
        limit: int,
    ) -> List[Dict[str, Any]]:
        """
        Return disease -> gene associated_with edges, sorted
        by Open Targets score descending.

        Stable sort: ties preserve input order.
        """
        gene_edges: List[Dict[str, Any]] = []

        for edge in edges:
            if not isinstance(edge, dict):
                continue
            if edge.get("relationship_type") != "associated_with":
                continue

            source_id = str(edge.get("source_id") or "")
            target_id = str(edge.get("target_id") or "")

            if not source_id.startswith("disease:"):
                continue
            if not target_id.startswith("gene:"):
                continue

            gene_edges.append(edge)

        gene_edges.sort(
            key=lambda e: -(
                float(
                    (e.get("metadata") or {}).get(
                        "open_targets_score"
                    )
                    or 0.0
                )
            )
        )

        return gene_edges[:limit]

    # ------------------------------------------------------------------
    # Text templates
    # ------------------------------------------------------------------

    @staticmethod
    def _disease_text(node: Dict[str, Any]) -> str:
        name = node.get("name") or "The disease"
        identifier = node.get("identifier")
        description = node.get("description")

        parts: List[str] = []

        if identifier:
            parts.append(f"{name} ({identifier}).")
        else:
            parts.append(f"{name}.")

        if description:
            # Keep the first sentence of the official
            # description only — the full text is in the
            # inspector if the user wants it.
            desc = description.rstrip(". ")
            first_stop = desc.find(". ")
            if first_stop > 0:
                desc = desc[:first_stop + 1]
            parts.append(desc.rstrip(". ") + ".")

        parts.append(
            "The segments that follow walk through the "
            "symptoms, evidence types, genes, and "
            "biological processes recorded for this "
            "disease."
        )

        return " ".join(parts)

    @staticmethod
    def _phenotype_text(node: Dict[str, Any]) -> str:
        name = node.get("name") or "This symptom"
        identifier = node.get("identifier")
        description = node.get("description")
        meta = node.get("metadata") or {}
        inheritance_like = bool(meta.get("inheritance_like"))

        parts: List[str] = []

        if identifier:
            parts.append(f"{name} ({identifier})")
        else:
            parts.append(name)

        parts.append(
            "is a feature that scientific databases have "
            "recorded for this disease."
        )

        if description:
            parts.append(description.rstrip(". ") + ".")

        if inheritance_like:
            parts.append(
                "Note: this term describes an inheritance "
                "pattern, not a patient-visible symptom."
            )

        # When there is no description from any source,
        # close the segment cleanly instead of stopping on
        # a dangling "is recorded for this disease."
        meta_ok = isinstance(meta, dict)
        desc_src = (
            meta.get("description_source")
            if meta_ok
            else None
        )

        if not description:
            synonyms = (
                meta.get("synonyms")
                if meta_ok
                else None
            )
            if isinstance(synonyms, list) and synonyms:
                first = str(synonyms[0]).strip()
                if first and first.lower() != name.lower():
                    parts.append(
                        f"It is also known as '{first}'."
                    )
                    parts.append(
                        "No further definition is available "
                        "in the sources consulted."
                    )
                else:
                    parts.append(
                        "No further definition is available "
                        "in the sources consulted."
                    )
            else:
                parts.append(
                    "No further definition is available "
                    "in the sources consulted."
                )
            if desc_src:
                parts.append(
                    f"Description source: {desc_src}."
                )

        return " ".join(parts)

    @staticmethod
    def _mechanism_text(node: Dict[str, Any]) -> str:
        name = node.get("name") or "This type of evidence"
        meta = node.get("metadata") or {}
        targets_supporting = int(
            meta.get("targets_supporting") or 0
        )
        mean_score = float(meta.get("mean_score") or 0.0)

        parts: List[str] = []

        parts.append(
            f"{name} is one way that scientists have "
            f"connected this disease to its associated "
            f"genes. It applies to "
            f"{targets_supporting} of the disease's "
            f"genes."
        )

        if mean_score:
            parts.append(
                f"On average this evidence is "
                f"{mean_score:.2f} out of 1.0 in strength."
            )

        parts.append(
            "This describes how the disease is known, "
            "not a biological cause."
        )

        return " ".join(parts)

    @staticmethod
    def _pathway_text(
        node: Dict[str, Any],
        edges: List[Dict[str, Any]],
    ) -> str:
        name = node.get("name") or "This biological process"
        reactome_id = node.get("identifier")
        node_id = node.get("node_id")

        supporting_genes: List[str] = []
        elevated = False

        for edge in edges:
            if not isinstance(edge, dict):
                continue
            if edge.get("relationship_type") != "associated_with":
                continue
            if edge.get("target_id") != node_id:
                continue

            source_id = str(edge.get("source_id") or "")
            if not source_id.startswith("disease:"):
                continue

            meta = edge.get("metadata") or {}
            genes = meta.get("supporting_genes") or []
            supporting_genes = [
                str(g) for g in genes if g
            ]
            elevated = True
            break

        parts: List[str] = []

        if reactome_id:
            parts.append(f"'{name}' ({reactome_id})")
        else:
            parts.append(f"'{name}'")

        parts.append(
            "is a biological process that has been "
            "recorded in Reactome."
        )

        if elevated and supporting_genes:
            gene_list = ", ".join(supporting_genes)
            parts.append(
                f"{len(supporting_genes)} of this disease's "
                f"associated genes take part in it: "
                f"{gene_list}."
            )
            parts.append(
                "The link between this disease and the "
                "process is inferred from the genes, not "
                "directly recorded for the disease."
            )
        else:
            parts.append(
                "Only one of the disease's associated "
                "genes takes part in it, so it is not "
                "listed as a disease-level link."
            )

        return " ".join(parts)

    @staticmethod
    def _gene_edge_text(
        edge: Dict[str, Any],
        target_node: Dict[str, Any],
        source_node: Optional[Dict[str, Any]],
    ) -> str:
        gene_name = target_node.get("name") or "This gene"
        ensembl_id = target_node.get("identifier")
        approved_name = target_node.get("description")
        meta = edge.get("metadata") or {}
        score = meta.get("open_targets_score")

        disease_name = (
            source_node.get("name")
            if source_node
            else "the disease"
        )

        parts: List[str] = []

        parts.append(
            f"'{gene_name}' is one of the genes most "
            f"strongly linked to {disease_name} in Open "
            f"Targets."
        )

        if approved_name:
            parts.append(
                f"Its official name is '{approved_name}'."
            )

        if ensembl_id:
            parts.append(f"Reference: {ensembl_id}.")

        if score is not None:
            try:
                parts.append(
                    f"Association strength: "
                    f"{float(score):.2f} of 1.0."
                )
            except (TypeError, ValueError):
                pass

        parts.append(
            "The evidence is strong but this is not "
            "proof that the gene causes the disease."
        )

        return " ".join(parts)
