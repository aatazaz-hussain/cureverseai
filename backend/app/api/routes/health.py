from datetime import datetime, timezone

from fastapi import APIRouter


router = APIRouter(
    prefix="/health",
    tags=["System"],
)


@router.get("")
def health_check():
    return {
        "status": "healthy",
        "service": "CureVerseAI API",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
