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
