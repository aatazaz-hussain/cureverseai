from typing import Dict, Optional

from app.data.knowledge_service import BiologicalKnowledgeService
from app.analysis.perturbation import simulate_perturbation
from app.analysis.cell_state import interpret_cell_state
from app.models.features.protein_features import ProteinFeatureService
from app.models.features.molecule_features import MoleculeFeatureService
from app.models.features.cell_features import CellFeatureService


class BiologicalInferenceEngine:
    """
    Unified biological inference engine.

    Combines biological knowledge, pretrained protein and molecular
    representations, cellular state analysis, pathway analysis,
    and perturbation analysis into a single inference workflow.
    """

    def __init__(self):
        self.knowledge = BiologicalKnowledgeService()
        self.protein_features = ProteinFeatureService()
        self.molecule_features = MoleculeFeatureService()
        self.cell_features = CellFeatureService()

    def analyze_gene(
        self,
        gene: str,
        perturbation: Optional[float] = None,
    ) -> Dict:
        """
        Run an integrated biological analysis for a gene.
        """

        context = self.knowledge.get_biological_context(gene)

        result = {
            "gene": gene,
            "biological_context": context,
        }

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
                result["cell_features"] = self.cell_features.extract_features(
                    cell_state["cell_state"]
                )

        return result

    def analyze_molecule(self, smiles: str) -> Dict:
        """
        Generate molecular representation for a compound.
        """

        return self.molecule_features.extract_features(smiles)

    def analyze_protein_sequence(self, sequence: str) -> Dict:
        """
        Generate protein representation for a sequence.
        """

        return self.protein_features.extract_features(sequence)
