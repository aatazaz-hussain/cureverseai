from typing import Any, Dict, List

from app.drug_development.evidence import (
    EvidenceBundle,
    TargetEvidence,
)
from app.drug_development.sources.open_targets import (
    OpenTargetsClient,
)


class OpenTargetsEvidenceService:
    """
    Converts Open Targets target-disease associations into
    structured CureVerseAI drug-development evidence.

    Open Targets association scores are preserved as source
    evidence metadata. They are not interpreted as clinical
    probabilities or treatment efficacy.
    """

    SOURCE_NAME = "Open Targets"

    def __init__(
        self,
        client: OpenTargetsClient | None = None,
    ):
        self.client = client or OpenTargetsClient()

    def get_target_disease_evidence(
        self,
        target_id: str,
        size: int = 10,
    ) -> EvidenceBundle:
        """
        Retrieve target-disease associations from Open Targets
        and convert them into CureVerseAI evidence records.
        """

        result = self.client.get_target_disease_associations(
            target_id=target_id,
            size=size,
        )

        bundle = EvidenceBundle()

        target = result.get("target") or {}
        rows = result.get("rows") or []

        target_symbol = (
            target.get("symbol")
            or target_id
        )

        bundle.add_source(self.SOURCE_NAME)

        bundle.provenance[
            "open_targets"
        ] = {
            "target_id": target_id,
            "total_associations": result.get(
                "count",
                0,
            ),
            "retrieved_rows": len(rows),
        }

        for row in rows:
            disease = row.get("disease") or {}

            disease_id = disease.get("id")
            disease_name = disease.get("name")

            if not disease_id:
                continue

            description = (
                f"{target_symbol} has a target-disease "
                f"association with {disease_name or disease_id} "
                f"according to Open Targets."
            )

            evidence = TargetEvidence(
                target=target_symbol,
                target_id=target_id,
                source=self.SOURCE_NAME,
                evidence_type="target_disease_association",
                description=description,
                identifiers={
                    "target_id": target_id,
                    "disease_id": disease_id,
                },
                metadata={
                    "disease_name": disease_name,
                    "association_score": row.get(
                        "score"
                    ),
                    "novelty": row.get(
                        "novelty"
                    ),
                    "datasource_scores": row.get(
                        "datasourceScores"
                    ),
                    "datatype_scores": row.get(
                        "datatypeScores"
                    ),
                },
            )

            bundle.targets.append(evidence)

        return bundle

    def summarize(
        self,
        target_id: str,
        size: int = 10,
    ) -> Dict[str, Any]:
        """
        Return a compact summary of Open Targets evidence.
        """

        bundle = self.get_target_disease_evidence(
            target_id=target_id,
            size=size,
        )

        return {
            "summary": bundle.summary(),
            "provenance": bundle.provenance,
            "evidence": [
                {
                    "target": item.target,
                    "target_id": item.target_id,
                    "source": item.source,
                    "evidence_type": item.evidence_type,
                    "description": item.description,
                    "identifiers": item.identifiers,
                    "metadata": item.metadata,
                }
                for item in bundle.targets
            ],
        }
