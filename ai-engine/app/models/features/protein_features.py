from typing import Dict, Any

from app.models.pretrained.protein_model import ProteinModel


class ProteinFeatureService:
    def __init__(self):
        self.model = ProteinModel()

    def extract_features(self, sequence: str) -> Dict[str, Any]:
        sequence = sequence.upper().replace(" ", "")

        embedding = self.model.encode(sequence)

        return {
            "sequence_length": len(sequence),
            "embedding_dimension": len(embedding),
            "embedding": embedding,
            "model": self.model.info(),
        }
