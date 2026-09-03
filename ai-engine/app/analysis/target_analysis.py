from typing import Dict, List, Any


class TargetAnalysisEngine:
    """
    Evidence-oriented biological target analysis engine.

    Combines gene identity, pathway context, known variants,
    protein representation, molecular context, and cellular
    context into a structured target assessment.

    This layer is an inference/orchestration component. It does
    not claim clinical validation or therapeutic efficacy.
    """

    def analyze(
        self,
        biological_context: Dict[str, Any],
        protein_features: Dict[str, Any] | None = None,
        molecule_features: Dict[str, Any] | None = None,
        cell_features: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:

        gene = biological_context.get("gene", {})
        variants = biological_context.get("variants", [])
        reactome_entities = biological_context.get(
            "reactome_entities",
            [],
        )

        symbol = self._get_value(gene, "symbol")
        ensembl_id = self._get_value(gene, "ensembl_id")

        pathway_summary = self._analyze_pathways(
            reactome_entities
        )

        variant_summary = self._analyze_variants(
            variants
        )

        protein_summary = self._analyze_protein(
            protein_features
        )

        molecule_summary = self._analyze_molecule(
            molecule_features
        )

        cellular_summary = self._analyze_cell(
            cell_features
        )

        evidence = self._build_evidence(
            symbol=symbol,
            ensembl_id=ensembl_id,
            pathway_summary=pathway_summary,
            variant_summary=variant_summary,
            protein_summary=protein_summary,
            molecule_summary=molecule_summary,
            cellular_summary=cellular_summary,
        )

        assessment = self._build_assessment(
            pathway_summary=pathway_summary,
            variant_summary=variant_summary,
            protein_summary=protein_summary,
            molecule_summary=molecule_summary,
            cellular_summary=cellular_summary,
        )

        return {
            "analysis_type": "target_analysis",
            "gene": symbol,
            "ensembl_id": ensembl_id,
            "target_assessment": assessment,
            "pathways": pathway_summary,
            "variants": variant_summary,
            "protein": protein_summary,
            "molecule": molecule_summary,
            "cellular_context": cellular_summary,
            "evidence": evidence,
            "provenance": {
                "biological_knowledge": [
                    "Ensembl",
                    "Reactome",
                ],
                "representation_models": self._models_used(
                    protein_features,
                    molecule_features,
                    cell_features,
                ),
            },
        }

    @staticmethod
    def _get_value(
        obj: Any,
        key: str,
    ) -> Any:
        if isinstance(obj, dict):
            return obj.get(key)

        return getattr(obj, key, None)

    def _analyze_pathways(
        self,
        entities: List[Any],
    ) -> Dict[str, Any]:

        pathways = []

        for entity in entities:
            name = self._get_value(entity, "name")
            identifier = self._get_value(
                entity,
                "identifier",
            )
            entity_type = self._get_value(
                entity,
                "entity_type",
            )

            if name or identifier:
                pathways.append(
                    {
                        "name": name,
                        "identifier": identifier,
                        "entity_type": entity_type,
                    }
                )

        return {
            "entity_count": len(entities),
            "mapped_entities": len(pathways),
            "entities": pathways[:100],
        }

    def _analyze_variants(
        self,
        variants: List[Any],
    ) -> Dict[str, Any]:

        normalized = []

        for variant in variants:
            if isinstance(variant, dict):
                item = dict(variant)
            else:
                item = {
                    "variant": str(variant)
                }

            normalized.append(item)

        return {
            "variant_count": len(normalized),
            "known_variants": normalized[:100],
        }

    def _analyze_protein(
        self,
        features: Dict[str, Any] | None,
    ) -> Dict[str, Any]:

        if not features:
            return {
                "available": False,
                "reason": "Protein representation not supplied.",
            }

        embedding = features.get(
            "embedding",
            [],
        )

        return {
            "available": True,
            "sequence_length": features.get(
                "sequence_length"
            ),
            "embedding_dimension": features.get(
                "embedding_dimension",
                len(embedding),
            ),
            "model": features.get("model"),
        }

    def _analyze_molecule(
        self,
        features: Dict[str, Any] | None,
    ) -> Dict[str, Any]:

        if not features:
            return {
                "available": False,
                "reason": "Molecular representation not supplied.",
            }

        nested = features.get(
            "features",
            {},
        )

        embedding = nested.get(
            "embedding",
            [],
        )

        return {
            "available": True,
            "smiles": features.get("smiles"),
            "embedding_dimension": nested.get(
                "embedding_dimension",
                len(embedding),
            ),
            "model": features.get("model"),
        }

    def _analyze_cell(
        self,
        features: Dict[str, Any] | None,
    ) -> Dict[str, Any]:

        if not features:
            return {
                "available": False,
                "reason": "Cellular representation not supplied.",
            }

        nested = features.get(
            "features",
            {},
        )

        return {
            "available": True,
            "cell_state": features.get(
                "cell_state"
            ),
            "embedding_dimension": nested.get(
                "embedding_dimension"
            ),
            "model": features.get("model"),
        }

    def _build_evidence(
        self,
        symbol: str | None,
        ensembl_id: str | None,
        pathway_summary: Dict[str, Any],
        variant_summary: Dict[str, Any],
        protein_summary: Dict[str, Any],
        molecule_summary: Dict[str, Any],
        cellular_summary: Dict[str, Any],
    ) -> List[Dict[str, Any]]:

        evidence = []

        if symbol:
            evidence.append(
                {
                    "type": "gene_identity",
                    "source": "Ensembl",
                    "subject": symbol,
                    "identifier": ensembl_id,
                    "strength": "direct",
                }
            )

        if pathway_summary["entity_count"] > 0:
            evidence.append(
                {
                    "type": "pathway_context",
                    "source": "Reactome",
                    "entity_count": pathway_summary[
                        "entity_count"
                    ],
                    "strength": "direct",
                }
            )

        if variant_summary["variant_count"] > 0:
            evidence.append(
                {
                    "type": "variant_context",
                    "source": "Reactome",
                    "variant_count": variant_summary[
                        "variant_count"
                    ],
                    "strength": "direct",
                }
            )

        if protein_summary["available"]:
            evidence.append(
                {
                    "type": "protein_representation",
                    "model": protein_summary.get("model"),
                    "embedding_dimension": protein_summary[
                        "embedding_dimension"
                    ],
                    "strength": "model_derived",
                }
            )

        if molecule_summary["available"]:
            evidence.append(
                {
                    "type": "molecular_representation",
                    "model": molecule_summary.get("model"),
                    "embedding_dimension": molecule_summary[
                        "embedding_dimension"
                    ],
                    "strength": "model_derived",
                }
            )

        if cellular_summary["available"]:
            evidence.append(
                {
                    "type": "cellular_context",
                    "model": cellular_summary.get("model"),
                    "embedding_dimension": cellular_summary[
                        "embedding_dimension"
                    ],
                    "strength": "model_derived",
                }
            )

        return evidence

    def _build_assessment(
        self,
        pathway_summary: Dict[str, Any],
        variant_summary: Dict[str, Any],
        protein_summary: Dict[str, Any],
        molecule_summary: Dict[str, Any],
        cellular_summary: Dict[str, Any],
    ) -> Dict[str, Any]:

        evidence_dimensions = 0

        if pathway_summary["entity_count"] > 0:
            evidence_dimensions += 1

        if variant_summary["variant_count"] > 0:
            evidence_dimensions += 1

        if protein_summary["available"]:
            evidence_dimensions += 1

        if molecule_summary["available"]:
            evidence_dimensions += 1

        if cellular_summary["available"]:
            evidence_dimensions += 1

        confidence = round(
            evidence_dimensions / 5,
            2,
        )

        return {
            "evidence_dimensions": evidence_dimensions,
            "evidence_coverage": confidence,
            "interpretation": (
                "Target context assembled from biological "
                "knowledge and available model-derived "
                "representations."
            ),
            "clinical_claim": False,
        }

    @staticmethod
    def _models_used(
        protein_features: Dict[str, Any] | None,
        molecule_features: Dict[str, Any] | None,
        cell_features: Dict[str, Any] | None,
    ) -> List[str]:

        models = []

        for features in (
            protein_features,
            molecule_features,
            cell_features,
        ):
            if not features:
                continue

            model = features.get("model")

            if isinstance(model, dict):
                checkpoint = model.get(
                    "checkpoint"
                )

                if checkpoint:
                    models.append(checkpoint)

                else:
                    model_name = model.get(
                        "model_name"
                    )

                    if model_name:
                        models.append(
                            model_name
                        )

        return models
