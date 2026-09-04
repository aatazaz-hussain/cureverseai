from typing import Any, Dict, List


class EvidenceReasoningEngine:
    """
    Evidence reasoning layer for CureVerseAI.

    Separates:
    - directly observed biological evidence
    - external curated/aggregated evidence
    - model-derived representations
    - contextual evidence
    - inferred conclusions

    External evidence is kept separate from direct biological
    observations and model-derived representations.
    """

    def reason(
        self,
        biological_context: Dict[str, Any],
        target_analysis: Dict[str, Any],
        open_targets_evidence: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:

        evidence = target_analysis.get("evidence", [])

        direct_evidence = []
        model_evidence = []
        contextual_evidence = []

        for item in evidence:
            strength = item.get("strength")

            if strength == "direct":
                direct_evidence.append(item)

            elif strength == "model_derived":
                model_evidence.append(item)

            else:
                contextual_evidence.append(item)

        external_evidence = self._extract_external_evidence(
            open_targets_evidence
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
            external_evidence=external_evidence,
        )

        coverage = self._calculate_coverage(
            direct_evidence=direct_evidence,
            model_evidence=model_evidence,
            contextual_evidence=contextual_evidence,
            external_evidence=external_evidence,
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
                    + len(external_evidence)
                ),
                "direct": len(direct_evidence),
                "external": len(external_evidence),
                "model_derived": len(model_evidence),
                "contextual": len(contextual_evidence),
            },
            "coverage": coverage,
            "findings": findings,
            "external_sources": self._extract_external_sources(
                open_targets_evidence
            ),
            "limitations": [
                "Model-derived representations are not treated "
                "as direct biological evidence.",
                "External association scores are preserved as "
                "source evidence and are not interpreted as "
                "clinical probabilities or therapeutic efficacy.",
                "Evidence coverage does not establish clinical "
                "validity or therapeutic efficacy.",
                "Task-specific experimental validation is required "
                "for biological claims.",
            ],
        }

    @staticmethod
    def _extract_external_evidence(
        open_targets_evidence: Dict[str, Any] | None,
    ) -> List[Dict[str, Any]]:

        if not isinstance(
            open_targets_evidence,
            dict,
        ):
            return []

        evidence = open_targets_evidence.get(
            "evidence",
            [],
        )

        if not isinstance(
            evidence,
            list,
        ):
            return []

        return [
            item
            for item in evidence
            if isinstance(item, dict)
        ]

    @staticmethod
    def _extract_external_sources(
        open_targets_evidence: Dict[str, Any] | None,
    ) -> List[str]:

        if not isinstance(
            open_targets_evidence,
            dict,
        ):
            return []

        summary = open_targets_evidence.get(
            "summary",
            {},
        )

        if not isinstance(
            summary,
            dict,
        ):
            return []

        sources = summary.get(
            "sources",
            [],
        )

        if not isinstance(
            sources,
            list,
        ):
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
    def _calculate_coverage(
        direct_evidence: List[Dict[str, Any]],
        model_evidence: List[Dict[str, Any]],
        contextual_evidence: List[Dict[str, Any]],
        external_evidence: List[Dict[str, Any]],
    ) -> Dict[str, Any]:

        total = (
            len(direct_evidence)
            + len(model_evidence)
            + len(contextual_evidence)
            + len(external_evidence)
        )

        if total == 0:
            return {
                "score": 0.0,
                "level": "insufficient",
            }

        direct_ratio = (
            len(direct_evidence) / total
        )

        external_ratio = (
            len(external_evidence) / total
        )

        if direct_ratio >= 0.5:
            level = "strong"
        elif (
            direct_ratio >= 0.25
            or external_ratio >= 0.25
        ):
            level = "moderate"
        elif external_evidence:
            level = "externally_supported"
        else:
            level = "model_supported"

        return {
            "score": round(
                direct_ratio,
                2,
            ),
            "level": level,
            "direct_ratio": round(
                direct_ratio,
                2,
            ),
            "external_ratio": round(
                external_ratio,
                2,
            ),
        }

    @staticmethod
    def _generate_findings(
        gene: Any,
        pathway_count: int,
        variant_count: int,
        direct_evidence: List[Dict[str, Any]],
        model_evidence: List[Dict[str, Any]],
        external_evidence: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:

        findings = []

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
                    "type": "pathway_association",
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
                        f"{variant_count} variant records are "
                        "available in the current biological "
                        "context."
                    ),
                    "evidence_type": "direct",
                }
            )

        if external_evidence:
            diseases = []

            for item in external_evidence:
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

                score = metadata.get(
                    "association_score"
                )

                if disease_name:
                    diseases.append(
                        {
                            "name": disease_name,
                            "association_score": score,
                        }
                    )

            findings.append(
                {
                    "type": "target_disease_associations",
                    "statement": (
                        f"{gene} has {len(external_evidence)} "
                        "retrieved target-disease associations "
                        "from Open Targets."
                    ),
                    "evidence_type": "external",
                    "source": "Open Targets",
                    "associations": diseases,
                }
            )

        if model_evidence:
            models = []

            for item in model_evidence:
                model = item.get(
                    "model"
                )

                if isinstance(
                    model,
                    dict,
                ):
                    checkpoint = model.get(
                        "checkpoint"
                    )

                    model_name = model.get(
                        "model_name"
                    )

                    if checkpoint:
                        models.append(
                            checkpoint
                        )
                    elif model_name:
                        models.append(
                            model_name
                        )

            findings.append(
                {
                    "type": "multimodal_representation",
                    "statement": (
                        "The target context includes "
                        "model-derived representations that "
                        "can support downstream biological "
                        "inference."
                    ),
                    "models": models,
                    "evidence_type": "model_derived",
                }
            )

        return findings
