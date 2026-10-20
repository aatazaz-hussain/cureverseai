"""
CureVerseAI — Drug Development
GTEx Portal API client.

Provides gene -> tissue median expression used by the
Disease -> Tissue layer of the Biological Impact Graph.

Why GTEx
--------

GTEx publishes bulk RNA-seq median expression per tissue
across 54 human tissue sites. It is the standard source for
tissue-specific expression, is free, has no API key, and
returns TPM values that can be reasoned about directly.

Two-step resolution
-------------------

GTEx versioned GENCODE IDs must match the dataset version.
The gtex_v10 dataset expects gencode v39 IDs (for example
"ENSG00000141510.18", not "...17"). Using the wrong version
silently returns zero expression rows.

Therefore this client ALWAYS resolves a gene symbol to a
versioned GENCODE ID against the current dataset version
before querying expression. No versioned ID is ever
hardcoded.

Endpoints used
--------------

    GET /reference/gene
        ?geneId=TP53
        &gencodeVersion=v39
        &genomeBuild=GRCh38/hg38

    GET /expression/medianGeneExpression
        ?gencodeId=ENSG00000141510.18
        &datasetId=gtex_v10

What this client does NOT do
----------------------------

- It does not threshold or filter by TPM. That is the
  mapper's concern (Phase 03 File 4b).
- It does not aggregate across genes. That is also the
  mapper's concern.
- It does not map GTEx tissue IDs to Uberon. GTEx IDs are
  used verbatim.
- It does not interpret TPM as anything other than the
  unit GTEx publishes. No score, no confidence.

Conventions
-----------

- httpx only.
- 404 returns an empty result, not an exception.
- Other HTTP errors raise RuntimeError.
- Empty inputs raise ValueError.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx


class GTExClient:
    """
    Minimal GTEx Portal V2 API client.
    """

    BASE_URL = "https://gtexportal.org/api/v2"

    #: Pinned dataset + gencode versions. If GTEx moves the
    #: current default these must be updated together.
    DATASET_ID = "gtex_v10"
    GENCODE_VERSION = "v39"
    GENOME_BUILD = "GRCh38/hg38"

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get(
        self,
        path: str,
        params: Dict[str, Any],
    ) -> Optional[Dict[str, Any]]:
        """
        Perform a GET against GTEx. 404 returns None.
        """

        url = f"{self.BASE_URL}{path}"

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
                    params=params,
                    headers={
                        "Accept": "application/json",
                        "User-Agent": "CureVerseAI/1.0",
                    },
                )

        except httpx.TimeoutException as exc:
            raise RuntimeError(
                f"GTEx request timed out: {url}"
            ) from exc

        except httpx.RequestError as exc:
            raise RuntimeError(
                f"Unable to reach GTEx: {exc}"
            ) from exc

        if response.status_code == 404:
            return None

        if response.status_code >= 400:
            raise RuntimeError(
                f"GTEx returned HTTP {response.status_code} "
                f"for {url}"
            )

        return response.json()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def resolve_gencode_id(
        self,
        gene_symbol: str,
    ) -> Optional[str]:
        """
        Resolve a gene symbol to a versioned GENCODE ID for
        the pinned dataset version.

        Returns None if the symbol cannot be resolved.
        """

        gene_symbol = (gene_symbol or "").strip()

        if not gene_symbol:
            raise ValueError(
                "Gene symbol cannot be empty."
            )

        payload = self._get(
            "/reference/gene",
            params={
                "geneId": gene_symbol,
                "gencodeVersion": self.GENCODE_VERSION,
                "genomeBuild": self.GENOME_BUILD,
                "format": "json",
            },
        )

        if not payload:
            return None

        items = payload.get("data") or []

        for item in items:
            if not isinstance(item, dict):
                continue

            symbol = item.get("geneSymbol")
            gencode_id = item.get("gencodeId")

            if (
                symbol
                and symbol.upper() == gene_symbol.upper()
                and gencode_id
            ):
                return str(gencode_id)

        return None

    def get_median_expression(
        self,
        gencode_id: str,
    ) -> Dict[str, Any]:
        """
        Retrieve median gene expression per tissue for a
        versioned GENCODE ID.

        Return shape:

            {
                "gencode_id": <input>,
                "dataset_id": <dataset>,
                "tissues": [
                    {
                        "tissue_id":   "Brain_Cortex",
                        "median_tpm":  123.45,
                        "unit":        "TPM",
                    },
                    ...
                ],
                "count":    <number of tissues>,
                "source":   "GTEx",
                "found":    <bool>,
            }

        A gencode_id with no data returns an empty tissue
        list and found=False.
        """

        gencode_id = (gencode_id or "").strip()

        if not gencode_id:
            raise ValueError(
                "GENCODE ID cannot be empty."
            )

        payload = self._get(
            "/expression/medianGeneExpression",
            params={
                "gencodeId": gencode_id,
                "datasetId": self.DATASET_ID,
                "format": "json",
            },
        )

        if not payload:
            return self._empty(gencode_id)

        items = payload.get("data") or []

        tissues: List[Dict[str, Any]] = []

        for item in items:
            if not isinstance(item, dict):
                continue

            tissue_id = item.get("tissueSiteDetailId")
            median = item.get("median")
            unit = item.get("unit") or "TPM"

            if not tissue_id:
                continue

            try:
                median_value = float(median)
            except (TypeError, ValueError):
                continue

            tissues.append(
                {
                    "tissue_id": str(tissue_id),
                    "median_tpm": median_value,
                    "unit": str(unit),
                }
            )

        return {
            "gencode_id": gencode_id,
            "dataset_id": self.DATASET_ID,
            "tissues": tissues,
            "count": len(tissues),
            "source": "GTEx",
            "found": len(tissues) > 0,
        }

    # ------------------------------------------------------------------
    # Composite
    # ------------------------------------------------------------------

    def get_gene_tissue_expression(
        self,
        gene_symbol: str,
    ) -> Dict[str, Any]:
        """
        Resolve a gene symbol and retrieve tissue expression
        in one call.

        Returns:

            {
                "gene_symbol":    <input>,
                "gencode_id":     <resolved or None>,
                "tissues":        [...],
                "count":          <int>,
                "source":         "GTEx",
                "found":          <bool>,
                "reason":         <str or None>,
            }
        """

        gencode_id = self.resolve_gencode_id(gene_symbol)

        if not gencode_id:
            return {
                "gene_symbol": gene_symbol,
                "gencode_id": None,
                "tissues": [],
                "count": 0,
                "source": "GTEx",
                "found": False,
                "reason": (
                    f"Gene symbol '{gene_symbol}' could not "
                    f"be resolved to a versioned GENCODE ID "
                    f"for {self.DATASET_ID}."
                ),
            }

        expr = self.get_median_expression(gencode_id)

        return {
            "gene_symbol": gene_symbol,
            "gencode_id": gencode_id,
            "tissues": expr["tissues"],
            "count": expr["count"],
            "source": "GTEx",
            "found": expr["found"],
            "reason": None if expr["found"] else (
                "No median expression rows returned for "
                f"{gencode_id}."
            ),
        }

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _empty(gencode_id: str) -> Dict[str, Any]:
        return {
            "gencode_id": gencode_id,
            "dataset_id": GTExClient.DATASET_ID,
            "tissues": [],
            "count": 0,
            "source": "GTEx",
            "found": False,
        }
