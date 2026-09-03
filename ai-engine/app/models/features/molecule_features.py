from typing import Dict

from app.models.pretrained.molecule_model import MoleculeModel


class MoleculeFeatureService:
    """
    Molecular feature extraction service.

    Converts molecular SMILES into machine-readable molecular
    representations for downstream CureVerse AI analysis.
    """

    def __init__(self):
        self.model = MoleculeModel()

    def extract_features(self, smiles: str) -> Dict:
        if not isinstance(smiles, str) or not smiles.strip():
            raise ValueError("SMILES must be a non-empty string")

        embedding = self.model.encode(smiles)

        return {
            "smiles": smiles,
            "features": {
                "embedding": embedding,
                "embedding_dimension": len(embedding),
            },
            "model": self.model.info(),
        }
