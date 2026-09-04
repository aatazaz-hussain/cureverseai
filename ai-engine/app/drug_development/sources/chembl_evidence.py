from __future__ import annotations

from typing import Any, Dict, List, Optional

from app.drug_development.evidence import (
    CompoundEvidence,
    DrugTargetEvidence,
    EvidenceBundle,
    TargetEvidence,
)

from app.drug_development.sources.chembl import ChEMBLClient


class ChEMBLEvidenceService:
    """
    Converts validated ChEMBL activity records into CureVerseAI
    drug-development evidence bundles.

    ChEMBL measurements are preserved as scientific observations.
    No artificial potency or effectiveness score is generated.
    """

    SOURCE = "ChEMBL"

    def __init__(
        self,
        client: Optional[ChEMBLClient] = None,
    ) -> None:
        self.client = client or ChEMBLClient()

    def close(self) -> None:
        self.client.close()

    def __enter__(self) -> "ChEMBLEvidenceService":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.close()

    def get_target_evidence(
        self,
        gene_symbol: str,
        uniprot_id: str,
        preferred_name: str,
    ) -> TargetEvidence:
        """
        Resolve and validate a human ChEMBL target.
        """

        target = self.client.find_human_protein_target(
            gene_symbol=gene_symbol,
            required_uniprot=uniprot_id,
            preferred_name=preferred_name,
        )

        target_id = target.get("target_chembl_id")

        return TargetEvidence(
            target=gene_symbol,
            target_id=target_id,
            source=self.SOURCE,
            evidence_type="target_identity",
            description=(
                f"Validated ChEMBL human protein target for "
                f"{gene_symbol}: {preferred_name}."
            ),
            identifiers={
                "chembl_target_id": target_id,
                "uniprot": uniprot_id,
            },
            metadata={
                "preferred_name": preferred_name,
                "organism": target.get("organism"),
                "target_type": target.get("target_type"),
                "target_components": target.get(
                    "target_components", []
                ),
                "source": self.SOURCE,
            },
        )

    def get_bioactivity_evidence(
        self,
        target_chembl_id: str,
        target_name: str,
        limit: int = 100,
        standard_types: Optional[List[str]] = None,
    ) -> EvidenceBundle:
        """
        Retrieve validated ChEMBL activities and convert them into
        a CureVerseAI EvidenceBundle.
        """

        activities = self.client.get_validated_activities(
            target_chembl_id=target_chembl_id,
            target_name=target_name,
            standard_types=standard_types,
            limit=limit,
        )

        bundle = EvidenceBundle()

        bundle.add_source(self.SOURCE)

        seen_compounds: set[str] = set()

        for activity in activities:
            compound = activity["compound"]
            measurement = activity["measurement"]
            assay = activity["assay"]
            publication = activity["publication"]
            quality = activity["quality"]

            compound_id = compound.get("chembl_id")

            if compound_id and compound_id not in seen_compounds:
                bundle.compounds.append(
                    CompoundEvidence(
                        smiles=compound.get("canonical_smiles") or "",
                        compound_id=compound_id,
                        name=compound.get("name"),
                        source=self.SOURCE,
                        evidence_type="molecular",
                        description=(
                            f"ChEMBL compound associated with "
                            f"bioactivity evidence against "
                            f"{target_name}."
                        ),
                        identifiers={
                            "chembl_compound_id": compound_id,
                        },
                        metadata={
                            "parent_chembl_id": compound.get(
                                "parent_chembl_id"
                            ),
                        },
                    )
                )

                seen_compounds.add(compound_id)

            standard_type = measurement.get("standard_type")
            standard_value = measurement.get("standard_value")
            standard_units = measurement.get("standard_units")
            relation = measurement.get("standard_relation")
            pchembl = measurement.get("pchembl_value")
            text_value = measurement.get("standard_text_value")

            if standard_value is not None:
                evidence_level = "quantitative"
            elif text_value is not None:
                evidence_level = "qualitative"
            else:
                evidence_level = "observational"

            relationship = DrugTargetEvidence(
                target=target_name,
                compound=compound_id or "",
                source=self.SOURCE,
                relationship_type="bioactivity",
                evidence_level=evidence_level,
                description=(
                    f"{standard_type or 'Activity'} measurement "
                    f"from ChEMBL assay "
                    f"{assay.get('chembl_id')}."
                ),
                identifiers={
                    "chembl_target_id": target_chembl_id,
                    "chembl_activity_id": str(
                        activity.get("activity_id")
                    ),
                    "chembl_record_id": str(
                        activity.get("record_id")
                    ),
                    "chembl_assay_id": str(
                        assay.get("chembl_id")
                    ),
                },
                metadata={
                    "measurement": measurement,
                    "assay": assay,
                    "publication": publication,
                    "quality": quality,
                    "canonical_smiles": compound.get(
                        "canonical_smiles"
                    ),
                    "compound_name": compound.get("name"),
                    "target_organism": activity[
                        "target"
                    ].get("organism"),
                },
            )

            bundle.relationships.append(relationship)

        bundle.provenance = {
            "source": self.SOURCE,
            "target_chembl_id": target_chembl_id,
            "target_name": target_name,
            "standard_types": standard_types,
            "activity_count": len(activities),
            "quantitative_count": sum(
                1
                for activity in activities
                if activity["measurement"].get(
                    "standard_value"
                )
                is not None
            ),
            "qualitative_count": sum(
                1
                for activity in activities
                if activity["measurement"].get(
                    "standard_text_value"
                )
                is not None
            ),
        }

        return bundle

    def get_target_evidence_bundle(
        self,
        gene_symbol: str,
        uniprot_id: str,
        preferred_name: str,
        limit: int = 100,
        standard_types: Optional[List[str]] = None,
    ) -> EvidenceBundle:
        """
        Build a complete ChEMBL evidence bundle containing:

        - validated target identity
        - compounds
        - target-compound bioactivity relationships
        - provenance
        """

        target = self.client.find_human_protein_target(
            gene_symbol=gene_symbol,
            required_uniprot=uniprot_id,
            preferred_name=preferred_name,
        )

        target_id = target.get("target_chembl_id")

        bundle = self.get_bioactivity_evidence(
            target_chembl_id=target_id,
            target_name=preferred_name,
            limit=limit,
            standard_types=standard_types,
        )

        target_evidence = self.get_target_evidence(
            gene_symbol=gene_symbol,
            uniprot_id=uniprot_id,
            preferred_name=preferred_name,
        )

        bundle.targets.append(target_evidence)

        bundle.provenance.update(
            {
                "gene_symbol": gene_symbol,
                "uniprot_id": uniprot_id,
                "chembl_target_id": target_id,
                "target_validated": True,
            }
        )

        return bundle

    @staticmethod
    def summarize(
        bundle: EvidenceBundle,
    ) -> Dict[str, Any]:
        """
        Return a compact summary suitable for inference APIs.
        """

        summary = bundle.summary()

        summary.update(
            {
                "provenance": bundle.provenance,
                "quantitative_relationships": sum(
                    1
                    for relationship in bundle.relationships
                    if relationship.evidence_level
                    == "quantitative"
                ),
                "qualitative_relationships": sum(
                    1
                    for relationship in bundle.relationships
                    if relationship.evidence_level
                    == "qualitative"
                ),
            }
        )

        return summary
