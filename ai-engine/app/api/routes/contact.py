from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, EmailStr, Field

from app.db.database import SessionLocal
from app.db.models import ContactMessage


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
def create_contact_message(request: ContactRequest):
    db = SessionLocal()

    try:
        contact = ContactMessage(
            name=request.name.strip(),
            email=str(request.email),
            conversation_type=(
                request.conversation_type.strip()
                if request.conversation_type
                else None
            ),
            message=request.message.strip(),
            status="new",
        )

        db.add(contact)
        db.commit()
        db.refresh(contact)

        return {
            "success": True,
            "message": "Contact message received successfully.",
            "data": {
                "id": contact.id,
                "status": contact.status,
                "created_at": (
                    contact.created_at.isoformat()
                    if contact.created_at
                    else None
                ),
            },
        }

    except Exception as exc:
        db.rollback()

        raise HTTPException(
            status_code=500,
            detail={
                "error": "Failed to store contact message.",
                "message": str(exc),
            },
        ) from exc

    finally:
        db.close()
