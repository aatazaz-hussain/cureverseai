from typing import Any, Dict

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.ai_engine import AI_ENGINE_URL
import httpx

router = APIRouter(prefix="/variants", tags=["Variants"])


class VariantRequest(BaseModel):
    gene: str = Field(..., min_length=2, max_length=30)
    variant: str = Field(..., min_length=2, max_length=50)


@router.post("/analyze")
async def analyze_variant(request: VariantRequest) -> Dict[str, Any]:
    payload = {
        "gene": request.gene.strip().upper(),
        "variant": request.variant.strip().upper(),
    }

    try:
        async with httpx.AsyncClient(
            timeout=httpx.Timeout(
                connect=10.0,
                read=120.0,
                write=30.0,
                pool=30.0,
            )
        ) as client:
            response = await client.post(
                f"{AI_ENGINE_URL}/internal/variants/analyze",
                json=payload,
            )

        response.raise_for_status()
        return response.json()

    except httpx.HTTPStatusError as exc:
        try:
            detail = exc.response.json()
        except Exception:
            detail = exc.response.text

        raise HTTPException(
            status_code=exc.response.status_code,
            detail=detail,
        ) from exc

    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "error": "Variant analysis service unavailable.",
                "message": str(exc),
            },
        ) from exc
