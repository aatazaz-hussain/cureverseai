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

    def search_molecules_by_name(
        self,
        query: str,
        limit: int = 5,
    ) -> Dict[str, Any]:
        """
        Search ChEMBL molecules (compounds / drugs) by free-text
        name or synonym.

        Returns a curated shape rather than the raw ChEMBL
        response so callers do not depend on ChEMBL's pagination
        wrapper:

            {
                "query":         <original query>,
                "count":         <int>,
                "found":         <bool>,
                "molecules": [
                    {
                        "chembl_id":        "CHEMBL1200681",
                        "pref_name":        "MONTELUKAST SODIUM",
                        "molecule_type":    "Small molecule",
                        "max_phase":        4,
                        "therapeutic_flag": True,
                        "synonyms":         ["..."],
                    },
                    ...
                ],
            }

        An empty result is a valid answer, not an error: the
        returned ``found`` is False and the list is empty. The
        caller decides how to surface that.
        """
        cleaned = (query or "").strip()

        if not cleaned:
            return {
                "query": cleaned,
                "count": 0,
                "found": False,
                "molecules": [],
            }

        data = self._get(
            "molecule/search.json",
            params={
                "q": cleaned,
                "limit": int(limit),
            },
        )

        raw = data.get("molecules") or []

        molecules: List[Dict[str, Any]] = []

        for entry in raw:
            if not isinstance(entry, dict):
                continue

            chembl_id = entry.get("molecule_chembl_id")
            if not chembl_id:
                continue

            synonyms: List[str] = []
            for syn in entry.get("molecule_synonyms") or []:
                if isinstance(syn, dict):
                    val = syn.get("molecule_synonym")
                    if val:
                        synonyms.append(str(val))

            molecules.append(
                {
                    "chembl_id": str(chembl_id).strip().upper(),
                    "pref_name": entry.get("pref_name"),
                    "molecule_type": entry.get("molecule_type"),
                    "max_phase": entry.get("max_phase"),
                    "therapeutic_flag": bool(
                        entry.get("therapeutic_flag")
                    ),
                    "synonyms": synonyms[:5],
                }
            )

        return {
            "query": cleaned,
            "count": len(molecules),
            "found": len(molecules) > 0,
            "molecules": molecules,
        }

    def get_molecule(
        self,
        chembl_id: str,
    ) -> Dict[str, Any]:
        """
        Retrieve one ChEMBL molecule by its ChEMBL molecule id.

        Returns a curated shape:

            {
                "chembl_id":            "CHEMBL1200681",
                "pref_name":            "MONTELUKAST SODIUM",
                "molecule_type":        "Small molecule",
                "max_phase":            4,
                "therapeutic_flag":     True,
                "synonyms":             ["..."],
                "molecule_structures":  { ... } | None,
                "source":               "ChEMBL",
                "found":                True,
            }

        A 404 from ChEMBL raises LookupError, matching the
        convention used by find_human_protein_target for a
        requested resource that does not exist. Transport
        failures propagate through the existing retry path.
        """
        cleaned = (chembl_id or "").strip().upper()

        if not cleaned:
            raise ValueError("ChEMBL molecule id cannot be empty.")

        try:
            data = self._get(f"molecule/{cleaned}.json")
        except httpx.HTTPStatusError as exc:
            if exc.response is not None and exc.response.status_code == 404:
                raise LookupError(
                    f"ChEMBL molecule {cleaned} does not exist."
                ) from exc
            raise

        if not isinstance(data, dict):
            raise LookupError(
                f"ChEMBL molecule {cleaned} returned an unexpected payload."
            )

        synonyms: List[str] = []
        for syn in data.get("molecule_synonyms") or []:
            if isinstance(syn, dict):
                val = syn.get("molecule_synonym")
                if val:
                    synonyms.append(str(val))

        return {
            "chembl_id": str(
                data.get("molecule_chembl_id") or cleaned
            ).strip().upper(),
            "pref_name": data.get("pref_name"),
            "molecule_type": data.get("molecule_type"),
            "max_phase": data.get("max_phase"),
            "therapeutic_flag": bool(data.get("therapeutic_flag")),
            "synonyms": synonyms[:10],
            "molecule_structures": data.get("molecule_structures"),
            "source": "ChEMBL",
            "found": True,
        }

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

    def get_activities_for_molecule(
        self,
        molecule_chembl_id: str,
        limit: int = 100,
        offset: int = 0,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve ChEMBL activity records for a molecule across
        all its targets.

        The existing get_activities method requires a target id
        because its primary purpose is target-centric evidence.
        This method takes the molecule as the primary key so
        callers can discover the targets a molecule acts on.

        Each raw activity is normalized via normalize_activity
        so the return shape is identical to what
        get_validated_activities produces. No potency is
        averaged, no effectiveness score is fabricated.

        Returns [] if the molecule has no recorded activities.
        Raises through the existing _get retry path on
        transport failure.
        """
        cleaned = (molecule_chembl_id or "").strip().upper()

        if not cleaned:
            raise ValueError("ChEMBL molecule id cannot be empty.")

        data = self._get(
            "activity.json",
            params={
                "molecule_chembl_id": cleaned,
                "limit": limit,
                "offset": offset,
            },
        )

        activities = data.get("activities") or []

        validated: List[Dict[str, Any]] = []

        for activity in activities:
            if not isinstance(activity, dict):
                continue
            validated.append(
                self.normalize_activity(activity)
            )

        return validated

    def get_mechanism(
        self,
        molecule_chembl_id: str,
    ) -> List[Dict[str, Any]]:
        """
        Retrieve ChEMBL mechanism-of-action records for a
        molecule.

        Endpoint:
            GET /mechanism.json?molecule_chembl_id=X

        ChEMBL attaches mechanism records to a specific ChEMBL
        molecule id — sometimes the parent, sometimes the salt.
        The caller is responsible for trying both. This method
        just returns whatever ChEMBL has for the given id.

        Return shape (one dict per mechanism):

            {
                "molecule_chembl_id": "CHEMBL1200681",
                "target_chembl_id":   "CHEMBL1798",
                "mechanism_of_action":"Cysteinyl leukotriene receptor 1 antagonist",
                "action_type":        "ANTAGONIST",
                "direct_interaction": <bool|None>,
            }

        Returns [] when the molecule has no recorded mechanism.
        Never raises for a missing record.
        """
        cleaned = (molecule_chembl_id or "").strip().upper()

        if not cleaned:
            return []

        try:
            data = self._get(
                "mechanism.json",
                params={
                    "molecule_chembl_id": cleaned,
                    "limit": 50,
                },
            )
        except Exception:
            return []

        if not isinstance(data, dict):
            return []

        raw = data.get("mechanisms") or []
        out: List[Dict[str, Any]] = []

        for m in raw:
            if not isinstance(m, dict):
                continue
            tid = m.get("target_chembl_id")
            if not tid:
                continue
            out.append({
                "molecule_chembl_id": m.get("molecule_chembl_id"),
                "target_chembl_id": str(tid).strip().upper(),
                "mechanism_of_action": m.get("mechanism_of_action"),
                "action_type": m.get("action_type"),
                "direct_interaction": m.get("direct_interaction"),
            })

        return out

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

        # ChEMBL target names can legitimately differ from the
        # preferred biological name (for example multi-target records
        # such as "EGFR/PPP1CA"). The validated ChEMBL target ID is
        # the authoritative identity check; organism remains required.
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

        # Some ChEMBL targets may not expose quantitative measurements
        # (IC50/Ki/Kd/etc.) even though legitimate activity records exist.
        # If the filtered query returns nothing, perform one unfiltered
        # fallback so qualitative/observational records are not silently lost.
        # No potency value is inferred from these records.
        if not activities and standard_types:
            fallback = self.get_activities(
                target_chembl_id=target_chembl_id,
                molecule_chembl_id=molecule_chembl_id,
                standard_types=None,
                limit=limit,
                offset=offset,
            )
            activities = fallback.get("activities", [])

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
