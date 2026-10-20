"""
CureVerseAI — Drug Development
Workflow 02 — Reverse Disease Engineering.

This package reconstructs the biological mechanisms that may
explain a disease, from a free-text disease query.

The investigation direction is:

    disease
      -> phenotype / manifestations
      -> mechanisms
      -> genes / variants
      -> pathways
      -> contributing factors

Every relationship in the produced graph carries its own
evidence, provenance, and support classification. The engine
never converts an association into a causal claim.

Package layout (files added incrementally)
------------------------------------------

    service.py                 top-level entry point
    schemas.py                 W02 result dataclasses
    disease_resolver.py        free-text -> DiseaseIdentity
    phenotype_retriever.py     disease -> phenotype layer
    mechanism_retriever.py     disease -> mechanism layer
    gene_variant_mapper.py     mechanism / disease -> genes + variants
    pathway_mapper.py          gene / mechanism -> Reactome pathways
    causal_graph_builder.py    assembles the directed graph
    evidence_integrator.py     merges evidence + reasoning
    mechanism_ranker.py        orders mechanisms for investigation
    explanation_builder.py     narration segments tied to graph ids

Public surface (added at File 16)
---------------------------------

Until service.py is written, this package exports nothing.
Downstream callers import from the specific module path, e.g.:

    from app.drug_development.reverse_disease.schemas import (
        ReverseDiseaseResult,
    )

After service.py exists, this module will re-export:

    ReverseDiseaseService
    run_reverse_disease

No other names are part of the public API.
"""

__version__ = "0.1.0"

__all__: list = []
