from typing import Any, Dict

from app.models.inference.inference_engine import BiologicalInferenceEngine


SUPPORTED_DOMAINS = {
    "research",
    "drug_development",
    "medicine",
    "biotechnology",
    "education",
}


class CureVerseAIOrchestrator:
    """
    Central orchestration layer for all CureVerseAI domains.
    """

    def __init__(self):
        self.biological_engine = BiologicalInferenceEngine()

    def analyze(
        self,
        domain: str,
        task: str,
        input_data: Dict[str, Any],
    ) -> Dict[str, Any]:

        domain = domain.strip().lower()

        if domain not in SUPPORTED_DOMAINS:
            raise ValueError(
                f"Unsupported domain '{domain}'. "
                f"Supported domains: {sorted(SUPPORTED_DOMAINS)}"
            )

        if domain in {
            "research",
            "drug_development",
            "medicine",
            "biotechnology",
        }:
            return self._biological_analysis(
                domain=domain,
                task=task,
                input_data=input_data,
            )

        if domain == "education":
            return self._education_analysis(
                task=task,
                input_data=input_data,
            )

        raise ValueError(f"No engine configured for domain: {domain}")

    def _biological_analysis(
        self,
        domain: str,
        task: str,
        input_data: Dict[str, Any],
    ) -> Dict[str, Any]:

        gene = input_data.get("gene")

        if not gene:
            raise ValueError(
                "A gene symbol is required for this biological analysis."
            )

        smiles = input_data.get("smiles")
        result = self.biological_engine.analyze_gene(
        gene=gene,
        smiles=smiles,
           )
        return {
            "domain": domain,
            "task": task,
            "engine": "biological_inference_engine",
            "result": result,
        }

    def _education_analysis(
        self,
        task: str,
        input_data: Dict[str, Any],
    ) -> Dict[str, Any]:

        topic = input_data.get("topic")

        if not topic:
            raise ValueError(
                "A topic is required for education analysis."
            )

        return {
            "domain": "education",
            "task": task,
            "engine": "education_intelligence",
            "result": {
                "topic": topic,
                "level": input_data.get(
                    "level",
                    "general",
                ),
                "mode": input_data.get(
                    "mode",
                    "explanation",
                ),
                "status": "ready",
            },
        }


def get_supported_domains() -> list[str]:
    return sorted(SUPPORTED_DOMAINS)
