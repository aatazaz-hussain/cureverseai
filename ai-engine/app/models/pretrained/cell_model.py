from typing import Dict, List, Optional

import torch


class CellModel:
    """
    Cellular representation model adapter.

    The adapter exposes a stable interface for CureVerse AI's
    cellular intelligence layer.

    The implementation currently supports a lightweight cellular
    state representation and is structured so a pretrained
    single-cell foundation model can be plugged in later without
    changing downstream services.
    """

    MODEL_NAME = "cellular_state_adapter"
    MODEL_TYPE = "cellular_representation_model"

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name or self.MODEL_NAME

        self.device = torch.device(
            "cuda" if torch.cuda.is_available() else "cpu"
        )

        self.required_features = [
            "apoptosis",
            "proliferation",
            "survival",
        ]

    def encode(self, cell_state: Dict[str, float]) -> List[float]:
        """
        Convert cellular state measurements into a normalized
        representation.

        This interface is intentionally model-independent so that
        a future pretrained cellular model can replace the internal
        implementation without changing the API.
        """

        if not isinstance(cell_state, dict):
            raise ValueError("cell_state must be a dictionary")

        values = []

        for feature in self.required_features:
            value = cell_state.get(feature, 0.0)

            if not isinstance(value, (int, float)):
                raise ValueError(
                    f"Cell-state value for '{feature}' must be numeric"
                )

            values.append(float(value))

        tensor = torch.tensor(values, dtype=torch.float32)

        norm = torch.linalg.vector_norm(tensor)

        if norm > 0:
            tensor = tensor / norm

        return tensor.tolist()

    def info(self) -> Dict:
        return {
            "model_name": self.model_name,
            "model_type": self.MODEL_TYPE,
            "device": str(self.device),
            "representation": "cellular_state_embedding",
            "dimensions": len(self.required_features),
            "pretrained": False,
            "adapter_ready": True,
        }
