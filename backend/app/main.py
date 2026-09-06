from fastapi import FastAPI

from app.api.routes.health import router as health_router
from app.api.routes.analyze import router as analyze_router


app = FastAPI(
    title="CureVerseAI API",
    description=(
        "AI-powered biomedical intelligence platform for "
        "research, drug development, medicine, biotechnology, "
        "and education."
    ),
    version="1.0.0",
)


app.include_router(
    health_router,
    prefix="/api/v1",
)

app.include_router(analyze_router, prefix="/api/v1")


@app.get("/")
def root():
    return {
        "name": "CureVerseAI",
        "status": "online",
        "version": "1.0.0",
        "message": "CureVerseAI API is running.",
    }
