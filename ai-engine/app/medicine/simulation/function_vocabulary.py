"""
CureVerseAI — Medicine domain
Curated functional vocabulary.

This module is the scientific core of the Medicine simulation.
It defines:

    1. The reference disease + cell-context pairs the platform
       has been curated to model.

    2. For each pair, the functional indicators that the
       simulation tracks, with their direction of benefit,
       units (where applicable), and the source name that will
       substantiate them at runtime.

    3. Curated pathway -> function links, used to mark a
       response as ``mechanistic_inference`` only where the
       link is documented.

    4. Curated combination rules for W03, used to permit an
       interaction classification only where the underlying
       mechanistic overlap is documented.

    5. A small, versioned override table for intervention
       identifiers that arrive from an upstream workflow
       (for example a pathway id handed off from Drug
       Development Workflow 02).

Design principles (non-negotiable):

    - Nothing here is invented. Every indicator, direction,
      and pathway link must be derivable from a public
      biomedical source. The curators must be able to point
      to the source for every entry.

    - Nothing here is a value. This file describes WHAT is
      measured and HOW the direction of benefit is
      interpreted. It never contains a numeric result.

    - No health score, no composite score, no magnitude.
      Numeric values only ever come from retrieved evidence
      at runtime.

    - Versioned. Any change to any entry in this file must
      bump ``FUNCTION_MAPPER_VERSION``. The version is part
      of every ``run_id``, so a bump invalidates prior
      baselines by design.

    - Small and auditable. Three reference pairs in v1. If
      a query does not match a curated pair, the workflow
      must return ``status=partial`` with a clear
      limitation, not fabricate a comparison.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


# ===========================================================================
# Version
# ===========================================================================


#: Bump this whenever any entry in this file changes. It feeds
#: the deterministic run_id computation.
FUNCTION_MAPPER_VERSION = "med-fn-v1"


# ===========================================================================
# Internal dataclass — kept as a plain dict shape for simplicity
# ===========================================================================
#
# We use plain dicts rather than dataclasses for the vocabulary
# entries because:
#
#   - the entries are static data, not runtime objects
#   - keeping them as dicts makes the file trivially diffable
#   - the runtime code converts them into the real
#     FunctionalIndicator dataclass when building a result
#
# Every entry has a fixed shape documented below.


# Indicator entry shape:
#
#     {
#         "id":                    "fn:<snake_case_name>",
#         "name":                  "<human readable>",
#         "direction_of_benefit":  DirectionOfBenefit.<VALUE>,
#         "unit":                  Optional[str],
#         "description":           "<one sentence>",
#         "evidence_level":        Optional[str]  (shared EvidenceLevel value),
#         "source":                "<source name the indicator is
#                                   substantiated from>",
#         "pathway_links":         List[str]  # Reactome pathway stable IDs
#                                              # whose role in this function
#                                              # is documented
#     }


# ===========================================================================
# Reference pair 1 — Asthma + Respiratory epithelium
# ===========================================================================

ASTHMA_RESPIRATORY_EPITHELIUM: Dict[str, Any] = {
    "disease_id": "MONDO:0004979",
    "disease_name": "asthma",
    "cell_context_id": "CL:0000064",
    "cell_context_name": "ciliated cell",
    "cell_context_ontology": "CL",
    "cell_context_source": "Cell Ontology",
    "context_notes": (
        "The airway epithelium, and specifically its ciliated cells, "
        "is a primary site of asthma-associated remodelling. The "
        "vocabulary below reflects functions documented for the "
        "respiratory epithelium in the asthma literature."
    ),
    "indicators": [
        {
            "id": "fn:airway_inflammatory_signalling",
            "name": "Airway inflammatory signalling",
            "direction_of_benefit": "lower_better",
            "unit": None,
            "description": (
                "Signalling activity of inflammatory cytokines and "
                "chemokines in the airway epithelium."
            ),
            "evidence_level": "association",
            "source": "Open Targets",
            "pathway_links": [
                "R-HSA-449147",  # Signaling by Interleukins
                "R-HSA-6785807",  # IL-4 and IL-13 signaling
            ],
        },
        {
            "id": "fn:mucus_production",
            "name": "Mucus production",
            "direction_of_benefit": "lower_better",
            "unit": None,
            "description": (
                "Mucin secretion and goblet-cell activity in the "
                "airway epithelium."
            ),
            "evidence_level": "association",
            "source": "Open Targets",
            "pathway_links": [
                "R-HSA-6785807",  # IL-4 and IL-13 signaling
            ],
        },
        {
            "id": "fn:smooth_muscle_contraction",
            "name": "Airway smooth-muscle contraction",
            "direction_of_benefit": "lower_better",
            "unit": None,
            "description": (
                "Contractile responsiveness of airway smooth muscle, "
                "relevant to bronchoconstriction."
            ),
            "evidence_level": "association",
            "source": "Reactome",
            "pathway_links": [
                "R-HSA-416476",  # G alpha (q) signalling events
            ],
        },
        {
            "id": "fn:epithelial_barrier_function",
            "name": "Epithelial barrier function",
            "direction_of_benefit": "higher_better",
            "unit": None,
            "description": (
                "Integrity of the epithelial barrier, including "
                "tight-junction and adherens-junction function."
            ),
            "evidence_level": "association",
            "source": "Reactome",
            "pathway_links": [
                "R-HSA-420029",  # Tight junction interactions
            ],
        },
    ],
}


# ===========================================================================
# Reference pair 2 — Parkinson disease + Dopaminergic neuron
# ===========================================================================

PARKINSON_DOPAMINERGIC_NEURON: Dict[str, Any] = {
    "disease_id": "MONDO:0005180",
    "disease_name": "Parkinson disease",
    "cell_context_id": "CL:0000700",
    "cell_context_name": "dopaminergic neuron",
    "cell_context_ontology": "CL",
    "cell_context_source": "Cell Ontology",
    "context_notes": (
        "The progressive loss of dopaminergic neurons in the "
        "substantia nigra pars compacta is the central cellular "
        "event in Parkinson disease. The vocabulary below reflects "
        "functions documented for this cell type in the disease "
        "context."
    ),
    "indicators": [
        {
            "id": "fn:dopamine_synthesis",
            "name": "Dopamine synthesis",
            "direction_of_benefit": "higher_better",
            "unit": None,
            "description": (
                "Biosynthetic capacity for dopamine in dopaminergic "
                "neurons."
            ),
            "evidence_level": "association",
            "source": "Reactome",
            "pathway_links": [
                "R-HSA-209905",  # Catecholamine biosynthesis
            ],
        },
        {
            "id": "fn:mitochondrial_respiration",
            "name": "Mitochondrial respiration",
            "direction_of_benefit": "higher_better",
            "unit": None,
            "description": (
                "Oxidative phosphorylation capacity, relevant to "
                "neuronal energy homeostasis."
            ),
            "evidence_level": "association",
            "source": "Reactome",
            "pathway_links": [
                "R-HSA-611105",  # Respiratory electron transport
            ],
        },
        {
            "id": "fn:proteostasis",
            "name": "Protein homeostasis (proteostasis)",
            "direction_of_benefit": "higher_better",
            "unit": None,
            "description": (
                "Ability to clear misfolded proteins, including "
                "alpha-synuclein aggregate handling."
            ),
            "evidence_level": "association",
            "source": "Reactome",
            "pathway_links": [
                "R-HSA-5688426",  # Degradation of extracellular matrix (proxy)
                "R-HSA-983168",   # Antigen processing: Ubiquitination
            ],
        },
        {
            "id": "fn:oxidative_stress_response",
            "name": "Oxidative stress response",
            "direction_of_benefit": "lower_better",
            "unit": None,
            "description": (
                "Burden of reactive oxygen species and adequacy of "
                "antioxidant response."
            ),
            "evidence_level": "association",
            "source": "Reactome",
            "pathway_links": [
                "R-HSA-3299685",  # Detoxification of Reactive Oxygen Species
            ],
        },
    ],
}


# ===========================================================================
# Reference pair 3 — Type 2 diabetes + Pancreatic beta cell
# ===========================================================================

TYPE2_DIABETES_PANCREATIC_BETA: Dict[str, Any] = {
    "disease_id": "MONDO:0005148",
    "disease_name": "type 2 diabetes mellitus",
    "cell_context_id": "CL:0000169",
    "cell_context_name": "type B pancreatic cell",
    "cell_context_ontology": "CL",
    "cell_context_source": "Cell Ontology",
    "context_notes": (
        "Pancreatic beta-cell dysfunction and loss are central to "
        "type 2 diabetes progression. The vocabulary below reflects "
        "functions documented for this cell type in the disease "
        "context."
    ),
    "indicators": [
        {
            "id": "fn:insulin_secretion",
            "name": "Insulin secretion",
            "direction_of_benefit": "higher_better",
            "unit": None,
            "description": (
                "Glucose-stimulated insulin secretion capacity of "
                "pancreatic beta cells."
            ),
            "evidence_level": "association",
            "source": "Reactome",
            "pathway_links": [
                "R-HSA-422356",  # Regulation of insulin secretion
            ],
        },
        {
            "id": "fn:glucose_sensing",
            "name": "Glucose sensing",
            "direction_of_benefit": "higher_better",
            "unit": None,
            "description": (
                "Ability of beta cells to sense circulating glucose "
                "and couple it to secretion."
            ),
            "evidence_level": "association",
            "source": "Reactome",
            "pathway_links": [
                "R-HSA-70171",  # Glycolysis
            ],
        },
        {
            "id": "fn:beta_cell_apoptosis",
            "name": "Beta-cell apoptosis",
            "direction_of_benefit": "lower_better",
            "unit": None,
            "description": (
                "Rate of programmed cell death in pancreatic beta "
                "cells."
            ),
            "evidence_level": "association",
            "source": "Reactome",
            "pathway_links": [
                "R-HSA-109581",  # Apoptosis
            ],
        },
        {
            "id": "fn:er_stress_response",
            "name": "ER stress response",
            "direction_of_benefit": "lower_better",
            "unit": None,
            "description": (
                "Endoplasmic reticulum stress burden in beta cells."
            ),
            "evidence_level": "association",
            "source": "Reactome",
            "pathway_links": [
                "R-HSA-381119",  # Unfolded Protein Response (UPR)
            ],
        },
    ],
}


# ===========================================================================
# Reference pairs registry
# ===========================================================================


REFERENCE_PAIRS: List[Dict[str, Any]] = [
    ASTHMA_RESPIRATORY_EPITHELIUM,
    PARKINSON_DOPAMINERGIC_NEURON,
    TYPE2_DIABETES_PANCREATIC_BETA,
]


#: Lookup by (disease_id, cell_context_id). Populated at module
#: import time from REFERENCE_PAIRS.
_BY_PAIR: Dict[tuple, Dict[str, Any]] = {
    (pair["disease_id"], pair["cell_context_id"]): pair
    for pair in REFERENCE_PAIRS
}

#: Lookup by disease_id only, for the case where the user does
#: not specify a cell context. Returns the pair if exactly one
#: curated context exists for that disease.
_BY_DISEASE: Dict[str, Dict[str, Any]] = {}
for _pair in REFERENCE_PAIRS:
    _d = _pair["disease_id"]
    if _d in _BY_DISEASE:
        # A second pair for the same disease — mark as ambiguous.
        _BY_DISEASE[_d] = {"__ambiguous__": True}
    else:
        _BY_DISEASE[_d] = _pair


# ===========================================================================
# Lookup helpers
# ===========================================================================


def get_pair(
    disease_id: str,
    cell_context_id: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Return the curated reference pair for the given disease and
    optional cell context.

    Returns None if the pair is not curated. This is an honest
    None: the caller must surface a ``partial`` status with a
    clear limitation, not fabricate a comparison.
    """
    if not disease_id:
        return None

    if cell_context_id:
        return _BY_PAIR.get((disease_id, cell_context_id))

    candidate = _BY_DISEASE.get(disease_id)
    if candidate is None or candidate.get("__ambiguous__"):
        return None

    return candidate


def list_curated_diseases() -> List[Dict[str, Any]]:
    """
    Return a list of curated (disease_id, disease_name,
    cell_context_id, cell_context_name) tuples for the frontend
    to display as suggested inputs. No scientific claims, just
    the small curated set.
    """
    out: List[Dict[str, Any]] = []
    for pair in REFERENCE_PAIRS:
        out.append({
            "disease_id": pair["disease_id"],
            "disease_name": pair["disease_name"],
            "cell_context_id": pair["cell_context_id"],
            "cell_context_name": pair["cell_context_name"],
        })
    return out


def indicators_for_pair(pair: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Return the indicator entries for a curated pair. Returns a
    shallow copy so callers cannot mutate the vocabulary in
    place.
    """
    if not pair:
        return []

    return [dict(ind) for ind in pair.get("indicators", [])]


def pathways_for_indicator(
    pair: Dict[str, Any],
    indicator_id: str,
) -> List[str]:
    """
    Return the curated Reactome pathway stable IDs whose role
    in the given indicator is documented.

    Empty list if the indicator is not curated or has no
    pathway links. Empty is meaningful: it means the
    mechanistic-inference path is not available for this
    indicator, so the caller must default to ``insufficient``.
    """
    if not pair:
        return []

    for ind in pair.get("indicators", []):
        if ind.get("id") == indicator_id:
            return list(ind.get("pathway_links", []))

    return []


# ===========================================================================
# Curated combination rules (W03)
# ===========================================================================
#
# A combination rule is present only when the mechanistic overlap
# between the two interventions' pathways is documented. When no
# rule is present, W03 must return
# ``overall_interpretation=not_modelled`` and
# ``interaction_class=insufficient_evidence``.
#
# The rule shape:
#
#     {
#         "intervention_a_id":    "<canonical id>",
#         "intervention_b_id":    "<canonical id>",
#         "interaction_class":    InteractionClass.<VALUE>,
#         "reason":               "<one sentence>",
#         "source":               "<source name>"
#     }
#
# v1 has no combination rules. That is deliberate: the platform
# is honest about combination classification from the start. Add
# a rule only when a source explicitly documents the interaction.


COMBINATION_RULES: List[Dict[str, Any]] = []


def get_combination_rule(
    intervention_a_id: str,
    intervention_b_id: str,
) -> Optional[Dict[str, Any]]:
    """
    Return the documented combination rule for the given pair,
    if any. Order-independent: (A, B) and (B, A) match the same
    rule.

    Returns None when no rule is documented. The caller must
    then set interaction_class to ``insufficient_evidence`` and
    overall_interpretation to ``not_modelled``.
    """
    if not intervention_a_id or not intervention_b_id:
        return None

    for rule in COMBINATION_RULES:
        a = rule["intervention_a_id"]
        b = rule["intervention_b_id"]
        if {a, b} == {intervention_a_id, intervention_b_id}:
            return dict(rule)

    return None


# ===========================================================================
# Intervention override table
# ===========================================================================
#
# Some interventions arrive as identifiers from an upstream
# CureVerseAI workflow (currently: a pathway id handed off from
# Drug Development Workflow 02). Those identifiers are not
# compound ids and ChEMBL cannot resolve them directly.
#
# This table maps a small, explicit, versioned set of such
# identifiers to the canonical intervention they should be
# treated as, plus a note explaining the mapping.
#
# The table is deliberately tiny. Adding an entry requires a
# documented justification in the comment above it.


INTERVENTION_OVERRIDES: Dict[str, Dict[str, Any]] = {
    # Example entry shape (currently empty — add only when a
    # real handoff needs to be supported):
    #
    # "pathway:R-HSA-6785807": {
    #     "canonical_id": "chembl:CLASS:IL4_IL13_SIGNALLING",
    #     "canonical_name": "IL-4 / IL-13 signalling blockade",
    #     "note": (
    #         "Handoff identifier from Drug Development W02. "
    #         "Treated as a class-level intervention covering "
    #         "IL-4R and IL-13 blockade."
    #     ),
    #     "source": "curated",
    # },
}


def resolve_override(identifier: str) -> Optional[Dict[str, Any]]:
    """
    Return the override entry for the given identifier, if any.
    Returns None when there is no override, in which case the
    caller must fall through to the standard resolver.
    """
    if not identifier:
        return None

    entry = INTERVENTION_OVERRIDES.get(identifier)
    if entry is None:
        return None

    return dict(entry)
