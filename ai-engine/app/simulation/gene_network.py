import networkx as nx


def build_gene_network():
    graph = nx.DiGraph()

    genes = [
        "TP53",
        "MDM2",
        "CDKN1A",
        "BAX",
        "BCL2",
        "MYC",
    ]

    graph.add_nodes_from(genes)

    graph.add_edges_from([
        ("TP53", "MDM2"),
        ("TP53", "CDKN1A"),
        ("TP53", "BAX"),
        ("MDM2", "TP53"),
        ("BCL2", "BAX"),
        ("MYC", "BCL2"),
    ])

    return graph


def simulate_perturbation(gene: str, effect: str = "inhibit"):
    graph = build_gene_network()

    if gene not in graph:
        raise ValueError(f"Unknown gene: {gene}")

    state = {
        node: 1.0
        for node in graph.nodes
    }

    if effect == "inhibit":
        state[gene] = 0.0

    elif effect == "activate":
        state[gene] = 2.0

    else:
        raise ValueError("Effect must be 'inhibit' or 'activate'")

    return {
        "perturbed_gene": gene,
        "effect": effect,
        "gene_state": state,
        "network": {
            "nodes": list(graph.nodes),
            "edges": list(graph.edges),
        },
    }
