from pathlib import Path as _Path

import httpx

from app.data.cache import DiskCache


REACTOME_BASE_URL = "https://reactome.org/ContentService"

#: Default cache directory for Reactome responses.
_DEFAULT_CACHE_DIR = (
    _Path(__file__).resolve().parents[3]
    / "data" / "cache" / "reactome"
)

#: Reactome pathway annotations change slowly; 30 days is
#: a reasonable TTL.
_DEFAULT_CACHE_TTL = 30 * 24 * 3600


class ReactomeClient:
    def __init__(
        self,
        timeout: float = 30.0,
        cache_dir: str | None = None,
        cache_ttl: int = _DEFAULT_CACHE_TTL,
    ):
        self.timeout = timeout
        self.cache = DiskCache(
            cache_dir or _DEFAULT_CACHE_DIR,
            ttl_seconds=cache_ttl,
        )

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

    # ------------------------------------------------------------------
    # Pathways for a protein
    # ------------------------------------------------------------------

    def get_pathways_for_protein(
        self,
        uniprot_accession: str,
    ) -> dict:
        """
        Retrieve Reactome pathways that a UniProt protein
        participates in.

        Endpoint:
            GET /data/mapping/UniProt/{accession}/pathways

        Return shape:

            {
                "uniprot_accession": <input>,
                "pathways": [
                    {
                        "st_id":        "R-HSA-114608",
                        "st_id_version":"R-HSA-114608.5",
                        "db_id":        114608,
                        "display_name": "Platelet degranulation",
                        "name":         "Platelet degranulation",
                        "species_name": "Homo sapiens",
                        "is_in_disease": False,
                        "is_inferred":  False,
                        "has_diagram":  False,
                        "has_ehld":     False,
                        "release_date": "2004-10-27",
                        "last_updated_date": "2021-06-14",
                        "schema_class": "Pathway",
                    },
                    ...
                ],
                "count":  <int>,
                "source": "Reactome",
                "found":  <bool>,
            }

        A protein that does not map to any pathway returns
        found=False and an empty list. A 404 returns the
        same empty shape rather than raising.
        """

        uniprot_accession = (
            uniprot_accession or ""
        ).strip().upper()

        if not uniprot_accession:
            raise ValueError(
                "UniProt accession cannot be empty."
            )

        # Cache lookup
        cache_key = DiskCache.make_key(
            "reactome:pathways_for_protein",
            uniprot_accession,
        )
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached.get("data")

        # Network path
        url = (
            f"{REACTOME_BASE_URL}"
            f"/data/mapping/UniProt/"
            f"{uniprot_accession}/pathways"
        )

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
                f"Reactome request timed out for "
                f"{uniprot_accession}"
            ) from exc
        except httpx.RequestError as exc:
            raise RuntimeError(
                f"Unable to reach Reactome: {exc}"
            ) from exc

        if response.status_code == 404:
            result = self._empty_protein_pathways(
                uniprot_accession
            )
            self.cache.set(cache_key, {"data": result})
            return result

        if response.status_code >= 400:
            raise RuntimeError(
                f"Reactome returned HTTP "
                f"{response.status_code} for "
                f"{uniprot_accession}"
            )

        payload = response.json()

        if not isinstance(payload, list):
            result = self._empty_protein_pathways(
                uniprot_accession
            )
            self.cache.set(cache_key, {"data": result})
            return result

        pathways = []

        for entry in payload:
            if not isinstance(entry, dict):
                continue

            st_id = entry.get("stId")
            if not st_id:
                continue

            display_name = entry.get("displayName")
            if not display_name:
                continue

            pathways.append(
                {
                    "st_id": str(st_id),
                    "st_id_version": entry.get("stIdVersion"),
                    "db_id": entry.get("dbId"),
                    "display_name": str(display_name).strip(),
                    "name": (
                        entry.get("name") or [display_name]
                    ),
                    "species_name": entry.get("speciesName"),
                    "is_in_disease": bool(entry.get("isInDisease")),
                    "is_inferred": bool(entry.get("isInferred")),
                    "has_diagram": bool(entry.get("hasDiagram")),
                    "has_ehld": bool(entry.get("hasEHLD")),
                    "release_date": entry.get("releaseDate"),
                    "last_updated_date": entry.get("lastUpdatedDate"),
                    "schema_class": entry.get("schemaClass"),
                }
            )

        result = {
            "uniprot_accession": uniprot_accession,
            "pathways": pathways,
            "count": len(pathways),
            "source": "Reactome",
            "found": len(pathways) > 0,
        }

        self.cache.set(cache_key, {"data": result})
        return result

    # ------------------------------------------------------------------
    # Pathway metadata by stable id
    # ------------------------------------------------------------------

    def get_pathway_by_id(self, st_id: str) -> dict:
        """
        Retrieve pathway metadata for a Reactome stable identifier.

        Endpoint:
            GET /data/query/{st_id}

        Example:
            st_id = "R-HSA-6785807"

        Return shape:

            {
                "st_id":          "R-HSA-6785807",
                "st_id_version":  "R-HSA-6785807.8",
                "db_id":          6785807,
                "display_name":   "Interleukin-4 and Interleukin-13 signaling",
                "name":           ["Interleukin-4 and Interleukin-13 signaling"],
                "species_name":   "Homo sapiens",
                "is_in_disease":  False,
                "is_inferred":    False,
                "has_diagram":    False,
                "has_ehld":       False,
                "review_status":  "..." | None,
                "release_date":   "2016-12-12",
                "last_updated_date": "..." | None,
                "go_biological_process": {
                    "accession":  "0019221",
                    "name":       "cytokine-mediated signaling pathway",
                    "definition": "...",
                    "url":        "https://www.ebi.ac.uk/QuickGO/term/GO:0019221",
                } | None,
                "literature_count": <int>,
                "cross_references": [
                    {"database_name": "...", "identifier": "...", "url": "..."},
                    ...
                ],
                "summation": [{"text": "..."}, ...],
                "source": "Reactome",
                "found":  True,
            }

        A stable id that does not resolve returns found=False
        and a minimal shape with the input st_id preserved.
        A 404 does not raise.
        """

        st_id = (st_id or "").strip()

        if not st_id:
            raise ValueError("Reactome stable id cannot be empty.")

        cache_key = DiskCache.make_key(
            "reactome:pathway_by_id",
            st_id,
        )
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached.get("data")

        url = f"{REACTOME_BASE_URL}/data/query/{st_id}"

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
                f"Reactome request timed out for {st_id}"
            ) from exc
        except httpx.RequestError as exc:
            raise RuntimeError(
                f"Unable to reach Reactome: {exc}"
            ) from exc

        if response.status_code == 404:
            result = self._empty_pathway(st_id)
            self.cache.set(cache_key, {"data": result})
            return result

        if response.status_code >= 400:
            raise RuntimeError(
                f"Reactome returned HTTP "
                f"{response.status_code} for {st_id}"
            )

        payload = response.json()

        if not isinstance(payload, dict):
            result = self._empty_pathway(st_id)
            self.cache.set(cache_key, {"data": result})
            return result

        go_bp_raw = payload.get("goBiologicalProcess")
        go_bp = None
        if isinstance(go_bp_raw, dict):
            go_bp = {
                "accession": go_bp_raw.get("accession"),
                "name": go_bp_raw.get("name"),
                "definition": go_bp_raw.get("definition"),
                "url": go_bp_raw.get("url"),
            }

        cross_refs = []
        for entry in payload.get("crossReference") or []:
            if not isinstance(entry, dict):
                continue
            cross_refs.append({
                "database_name": entry.get("databaseName"),
                "identifier": entry.get("identifier"),
                "url": entry.get("url"),
            })

        summations = []
        for entry in payload.get("summation") or []:
            if isinstance(entry, dict):
                text = entry.get("text")
                if text:
                    summations.append({"text": str(text)})
            elif isinstance(entry, str):
                summations.append({"text": entry})

        lit_refs = payload.get("literatureReference") or []
        literature_count = len(lit_refs) if isinstance(lit_refs, list) else 0

        name_raw = payload.get("name")
        if isinstance(name_raw, list):
            name_list = [str(n) for n in name_raw if n]
        elif isinstance(name_raw, str):
            name_list = [name_raw]
        else:
            name_list = []

        display_name = payload.get("displayName")

        result = {
            "st_id": str(payload.get("stId") or st_id),
            "st_id_version": payload.get("stIdVersion"),
            "db_id": payload.get("dbId"),
            "display_name": (
                str(display_name).strip() if display_name else None
            ),
            "name": name_list,
            "species_name": payload.get("speciesName"),
            "is_in_disease": bool(payload.get("isInDisease")),
            "is_inferred": bool(payload.get("isInferred")),
            "has_diagram": bool(payload.get("hasDiagram")),
            "has_ehld": bool(payload.get("hasEHLD")),
            "review_status": payload.get("reviewStatus"),
            "release_date": payload.get("releaseDate"),
            "last_updated_date": payload.get("lastUpdatedDate"),
            "go_biological_process": go_bp,
            "literature_count": literature_count,
            "cross_references": cross_refs,
            "summation": summations,
            "source": "Reactome",
            "found": bool(display_name),
        }

        self.cache.set(cache_key, {"data": result})
        return result

    # ------------------------------------------------------------------
    # Pathway participants by stable id
    # ------------------------------------------------------------------

    def get_pathway_participants(self, st_id: str) -> dict:
        """
        Retrieve participants (physical entities) for a pathway.

        Endpoint:
            GET /data/participants/{st_id}

        Return shape:

            {
                "st_id": "R-HSA-6785807",
                "participants": [
                    {
                        "pe_db_id":     6786088,
                        "display_name":  "IL4:p-Y-IL4R:JAK2:... [plasma membrane]",
                        "schema_class":  "Complex",
                        "ref_entities": [
                            {
                                "st_id":         "uniprot:P24394",
                                "identifier":    "P24394",
                                "schema_class":  "ReferenceGeneProduct",
                                "display_name":  "UniProt:P24394 IL4R",
                                "url":           "http://purl.uniprot.org/uniprot/P24394",
                            },
                            ...
                        ],
                    },
                    ...
                ],
                "count": <int>,
                "source": "Reactome",
                "found": <bool>,
            }

        A stable id with no participants returns found=False
        and an empty list. A 404 does not raise.
        """

        st_id = (st_id or "").strip()

        if not st_id:
            raise ValueError("Reactome stable id cannot be empty.")

        cache_key = DiskCache.make_key(
            "reactome:pathway_participants",
            st_id,
        )
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached.get("data")

        url = f"{REACTOME_BASE_URL}/data/participants/{st_id}"

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
                f"Reactome request timed out for {st_id}"
            ) from exc
        except httpx.RequestError as exc:
            raise RuntimeError(
                f"Unable to reach Reactome: {exc}"
            ) from exc

        if response.status_code == 404:
            result = self._empty_pathway_participants(st_id)
            self.cache.set(cache_key, {"data": result})
            return result

        if response.status_code >= 400:
            raise RuntimeError(
                f"Reactome returned HTTP "
                f"{response.status_code} for {st_id}"
            )

        payload = response.json()

        if not isinstance(payload, list):
            result = self._empty_pathway_participants(st_id)
            self.cache.set(cache_key, {"data": result})
            return result

        participants = []
        for entry in payload:
            if not isinstance(entry, dict):
                continue

            refs = []
            for ref in entry.get("refEntities") or []:
                if not isinstance(ref, dict):
                    continue
                refs.append({
                    "st_id": ref.get("stId"),
                    "identifier": ref.get("identifier"),
                    "schema_class": ref.get("schemaClass"),
                    "display_name": ref.get("displayName"),
                    "url": ref.get("url"),
                })

            participants.append({
                "pe_db_id": entry.get("peDbId"),
                "display_name": entry.get("displayName"),
                "schema_class": entry.get("schemaClass"),
                "ref_entities": refs,
            })

        result = {
            "st_id": st_id,
            "participants": participants,
            "count": len(participants),
            "source": "Reactome",
            "found": len(participants) > 0,
        }

        self.cache.set(cache_key, {"data": result})
        return result

    def get_event_ancestors(self, st_id: str) -> list:
        """
        Retrieve the ancestor chain for a Reactome event.

        Endpoint:
            GET /data/event/{st_id}/ancestors

        Response shape from Reactome is a list containing one
        element which is itself a list of ancestor records
        ordered from the event itself upward to the top-level
        event. Example (abbreviated):

            [
                [
                    {"stId": "R-HSA-1227986", "displayName": "Signaling by ERBB2", "schemaClass": "Pathway", ...},
                    {"stId": "R-HSA-9006934", "displayName": "Signaling by Receptor Tyrosine Kinases", ...},
                    ...,
                    {"stId": "R-HSA-162582", "displayName": "Signal Transduction", ...},
                ]
            ]

        This method flattens that quirk into a single list of
        ancestor dicts, each with the fields the caller needs:

            {
                "st_id":          "R-HSA-...",
                "display_name":   "...",
                "schema_class":   "Pathway" | "TopLevelPathway" | ...,
                "species_name":   "Homo sapiens",
            }

        Returns [] on 404, on transport failure, or when the
        response does not have the expected shape. Never raises.

        The last element of the returned list is the top-level
        ancestor. Callers that want the top-level category
        should read ``result[-1]`` when the list is non-empty.
        """

        st_id = (st_id or "").strip()

        if not st_id:
            return []

        cache_key = DiskCache.make_key(
            "reactome:event_ancestors",
            st_id,
        )
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached.get("data") or []

        url = f"{REACTOME_BASE_URL}/data/event/{st_id}/ancestors"

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
        except httpx.TimeoutException:
            return []
        except httpx.RequestError:
            return []

        if response.status_code == 404:
            self.cache.set(cache_key, {"data": []})
            return []

        if response.status_code >= 400:
            return []

        try:
            payload = response.json()
        except ValueError:
            return []

        if not isinstance(payload, list):
            return []

        # Flatten the list-of-lists quirk. Keep the first inner
        # list — Reactome returns one inner list per requested
        # event, and we always request exactly one.
        inner = None
        for item in payload:
            if isinstance(item, list):
                inner = item
                break

        if inner is None:
            return []

        out = []
        for anc in inner:
            if not isinstance(anc, dict):
                continue
            anc_st_id = anc.get("stId")
            if not anc_st_id:
                continue
            out.append({
                "st_id": str(anc_st_id),
                "display_name": anc.get("displayName"),
                "schema_class": anc.get("schemaClass"),
                "species_name": anc.get("speciesName"),
            })

        self.cache.set(cache_key, {"data": out})
        return out

    @staticmethod
    def _empty_pathway(st_id: str) -> dict:
        return {
            "st_id": st_id,
            "st_id_version": None,
            "db_id": None,
            "display_name": None,
            "name": [],
            "species_name": None,
            "is_in_disease": False,
            "is_inferred": False,
            "has_diagram": False,
            "has_ehld": False,
            "review_status": None,
            "release_date": None,
            "last_updated_date": None,
            "go_biological_process": None,
            "literature_count": 0,
            "cross_references": [],
            "summation": [],
            "source": "Reactome",
            "found": False,
        }

    @staticmethod
    def _empty_pathway_participants(st_id: str) -> dict:
        return {
            "st_id": st_id,
            "participants": [],
            "count": 0,
            "source": "Reactome",
            "found": False,
        }

    @staticmethod
    def _empty_protein_pathways(
        uniprot_accession: str,
    ) -> dict:
        return {
            "uniprot_accession": uniprot_accession,
            "pathways": [],
            "count": 0,
            "source": "Reactome",
            "found": False,
        }
