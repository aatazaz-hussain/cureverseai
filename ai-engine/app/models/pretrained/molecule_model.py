from typing import List, Dict

import torch
from transformers import AutoTokenizer, AutoModel


class MoleculeModel:
    """
    Pretrained molecular language model wrapper.

    Converts molecular SMILES strings into dense molecular
    representations that can be consumed by downstream
    CureVerse AI intelligence modules.
    """

    CHECKPOINT = "seyonec/ChemBERTa-zinc-base-v1"

    def __init__(self):
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

        self.tokenizer = AutoTokenizer.from_pretrained(self.CHECKPOINT)
        self.model = AutoModel.from_pretrained(self.CHECKPOINT)

        self.model.to(self.device)
        self.model.eval()

    def encode(self, smiles: str) -> List[float]:
        """
        Encode a SMILES string into a fixed-size molecular embedding.
        """

        if not isinstance(smiles, str) or not smiles.strip():
            raise ValueError("SMILES must be a non-empty string")

        inputs = self.tokenizer(
            smiles,
            return_tensors="pt",
            truncation=True,
            max_length=512,
        )

        inputs = {
            key: value.to(self.device)
            for key, value in inputs.items()
        }

        with torch.no_grad():
            outputs = self.model(**inputs)

        # Mean pooling over the sequence dimension
        hidden_states = outputs.last_hidden_state
        attention_mask = inputs["attention_mask"].unsqueeze(-1)

        masked_hidden = hidden_states * attention_mask
        pooled = masked_hidden.sum(dim=1) / attention_mask.sum(dim=1).clamp(min=1)

        return pooled[0].cpu().tolist()

    def info(self) -> Dict:
        """
        Return model metadata.
        """

        return {
            "checkpoint": self.CHECKPOINT,
            "device": str(self.device),
            "model_type": "molecular_language_model",
        }
