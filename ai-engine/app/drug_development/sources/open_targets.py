from typing import Any, Dict, Optional

import httpx


class OpenTargetsClient:
    """
    Client for the official Open Targets Platform GraphQL API.

    Open Targets provides evidence used in drug discovery and
    target prioritization workflows.
    """

    BASE_URL = (
        "https://api.platform.opentargets.org/api/v4/graphql"
    )

    def __init__(self, timeout: float = 30.0):
        self.timeout = timeout

    def query(
        self,
        graphql_query: str,
        variables: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:

        response = httpx.post(
            self.BASE_URL,
            json={
                "query": graphql_query,
                "variables": variables or {},
            },
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json",
            },
            timeout=self.timeout,
        )

        payload = response.json()

        if "errors" in payload:
            raise RuntimeError(
                "Open Targets GraphQL error: "
                f"{payload['errors']}"
            )

        response.raise_for_status()

        return payload.get("data", {})
    def get_target(
        self,
        target_id: str,
    ) -> Dict[str, Any]:

        graphql_query = """
        query Target($id: String!) {
          target(ensemblId: $id) {
            id
            approvedSymbol
            approvedName
            biotype
          }
        }
        """
        data = self.query(
            graphql_query,
            {"id": target_id},
        )

        return data.get("target") or {}
    def get_target_disease_associations(
        self,
        target_id: str,
        size: int = 20,
    ) -> Dict[str, Any]:

        graphql_query = """
        query TargetDiseases(
          $id: String!,
          $size: Int!
        ) {
          target(ensemblId: $id) {
            id
            approvedSymbol
            associatedDiseases(
              page: {
                index: 0,
                size: $size
              }
            ) {
              count
              rows {
                score
                novelty
                disease {
                  id
                  name
                  description
                }
              }
            }
          }
        }
        """

        data = self.query(
            graphql_query,
            {
                "id": target_id,
                "size": size,
            },
        )

        target = data.get("target")

        if not target:
            return {}

        associations = (
            target.get(
                "associatedDiseases"
            )
            or {}
        )

        return {
            "target": {
                "id": target.get("id"),
                "symbol": target.get(
                    "approvedSymbol"
                ),
            },
            "count": associations.get(
                "count",
                0,
            ),
            "rows": associations.get(
                "rows",
                [],
            ),
        }
