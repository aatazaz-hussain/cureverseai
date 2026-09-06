from typing import Any, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.models.inference.inference_engine import BiologicalInferenceEngine


router = APIRouter(
    prefix="/drug-development",
    tags=["Drug Development"],
)


class DrugDevelopmentRequest(BaseModel):
    gene: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Gene symbol, for example TP53.",
    )
    smiles: Optional[str] = Field(
        default=None,
        description="Optional molecular SMILES string.",
    )
    cell_state: Optional[dict[str, Any]] = Field(
        default=None,
        description="Optional cellular state.",
    )


_engine: Optional[BiologicalInferenceEngine] = None


def get_engine() -> BiologicalInferenceEngine:
    global _engine

    if _engine is None:
        _engine = BiologicalInferenceEngine()

    return _engine


@router.post("/analyze")
def analyze_drug_development(
    request: DrugDevelopmentRequest,
):
    try:
        engine = get_engine()

        result = engine.analyze_gene(
            gene=request.gene,
            smiles=request.smiles,
            cell_state=request.cell_state,
        )

        return {
            "success": True,
            "domain": "drug_development",
            "analysis_type": "integrated_biological_analysis",
            "data": result,
        }

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Drug development analysis failed.",
                "message": str(exc),
            },
        ) from exc
