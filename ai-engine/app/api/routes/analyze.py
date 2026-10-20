from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.orchestrator.engine import (
    CureVerseAIOrchestrator,
    get_supported_domains,
)


router = APIRouter(
    prefix="/analyze",
    tags=["AI Orchestrator"],
)

orchestrator = CureVerseAIOrchestrator()


class AnalyzeRequest(BaseModel):
    domain: str = Field(
        ...,
        description="CureVerseAI domain.",
    )

    task: str = Field(
        ...,
        min_length=1,
        description="Requested AI task.",
    )

    input: Dict[str, Any] = Field(
        default_factory=dict,
    )


@router.get("/domains")
def supported_domains():
    return {
        "domains": get_supported_domains(),
        "count": len(get_supported_domains()),
    }


@router.get("/medicine/curated")
def medicine_curated():
    """
    Return the list of disease + cell-context pairs the
    Medicine simulation is currently curated to model.

    Read-only. Contains no scientific claim; it is an index
    of the curated vocabulary version currently loaded.

    Response shape:

        {
            "success": True,
            "version": FUNCTION_MAPPER_VERSION,
            "count": <int>,
            "curated": [
                {
                    "disease_id":        "MONDO:0004979",
                    "disease_name":      "asthma",
                    "cell_context_id":   "CL:0000064",
                    "cell_context_name": "ciliated cell",
                },
                ...
            ],
        }

    If the Medicine vocabulary cannot be imported, the route
    returns success=False with an explicit reason, never a
    fabricated list.
    """

    try:
        from app.medicine.simulation import function_vocabulary as fv
    except Exception as exc:
        return {
            "success": False,
            "error": "Medicine vocabulary unavailable.",
            "message": str(exc),
            "curated": [],
            "count": 0,
        }

    pairs = fv.list_curated_diseases()

    return {
        "success": True,
        "version": fv.FUNCTION_MAPPER_VERSION,
        "count": len(pairs),
        "curated": pairs,
    }


@router.post("")
def analyze(request: AnalyzeRequest):

    try:
        result = orchestrator.analyze(
            domain=request.domain,
            task=request.task,
            input_data=request.input,
        )

        return {
            "success": True,
            "domain": request.domain.lower(),
            "task": request.task,
            "data": result,
        }

    except ValueError as exc:
        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Analysis failed.",
                "message": str(exc),
            },
        ) from exc
