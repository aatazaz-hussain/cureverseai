import time

import httpx


ENSEMBL_BASE_URL = "https://rest.ensembl.org"


class EnsemblClient:
    def __init__(
        self,
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        self.timeout = timeout
        self.max_retries = max_retries

    def lookup_gene(self, symbol: str):
        symbol = symbol.strip().upper()

        if not symbol:
            raise ValueError("Gene symbol cannot be empty.")

        url = f"{ENSEMBL_BASE_URL}/lookup/symbol/homo_sapiens/{symbol}"

        headers = {
            "Accept": "application/json",
            "User-Agent": "CureVerseAI/1.0",
        }

        last_error = None

        for attempt in range(self.max_retries):
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
                        headers=headers,
                    )

                if response.status_code == 404:
                    return None

                if response.status_code in {429, 500, 502, 503, 504}:
                    last_error = RuntimeError(
                        f"Ensembl returned HTTP "
                        f"{response.status_code}"
                    )

                    if attempt < self.max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue

                    raise last_error

                response.raise_for_status()

                return response.json()

            except httpx.TimeoutException as exc:
                last_error = RuntimeError(
                    f"Ensembl request timed out for {symbol}."
                )

            except httpx.RequestError as exc:
                last_error = RuntimeError(
                    f"Unable to reach Ensembl for {symbol}: {exc}"
                )

            if attempt < self.max_retries - 1:
                time.sleep(2 ** attempt)

        raise last_error or RuntimeError(
            f"Unable to retrieve Ensembl data for {symbol}."
        )
