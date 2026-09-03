import networkx as nx


def simulate_pathway(
    graph: nx.DiGraph,
    initial_gene: str,
    initial_value: float = 1.0,
    steps: int = 3,
):
    if initial_gene not in graph:
        raise ValueError(f"Unknown gene: {initial_gene}")

    state = {node: 0.0 for node in graph.nodes}
    state[initial_gene] = initial_value

    history = [state.copy()]

    for _ in range(steps):
        new_state = state.copy()

        for source, target in graph.edges:
            signal = state[source]

            if signal > 0:
                new_state[target] = min(
                    1.0,
                    new_state[target] + signal * 0.5
                )

        state = new_state
        history.append(state.copy())

    return {
        "initial_gene": initial_gene,
        "initial_value": initial_value,
        "steps": steps,
        "history": history,
        "final_state": state,
    }
