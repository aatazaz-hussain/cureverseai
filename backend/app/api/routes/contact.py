from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, Field

from app.services.contact import submit_contact


router = APIRouter(prefix="/contact", tags=["Contact"])


class ContactRequest(BaseModel):
    name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    conversation_type: Optional[str] = Field(
        default=None,
        max_length=150,
    )
    message: str = Field(..., min_length=5, max_length=10000)


@router.post("")
async def create_contact_message(request: ContactRequest):
    try:
        return await submit_contact(request.model_dump())
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Contact submission failed.",
                "message": str(exc),
            },
        ) from exc
