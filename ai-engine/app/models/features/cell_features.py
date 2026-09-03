from typing import Dict

from app.models.pretrained.cell_model import CellModel


class CellFeatureService:
    """
    Cellular feature extraction service.

    Converts cellular state information into a standardized
    representation for downstream CureVerse AI inference.
    """

    def __init__(self):
        self.model = CellModel()

    def extract_features(self, cell_state: Dict[str, float]) -> Dict:
        if not isinstance(cell_state, dict):
            raise ValueError("cell_state must be a dictionary")

        embedding = self.model.encode(cell_state)

        return {
            "cell_state": cell_state,
            "features": {
                "embedding": embedding,
                "embedding_dimension": len(embedding),
            },
            "model": self.model.info(),
        }
