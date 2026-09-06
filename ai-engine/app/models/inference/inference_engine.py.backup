from typing import Dict, Optional

from app.data.knowledge_service import BiologicalKnowledgeService
from app.analysis.perturbation import simulate_perturbation
from app.analysis.cell_state import interpret_cell_state
from app.analysis.evidence_reasoning import EvidenceReasoningEngine
from app.analysis.target_analysis import TargetAnalysisEngine
from app.models.features.protein_features import ProteinFeatureService
from app.models.features.molecule_features import MoleculeFeatureService
from app.models.features.cell_features import CellFeatureService
from app.drug_development.sources.open_targets_evidence import (
    OpenTargetsEvidenceService,
)
from app.data.sources.ensembl import EnsemblClient
from app.drug_development.sources.chembl_evidence import (
    ChEMBLEvidenceService,
)

class BiologicalInferenceEngine:
    """
    Unified biological inference engine.

    Combines biological knowledge, pretrained protein and molecular
    representations, cellular context, pathway information,
    perturbation analysis, target analysis, and external
    drug-development evidence.
    """

    def __init__(self):
        self.knowledge = BiologicalKnowledgeService()
        self.protein_features = ProteinFeatureService()
        self.molecule_features = MoleculeFeatureService()
        self.cell_features = CellFeatureService()
        self.evidence_reasoning = EvidenceReasoningEngine()
        self.target_analysis = TargetAnalysisEngine()
        self.open_targets = OpenTargetsEvidenceService()
        self.ensembl = EnsemblClient()
        self.chembl_evidence = ChEMBLEvidenceService()
    def analyze_gene(
        self,
        gene: str,
        perturbation: Optional[float] = None,
        smiles: Optional[str] = None,
    ) -> Dict:
        """
        Run an integrated biological analysis for a gene.

        Parameters
        ----------
        gene:
            Gene symbol or supported biological identifier.

        perturbation:
            Optional perturbation value used to generate
            cellular-state context.

        smiles:
            Optional molecular SMILES string for compound context.
        """

        context = self.knowledge.get_biological_context(gene)

        result = {
            "analysis_type": "integrated_gene_analysis",
            "gene": gene,
            "biological_context": context,
        }

        protein_result = None
        molecule_result = None
        cell_result = None
        ensembl_id = None

        # ---------------------------------------------------------
        # Protein representation
        # ---------------------------------------------------------

        gene_record = context.get("gene")

        if gene_record:
            ensembl_id = self._get_value(
                gene_record,
                "ensembl_id",
            )

            transcript_id = self._get_value(
                gene_record,
                "canonical_transcript",
            )

            if transcript_id:
                try:
                    from app.data.sources.ensembl_sequence import (
                        EnsemblSequenceClient,
                    )

                    sequence_client = EnsemblSequenceClient()

                    sequence = sequence_client.get_protein_sequence(
                        transcript_id
                    )

                    if sequence:
                        protein_result = (
                            self.protein_features.extract_features(
                                sequence
                            )
                        )

                        result["protein_features"] = protein_result

                except Exception as exc:
                    result["protein_features_error"] = str(exc)

        # ---------------------------------------------------------
        # Molecular representation
        # ---------------------------------------------------------

        if smiles:
            try:
                molecule_result = (
                    self.molecule_features.extract_features(
                        smiles
                    )
                )

                result["molecule_features"] = molecule_result

            except Exception as exc:
                result["molecule_features_error"] = str(exc)

        # ---------------------------------------------------------
        # Cellular context
        # ---------------------------------------------------------

        if perturbation is not None:
            perturbation_result = simulate_perturbation(
                gene,
                perturbation,
            )

            result["perturbation"] = perturbation_result

            cell_state = interpret_cell_state(
                perturbation_result
            )

            result["cell_state"] = cell_state

            if cell_state.get("status") == "success":
                cell_result = (
                    self.cell_features.extract_features(
                        cell_state["cell_state"]
                    )
                )

                result["cell_features"] = cell_result

        # ---------------------------------------------------------
        # Target analysis
        # ---------------------------------------------------------

        target_result = self.target_analysis.analyze(
            biological_context=context,
            protein_features=protein_result,
            molecule_features=molecule_result,
            cell_features=cell_result,
        )

        result["target_analysis"] = target_result

        # ---------------------------------------------------------
        # Open Targets drug-development evidence
        # ---------------------------------------------------------

        if ensembl_id:
            try:
                open_targets_evidence = (
                    self.open_targets.get_target_disease_evidence(
                        target_id=ensembl_id,
                        size=10,
                    )
                )

                result["open_targets_evidence"] = {
                    "summary": (
                        open_targets_evidence.summary()
                    ),
                    "provenance": (
                        open_targets_evidence.provenance
                    ),
                    "evidence": [
                        {
                            "target": item.target,
                            "target_id": item.target_id,
                            "source": item.source,
                            "evidence_type": (
                                item.evidence_type
                            ),
                            "description": (
                                item.description
                            ),
                            "identifiers": (
                                item.identifiers
                            ),
                            "metadata": (
                                item.metadata
                            ),
                        }
                        for item in (
                            open_targets_evidence.targets
                        )
                    ],
                }

            except Exception as exc:
                result["open_targets_evidence_error"] = str(
                    exc
                )
        if ensembl_id:
            try:
                uniprot_resolution = (
                    self.ensembl
                    .resolve_reviewed_uniprot_accession(
                        ensembl_id=ensembl_id,
                    )
                )

                result["uniprot_resolution"] = (
                    uniprot_resolution
                )

                if uniprot_resolution:
                    uniprot_accession = (
                        uniprot_resolution["accession"]
                    )

                    preferred_name = (
                        uniprot_resolution.get(
                            "protein_name"
                        )
                    )

                    if preferred_name:
                        chembl_evidence = (
                            self.chembl_evidence
                            .get_target_evidence_bundle(
                                gene_symbol=gene,
                                uniprot_id=(
                                    uniprot_accession
                                ),
                                preferred_name=(
                                    preferred_name
                                ),
                                limit=20,
                                standard_types=[
                                    "IC50",
                                    "EC50",
                                    "Ki",
                                    "Kd",
                                    "AC50",
                                ],
                            )
                        )

                        result["chembl_evidence"] = {
                            "summary": (
                                self.chembl_evidence
                                .summarize(
                                    chembl_evidence
                                )
                            ),
                            "provenance": (
                                chembl_evidence
                                .provenance
                            ),
                            "targets": [
                                {
                                    "target": item.target,
                                    "target_id": (
                                        item.target_id
                                    ),
                                    "source": item.source,
                                    "evidence_type": (
                                        item.evidence_type
                                    ),
                                    "description": (
                                        item.description
                                    ),
                                    "identifiers": (
                                        item.identifiers
                                    ),
                                    "metadata": (
                                        item.metadata
                                    ),
                                }
                                for item in (
                                    chembl_evidence.targets
                                )
                            ],
                            "compounds": [
                                {
                                    "compound_id": (
                                        item.compound_id
                                    ),
                                    "name": item.name,
                                    "source": item.source,
                                    "evidence_type": (
                                        item.evidence_type
                                    ),
                                    "description": (
                                        item.description
                                    ),
                                    "identifiers": (
                                        item.identifiers
                                    ),
                                    "metadata": (
                                        item.metadata
                                    ),
                                }
                                for item in (
                                    chembl_evidence.compounds
                                )
                            ],
                            "relationships": [
                                {
                                    "target": item.target,
                                    "compound": item.compound,
                                    "source": item.source,
                                    "relationship_type": (
                                        item.relationship_type
                                    ),
                                    "evidence_level": (
                                        item.evidence_level
                                    ),
                                    "description": (
                                        item.description
                                    ),
                                    "identifiers": (
                                        item.identifiers
                                    ),
                                    "metadata": (
                                        item.metadata
                                    ),
                                }
                                for item in (
                                    chembl_evidence
                                    .relationships
                                )
                            ],
                        }

            except Exception as exc:
                result[
                    "chembl_evidence_error"
                ] = str(exc)
        # ---------------------------------------------------------
        # Evidence reasoning
        # ---------------------------------------------------------

        reasoning_result = self.evidence_reasoning.reason(
            biological_context=context,
            target_analysis=target_result,
            open_targets_evidence=result.get(
                "open_targets_evidence"
            ),
            chembl_evidence=result.get(
                "chembl_evidence"
            ),
        )

        result["evidence_reasoning"] = reasoning_result

        return result
    def analyze_molecule(
        self,
        smiles: str,
    ) -> Dict:
        """
        Generate molecular representation for a compound.
        """

        return self.molecule_features.extract_features(
            smiles
        )

    def analyze_protein_sequence(
        self,
        sequence: str,
    ) -> Dict:
        """
        Generate protein representation for a sequence.
        """

        return self.protein_features.extract_features(
            sequence
        )

    @staticmethod
    def _get_value(
        obj,
        key: str,
    ):
        if isinstance(obj, dict):
            return obj.get(key)

        return getattr(
            obj,
            key,
            None,
        )
