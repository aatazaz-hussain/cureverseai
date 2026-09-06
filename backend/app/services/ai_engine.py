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
