from __future__ import annotations

import time
from typing import Any, Dict, List, Optional

import httpx


class ChEMBLClient:
    """
    Client for the ChEMBL REST API.

    Designed for evidence retrieval rather than predictive scoring.
    Raw assay measurements and provenance are preserved.
    """

    BASE_URL = "https://www.ebi.ac.uk/chembl/api/data"

    def __init__(
        self,
        base_url: str | None = None,
        timeout: float = 30.0,
        max_retries: int = 3,
    ) -> None:
        self.base_url = (base_url or self.BASE_URL).rstrip("/")
        self.timeout = timeout
        self.max_retries = max_retries

        self.client = httpx.Client(
            timeout=self.timeout,
            headers={
                "Accept": "application/json",
                "User-Agent": "CureVerseAI/1.0",
            },
        )

    def close(self) -> None:
        self.client.close()

    def __enter__(self) -> "ChEMBLClient":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    def _get(
        self,
        path: str,
        params: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        url = f"{self.base_url}/{path.lstrip('/')}"

        last_error: Exception | None = None

        for attempt in range(self.max_retries + 1):
            try:
                response = self.client.get(url, params=params)

                if response.status_code in {429, 500, 502, 503, 504}:
                    if attempt < self.max_retries:
                        time.sleep(2**attempt)
                        continue

                response.raise_for_status()
                return response.json()

            except (httpx.HTTPError, ValueError) as exc:
                last_error = exc

                if attempt < self.max_retries:
                    time.sleep(2**attempt)
                    continue

                raise

        if last_error:
            raise last_error

        raise RuntimeError("ChEMBL request failed without an exception.")

    def search_targets(
        self,
        query: str,
        limit: int = 20,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Search ChEMBL targets by text query.
        """
        return self._get(
            "target/search.json",
            params={
                "q": query,
                "limit": limit,
                "offset": offset,
            },
        )

    def get_target(
        self,
        target_chembl_id: str,
    ) -> Dict[str, Any]:
        """
        Retrieve one ChEMBL target by ChEMBL target ID.
        """
        target_id = target_chembl_id.strip().upper()

        return self._get(
            f"target/{target_id}.json",
        )

    def find_human_protein_target(
        self,
        gene_symbol: str,
        required_uniprot: str | None = None,
        preferred_name: str | None = None,
        limit: int = 50,
    ) -> Dict[str, Any]:
        """
        Resolve a human protein target while validating the biological identity.

        This prevents a search-term match such as TP53BP1 from being
        incorrectly treated as TP53.
        """
        symbol = gene_symbol.strip().upper()

        data = self.search_targets(
            query=symbol,
            limit=limit,
        )

        targets = data.get("targets", [])

        candidates: List[Dict[str, Any]] = []

        for target in targets:
            if target.get("organism") != "Homo sapiens":
                continue

            components = target.get("target_components", [])

            for component in components:
                accession = component.get("accession")
                synonyms = component.get("target_component_synonyms", [])

                synonym_values = {
                    str(item.get("component_synonym", "")).upper()
                    for item in synonyms
                }

                exact_symbol_match = symbol in synonym_values
                exact_uniprot_match = (
                    required_uniprot is not None
                    and accession == required_uniprot
                )

                name_match = (
                    preferred_name is not None
                    and component.get("component_description") == preferred_name
                )

                if exact_uniprot_match or exact_symbol_match or name_match:
                    candidates.append(target)
                    break

        if not candidates:
            raise LookupError(
                f"No validated human ChEMBL protein target found for {symbol}."
            )

        if required_uniprot:
            for target in candidates:
                for component in target.get("target_components", []):
                    if component.get("accession") == required_uniprot:
                        return target

        if preferred_name:
            for target in candidates:
                if target.get("pref_name") == preferred_name:
                    return target

        return candidates[0]

    def get_activities(
        self,
        target_chembl_id: str,
        molecule_chembl_id: str | None = None,
        standard_types: Optional[List[str]] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> Dict[str, Any]:
        """
        Retrieve ChEMBL activity records for a target.

        Raw activity records are preserved. No potency averaging or
        fabricated effectiveness score is performed.
        """
        target_id = target_chembl_id.strip().upper()

        params: Dict[str, Any] = {
            "target_chembl_id": target_id,
            "limit": limit,
            "offset": offset,
        }

        if molecule_chembl_id:
            params["molecule_chembl_id"] = molecule_chembl_id.strip().upper()

        if standard_types:
            params["standard_type__in"] = ",".join(standard_types)

        return self._get(
            "activity.json",
            params=params,
        )

    @staticmethod
    def validate_activity_target(
        activity: Dict[str, Any],
        expected_target_id: str,
        expected_target_name: str | None = None,
        expected_organism: str = "Homo sapiens",
    ) -> bool:
        """
        Validate that an activity record belongs to the intended target.
        """
        expected_id = expected_target_id.strip().upper()

        if activity.get("target_chembl_id") != expected_id:
            return False

        if expected_target_name:
            if activity.get("target_pref_name") != expected_target_name:
                return False

        if activity.get("target_organism") != expected_organism:
            return False

        return True

    @staticmethod
    def normalize_activity(
        activity: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Convert a raw ChEMBL activity into a stable CureVerseAI evidence record.

        The original scientific measurement is retained.
        """
        ligand_efficiency = activity.get("ligand_efficiency")

        return {
            "activity_id": activity.get("activity_id"),
            "record_id": activity.get("record_id"),

            "target": {
                "chembl_id": activity.get("target_chembl_id"),
                "name": activity.get("target_pref_name"),
                "organism": activity.get("target_organism"),
                "tax_id": activity.get("target_tax_id"),
            },

            "compound": {
                "chembl_id": activity.get("molecule_chembl_id"),
                "parent_chembl_id": activity.get(
                    "parent_molecule_chembl_id"
                ),
                "name": activity.get("molecule_pref_name"),
                "canonical_smiles": activity.get("canonical_smiles"),
            },

            "measurement": {
                "standard_type": activity.get("standard_type"),
                "standard_value": activity.get("standard_value"),
                "standard_units": activity.get("standard_units"),
                "standard_relation": activity.get("standard_relation"),
                "standard_upper_value": activity.get(
                    "standard_upper_value"
                ),
                "standard_text_value": activity.get(
                    "standard_text_value"
                ),
                "pchembl_value": activity.get("pchembl_value"),
                "raw_type": activity.get("type"),
                "raw_value": activity.get("value"),
                "raw_units": activity.get("units"),
                "relation": activity.get("relation"),
            },

            "assay": {
                "chembl_id": activity.get("assay_chembl_id"),
                "description": activity.get("assay_description"),
                "type": activity.get("assay_type"),
                "bao_endpoint": activity.get("bao_endpoint"),
                "bao_format": activity.get("bao_format"),
                "bao_label": activity.get("bao_label"),
                "variant_accession": activity.get(
                    "assay_variant_accession"
                ),
                "variant_mutation": activity.get(
                    "assay_variant_mutation"
                ),
            },

            "publication": {
                "chembl_id": activity.get("document_chembl_id"),
                "journal": activity.get("document_journal"),
                "year": activity.get("document_year"),
            },

            "quality": {
                "standard_flag": activity.get("standard_flag"),
                "potential_duplicate": activity.get(
                    "potential_duplicate"
                ),
                "data_validity_comment": activity.get(
                    "data_validity_comment"
                ),
                "data_validity_description": activity.get(
                    "data_validity_description"
                ),
            },

            "ligand_efficiency": ligand_efficiency,

            "source": "ChEMBL",
        }

    def get_validated_activities(
        self,
        target_chembl_id: str,
        target_name: str,
        organism: str = "Homo sapiens",
        molecule_chembl_id: str | None = None,
        standard_types: Optional[List[str]] = None,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve and validate activities for one biological target.
        """
        data = self.get_activities(
            target_chembl_id=target_chembl_id,
            molecule_chembl_id=molecule_chembl_id,
            standard_types=standard_types,
            limit=limit,
            offset=offset,
        )

        activities = data.get("activities", [])

        validated: List[Dict[str, Any]] = []

        for activity in activities:
            if not self.validate_activity_target(
                activity=activity,
                expected_target_id=target_chembl_id,
                expected_target_name=target_name,
                expected_organism=organism,
            ):
                continue

            validated.append(
                self.normalize_activity(activity)
            )

        return validated
