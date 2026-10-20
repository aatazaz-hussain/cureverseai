from typing import Any, Dict

from app.models.inference.inference_engine import BiologicalInferenceEngine
from app.data.sources.reactome import ReactomeClient
from app.data.normalizer import extract_reactome_entities
from app.drug_development.pipeline import run_disease_impact
from app.drug_development.reverse_disease.service import (
    run_reverse_disease,
)
from app.drug_development.therapeutic_discovery.service import (
    run_therapeutic_discovery,
)


def _medicine_service():
    """
    Lazy import of the Medicine simulation service.

    Kept lazy so that an import-time failure in any Medicine
    module cannot break the orchestrator for the other
    domains (Research, Drug Development, Education). If the
    import fails, the caller gets a clear RuntimeError rather
    than a silent fallback.
    """
    try:
        from app.medicine.simulation import service as medicine_service
    except Exception as exc:
        raise RuntimeError(
            f"Medicine simulation service unavailable: {exc}"
        ) from exc

    return medicine_service


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
        self.reactome = ReactomeClient()

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

        if domain == "research" and task.strip().lower() == "pathway_exploration":
            return self._pathway_analysis(
                task=task,
                input_data=input_data,
            )

        if (
            domain == "drug_development"
            and task.strip().lower() == "disease_biological_impact"
        ):
            return self._disease_biological_impact_analysis(
                task=task,
                input_data=input_data,
            )

        if (
            domain == "drug_development"
            and task.strip().lower() == "reverse_disease_engineering"
        ):
            return self._reverse_disease_engineering_analysis(
                task=task,
                input_data=input_data,
            )

        if (
            domain == "drug_development"
            and task.strip().lower() == "therapeutic_discovery"
        ):
            return self._therapeutic_discovery_analysis(
                task=task,
                input_data=input_data,
            )

        if (
            domain == "medicine"
            and task.strip().lower() == "virtual_disease_simulation"
        ):
            return self._medicine_virtual_disease_analysis(
                task=task,
                input_data=input_data,
            )

        if (
            domain == "medicine"
            and task.strip().lower() == "treatment_simulation"
        ):
            return self._medicine_treatment_analysis(
                task=task,
                input_data=input_data,
            )

        if (
            domain == "medicine"
            and task.strip().lower() == "combination_treatment_simulation"
        ):
            return self._medicine_combination_analysis(
                task=task,
                input_data=input_data,
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

    def _pathway_analysis(
        self,
        task: str,
        input_data: Dict[str, Any],
    ) -> Dict[str, Any]:

        pathway_query = str(
            input_data.get("pathway") or ""
        ).strip()

        if not pathway_query:
            raise ValueError(
                "A pathway or biological term is required."
            )

        search_results = self.reactome.search_pathways(
            pathway_query
        )

        entities = extract_reactome_entities(
            search_results
        )

        pathways = []

        for entity in entities:
            if str(entity.entity_type).strip().lower() != "pathway":
                continue

            metadata = entity.metadata or {}

            pathways.append({
                "id": entity.identifier,
                "name": entity.name,
                "species": entity.species,
                "description": metadata.get("reactome_name"),
                "is_in_disease": False,
                "is_inferred": False,
                "type": "Pathway",
                "review_status": "",
                "has_diagram": False,
                "has_ehld": False,
                "release_date": "",
                "matched_query": pathway_query,
                "compartment": entity.compartment,
                "literature": [],
                "cross_references": [],
                "raw": {
                    "identifier": entity.identifier,
                    "name": entity.name,
                    "species": entity.species,
                    "entity_type": entity.entity_type,
                    "metadata": metadata,
                },
            })

        unique = {}
        for pathway in pathways:
            key = pathway["id"] or pathway["name"]
            if key and key not in unique:
                unique[key] = pathway

        pathways = list(unique.values())

        return {
            "domain": "research",
            "task": task,
            "engine": "reactome_pathway_intelligence",
            "result": {
                "pathways": pathways,
                "expanded_queries": [pathway_query],
                "search_results": search_results,
                "evidence_reasoning": {
                    "evidence_summary": (
                        f"Reactome returned {len(pathways)} "
                        f"pathway records for '{pathway_query}'."
                    ),
                    "source": "Reactome",
                    "query": pathway_query,
                },
            },
        }


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

    def _disease_biological_impact_analysis(
        self,
        task: str,
        input_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Full Disease -> Biological Impact pipeline.

        Input:
            { "disease": "<free text query>" }

        Output:
            {
                "domain": "drug_development",
                "task": task,
                "engine": "disease_impact_pipeline",
                "result": <serialized BiologicalImpactResult>,
            }

        Never raises for an unresolvable disease. Raises
        ValueError only when the disease input is missing
        or empty, matching the pattern used by the other
        analysis methods.
        """

        disease_query = str(
            input_data.get("disease") or ""
        ).strip()

        if not disease_query:
            raise ValueError(
                "A disease query is required for the "
                "Disease -> Biological Impact pipeline."
            )

        result = run_disease_impact(disease_query)

        return {
            "domain": "drug_development",
            "task": task,
            "engine": "disease_impact_pipeline",
            "result": result,
        }

    def _reverse_disease_engineering_analysis(
        self,
        task: str,
        input_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Workflow 02 — Reverse Disease Engineering pipeline.

        Input:
            {
                "disease":       "<free text query>",
                "fetch_chembl":  <bool, optional, default true>,
            }

        Output:
            {
                "domain": "drug_development",
                "task": task,
                "engine": "reverse_disease_engineering_pipeline",
                "result": <serialized W02 result>,
            }

        Never raises for an unresolvable or empty disease
        query. The W02 service returns a well-formed result
        with resolution_status="unresolved" in that case.
        """

        disease_query = str(
            input_data.get("disease") or ""
        ).strip()

        fetch_chembl_raw = input_data.get("fetch_chembl", True)
        fetch_chembl = bool(fetch_chembl_raw) if isinstance(
            fetch_chembl_raw, (bool, int)
        ) else True

        result = run_reverse_disease(
            disease_query,
            fetch_chembl=fetch_chembl,
        )

        return {
            "domain": "drug_development",
            "task": task,
            "engine": "reverse_disease_engineering_pipeline",
            "result": result,
        }

    def _therapeutic_discovery_analysis(
        self,
        task: str,
        input_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Workflow 03 — Therapeutic Discovery pipeline.

        Input:
            {
                "disease":       "<free text query>",
                "mechanism_id":  <str, optional>,
                "target_id":     <str, optional>,
            }

        Output:
            {
                "domain": "drug_development",
                "task": task,
                "engine": "therapeutic_discovery_pipeline",
                "result": <serialized W03 result>,
            }

        Never raises for an unresolvable disease or a
        request that returns no candidates. The W03 service
        returns a well-formed result with
        resolution_status="unresolved" or "no_candidates"
        in those cases.
        """

        disease_query = str(
            input_data.get("disease") or ""
        ).strip()

        mechanism_id_raw = input_data.get("mechanism_id")
        mechanism_id = (
            str(mechanism_id_raw).strip()
            if isinstance(mechanism_id_raw, str)
            and mechanism_id_raw.strip()
            else None
        )

        target_id_raw = input_data.get("target_id")
        target_id = (
            str(target_id_raw).strip()
            if isinstance(target_id_raw, str)
            and target_id_raw.strip()
            else None
        )

        result = run_therapeutic_discovery(
            disease_query=disease_query,
            mechanism_id=mechanism_id,
            target_id=target_id,
        )

        return {
            "domain": "drug_development",
            "task": task,
            "engine": "therapeutic_discovery_pipeline",
            "result": result,
        }

    # ------------------------------------------------------------------
    # Medicine domain handlers
    # ------------------------------------------------------------------

    def _medicine_virtual_disease_analysis(
        self,
        task: str,
        input_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Workflow 01 — Virtual Disease Simulation.

        Input:
            {
                "disease":   "<free text>",
                "cell_type": <optional str>,
                "context":   <optional str>,
            }

        Output:
            {
                "domain": "medicine",
                "task": task,
                "engine": "medicine_simulation_pipeline",
                "result": <serialized SimulationResult>,
            }

        Raises ValueError for a missing disease, matching the
        convention used by the other analysis methods.
        """
        disease = str(input_data.get("disease") or "").strip()
        if not disease:
            raise ValueError(
                "A disease query is required for the virtual "
                "disease simulation."
            )

        cell_type_raw = input_data.get("cell_type")
        cell_type = (
            str(cell_type_raw).strip()
            if isinstance(cell_type_raw, str) and cell_type_raw.strip()
            else None
        )

        context_raw = input_data.get("context")
        context = (
            str(context_raw).strip()
            if isinstance(context_raw, str) and context_raw.strip()
            else None
        )

        service = _medicine_service()
        result = service.run_virtual_disease_simulation(
            disease=disease,
            cell_type=cell_type,
            context=context,
        )

        from app.medicine.simulation import schemas as medicine_schemas

        return {
            "domain": "medicine",
            "task": task,
            "engine": "medicine_simulation_pipeline",
            "result": medicine_schemas.to_wire(result),
        }

    def _medicine_treatment_analysis(
        self,
        task: str,
        input_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Workflow 02 — Treatment Simulation.
        """
        disease = str(input_data.get("disease") or "").strip()
        if not disease:
            raise ValueError(
                "A disease query is required for the treatment "
                "simulation."
            )

        intervention_raw = input_data.get("intervention_id")
        intervention_id = (
            str(intervention_raw).strip()
            if isinstance(intervention_raw, str) and intervention_raw.strip()
            else None
        )
        if not intervention_id:
            raise ValueError(
                "An intervention id or query is required for "
                "the treatment simulation."
            )

        baseline_raw = input_data.get("baseline_id")
        baseline_id = (
            str(baseline_raw).strip()
            if isinstance(baseline_raw, str) and baseline_raw.strip()
            else None
        )

        service = _medicine_service()
        result = service.run_treatment_simulation(
            disease=disease,
            intervention_id=intervention_id,
            baseline_id=baseline_id,
        )

        from app.medicine.simulation import schemas as medicine_schemas

        return {
            "domain": "medicine",
            "task": task,
            "engine": "medicine_simulation_pipeline",
            "result": medicine_schemas.to_wire(result),
        }

    def _medicine_combination_analysis(
        self,
        task: str,
        input_data: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Workflow 03 — Combination Treatment Simulation.
        """
        disease = str(input_data.get("disease") or "").strip()
        if not disease:
            raise ValueError(
                "A disease query is required for the "
                "combination treatment simulation."
            )

        a_raw = input_data.get("intervention_a_id")
        intervention_a_id = (
            str(a_raw).strip()
            if isinstance(a_raw, str) and a_raw.strip()
            else None
        )
        if not intervention_a_id:
            raise ValueError(
                "An intervention A id or query is required."
            )

        b_raw = input_data.get("intervention_b_id")
        intervention_b_id = (
            str(b_raw).strip()
            if isinstance(b_raw, str) and b_raw.strip()
            else None
        )
        if not intervention_b_id:
            raise ValueError(
                "An intervention B id or query is required."
            )

        baseline_raw = input_data.get("baseline_id")
        baseline_id = (
            str(baseline_raw).strip()
            if isinstance(baseline_raw, str) and baseline_raw.strip()
            else None
        )

        service = _medicine_service()
        result = service.run_combination_treatment_simulation(
            disease=disease,
            intervention_a_id=intervention_a_id,
            intervention_b_id=intervention_b_id,
            baseline_id=baseline_id,
        )

        from app.medicine.simulation import schemas as medicine_schemas

        return {
            "domain": "medicine",
            "task": task,
            "engine": "medicine_simulation_pipeline",
            "result": medicine_schemas.to_wire(result),
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
