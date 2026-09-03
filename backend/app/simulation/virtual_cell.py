from typing import Dict


GENE_NETWORK = {
    "TP53": ["MDM2", "CDKN1A", "BAX"],
    "MDM2": ["TP53"],
    "BCL2": ["BAX"],
    "MYC": ["BCL2"],
}


def simulate_gene_perturbation(
    gene: str,
    effect: str = "inhibit"
) -> Dict:

    if gene not in GENE_NETWORK:
        raise ValueError(f"Gene '{gene}' is not available")

    if effect not in ["activate", "inhibit"]:
        raise ValueError("Effect must be 'activate' or 'inhibit'")

    state = {
        "TP53": 1.0,
        "MDM2": 1.0,
        "CDKN1A": 1.0,
        "BAX": 1.0,
        "BCL2": 1.0,
        "MYC": 1.0,
    }

    state[gene] = 1.0 if effect == "activate" else 0.0

    return {
        "gene": gene,
        "effect": effect,
        "predicted_state": state,
        "affected_genes": GENE_NETWORK[gene],
    }
