import os
from typing import Any, Dict

import httpx


AI_ENGINE_URL = os.getenv(
    "CUREVERSEAI_AI_ENGINE_URL",
    "http://localhost:8001",
)


async def analyze(payload: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{AI_ENGINE_URL}/api/v1/analyze"

    timeout = httpx.Timeout(
        connect=10.0,
        read=300.0,
        write=30.0,
        pool=30.0,
    )

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(
            url,
            json=payload,
        )

        response.raise_for_status()
        return response.json()


async def analyze_drug_development(
    payload: Dict[str, Any],
) -> Dict[str, Any]:
    url = f"{AI_ENGINE_URL}/internal/drug-development/analyze"

    timeout = httpx.Timeout(
        connect=10.0,
        read=300.0,
        write=30.0,
        pool=30.0,
    )

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(
            url,
            json=payload,
        )

        response.raise_for_status()
        return response.json()


async def get_medicine_curated() -> Dict[str, Any]:
    """
    Fetch the list of curated disease + cell-context pairs
    from the AI Engine.

    Endpoint:
        GET {AI_ENGINE_URL}/api/v1/analyze/medicine/curated

    Returns the AI Engine's JSON response verbatim. The
    response shape is documented in the AI Engine route and
    contains only the curated vocabulary entries plus a
    version string; it carries no scientific claim.

    Raises httpx.HTTPError subclasses (TimeoutException,
    HTTPStatusError, RequestError) on failure. The caller
    (the backend route) is responsible for translating those
    into the appropriate HTTP response.
    """
    url = f"{AI_ENGINE_URL}/api/v1/analyze/medicine/curated"

    timeout = httpx.Timeout(
        connect=10.0,
        read=30.0,
        write=10.0,
        pool=10.0,
    )

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.get(url)

        response.raise_for_status()
        return response.json()
