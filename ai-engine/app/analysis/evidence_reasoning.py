from typing import Any, Dict, List


class EvidenceReasoningEngine:
    """
    Evidence reasoning layer for CureVerseAI.

    Separates evidence into scientifically meaningful categories:

    - direct biological evidence
    - disease association evidence
    - experimental bioactivity evidence
    - model-derived evidence
    - contextual evidence

    Important:
    Evidence composition is not treated as clinical confidence,
    therapeutic efficacy, or probability of treatment success.
    """

    def reason(
        self,
        biological_context: Dict[str, Any],
        target_analysis: Dict[str, Any],
        open_targets_evidence: Dict[str, Any] | None = None,
        chembl_evidence: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:

        evidence = target_analysis.get(
            "evidence",
            [],
        )

        direct_evidence = []
        model_evidence = []
        contextual_evidence = []

        for item in evidence:
            if not isinstance(item, dict):
                continue

            strength = item.get("strength")

            if strength == "direct":
                direct_evidence.append(item)

            elif strength == "model_derived":
                model_evidence.append(item)

            else:
                contextual_evidence.append(item)

        disease_association_evidence = (
            self._extract_open_targets_evidence(
                open_targets_evidence
            )
        )

        bioactivity_evidence = (
            self._extract_chembl_relationships(
                chembl_evidence
            )
        )

        gene = self._extract_gene(
            biological_context
        )

        pathway_count = self._extract_count(
            target_analysis,
            "pathways",
            "entity_count",
        )

        variant_count = self._extract_count(
            target_analysis,
            "variants",
            "variant_count",
        )

        findings = self._generate_findings(
            gene=gene,
            pathway_count=pathway_count,
            variant_count=variant_count,
            direct_evidence=direct_evidence,
            model_evidence=model_evidence,
            disease_association_evidence=(
                disease_association_evidence
            ),
            bioactivity_evidence=bioactivity_evidence,
        )

        evidence_composition = (
            self._calculate_evidence_composition(
                direct_evidence=direct_evidence,
                model_evidence=model_evidence,
                contextual_evidence=contextual_evidence,
                disease_association_evidence=(
                    disease_association_evidence
                ),
                bioactivity_evidence=bioactivity_evidence,
            )
        )

        return {
            "reasoning_type": (
                "evidence_based_biological_reasoning"
            ),
            "gene": gene,

            "evidence_summary": {
                "total": (
                    len(direct_evidence)
                    + len(model_evidence)
                    + len(contextual_evidence)
                    + len(disease_association_evidence)
                    + len(bioactivity_evidence)
                ),
                "direct": len(direct_evidence),
                "disease_association": (
                    len(disease_association_evidence)
                ),
                "experimental_bioactivity": (
                    len(bioactivity_evidence)
                ),
                "model_derived": len(model_evidence),
                "contextual": len(contextual_evidence),
            },

            "evidence_composition": evidence_composition,

            "findings": findings,

            "sources": {
                "disease_association": (
                    self._extract_external_sources(
                        open_targets_evidence
                    )
                ),
                "experimental_bioactivity": (
                    self._extract_chembl_sources(
                        chembl_evidence
                    )
                ),
            },

            "limitations": [
                "Model-derived representations are not treated "
                "as direct biological evidence.",
                "Disease association evidence is not interpreted "
                "as clinical diagnosis, prognosis, or treatment "
                "efficacy.",
                "ChEMBL bioactivity measurements are preserved "
                "as experimental assay observations.",
                "IC50, EC50, Ki, Kd, and related measurements are "
                "not converted into artificial therapeutic "
                "effectiveness scores.",
                "Cell-based assay measurements are not assumed "
                "to represent direct molecular binding.",
                "Evidence composition does not establish clinical "
                "validity, safety, efficacy, or regulatory approval.",
                "Task-specific experimental and clinical validation "
                "is required for biological and therapeutic claims.",
            ],
        }

    @staticmethod
    def _extract_open_targets_evidence(
        evidence: Dict[str, Any] | None,
    ) -> List[Dict[str, Any]]:

        if not isinstance(evidence, dict):
            return []

        items = evidence.get(
            "evidence",
            [],
        )

        if not isinstance(items, list):
            return []

        return [
            item
            for item in items
            if isinstance(item, dict)
        ]

    @staticmethod
    def _extract_chembl_relationships(
        evidence: Dict[str, Any] | None,
    ) -> List[Dict[str, Any]]:

        if not isinstance(evidence, dict):
            return []

        relationships = evidence.get(
            "relationships",
            [],
        )

        if not isinstance(
            relationships,
            list,
        ):
            return []

        return [
            item
            for item in relationships
            if isinstance(item, dict)
        ]

    @staticmethod
    def _extract_external_sources(
        evidence: Dict[str, Any] | None,
    ) -> List[str]:

        if not isinstance(evidence, dict):
            return []

        summary = evidence.get(
            "summary",
            {},
        )

        if not isinstance(summary, dict):
            return []

        sources = summary.get(
            "sources",
            [],
        )

        if not isinstance(sources, list):
            return []

        return [
            str(source)
            for source in sources
        ]

    @staticmethod
    def _extract_chembl_sources(
        evidence: Dict[str, Any] | None,
    ) -> List[str]:

        if not isinstance(evidence, dict):
            return []

        summary = evidence.get(
            "summary",
            {},
        )

        if not isinstance(summary, dict):
            return []

        sources = summary.get(
            "sources",
            [],
        )

        if not isinstance(sources, list):
            return []

        return [
            str(source)
            for source in sources
        ]

    @staticmethod
    def _extract_gene(
        biological_context: Dict[str, Any],
    ) -> Any:

        gene = biological_context.get(
            "gene"
        )

        if isinstance(gene, dict):
            return gene.get("symbol")

        return getattr(
            gene,
            "symbol",
            None,
        )

    @staticmethod
    def _extract_count(
        target_analysis: Dict[str, Any],
        section: str,
        field: str,
    ) -> int:

        value = target_analysis.get(
            section,
            {},
        )

        if not isinstance(
            value,
            dict,
        ):
            return 0

        count = value.get(
            field,
            0,
        )

        return int(count or 0)

    @staticmethod
    def _calculate_evidence_composition(
        direct_evidence: List[Dict[str, Any]],
        model_evidence: List[Dict[str, Any]],
        contextual_evidence: List[Dict[str, Any]],
        disease_association_evidence: List[Dict[str, Any]],
        bioactivity_evidence: List[Dict[str, Any]],
    ) -> Dict[str, Any]:

        counts = {
            "direct": len(direct_evidence),
            "disease_association": (
                len(disease_association_evidence)
            ),
            "experimental_bioactivity": (
                len(bioactivity_evidence)
            ),
            "model_derived": len(model_evidence),
            "contextual": len(contextual_evidence),
        }

        total = sum(counts.values())

        if total == 0:
            return {
                "level": "insufficient",
                "basis": "no_evidence",
                "counts": counts,
                "ratios": {},
            }

        ratios = {
            key: round(
                value / total,
                3,
            )
            for key, value in counts.items()
        }

        if (
            counts["direct"] > 0
            and counts["experimental_bioactivity"] > 0
            and counts["disease_association"] > 0
        ):
            level = "multi_source_supported"

        elif (
            counts["direct"] > 0
            and counts["experimental_bioactivity"] > 0
        ):
            level = "biologically_and_experimentally_supported"

        elif (
            counts["experimental_bioactivity"] > 0
            and counts["disease_association"] > 0
        ):
            level = "externally_multi_source_supported"

        elif counts["experimental_bioactivity"] > 0:
            level = "experimentally_supported"

        elif counts["disease_association"] > 0:
            level = "disease_association_supported"

        elif counts["direct"] > 0:
            level = "directly_supported"

        elif counts["model_derived"] > 0:
            level = "model_supported"

        else:
            level = "contextually_supported"

        return {
            "level": level,
            "basis": (
                "evidence_category_composition"
            ),
            "counts": counts,
            "ratios": ratios,
        }

    @staticmethod
    def _generate_findings(
        gene: Any,
        pathway_count: int,
        variant_count: int,
        direct_evidence: List[Dict[str, Any]],
        model_evidence: List[Dict[str, Any]],
        disease_association_evidence: List[Dict[str, Any]],
        bioactivity_evidence: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:

        findings: List[Dict[str, Any]] = []

        if gene:
            findings.append(
                {
                    "type": "target_identity",
                    "statement": (
                        f"{gene} is represented by direct "
                        "biological knowledge from the integrated "
                        "knowledge layer."
                    ),
                    "evidence_type": "direct",
                }
            )

        if pathway_count > 0:
            findings.append(
                {
                    "type": "pathway_context",
                    "statement": (
                        f"{gene} has {pathway_count} mapped "
                        "biological entities in the current "
                        "Reactome-derived context."
                    ),
                    "evidence_type": "direct",
                }
            )

        if variant_count > 0:
            findings.append(
                {
                    "type": "variant_context",
                    "statement": (
                        f"{gene} has {variant_count} mapped "
                        "variant records in the current "
                        "biological context."
                    ),
                    "evidence_type": "direct",
                }
            )

        if model_evidence:
            findings.append(
                {
                    "type": "model_representation",
                    "statement": (
                        f"{gene} has model-derived biological "
                        "representations available for inference."
                    ),
                    "evidence_type": "model_derived",
                }
            )

        if disease_association_evidence:
            diseases = []

            for item in disease_association_evidence:
                metadata = item.get(
                    "metadata",
                    {},
                )

                if not isinstance(
                    metadata,
                    dict,
                ):
                    continue

                disease_name = metadata.get(
                    "disease_name"
                )

                if (
                    disease_name
                    and disease_name not in diseases
                ):
                    diseases.append(
                        str(disease_name)
                    )

            findings.append(
                {
                    "type": "disease_association",
                    "statement": (
                        f"{gene} has {len(disease_association_evidence)} "
                        "retrieved disease-association records "
                        "from Open Targets."
                    ),
                    "evidence_type": (
                        "disease_association"
                    ),
                    "diseases": diseases[:10],
                }
            )

        if bioactivity_evidence:
            quantitative = 0
            qualitative = 0

            for item in bioactivity_evidence:
                level = item.get(
                    "evidence_level"
                )

                if level == "quantitative":
                    quantitative += 1

                elif level == "qualitative":
                    qualitative += 1

            findings.append(
                {
                    "type": "experimental_bioactivity",
                    "statement": (
                        f"{gene} has {len(bioactivity_evidence)} "
                        "experimental bioactivity assay "
                        "relationships retrieved from ChEMBL."
                    ),
                    "evidence_type": (
                        "experimental_bioactivity"
                    ),
                    "quantitative_measurements": (
                        quantitative
                    ),
                    "qualitative_measurements": (
                        qualitative
                    ),
                }
            )

        return findings
