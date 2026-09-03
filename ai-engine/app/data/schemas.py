from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class GeneRecord:
    symbol: str
    ensembl_id: Optional[str] = None
    name: Optional[str] = None
    species: Optional[str] = None
    biotype: Optional[str] = None
    chromosome: Optional[str] = None
    start: Optional[int] = None
    end: Optional[int] = None
    strand: Optional[int] = None
    assembly: Optional[str] = None
    canonical_transcript: Optional[str] = None
    description: Optional[str] = None
    pathways: List[str] = field(default_factory=list)


@dataclass
class BiologicalEntity:
    identifier: str
    name: str
    entity_type: str
    source: str
    species: Optional[List[str]] = None
    compartment: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class MutationRecord:
    gene: str
    variant: str
    identifier: Optional[str] = None
    source: str = "Reactome"
    species: Optional[List[str]] = None
    compartment: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
