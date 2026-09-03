def interpret_cell_state(perturbation_result):
    if not perturbation_result.get("found"):
        return {
            "status": "error",
            "message": perturbation_result.get("error", "Gene not found.")
        }

    gene = perturbation_result["gene"]
    effect = perturbation_result["perturbation"]

    apoptosis = 0.0
    proliferation = 0.0
    survival = 0.0

    for pathway in perturbation_result["pathways"]:
        pathway_name = pathway["pathway"].lower()
        activity = pathway["activity_change"]

        if "p53" in pathway_name:
            apoptosis += activity
            survival -= activity

        if "egfr" in pathway_name or "mapk" in pathway_name:
            proliferation += activity
            survival += activity

    return {
        "status": "success",
        "gene": gene,
        "perturbation": effect,
        "cell_state": {
            "apoptosis": round(apoptosis, 3),
            "proliferation": round(proliferation, 3),
            "survival": round(survival, 3),
        }
    }
