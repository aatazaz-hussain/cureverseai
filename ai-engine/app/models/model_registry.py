from dataclasses import dataclass
from typing import Optional


@dataclass
class ModelSpec:
    name: str
    task: str
    provider: str
    checkpoint: Optional[str]
    status: str
    description: str


MODEL_REGISTRY = {
    "protein": ModelSpec(
        name="Protein Language Model",
        task="protein_representation",
        provider="huggingface",
        checkpoint=None,
        status="planned",
        description="Pretrained protein representation model for sequence-level biological features.",
    ),

    "molecule": ModelSpec(
        name="Molecular Language Model",
        task="molecular_representation",
        provider="huggingface",
        checkpoint=None,
        status="planned",
        description="Pretrained molecular representation model for drug and compound analysis.",
    ),

    "cell": ModelSpec(
        name="Single-Cell Foundation Model",
        task="cellular_representation",
        provider="huggingface",
        checkpoint=None,
        status="planned",
        description="Pretrained biological model for cellular state and perturbation analysis.",
    ),
}


def get_model(name: str) -> Optional[ModelSpec]:
    return MODEL_REGISTRY.get(name)


def get_all_models():
    return MODEL_REGISTRY
