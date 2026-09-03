import httpx


REACTOME_BASE_URL = "https://reactome.org/ContentService"


class ReactomeClient:
    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout

    def database_version(self):
        url = f"{REACTOME_BASE_URL}/data/database/version"

        try:
            with httpx.Client(
                timeout=httpx.Timeout(
                    connect=10.0,
                    read=self.timeout,
                    write=10.0,
                    pool=10.0,
                ),
                follow_redirects=True,
            ) as client:

                response = client.get(
                    url,
                    headers={
                        "Accept": "text/plain",
                        "User-Agent": "CureVerseAI/1.0",
                    },
                )

        except httpx.TimeoutException as exc:
            raise RuntimeError(
                "Reactome request timed out."
            ) from exc

        except httpx.RequestError as exc:
            raise RuntimeError(
                f"Unable to reach Reactome: {exc}"
            ) from exc

        response.raise_for_status()

        return response.text.strip()

    def search_pathways(self, query: str):
        query = query.strip()

        if not query:
            raise ValueError("Reactome search query cannot be empty.")

        url = f"{REACTOME_BASE_URL}/search/query"

        try:
            with httpx.Client(
                timeout=httpx.Timeout(
                    connect=10.0,
                    read=self.timeout,
                    write=10.0,
                    pool=10.0,
                ),
                follow_redirects=True,
            ) as client:

                response = client.get(
                    url,
                    params={
                        "query": query,
                        "cluster": "true",
                        "format": "json",
                    },
                    headers={
                        "Accept": "application/json",
                        "User-Agent": "CureVerseAI/1.0",
                    },
                )

        except httpx.TimeoutException as exc:
            raise RuntimeError(
                f"Reactome search timed out for '{query}'."
            ) from exc

        except httpx.RequestError as exc:
            raise RuntimeError(
                f"Unable to reach Reactome: {exc}"
            ) from exc

        response.raise_for_status()

        return response.json()
