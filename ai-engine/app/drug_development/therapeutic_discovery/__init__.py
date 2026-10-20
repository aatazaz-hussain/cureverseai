"""
CureVerseAI — Drug Development
Workflow 03 — Therapeutic Discovery.

This package investigates what biological targets, drugs,
compounds, or other interventions could modify a disease
mechanism, and what evidence supports the proposed effect.

The investigation direction is:

    disease or selected mechanism
      -> therapeutic target
      -> candidate compound / intervention
      -> target interaction / biological action
      -> downstream mechanism / response
      -> evidence and limitations

Every edge in the produced graph is labeled by the nature
of its support:

    experimentally_measured — backed by an assay record
    predicted               — produced by computation
    supported_association   — recorded in a database
    mechanistic_inference   — derived from several edges
    unresolved              — the workflow tried and could
                              not establish the link

The engine never claims clinical efficacy or safety from
molecular activity alone.

Package layout (files added incrementally)
------------------------------------------

    service.py                top-level entry point
    schemas.py                W03-specific result dataclasses
    disease_context.py        resolve disease or accept W02 context
    mechanism_resolver.py     identify the mechanism under study
    target_discovery.py       find candidate biological targets
    compound_discovery.py     retrieve candidate compounds
    activity_interpreter.py   classify assay records
    mechanism_of_action.py    assemble the MoA chain
    candidate_evaluation.py   compare candidates across dimensions
    evidence_integrator.py    merge evidence, expose gaps
    therapeutic_graph.py      build the full intervention graph
    explanation_builder.py    narration tied to graph elements

Public surface
--------------

Until service.py is written, this package exports nothing.
Downstream callers import from the specific module path,
for example:

    from app.drug_development.therapeutic_discovery.schemas import (
        TherapeuticDiscoveryResult,
    )

After service.py exists, this module will re-export:

    TherapeuticDiscoveryService
    run_therapeutic_discovery
"""

__version__ = "0.1.0"

__all__: list = []
