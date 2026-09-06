from typing import Any, Dict

import httpx

from app.services.ai_engine import AI_ENGINE_URL


async def submit_contact(payload: Dict[str, Any]) -> Dict[str, Any]:
    url = f"{AI_ENGINE_URL}/internal/contact"

    timeout = httpx.Timeout(
        connect=10.0,
        read=30.0,
        write=30.0,
        pool=30.0,
    )

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(url, json=payload)
        response.raise_for_status()
        return response.json()
