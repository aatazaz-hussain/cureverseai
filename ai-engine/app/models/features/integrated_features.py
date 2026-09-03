from typing import Dict, Optional

from app.data.knowledge_service import BiologicalKnowledgeService
from app.data.sources.ensembl_sequence import EnsemblSequenceClient

from app.models.features.protein_features import ProteinFeatureService
from app.models.features.molecule_features import MoleculeFeatureService
from app.models.features.cell_features import CellFeatureService
from app.models.features.feature_fusion import BiologicalFeatureFusion


class IntegratedFeatureService:
    """
    Integrates real biological data with model-derived representations.

    Current modalities:
    - Gene / transcript / protein data
    - Protein language-model features
    - Molecular language-model features
    - Cellular state features
    - Multimodal feature fusion
    """

    def __init__(self):
        self.knowledge = BiologicalKnowledgeService()
        self.sequence = EnsemblSequenceClient()

        self.protein_features = ProteinFeatureService()
        self.molecule_features = MoleculeFeatureService()
        self.cell_features = CellFeatureService()

        self.fusion = BiologicalFeatureFusion()

    def get_gene_representation(
        self,
        symbol: str,
        smiles: Optional[str] = None,
        cell_state: Optional[Dict[str, float]] = None,
    ) -> Dict:

        # ---------------------------------------------------------
        # 1. Retrieve biological knowledge
        # ---------------------------------------------------------
        context = self.knowledge.get_biological_context(symbol)

        gene = context["gene"]

        # ---------------------------------------------------------
        # 2. Retrieve canonical protein sequence
        # ---------------------------------------------------------
        transcript_id = gene.canonical_transcript

        protein_sequence = self.sequence.get_protein_sequence(
            transcript_id
        )

        # ---------------------------------------------------------
        # 3. Generate protein representation
        # ---------------------------------------------------------
        protein_result = self.protein_features.extract_features(
            protein_sequence
        )

        # ---------------------------------------------------------
        # 4. Generate molecule representation if supplied
        # ---------------------------------------------------------
        molecule_result = None

        if smiles:
            molecule_result = self.molecule_features.extract_features(
                smiles
            )

        # ---------------------------------------------------------
        # 5. Generate cell representation if supplied
        # ---------------------------------------------------------
        cell_result = None

        if cell_state:
            cell_result = self.cell_features.extract_features(
                cell_state
            )
        # ---------------------------------------------------------
        # 6. Extract embeddings
        # ---------------------------------------------------------
        protein_embedding = protein_result["embedding"]

        molecule_embedding = (
            molecule_result["features"]["embedding"]
            if molecule_result
            else None
        )

        cell_embedding = (
            cell_result["features"]["embedding"]
            if cell_result
            else None
        )

        # ---------------------------------------------------------
        # 7. Multimodal fusion
        # ---------------------------------------------------------
        fused = self.fusion.fuse(
            protein_embedding=protein_embedding,
            molecule_embedding=molecule_embedding,
            cell_embedding=cell_embedding,
        )
        # ---------------------------------------------------------
        # 7. Multimodal fusion
        # ---------------------------------------------------------
        fused = self.fusion.fuse(
            protein_embedding=protein_embedding,
            molecule_embedding=molecule_embedding,
            cell_embedding=cell_embedding,
         )

        # ---------------------------------------------------------
        # 8. Return complete biological representation
        # ---------------------------------------------------------
        return {
            "gene": {
                "symbol": gene.symbol,
                "ensembl_id": gene.ensembl_id,
                "name": gene.name,
                "species": gene.species,
                "biotype": gene.biotype,
                "chromosome": gene.chromosome,
                "assembly": gene.assembly,
                "canonical_transcript": gene.canonical_transcript,
            },

            "protein": {
                "transcript_id": transcript_id,
                "sequence_length": len(protein_sequence),
            },

            "protein_features": protein_result,

            "molecule_features": molecule_result,

            "cell_features": cell_result,

            "reactome": {
                "entity_count": len(context["reactome_entities"]),
                "mutation_count": len(context["variants"]),
            },

            "fusion": fused,
        }
