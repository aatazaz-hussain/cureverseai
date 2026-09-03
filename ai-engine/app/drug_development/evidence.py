from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class TargetEvidence:
    """
    Structured evidence associated with a biological target.
    """

    target: str
    target_id: Optional[str] = None
    source: Optional[str] = None
    evidence_type: str = "biological"
    description: Optional[str] = None
    identifiers: Dict[str, str] = field(
        default_factory=dict
    )
    metadata: Dict[str, Any] = field(
        default_factory=dict
    )


@dataclass
class CompoundEvidence:
    """
    Structured evidence associated with a compound.
    """

    smiles: str
    compound_id: Optional[str] = None
    name: Optional[str] = None
    source: Optional[str] = None
    evidence_type: str = "molecular"
    description: Optional[str] = None
    identifiers: Dict[str, str] = field(
        default_factory=dict
    )
    metadata: Dict[str, Any] = field(
        default_factory=dict
    )


@dataclass
class DrugTargetEvidence:
    """
    Evidence describing a compound-target relationship.

    Relationship strength is intentionally kept separate from
    clinical interpretation. A relationship record does not
    imply efficacy, safety, or clinical validity.
    """

    target: str
    compound: str
    source: str
    relationship_type: str
    evidence_level: str
    description: Optional[str] = None
    identifiers: Dict[str, str] = field(
        default_factory=dict
    )
    metadata: Dict[str, Any] = field(
        default_factory=dict
    )


@dataclass
class EvidenceBundle:
    """
    Unified evidence package for downstream drug-development
    inference engines.
    """

    targets: List[TargetEvidence] = field(
        default_factory=list
    )

    compounds: List[CompoundEvidence] = field(
        default_factory=list
    )

    relationships: List[DrugTargetEvidence] = field(
        default_factory=list
    )

    sources: List[str] = field(
        default_factory=list
    )

    provenance: Dict[str, Any] = field(
        default_factory=dict
    )

    def add_source(
        self,
        source: str,
    ) -> None:

        if source not in self.sources:
            self.sources.append(source)

    def summary(self) -> Dict[str, Any]:
        """
        Return a compact summary suitable for APIs and UI.
        """

        return {
            "targets": len(self.targets),
            "compounds": len(self.compounds),
            "relationships": len(
                self.relationships
            ),
            "sources": list(self.sources),
        }
