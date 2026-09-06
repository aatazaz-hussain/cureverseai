from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.models.inference.inference_engine import BiologicalInferenceEngine

router = APIRouter(prefix="/variants", tags=["Variants"])

engine = BiologicalInferenceEngine()


class VariantRequest(BaseModel):
    gene: str = Field(..., min_length=2, max_length=30)
    variant: str = Field(..., min_length=2, max_length=50)


@router.post("/analyze")
def analyze_variant(request: VariantRequest) -> Dict[str, Any]:
    gene = request.gene.strip().upper()
    variant = request.variant.strip().upper()

    if not gene or not variant:
        raise HTTPException(
            status_code=400,
            detail="Gene and variant are required.",
        )

    try:
        result = engine.analyze_gene(
            gene=gene,
        )

        integrated = result.get("integrated_features") or {}
        context = result.get("biological_context") or {}
        reactome = context.get("reactome_entities") or []

        # Resolve canonical biological identity from the existing
        # inference-engine result.
        gene_record = context.get("gene") or result.get("gene_record") or {}
        if hasattr(gene_record, "__dict__"):
            gene_record = vars(gene_record)

        canonical_transcript = (
            result.get("canonical_transcript")
            or result.get("canonical_transcript_id")
            or gene_record.get("canonical_transcript")
            or gene_record.get("canonical_transcript_id")
            or ""
        )

        # Evidence sources are already represented by the reasoning layer.
        evidence_reasoning = result.get("evidence_reasoning") or {}
        reasoning_sources = evidence_reasoning.get("sources") or []

        evidence_sources = []

        if isinstance(reasoning_sources, list):
            for source in reasoning_sources:
                if isinstance(source, dict):
                    source_name = (
                        source.get("source")
                        or source.get("name")
                        or source.get("provider")
                    )
                else:
                    source_name = str(source)

                if source_name:
                    evidence_sources.append(str(source_name))

        # Also include known evidence layers when their result blocks exist.
        if context.get("gene") or result.get("ensembl"):
            evidence_sources.append("Ensembl")

        if result.get("uniprot_resolution"):
            evidence_sources.append("UniProt")

        if reactome:
            evidence_sources.append("Reactome")

        if result.get("open_targets"):
            evidence_sources.append("Open Targets")

        if result.get("chembl_evidence"):
            evidence_sources.append("ChEMBL")

        if result.get("protein_features"):
            evidence_sources.append("ESM-2")

        evidence_sources = list(dict.fromkeys(evidence_sources))

        matching_entities = []

        for entity in reactome:
            if hasattr(entity, "name"):
                name = str(entity.name or "")
                entity_data = {
                    "name": entity.name,
                    "identifier": entity.identifier,
                    "source": entity.source,
                    "species": entity.species,
                    "compartment": entity.compartment,
                    "metadata": entity.metadata,
                }
            else:
                name = str(entity.get("name") or "")
                entity_data = entity
            if variant in name.upper():
                matching_entities.append(entity_data)

        return {
            "success": True,
            "domain": "research",
            "task": "variant_investigation",
            "data": {
                "gene": gene,
                "variant": variant,
                "match_count": len(matching_entities),
                "variant_matches": matching_entities,
                "canonical_transcript": canonical_transcript,
                "evidence_sources": evidence_sources,
                "evidence_source_count": len(evidence_sources),
                "analysis": result,
            },
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Variant analysis failed.",
                "message": str(exc),
            },
        ) from exc
