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

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "CureVerseAI/1.0",
        }

        post_url = (
            f"{ENSEMBL_BASE_URL}"
            "/lookup/symbol/homo_sapiens"
        )

        get_url = (
            f"{ENSEMBL_BASE_URL}"
            f"/lookup/symbol/homo_sapiens/{symbol}"
        )

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

                    response = client.post(
                        post_url,
                        headers=headers,
                        json={
                            "symbols": [symbol],
                        },
                    )

                if response.status_code == 404:
                    return None

                if response.status_code in {
                    429,
                    500,
                    502,
                    503,
                    504,
                }:
                    last_error = RuntimeError(
                        f"Ensembl POST returned HTTP "
                        f"{response.status_code}"
                    )

                    if attempt < self.max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue

                    break

                response.raise_for_status()

                payload = response.json()

                gene = payload.get(symbol)

                if gene:
                    return gene

                return None

            except httpx.TimeoutException:
                last_error = RuntimeError(
                    f"Ensembl request timed out for {symbol}."
                )

            except httpx.RequestError as exc:
                last_error = RuntimeError(
                    f"Unable to reach Ensembl for {symbol}: {exc}"
                )

            if attempt < self.max_retries - 1:
                time.sleep(2 ** attempt)

        # ---------------------------------------------------------
        # GET fallback
        # ---------------------------------------------------------

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
                    get_url,
                    headers={
                        "Accept": "application/json",
                        "User-Agent": "CureVerseAI/1.0",
                    },
                )

            if response.status_code == 404:
                return None

            if response.status_code in {
                429,
                500,
                502,
                503,
                504,
            }:
                raise RuntimeError(
                    f"Ensembl GET returned HTTP "
                    f"{response.status_code}"
                )

            response.raise_for_status()

            return response.json()

        except httpx.TimeoutException:
            raise RuntimeError(
                f"Ensembl GET request timed out for {symbol}."
            )

        except httpx.RequestError as exc:
            raise RuntimeError(
                f"Unable to reach Ensembl GET for "
                f"{symbol}: {exc}"
            )

        except RuntimeError:
            if last_error:
                raise last_error

            raise

    def lookup_gene_batch(self, symbols):
        """
        Retrieve multiple human gene symbols in one Ensembl
        request.
        """

        normalized_symbols = [
            symbol.strip().upper()
            for symbol in symbols
            if symbol and symbol.strip()
        ]

        if not normalized_symbols:
            return {}

        url = (
            f"{ENSEMBL_BASE_URL}"
            "/lookup/symbol/homo_sapiens"
        )

        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "User-Agent": "CureVerseAI/1.0",
        }

        with httpx.Client(
            timeout=httpx.Timeout(
                connect=10.0,
                read=self.timeout,
                write=10.0,
                pool=10.0,
            ),
            follow_redirects=True,
        ) as client:

            response = client.post(
                url,
                headers=headers,
                json={
                    "symbols": normalized_symbols,
                },
            )

        response.raise_for_status()

        return response.json()
