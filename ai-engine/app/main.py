from fastapi import FastAPI
from app.api.routes.analyze import router as analyze_router
from app.api.routes.contact import router as contact_router
from app.api.routes.drug_development import router as drug_development_router


app = FastAPI(
    title="CureVerseAI AI Engine",
    description=(
        "Core AI and biomedical intelligence engine for CureVerseAI."
    ),
    version="1.0.0",
)


app.include_router(
    drug_development_router,
    prefix="/internal",
)
app.include_router(
    contact_router,
    prefix="/internal",
)
app.include_router(
    analyze_router,
    prefix="/api/v1",
)

@app.get("/")
def root():
    return {
        "service": "CureVerseAI AI Engine",
        "status": "online",
        "version": "1.0.0",
    }


@app.get("/health")
def health():
    return {
        "status": "healthy",
        "service": "ai-engine",
    }
