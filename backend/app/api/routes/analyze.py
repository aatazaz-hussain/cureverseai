from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.ai_engine import analyze


router = APIRouter(prefix="/analyze", tags=["AI Analysis"])


class AnalyzeRequest(BaseModel):
    domain: str = Field(..., min_length=1)
    task: str = Field(..., min_length=1)
    input: Dict[str, Any] = Field(default_factory=dict)


@router.get("/domains")
async def domains():
    return {
        "domains": [
            "research",
            "drug_development",
            "medicine",
            "biotechnology",
            "education",
        ],
        "count": 5,
    }


@router.post("")
async def run_analysis(request: AnalyzeRequest):
    try:
        return await analyze(
            {
                "domain": request.domain,
                "task": request.task,
                "input": request.input,
            }
        )
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "CureVerseAI analysis failed.",
                "message": str(exc),
            },
        ) from exc
