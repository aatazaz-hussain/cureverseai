from typing import Any, Optional

from pydantic import BaseModel, Field


class DrugDevelopmentRequest(BaseModel):
    gene: str = Field(
        ...,
        min_length=1,
        max_length=100,
        description="Gene symbol, for example TP53.",
    )

    smiles: Optional[str] = Field(
        default=None,
        description="Optional molecular SMILES string.",
    )

    cell_state: Optional[dict[str, Any]] = Field(
        default=None,
        description="Optional cellular state features.",
    )

    include_open_targets: bool = Field(
        default=True,
        description="Include Open Targets disease-association evidence.",
    )

    include_chembl: bool = Field(
        default=True,
        description="Include ChEMBL bioactivity evidence.",
    )


class DrugDevelopmentResponse(BaseModel):
    success: bool
    domain: str
    analysis_type: str

    gene: str
    ensembl_id: Optional[str] = None
    uniprot_id: Optional[str] = None

    analysis: dict[str, Any] = Field(default_factory=dict)

    evidence_reasoning: dict[str, Any] = Field(
        default_factory=dict
    )

    provenance: dict[str, Any] = Field(
        default_factory=dict
    )

    error: Optional[str] = None
