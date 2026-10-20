import time
from pathlib import Path as _Path

import httpx

from app.data.cache import DiskCache


ENSEMBL_BASE_URL = "https://rest.ensembl.org"

#: Default cache location for Ensembl lookups. Overridable
#: via the EnsemblClient constructor for tests.
_DEFAULT_CACHE_DIR = (
    _Path(__file__).resolve().parents[3]
    / "data" / "cache" / "ensembl"
)

#: Default TTL for cached Ensembl responses: 30 days.
#: Gene and protein annotations change on the scale of
#: months, not hours, so a long TTL is correct here.
_DEFAULT_CACHE_TTL = 30 * 24 * 3600


class EnsemblClient:
    def __init__(
        self,
        timeout: float = 30.0,
        max_retries: int = 3,
        cache_dir: str | None = None,
        cache_ttl: int = _DEFAULT_CACHE_TTL,
    ):
        self.timeout = timeout
        self.max_retries = max_retries

        self.cache = DiskCache(
            cache_dir or _DEFAULT_CACHE_DIR,
            ttl_seconds=cache_ttl,
        )

    def lookup_gene(self, symbol: str):
        symbol = symbol.strip().upper()

        if not symbol:
            raise ValueError("Gene symbol cannot be empty.")

        # --- cache check ------------------------------------
        cache_key = DiskCache.make_key("ensembl:lookup_gene", symbol)
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached.get("data")

        # --- network path -----------------------------------
        result = self._lookup_gene_uncached(symbol)

        self.cache.set(
            cache_key,
            {"data": result},
        )
        return result

    def _lookup_gene_uncached(self, symbol: str):
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

    def get_uniprot_sequence(self, accession: str):
        """Fetch the canonical protein sequence from UniProt."""
        accession = accession.strip().upper()

        if not accession:
            raise ValueError("UniProt accession cannot be empty.")

        url = (
            "https://rest.uniprot.org/uniprotkb/"
            f"{accession}.json"
        )

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

                if response.status_code in {
                    429,
                    500,
                    502,
                    503,
                    504,
                }:
                    last_error = RuntimeError(
                        f"UniProt sequence request returned HTTP "
                        f"{response.status_code}"
                    )
                    if attempt < self.max_retries - 1:
                        time.sleep(2 ** attempt)
                        continue

                response.raise_for_status()

                data = response.json()
                sequence = (data.get("sequence") or {}).get("value")

                if not sequence:
                    return None

                return {
                    "accession": accession,
                    "sequence": sequence,
                    "length": len(sequence),
                    "source": "UniProt",
                }

            except Exception as exc:
                last_error = exc
                if attempt < self.max_retries - 1:
                    time.sleep(2 ** attempt)

        raise RuntimeError(
            f"Failed to fetch UniProt sequence for {accession}: "
            f"{last_error}"
        )

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
    def get_uniprot_accessions(
        self,
        ensembl_id: str,
    ) -> list[str]:
        """
        Retrieve all UniProt accessions linked to an Ensembl gene ID.

        The Ensembl xrefs endpoint can return multiple UniProtKB
        mappings, including dependent entries. This method preserves
        all unique accessions and does not assume that the first
        accession is canonical.
        """

        ensembl_id = ensembl_id.strip()

        if not ensembl_id:
            raise ValueError(
                "Ensembl gene ID cannot be empty."
            )

        url = (
            f"{ENSEMBL_BASE_URL}"
            f"/xrefs/id/{ensembl_id}"
        )

        headers = {
            "Accept": "application/json",
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

            response = client.get(
                url,
                headers=headers,
            )

        if response.status_code == 404:
            return []

        if response.status_code in {
            429,
            500,
            502,
            503,
            504,
        }:
            raise RuntimeError(
                f"Ensembl xrefs returned HTTP "
                f"{response.status_code}"
            )

        response.raise_for_status()

        xrefs = response.json()

        accessions: list[str] = []

        for xref in xrefs:
            if xref.get("dbname") != "Uniprot_gn":
                continue

            accession = xref.get("primary_id")

            if (
                isinstance(accession, str)
                and accession.strip()
                and accession not in accessions
            ):
                accessions.append(
                    accession.strip()
                )

        return accessions

    def get_uniprot_mappings(
        self,
        ensembl_id: str,
    ) -> list[dict]:
        """
        Retrieve structured UniProt mappings from Ensembl.

        Unlike get_uniprot_accessions(), this preserves the metadata
        returned by Ensembl for each UniProt cross-reference.
        """

        ensembl_id = ensembl_id.strip()

        if not ensembl_id:
            raise ValueError(
                "Ensembl gene ID cannot be empty."
            )

        url = (
            f"{ENSEMBL_BASE_URL}"
            f"/xrefs/id/{ensembl_id}"
        )

        headers = {
            "Accept": "application/json",
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

            response = client.get(
                url,
                headers=headers,
            )

        if response.status_code == 404:
            return []

        if response.status_code in {
            429,
            500,
            502,
            503,
            504,
        }:
            raise RuntimeError(
                f"Ensembl xrefs returned HTTP "
                f"{response.status_code}"
            )

        response.raise_for_status()

        xrefs = response.json()

        mappings: list[dict] = []
        seen: set[str] = set()

        for xref in xrefs:
            if xref.get("dbname") != "Uniprot_gn":
                continue

            accession = xref.get("primary_id")

            if not isinstance(accession, str):
                continue

            accession = accession.strip()

            if not accession or accession in seen:
                continue

            seen.add(accession)

            mappings.append(
                {
                    "accession": accession,
                    "display_id": xref.get(
                        "display_id"
                    ),
                    "description": xref.get(
                        "description"
                    ),
                    "db_display_name": xref.get(
                        "db_display_name"
                    ),
                    "info_type": xref.get(
                        "info_type"
                    ),
                    "info_text": xref.get(
                        "info_text"
                    ),
                    "version": xref.get(
                        "version"
                    ),
                    "synonyms": xref.get(
                        "synonyms",
                        [],
                    ),
                    "source": "Ensembl",
                }
            )

        return mappings
    def resolve_reviewed_uniprot_accession(
        self,
        ensembl_id: str,
        organism: str = "Homo sapiens",
    ) -> dict | None:
        """
        Resolve the best UniProt accession for an Ensembl gene.

        Resolution strategy:
        1. Retrieve all UniProt mappings from Ensembl.
        2. Query UniProt metadata for each candidate.
        3. Prefer reviewed Swiss-Prot entries.
        4. Require the expected organism.
        5. Preserve the full candidate set for provenance.

        No accession is hard-coded.
        """

        # --- cache check ------------------------------------
        cache_key = DiskCache.make_key(
            "ensembl:resolve_uniprot",
            f"{ensembl_id}|{organism}",
        )
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached.get("data")

        # --- network path -----------------------------------
        result = self._resolve_reviewed_uniprot_accession_uncached(
            ensembl_id, organism
        )

        self.cache.set(
            cache_key,
            {"data": result},
        )
        return result

    def _resolve_reviewed_uniprot_accession_uncached(
        self,
        ensembl_id: str,
        organism: str = "Homo sapiens",
    ) -> dict | None:

        mappings = self.get_uniprot_mappings(
            ensembl_id
        )

        if not mappings:
            return None

        candidates: list[dict] = []

        headers = {
            "Accept": "application/json",
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

            for mapping in mappings:
                accession = mapping["accession"]

                url = (
                    "https://rest.uniprot.org/"
                    f"uniprotkb/{accession}.json"
                )

                try:
                    response = client.get(
                        url,
                        headers=headers,
                    )

                    if response.status_code == 404:
                        continue

                    if response.status_code in {
                        429,
                        500,
                        502,
                        503,
                        504,
                    }:
                        continue

                    response.raise_for_status()

                    data = response.json()

                except (
                    httpx.HTTPError,
                    ValueError,
                ):
                    continue

                entry_type = data.get(
                    "entryType"
                )

                scientific_name = (
                    data.get("organism", {})
                    .get("scientificName")
                )

                if scientific_name != organism:
                    continue

                reviewed = (
                    entry_type
                    == "UniProtKB reviewed (Swiss-Prot)"
                )

                candidates.append(
                    {
                        "accession": data.get(
                            "primaryAccession",
                            accession,
                        ),
                        "entry_type": entry_type,
                        "reviewed": reviewed,
                        "uniprot_id": data.get(
                            "uniProtkbId"
                        ),
                        "organism": scientific_name,
                        "protein_name": (
                            data.get(
                                "proteinDescription",
                                {}
                            )
                            .get(
                                "recommendedName",
                                {}
                            )
                            .get(
                                "fullName",
                                {}
                            )
                            .get("value")
                        ),
                        "ensembl_mapping": mapping,
                        "source": "UniProt",
                    }
                )

        if not candidates:
            return None

        candidates.sort(
            key=lambda item: (
                item["reviewed"],
            ),
            reverse=True,
        )

        selected = candidates[0]

        return {
            "accession": selected["accession"],
            "entry_type": selected["entry_type"],
            "reviewed": selected["reviewed"],
            "uniprot_id": selected["uniprot_id"],
            "organism": selected["organism"],
            "protein_name": selected["protein_name"],
            "candidates": candidates,
            "candidate_count": len(candidates),
            "selection_rule": (
                "Prefer reviewed Swiss-Prot "
                "entry for the expected organism."
            ),
            "ensembl_id": ensembl_id,
            "source": "Ensembl+UniProt",
        }
