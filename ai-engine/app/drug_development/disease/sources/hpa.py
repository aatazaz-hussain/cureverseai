"""
CureVerseAI — Drug Development
Human Protein Atlas (HPA) client.

Provides gene -> cell type expression used by the Cellular
Context layer of the Biological Impact Graph.

Why HPA
-------

The Open Targets `expressions` field was retired in favour
of `baselineExpression`, which returns tissue-level
biosample data only and does NOT disambiguate cell types.
HPA publishes the single-cell RNA expression data that
Open Targets used to surface, with explicit per-cell-type
columns.

HPA field naming
----------------

HPA search_download.php returns columns whose display name
is:

    "Single Cell Type RNA - <CellType> [nCPM]"

but the request column code is:

    sc_RNA_<CellType>

Cell-type name case and underscore placement are exact.
Unknown column codes are silently dropped by HPA — no
error is raised. Therefore this client always requests the
FULL verified column list and lets the mapper filter what
it cares about, per Decision I3(a).

Response compression
--------------------

HPA returns gzip-compressed bodies with:

    Content-Type:     application/gzip
    Content-Encoding: gzip

httpx does not auto-decompress in this case because the
`Content-Type` header makes it treat the body as an
application file rather than a transport-layer gzip.
This client detects the gzip magic bytes and decompresses
manually.

Unit
----

Single-cell values are nCPM (normalized counts per
million), NOT nTPM. The threshold in cellular_context.py
applies to nCPM.

What this client does NOT do
----------------------------

- It does not filter by nCPM threshold. That is the
  mapper's concern.
- It does not aggregate across genes. That is the
  mapper's concern.
- It does not interpret nCPM as a probability or
  confidence.

Conventions
-----------

- httpx only.
- 404 returns an empty result, not an exception.
- Other HTTP errors raise RuntimeError.
- Empty inputs raise ValueError.
"""

from __future__ import annotations

import gzip
import json
from typing import Any, Dict, List, Optional

import httpx


# ---------------------------------------------------------------------------
# Verified HPA single-cell column list
# ---------------------------------------------------------------------------

#: Request codes for the single-cell RNA columns this client
#: fetches. Case and underscores are exact; HPA silently
#: drops unknown codes.
#:
#: Sourced from the ToolUniverse project's verified list.
#: The display name for a code "sc_RNA_X" is
#: "Single Cell Type RNA - X [nCPM]" (with X's underscores
#: replaced by spaces).
SINGLE_CELL_COLUMN_CODES = (
    "Adipocytes",
    "Alveolar_cells_type_1",
    "Alveolar_cells_type_2",
    "Astrocytes",
    "B-cells",
    "Basal_keratinocytes",
    "Bergmann_glia",
    "Brain_excitatory_neurons",
    "Brain_inhibitory_neurons",
    "Cardiomyocytes",
    "Distal_convoluted_tubule_cells",
    "Early_spermatids",
    "Enterocytes",
    "Erythrocytes",
    "Fibroblasts",
    "Granulosa_cells",
    "Hematopoietic_stem_cells",
    "Hepatocytes",
    "Kupffer_cells",
    "Macrophages",
    "Mast_cells",
    "Microglia",
    "NK-cells",
    "Neutrophils",
    "Oligodendrocytes",
    "Smooth_muscle_cells",
    "T-cells",
    "Vascular_endothelial_cells",
    "cDC",
)


class HPAClient:
    """
    Minimal Human Protein Atlas client for single-cell
    gene expression.
    """

    BASE_URL = "https://www.proteinatlas.org/api/search_download.php"

    #: Prefix used on the wire for single-cell columns.
    COLUMN_PREFIX = "sc_RNA_"

    #: Prefix used in the display name returned by HPA.
    DISPLAY_PREFIX = "Single Cell Type RNA - "

    #: Suffix used in the display name returned by HPA.
    DISPLAY_SUFFIX = " [nCPM]"

    def __init__(self, timeout: float = 60.0):
        self.timeout = timeout

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _columns_param(self) -> str:
        """
        Compose the `columns` query parameter: gene symbol,
        Ensembl ID, then every single-cell column code
        prefixed with `sc_RNA_`.
        """

        codes = [
            f"{self.COLUMN_PREFIX}{c}"
            for c in SINGLE_CELL_COLUMN_CODES
        ]

        return ",".join(["g", "eg"] + codes)

    def _fetch_raw(
        self,
        gene_symbol: str,
    ) -> List[Dict[str, Any]]:
        """
        Fetch and decompress the HPA JSON payload for a
        gene symbol. Returns a list of row dicts.
        """

        url = self.BASE_URL

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
                        "search": gene_symbol,
                        "format": "json",
                        "columns": self._columns_param(),
                    },
                    headers={
                        "Accept": "application/json",
                        "User-Agent": "CureVerseAI/1.0",
                    },
                )

        except httpx.TimeoutException as exc:
            raise RuntimeError(
                f"HPA request timed out for {gene_symbol}"
            ) from exc

        except httpx.RequestError as exc:
            raise RuntimeError(
                f"Unable to reach HPA: {exc}"
            ) from exc

        if response.status_code == 404:
            return []

        if response.status_code >= 400:
            raise RuntimeError(
                f"HPA returned HTTP {response.status_code} "
                f"for {gene_symbol}"
            )

        # Manual gzip handling: HPA sends gzip with
        # Content-Type: application/gzip, which httpx does
        # not auto-decompress.
        raw = response.content
        if raw[:2] == b"\x1f\x8b":
            raw = gzip.decompress(raw)

        try:
            payload = json.loads(raw.decode("utf-8"))
        except (ValueError, UnicodeDecodeError) as exc:
            raise RuntimeError(
                f"HPA returned malformed JSON for "
                f"{gene_symbol}"
            ) from exc

        if not isinstance(payload, list):
            return []

        return [
            row for row in payload
            if isinstance(row, dict)
        ]

    @staticmethod
    def _display_name(code: str) -> str:
        """
        Convert a column code like
        'Brain_excitatory_neurons' into its display name
        fragment 'Brain excitatory neurons'.
        """

        return code.replace("_", " ")

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_gene_cell_type_expression(
        self,
        gene_symbol: str,
    ) -> Dict[str, Any]:
        """
        Retrieve single-cell RNA expression per cell type
        for a gene symbol.

        Return shape:

            {
                "gene_symbol":  <input symbol>,
                "ensembl_id":   <Ensembl ID or None>,
                "cell_types": [
                    {
                        "cell_type":  "Astrocytes",
                        "display":    "Astrocytes",
                        "ncpm":       154.7,
                    },
                    ...
                ],
                "count":  <number of cell types with numeric value>,
                "source": "Human Protein Atlas",
                "found":  <bool>,
            }

        Only the EXACT gene symbol match is used. HPA's search
        is fuzzy; the client filters the response down to
        the row whose `Gene` field matches `gene_symbol`
        case-insensitively.

        Cell types whose nCPM value is missing or
        non-numeric are skipped. No threshold is applied.
        """

        gene_symbol = (gene_symbol or "").strip()

        if not gene_symbol:
            raise ValueError(
                "Gene symbol cannot be empty."
            )

        rows = self._fetch_raw(gene_symbol)

        if not rows:
            return self._empty(gene_symbol)

        # Find exact gene-symbol match. HPA returns fuzzy
        # results, and we want only the requested gene.
        target_row: Optional[Dict[str, Any]] = None
        wanted = gene_symbol.upper()

        for row in rows:
            symbol = str(row.get("Gene") or "").strip()

            if symbol.upper() == wanted:
                target_row = row
                break

        if target_row is None:
            return self._empty(gene_symbol)

        ensembl_id = target_row.get("Ensembl") or None

        cell_types: List[Dict[str, Any]] = []

        for code in SINGLE_CELL_COLUMN_CODES:
            display_fragment = self._display_name(code)

            column_key = (
                f"{self.DISPLAY_PREFIX}"
                f"{display_fragment}"
                f"{self.DISPLAY_SUFFIX}"
            )

            raw_value = target_row.get(column_key)

            if raw_value is None or raw_value == "":
                continue

            try:
                ncpm = float(raw_value)
            except (TypeError, ValueError):
                continue

            cell_types.append(
                {
                    "cell_type": code,
                    "display": display_fragment,
                    "ncpm": ncpm,
                }
            )

        return {
            "gene_symbol": gene_symbol,
            "ensembl_id": str(ensembl_id) if ensembl_id else None,
            "cell_types": cell_types,
            "count": len(cell_types),
            "source": "Human Protein Atlas",
            "found": len(cell_types) > 0,
        }

    @staticmethod
    def _empty(gene_symbol: str) -> Dict[str, Any]:
        return {
            "gene_symbol": gene_symbol,
            "ensembl_id": None,
            "cell_types": [],
            "count": 0,
            "source": "Human Protein Atlas",
            "found": False,
        }
