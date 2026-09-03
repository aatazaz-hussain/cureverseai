from typing import Any, Dict

from app.data.sources.ensembl import EnsemblClient
from app.data.sources.ensembl_sequence import EnsemblSequenceClient
from app.data.sources.reactome import ReactomeClient
from app.data.normalizer import extract_reactome_entities, extract_mutations
from app.models.features.protein_features import ProteinFeatureService


class BiologicalFeatureService:
    def __init__(self):
        self.ensembl = EnsemblClient()
        self.sequence_client = EnsemblSequenceClient()
        self.reactome = ReactomeClient()
        self.protein_features = ProteinFeatureService()

    def get_gene_features(self, symbol: str) -> Dict[str, Any]:
        symbol = symbol.upper().strip()

        # -------------------------
        # Ensembl gene information
        # -------------------------

        gene = self.ensembl.lookup_gene(symbol)

        transcript = gene.get("canonical_transcript")

        if not transcript:
            raise ValueError(
                f"No canonical transcript found for {symbol}"
            )

        # -------------------------
        # Protein sequence
        # -------------------------

        sequence = self.sequence_client.get_protein_sequence(
            transcript
        )

        # -------------------------
        # Protein AI features
        # -------------------------

        protein_features = self.protein_features.extract_features(
            sequence
        )

        # -------------------------
        # Reactome knowledge
        # -------------------------

        reactome_data = self.reactome.search_pathways(symbol)

        reactome_entities = extract_reactome_entities(
            reactome_data
        )

        mutations = extract_mutations(
            reactome_entities
        )

        return {
            "gene": {
                "symbol": gene.get("display_name"),
                "ensembl_id": gene.get("id"),
                "description": gene.get("description"),
                "species": gene.get("species"),
                "assembly": gene.get("assembly_name"),
                "chromosome": gene.get("seq_region_name"),
                "biotype": gene.get("biotype"),
            },

            "transcript": {
                "id": transcript,
            },

            "protein": {
                "sequence_length": len(sequence),
                "sequence": sequence,
            },

            "protein_features": {
                "embedding_dimension": protein_features[
                    "embedding_dimension"
                ],
                "model": protein_features["model"],
            },

            "reactome": {
                "entity_count": len(reactome_entities),
                "mutation_count": len(mutations),
                "mutations": [
                    {
                        "gene": m.gene,
                        "variant": m.variant,
                        "identifier": m.identifier,
                    }
                    for m in mutations
                ],
            },
        }
