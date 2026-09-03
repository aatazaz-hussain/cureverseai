from typing import Dict, List, Optional
import math


class BiologicalFeatureFusion:
    """
    Combines biological representations from:
    - Protein
    - Molecule
    - Cell

    The fusion layer is intentionally lightweight so it can run
    efficiently on CPU while remaining model-agnostic.
    """

    def __init__(self):
        self.name = "biological_feature_fusion"
        self.version = "1.0"

    @staticmethod
    def _normalize(vector: List[float]) -> List[float]:
        """L2-normalize a vector."""
        if not vector:
            return []

        norm = math.sqrt(sum(float(x) ** 2 for x in vector))

        if norm == 0:
            return [0.0] * len(vector)

        return [float(x) / norm for x in vector]

    @staticmethod
    def _resize(vector: List[float], target_size: int) -> List[float]:
        """
        Resize a vector deterministically.

        If the vector is larger, divide it into bins and average.
        If smaller, zero-pad.

        This is a feature-alignment operation, not a learned model.
        """
        if not vector:
            return [0.0] * target_size

        vector = [float(x) for x in vector]

        if len(vector) == target_size:
            return vector

        if len(vector) < target_size:
            return vector + [0.0] * (target_size - len(vector))

        result = []

        for i in range(target_size):
            start = int(i * len(vector) / target_size)
            end = int((i + 1) * len(vector) / target_size)

            if end <= start:
                end = start + 1

            chunk = vector[start:end]
            result.append(sum(chunk) / len(chunk))

        return result

    def fuse(
        self,
        protein_embedding: Optional[List[float]] = None,
        molecule_embedding: Optional[List[float]] = None,
        cell_embedding: Optional[List[float]] = None,
    ) -> Dict:

        protein = self._normalize(protein_embedding or [])
        molecule = self._normalize(molecule_embedding or [])
        cell = self._normalize(cell_embedding or [])

        available = {
            "protein": bool(protein),
            "molecule": bool(molecule),
            "cell": bool(cell),
        }

        # Common representation size.
        target_size = 256

        aligned = {
            "protein": self._resize(protein, target_size),
            "molecule": self._resize(molecule, target_size),
            "cell": self._resize(cell, target_size),
        }

        # Count how many modalities are actually present.
        active = sum(available.values())

        if active == 0:
            fused = [0.0] * target_size

        else:
            fused = []

            for i in range(target_size):
                values = []

                if available["protein"]:
                    values.append(aligned["protein"][i])

                if available["molecule"]:
                    values.append(aligned["molecule"][i])

                if available["cell"]:
                    values.append(aligned["cell"][i])

                fused.append(sum(values) / len(values))

            fused = self._normalize(fused)

        return {
            "fusion_model": self.name,
            "version": self.version,
            "representation_dimension": len(fused),
            "modalities": available,
            "active_modalities": active,
            "protein_dimension": len(protein),
            "molecule_dimension": len(molecule),
            "cell_dimension": len(cell),
            "fused_embedding": fused,
        }

    def info(self) -> Dict:
        return {
            "name": self.name,
            "version": self.version,
            "target_dimension": 256,
            "supported_modalities": [
                "protein",
                "molecule",
                "cell",
            ],
            "learned": False,
            "purpose": "Multimodal biological feature alignment and fusion",
        }
