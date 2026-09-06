from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.health import router as health_router
from app.api.routes.analyze import router as analyze_router
from app.api.routes.contact import router as contact_router


app = FastAPI(
    title="CureVerseAI API",
    description=(
        "AI-powered biomedical intelligence platform for "
        "research, drug development, medicine, biotechnology, "
        "and education."
    ),
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(
    health_router,
    prefix="/api/v1",
)

app.include_router(analyze_router, prefix="/api/v1")
app.include_router(contact_router, prefix="/api/v1")


@app.get("/")
def root():
    return {
        "name": "CureVerseAI",
        "status": "online",
        "version": "1.0.0",
        "message": "CureVerseAI API is running.",
    }
