from fastapi import FastAPI

app = FastAPI(
    title="CureVerseAI API",
    description="AI-powered Virtual Cell platform",
    version="0.1.0"
)


@app.get("/")
def root():
    return {
        "project": "CureVerseAI",
        "status": "online",
        "message": "Virtual Cell AI Engine API"
    }


@app.get("/health")
def health():
    return {
        "status": "healthy"
    }

