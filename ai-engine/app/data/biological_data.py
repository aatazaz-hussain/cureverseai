GENES = {
    "TP53": {
        "name": "Tumor protein p53",
        "type": "tumor_suppressor",
        "pathways": [
            "p53 signaling",
            "apoptosis",
            "cell cycle",
        ],
    },

    "EGFR": {
        "name": "Epidermal growth factor receptor",
        "type": "receptor",
        "pathways": [
            "EGFR signaling",
            "MAPK signaling",
            "PI3K-AKT signaling",
        ],
    },

    "MYC": {
        "name": "MYC proto-oncogene",
        "type": "transcription_factor",
        "pathways": [
            "MYC signaling",
            "cell growth",
            "MAPK signaling",
        ],
    },

    "BAX": {
        "name": "BCL2 associated X",
        "type": "apoptosis_regulator",
        "pathways": [
            "p53 signaling",
            "apoptosis",
        ],
    },

    "BCL2": {
        "name": "B-cell lymphoma 2",
        "type": "apoptosis_regulator",
        "pathways": [
            "apoptosis",
        ],
    },

    "CDKN1A": {
        "name": "Cyclin dependent kinase inhibitor 1A",
        "type": "cell_cycle_regulator",
        "pathways": [
            "p53 signaling",
            "cell cycle",
        ],
    },

    "AKT1": {
        "name": "AKT serine/threonine kinase 1",
        "type": "kinase",
        "pathways": [
            "PI3K-AKT signaling",
        ],
    },

    "MTOR": {
        "name": "Mechanistic target of rapamycin kinase",
        "type": "kinase",
        "pathways": [
            "PI3K-AKT signaling",
            "cell growth",
        ],
    },

    "MAPK1": {
        "name": "Mitogen-activated protein kinase 1",
        "type": "kinase",
        "pathways": [
            "MAPK signaling",
        ],
    },
}


PATHWAYS = {
    "p53 signaling": {
        "description": (
            "Controls DNA damage response, cell-cycle arrest, "
            "senescence and apoptosis."
        ),
        "genes": [
            "TP53",
            "BAX",
            "CDKN1A",
        ],
    },

    "apoptosis": {
        "description": (
            "Programmed cell death pathway that eliminates "
            "damaged or unwanted cells."
        ),
        "genes": [
            "TP53",
            "BAX",
            "BCL2",
        ],
    },

    "cell cycle": {
        "description": (
            "Controls progression through the cell cycle "
            "and regulates cellular proliferation."
        ),
        "genes": [
            "TP53",
            "CDKN1A",
            "MYC",
        ],
    },

    "EGFR signaling": {
        "description": (
            "Cell-surface receptor signaling involved in "
            "cell growth, proliferation and survival."
        ),
        "genes": [
            "EGFR",
            "MYC",
        ],
    },

    "MAPK signaling": {
        "description": (
            "Signal-transduction pathway regulating "
            "proliferation, differentiation and survival."
        ),
        "genes": [
            "EGFR",
            "MAPK1",
            "MYC",
        ],
    },

    "PI3K-AKT signaling": {
        "description": (
            "Intracellular signaling pathway regulating "
            "cell survival, metabolism and growth."
        ),
        "genes": [
            "EGFR",
            "AKT1",
            "MTOR",
        ],
    },

    "MYC signaling": {
        "description": (
            "Transcriptional program associated with "
            "cell growth, proliferation and metabolism."
        ),
        "genes": [
            "MYC",
        ],
    },

    "cell growth": {
        "description": (
            "Regulatory processes controlling cellular "
            "growth, biomass accumulation and proliferation."
        ),
        "genes": [
            "MYC",
            "MTOR",
        ],
    },
}


def get_gene(gene: str):
    return GENES.get(gene.upper())


def get_pathway(pathway: str):
    return PATHWAYS.get(pathway)
