from typing import Any, Dict

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

router = APIRouter(prefix="/proteins", tags=["Proteins"])

UNIPROT_SEARCH_URL = "https://rest.uniprot.org/uniprotkb/search"


class ProteinResolveRequest(BaseModel):
    query: str = Field(..., min_length=2, max_length=500)


def build_queries(query: str) -> list[str]:
    clean = query.strip().replace('"', "")

    return [
        f'"{clean}"',
        clean,
    ]


async def search_uniprot(query: str) -> Dict[str, Any]:
    last_error = None

    async with httpx.AsyncClient(
        timeout=httpx.Timeout(
            connect=10.0,
            read=30.0,
            write=30.0,
            pool=30.0,
        )
    ) as client:

        for search_query in build_queries(query):
            params = {
                "query": search_query,
                "format": "json",
                "fields": (
                    "accession,id,protein_name,gene_names,"
                    "organism_name,length"
                ),
                "size": 10,
            }

            try:
                response = await client.get(
                    UNIPROT_SEARCH_URL,
                    params=params,
                )

                response.raise_for_status()

                return response.json()

            except httpx.HTTPStatusError as exc:
                last_error = exc

                # Try the next, simpler UniProt query.
                continue

            except Exception as exc:
                last_error = exc
                continue

    raise HTTPException(
        status_code=502,
        detail={
            "error": "UniProt resolution failed.",
            "message": str(last_error),
        },
    )


@router.post("/resolve")
async def resolve_protein(request: ProteinResolveRequest):
    query = request.query.strip()

    if not query:
        raise HTTPException(
            status_code=400,
            detail="Protein query is required.",
        )

    payload = await search_uniprot(query)

    results = payload.get("results", [])

    if not results:
        raise HTTPException(
            status_code=404,
            detail={
                "error": "Protein not found.",
                "message": (
                    f'No UniProt protein could be resolved for "{query}".'
                ),
            },
        )

    candidates = []

    for item in results:
        accession = item.get("primaryAccession")

        protein_description = item.get("proteinDescription") or {}

        recommended_name = (
            protein_description.get("recommendedName") or {}
        )

        protein_name = (
            recommended_name.get("fullName") or {}
        ).get("value")

        if not protein_name:
            submission_names = (
                protein_description.get("submissionNames") or []
            )

            if submission_names:
                protein_name = (
                    submission_names[0]
                    .get("fullName", {})
                    .get("value")
                )

        genes = item.get("genes") or []

        gene_symbol = None

        if genes:
            gene_symbol = (
                genes[0]
                .get("geneName", {})
                .get("value")
            )

        organism = (
            item.get("organism", {})
            .get("scientificName")
        )

        sequence_length = (
            item.get("sequence", {})
            .get("length")
        )

        entry_id = item.get("uniProtkbId")

        reviewed = (
            item.get("entryType")
            == "UniProtKB reviewed (Swiss-Prot)"
        )

        candidates.append(
            {
                "accession": accession,
                "entry_id": entry_id,
                "protein_name": protein_name,
                "gene_symbol": gene_symbol,
                "organism": organism,
                "sequence_length": sequence_length,
                "reviewed": reviewed,
            }
        )

    # Strongly prefer:
    # 1. Human proteins
    # 2. Reviewed Swiss-Prot proteins
    # 3. Results with a gene symbol
    # 4. Results with a protein name
    candidates.sort(
        key=lambda item: (
            item.get("organism") == "Homo sapiens",
            item.get("reviewed") is True,
            bool(item.get("gene_symbol")),
            bool(item.get("protein_name")),
        ),
        reverse=True,
    )

    selected = candidates[0]

    return {
        "success": True,
        "query": query,
        "resolved": True,
        "selected": selected,
        "candidates": candidates,
        "source": "UniProt",
    }
