from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from app.simulation.virtual_cell import simulate_gene_perturbation


app = FastAPI(
    title="CureVerseAI API",
    description="AI-powered Virtual Cell platform",
    version="0.2.0"
)


class PerturbationRequest(BaseModel):
    gene: str
    effect: str = "inhibit"


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


@app.post("/api/simulate/gene")
def simulate_gene(request: PerturbationRequest):
    try:
        result = simulate_gene_perturbation(
            request.gene,
            request.effect
        )

        return {
            "success": True,
            "simulation": result
        }

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error)
        )
