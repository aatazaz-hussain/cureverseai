from app.data.normalizer import (
    extract_mutations,
    extract_reactome_entities,
    normalize_ensembl_gene,
)
from app.data.sources.ensembl import EnsemblClient
from app.data.sources.reactome import ReactomeClient


class BiologicalKnowledgeService:
    def __init__(self):
        self.ensembl = EnsemblClient()
        self.reactome = ReactomeClient()

    def get_gene(self, symbol: str):
        data = self.ensembl.lookup_gene(symbol)

        if data is None:
            return None

        return normalize_ensembl_gene(data)

    def get_reactome_entities(self, symbol: str):
        data = self.reactome.search_pathways(symbol)

        return extract_reactome_entities(data)

    def get_variants(self, symbol: str):
        entities = self.get_reactome_entities(symbol)

        return extract_mutations(entities)

    def get_biological_context(self, symbol: str):
        gene = self.get_gene(symbol)

        if gene is None:
            return None

        entities = self.get_reactome_entities(symbol)
        variants = extract_mutations(entities)

        return {
            "gene": gene,
            "reactome_entities": entities,
            "variants": variants,
        }
