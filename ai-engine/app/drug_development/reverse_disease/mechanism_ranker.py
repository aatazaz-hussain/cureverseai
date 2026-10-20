"""
CureVerseAI — Drug Development
Workflow 02 — Reverse Disease Engineering
Mechanism Ranker.

Produces a ranked ordering of the W02 graph's two
"mechanism-like" entity sets:

    1. Mechanism-category nodes (from the mechanism layer)
       These are evidence-type categories aggregated across
       disease-associated targets. Each carries a
       `targets_supporting` count and a `mean_score` in its
       metadata.

    2. Pathway nodes (from the pathway layer)
       Each pathway's `supporting_gene_count` is derived
       from the disease -> pathway edges produced when >= 2
       disease-associated genes participate in it.

What this module does NOT do
----------------------------

It does NOT produce a probability of causation. Open
Targets' association scores are not probabilities; they
are normalized association weights. Reactome gene counts
are counts. The ranker:

    - SORTS by documented counts and scores,
    - PRESERVES the raw inputs on every ranked entry,
    - LABELS the ranking method explicitly in metadata.

Callers that want to display a number display the raw
count. The rank itself is ordinal only.

It also does NOT modify the graph. Nodes and edges are
read-only inputs. Ranking is a separate output document.

Stability
---------

Ties are broken by preserving input order (Python's
stable sort). The pathway layer emits pathways in
Reactome's server-returned order; the mechanism layer
emits categories in insertion order. Preserving those
orders means two runs against the same data produce the
same ranking.

Empty inputs
------------

If a node type is absent from the graph, that ranking is
returned as an empty list. No exception is raised. This
matches the spec's rule that partial results are valid.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------


#: Human-readable description of the mechanism-category
#: ranking method. Emitted verbatim in metadata.
RANKING_METHOD_CATEGORIES = (
    "targets_supporting desc, then mean_score desc, "
    "then input order"
)

#: Human-readable description of the pathway ranking method.
RANKING_METHOD_PATHWAYS = (
    "supporting_gene_count desc, then input order "
    "(Reactome server order)"
)


# ---------------------------------------------------------------------------
# Ranker
# ---------------------------------------------------------------------------


class MechanismRanker:
    """
    Ranks mechanism-category nodes and pathway nodes from a
    merged W02 graph.
    """

    def __init__(self) -> None:
        pass

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def rank(
        self,
        merged_graph: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Produce ranking documents from a merged graph.

        `merged_graph` is the output of
        CausalGraphBuilder.build(). Only `graph.nodes` and
        `graph.edges` are read.
        """

        graph = merged_graph.get("graph") or {}
        nodes = graph.get("nodes") or []
        edges = graph.get("edges") or []

        ranked_categories = self._rank_mechanism_categories(
            nodes
        )
        ranked_pathways = self._rank_pathways(nodes, edges)

        return {
            "ranked_mechanism_categories": ranked_categories,
            "ranked_pathways": ranked_pathways,
            "metadata": {
                "mechanism_categories_ranked": len(
                    ranked_categories
                ),
                "pathways_ranked": len(ranked_pathways),
                "ranking_method_categories": (
                    RANKING_METHOD_CATEGORIES
                ),
                "ranking_method_pathways": (
                    RANKING_METHOD_PATHWAYS
                ),
                "note": (
                    "Rankings are ordinal. Counts and scores "
                    "are preserved on each entry. Ranks are "
                    "not probabilities of causation."
                ),
            },
        }

    # ------------------------------------------------------------------
    # Mechanism-category ranking
    # ------------------------------------------------------------------

    @staticmethod
    def _rank_mechanism_categories(
        nodes: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Rank mechanism-category nodes by `targets_supporting`
        descending, then `mean_score` descending.

        Stable sort: ties preserve input order.
        """

        entries: List[Dict[str, Any]] = []

        for node in nodes:
            if not isinstance(node, dict):
                continue
            if node.get("node_type") != "mechanism":
                continue

            meta = node.get("metadata") or {}

            targets_supporting = int(
                meta.get("targets_supporting") or 0
            )
            mean_score = float(
                meta.get("mean_score") or 0.0
            )

            entries.append(
                {
                    "node_id": node.get("node_id"),
                    "name": node.get("name"),
                    "datatype_id": meta.get("datatype_id"),
                    "targets_supporting": targets_supporting,
                    "mean_score": round(mean_score, 4),
                    "datasources": dict(
                        meta.get("datasources") or {}
                    ),
                    "rank": None,
                }
            )

        # Python's sort is stable, so this preserves input
        # order within ties.
        entries.sort(
            key=lambda e: (
                -e["targets_supporting"],
                -e["mean_score"],
            )
        )

        for i, entry in enumerate(entries, 1):
            entry["rank"] = i

        return entries

    # ------------------------------------------------------------------
    # Pathway ranking
    # ------------------------------------------------------------------

    @staticmethod
    def _rank_pathways(
        nodes: List[Dict[str, Any]],
        edges: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """
        Rank pathway nodes by supporting gene count
        descending.

        A pathway's supporting gene count comes from the
        disease -> pathway edge for that pathway when one
        exists. Otherwise, the pathway is one that appears
        only as a single-gene gene -> pathway edge, and the
        count is 1.
        """

        # Collect the supporting genes for each pathway from
        # the disease -> pathway edges.
        pathway_support: Dict[str, List[str]] = {}

        for edge in edges:
            if not isinstance(edge, dict):
                continue
            if edge.get("relationship_type") != "associated_with":
                continue
            source_id = str(edge.get("source_id") or "")
            target_id = str(edge.get("target_id") or "")
            if not source_id.startswith("disease:"):
                continue
            if not target_id.startswith("pathway:"):
                continue

            meta = edge.get("metadata") or {}
            genes = list(meta.get("supporting_genes") or [])

            if target_id not in pathway_support:
                pathway_support[target_id] = list(genes)
            else:
                for gene in genes:
                    if gene not in pathway_support[target_id]:
                        pathway_support[target_id].append(gene)

        entries: List[Dict[str, Any]] = []

        for node in nodes:
            if not isinstance(node, dict):
                continue
            if node.get("node_type") != "pathway":
                continue

            node_id = node.get("node_id")
            if not node_id:
                continue

            support = pathway_support.get(node_id)

            if support:
                supporting_genes = list(support)
                supporting_gene_count = len(support)
                elevated = True
            else:
                # Pathway appears only via single-gene
                # gene -> pathway edges.
                supporting_genes = []
                supporting_gene_count = 1
                elevated = False

            entries.append(
                {
                    "node_id": node_id,
                    "name": node.get("name"),
                    "reactome_id": node.get("identifier"),
                    "supporting_gene_count": (
                        supporting_gene_count
                    ),
                    "supporting_genes": supporting_genes,
                    "elevated": elevated,
                    "rank": None,
                }
            )

        # Stable sort by count descending. Ties preserve the
        # order the pathway layer emitted nodes in.
        entries.sort(
            key=lambda e: -e["supporting_gene_count"]
        )

        for i, entry in enumerate(entries, 1):
            entry["rank"] = i

        return entries
