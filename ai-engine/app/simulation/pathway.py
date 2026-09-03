from app.data.biological_data import GENES, PATHWAYS


def analyze_gene_pathways(gene: str):
    gene = gene.upper()

    gene_data = GENES.get(gene)

    if not gene_data:
        return {
            "gene": gene,
            "found": False,
            "pathways": [],
        }

    pathway_results = []

    for pathway_name in gene_data["pathways"]:
        pathway = PATHWAYS.get(pathway_name)

        if not pathway:
            continue

        related_genes = []

        for related_gene in pathway["genes"]:
            if related_gene != gene:
                related_genes.append(related_gene)

        pathway_results.append({
            "pathway": pathway_name,
            "description": pathway["description"],
            "related_genes": related_genes,
        })

    return {
        "gene": gene,
        "found": True,
        "pathways": pathway_results,
    }
