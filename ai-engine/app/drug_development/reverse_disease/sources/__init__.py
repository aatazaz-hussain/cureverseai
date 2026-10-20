"""
CureVerseAI — Drug Development
Workflow 02 — Reverse Disease Engineering
External source clients.

This subpackage holds thin clients for external data sources
that are specific to Workflow 02 and are NOT already wrapped
by an existing client elsewhere in the codebase.

What lives here
---------------

    hpo.py        EBI OLS4 HPO ontology client
                  (thin wrapper around OLS4's /ontologies/hp
                  and /search?ontology=hp surfaces)

What does NOT live here
-----------------------

W02 reuses existing clients for Open Targets, Reactome,
Ensembl, UniProt, and ChEMBL. Their wrappers already exist:

    app/drug_development/sources/open_targets.py
    app/drug_development/sources/open_targets_evidence.py
    app/drug_development/sources/chembl.py
    app/drug_development/sources/chembl_evidence.py
    app/data/sources/reactome.py
    app/data/sources/ensembl.py

The existing OLSClient in
app/drug_development/disease/sources/ols.py is deliberately
NOT reused for HPO lookups, because its supported-ontology
tuples (MONDO/DOID and Uberon) are locked to Workflow 01's
needs. HPO queries go through the W02-local client here.

Public surface
--------------

Until hpo.py is written, this subpackage exports nothing.
Downstream code imports directly from the module path:

    from app.drug_development.reverse_disease.sources.hpo import (
        HPOClient,
    )
"""

__all__: list = []
