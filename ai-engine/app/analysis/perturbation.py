from app.data.biological_data import GENES, PATHWAYS


def simulate_perturbation(gene: str, effect: float):
    gene = gene.upper()

    if gene not in GENES:
        return {
            "gene": gene,
            "found": False,
            "error": f"Gene {gene} is not available in the biological dataset."
        }

    gene_data = GENES[gene]

    pathway_results = []

    for pathway_name in gene_data["pathways"]:
        pathway = PATHWAYS.get(pathway_name)

        if not pathway:
            continue

        affected_genes = []

        for related_gene in pathway["genes"]:
            if related_gene == gene:
                continue

            predicted_change = round(effect * 0.5, 3)

            affected_genes.append({
                "gene": related_gene,
                "predicted_change": predicted_change
            })

        pathway_results.append({
            "pathway": pathway_name,
            "activity_change": effect,
            "affected_genes": affected_genes
        })

    return {
        "gene": gene,
        "found": True,
        "perturbation": effect,
        "pathways": pathway_results
    }
