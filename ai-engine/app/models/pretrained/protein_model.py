import os
from typing import List

import torch
from transformers import AutoTokenizer, AutoModel


class ProteinModel:
    def __init__(self):
        self.checkpoint = os.getenv(
            "CUREVERSE_PROTEIN_MODEL",
            "facebook/esm2_t6_8M_UR50D"
        )

        self.device = torch.device("cpu")

        self.tokenizer = AutoTokenizer.from_pretrained(
            self.checkpoint
        )

        self.model = AutoModel.from_pretrained(
            self.checkpoint
        )

        self.model.to(self.device)
        self.model.eval()

    @torch.no_grad()
    def encode(self, sequence: str) -> List[float]:
        sequence = sequence.upper().replace(" ", "")

        inputs = self.tokenizer(
            sequence,
            return_tensors="pt",
            truncation=True,
            max_length=1024,
        )

        inputs = {
            key: value.to(self.device)
            for key, value in inputs.items()
        }

        outputs = self.model(**inputs)

        embedding = outputs.last_hidden_state.mean(
            dim=1
        ).squeeze(0)

        return embedding.cpu().tolist()

    def info(self):
        return {
            "checkpoint": self.checkpoint,
            "device": str(self.device),
            "model_type": "protein_language_model",
        }
