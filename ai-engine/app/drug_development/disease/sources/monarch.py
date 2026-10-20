"""
CureVerseAI — Drug Development
Monarch Initiative API client.

This client provides the DISEASE -> SYSTEM mapping used by
the Disease -> Biological Impact workflow.

Why Monarch instead of HPO's own API
------------------------------------

HPO publishes the disease-phenotype annotations, but its own
REST API is mid-migration and its disease-phenotype surface
is not reliably reachable (verified by 11x 404 across both
ontology.jax.org and hpo.jax.org bases during Phase 03
development).

Monarch Initiative aggregates HPO's phenotype annotations
into body-system groupings and exposes them through a stable
V3 API. The underlying data is HPO's; the delivery surface
is Monarch's.

The endpoint used is:

    GET /v3/api/histopheno/{disease_id}

which returns counts of HPO phenotype terms grouped by
anatomical system, sorted by count descending. This is
literally the disease -> system aggregation the workflow
needs, and it accepts the MONDO IDs the resolver already
produces.

What this client does NOT do
----------------------------

- It does not interpret `count` as a probability, score,
  or confidence. `count` is the number of HPO phenotype
  annotations Monarch aggregated under that system. It is
  preserved verbatim as a ranking signal only.

- It does not map systems to organs or tissues. That is
  the job of the Uberon surface on OLSClient (see ols.py)
  and of tissue_mapping.py.

- It does not fabricate a system if the disease has no
  histopheno entry. It returns count=0 and an empty
  systems list.

Conventions
-----------

- httpx only, matching OpenTargetsClient, OLSClient, and
  EnsemblClient in this codebase.
- No external libraries beyond httpx.
- 404 returns an empty result, not an exception. Other
  HTTP errors raise RuntimeError.
- The client returns raw aggregated data. It does not
  filter, rank beyond Monarch's own ordering, or
  deduplicate.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional

import httpx


class MonarchClient:
    """
    Minimal Monarch Initiative V3 API client for the
    disease -> anatomical system aggregation.
    """

    BASE_URL = "https://api-v3.monarchinitiative.org/v3/api"

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _get(
        self,
        path: str,
    ) -> Optional[Dict[str, Any]]:
        """
        Perform a GET against Monarch and return the parsed
        JSON. A 404 returns None so callers can distinguish
        "not found" from a transport failure.
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
                    headers={
                        "Accept": "application/json",
                        "User-Agent": "CureVerseAI/1.0",
                    },
                )

        except httpx.TimeoutException as exc:
            raise RuntimeError(
                f"Monarch request timed out: {url}"
            ) from exc

        except httpx.RequestError as exc:
            raise RuntimeError(
                f"Unable to reach Monarch: {exc}"
            ) from exc

        if response.status_code == 404:
            return None

        if response.status_code >= 400:
            raise RuntimeError(
                f"Monarch returned HTTP {response.status_code} "
                f"for {url}"
            )

        return response.json()

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_histopheno(
        self,
        disease_id: str,
    ) -> Dict[str, Any]:
        """
        Retrieve the anatomical-system breakdown of a
        disease's HPO phenotype annotations.

        `disease_id` must be a Monarch-accepted identifier.
        MONDO IDs in colon form ("MONDO:0004975") are known
        to work; the resolver already produces this form.

        Return shape:

            {
                "disease_id": <input>,
                "systems": [
                    {
                        "label":       <system label, underscored>,
                        "count":       <integer>,
                        "id":          <UPHENO or HP id>,
                    },
                    ...
                ],
                "count":     <number of system entries>,
                "source":    "Monarch Initiative",
                "found":     <bool>,
            }

        A disease with no real annotation data returns
        found=False. Monarch's histopheno endpoint returns
        the full system vocabulary regardless of whether the
        disease exists, so `found` is determined by whether
        any system has a positive count.

            { "disease_id": ..., "systems": [<full vocab>],
              "count": N, "annotated_count": 0,
              "source": ..., "found": False }

        `count` is preserved verbatim and is NOT a probability,
        score, or confidence. It is a phenotype annotation
        count.
        """

        disease_id = (disease_id or "").strip()

        if not disease_id:
            raise ValueError(
                "Disease identifier cannot be empty."
            )

        payload = self._get(
            f"/histopheno/{disease_id}"
        )

        if not payload:
            return {
                "disease_id": disease_id,
                "systems": [],
                "count": 0,
                "source": "Monarch Initiative",
                "found": False,
            }

        items = payload.get("items") or []

        systems: List[Dict[str, Any]] = []

        for item in items:
            if not isinstance(item, dict):
                continue

            label = item.get("label")
            count = item.get("count")
            system_id = item.get("id")

            if not label:
                continue

            # Preserve count exactly as Monarch returned it.
            # Cast is defensive only.
            try:
                count_value = int(count or 0)
            except (TypeError, ValueError):
                count_value = 0

            systems.append(
                {
                    "label": str(label),
                    "count": count_value,
                    "id": str(system_id) if system_id else None,
                }
            )

        # `found` means Monarch has REAL annotation data for
        # this disease. Monarch returns the full system
        # vocabulary even for unknown IDs, with all counts at
        # zero. We therefore require at least one system with
        # a positive count before reporting found=True.
        #
        # The full systems list (including zero-count entries)
        # is still preserved verbatim in `systems`, so callers
        # can see exactly what Monarch returned. But `found`
        # and the `annotated_count` flag reflect reality.
        positive = sum(
            1 for s in systems if s["count"] > 0
        )

        return {
            "disease_id": disease_id,
            "systems": systems,
            "count": len(systems),
            "annotated_count": positive,
            "source": "Monarch Initiative",
            "found": positive > 0,
        }
