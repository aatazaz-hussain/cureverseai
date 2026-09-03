CUREVERSEAI_DOMAINS = {
    "research": {
        "name": "Research",
        "capabilities": [
            "gene_analysis",
            "pathway_analysis",
            "variant_analysis",
            "gene_network_analysis",
            "hypothesis_generation",
            "perturbation_analysis",
            "biological_reasoning",
            "evidence_exploration",
        ],
    },

    "drug_development": {
        "name": "Drug Development",
        "capabilities": [
            "target_analysis",
            "drug_target_analysis",
            "mechanism_of_action",
            "perturbation_response",
            "drug_response_prediction",
            "biomarker_analysis",
            "resistance_analysis",
            "combination_analysis",
        ],
    },

    "medicine": {
        "name": "Medicine",
        "capabilities": [
            "variant_interpretation",
            "gene_disease_analysis",
            "molecular_mechanism",
            "biomarker_analysis",
            "disease_pathway_analysis",
            "treatment_response_research",
        ],
    },

    "biotechnology": {
        "name": "Biotechnology",
        "capabilities": [
            "sequence_analysis",
            "protein_analysis",
            "biological_system_analysis",
            "pathway_engineering",
            "experiment_planning",
            "biological_optimization",
            "synthetic_biology_support",
        ],
    },

    "education": {
        "name": "Education",
        "capabilities": [
            "ai_tutoring",
            "adaptive_explanations",
            "interactive_simulation",
            "concept_explanation",
            "quiz_generation",
            "learning_assessment",
            "visual_learning",
        ],
    },
}


def get_domain(domain: str):
    return CUREVERSEAI_DOMAINS.get(domain.lower())


def get_all_domains():
    return CUREVERSEAI_DOMAINS


def get_capabilities(domain: str):
    selected = get_domain(domain)

    if selected is None:
        return []

    return selected["capabilities"]
