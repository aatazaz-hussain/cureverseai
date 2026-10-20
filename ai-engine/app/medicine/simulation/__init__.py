"""
CureVerseAI — Medicine simulation package.

This package holds the shared simulation contract and the
three Medicine workflows:

    virtual_disease_simulation
        healthy reference vs disease-associated state

    treatment_simulation
        disease state vs single-intervention scenario

    combination_treatment_simulation
        disease state vs intervention A, B, and A+B

The shared contract lives in schemas.py and is imported here
so callers can use:

    from app.medicine.simulation import SimulationResult

instead of reaching into the schemas module directly.

Only schema names are re-exported. Task handlers, service
functions, resolvers, and models live in their own modules
and are imported by their consumers, not by this package
initializer. This keeps package import cheap and prevents
import cycles as the package grows.
"""

from app.medicine.simulation.schemas import (  # noqa: F401
    SimulationTask,
    SimulationStatus,
    StateKind,
    DirectionOfBenefit,
    ResponseDirection,
    ResponseMethod,
    OverallInterpretation,
    InteractionClass,
    CellContext,
    DiseaseRef,
    InterventionRef,
    TargetRef,
    FunctionalIndicator,
    Measurement,
    IndicatorValue,
    BiologicalState,
    Response,
    ScenarioComparison,
    ProvenanceRecord,
    SourceStatus,
    MedicineEvidence,
    SimulationRun,
    SimulationResult,
    to_dict,
    to_wire,
)




# ---------------------------------------------------------------------------
# Service entry points (Workflow handlers)
# ---------------------------------------------------------------------------

from app.medicine.simulation.service import (  # noqa: F401,E402
    run_virtual_disease_simulation,
    run_treatment_simulation,
    run_combination_treatment_simulation,
    PIPELINE_VERSION,
)

from app.medicine.simulation.disease_resolver import (  # noqa: F401,E402
    resolve_disease,
    resolve_disease_with_status,
)

from app.medicine.simulation.intervention_resolver import (  # noqa: F401,E402
    resolve_intervention,
    resolve_intervention_with_status,
)

from app.medicine.simulation.function_vocabulary import (  # noqa: F401,E402
    FUNCTION_MAPPER_VERSION,
    REFERENCE_PAIRS,
    get_pair,
    list_curated_diseases,
)

from app.medicine.simulation.response_model import (  # noqa: F401,E402
    build_w01_comparison,
    build_w02_comparison,
)

from app.medicine.simulation.combination_model import (  # noqa: F401,E402
    build_w03_comparison,
)

from app.medicine.simulation.uncertainty import (  # noqa: F401,E402
    from_source_status,
    from_evidence_method,
    combine as combine_uncertainty,
)



from app.medicine.simulation.medicine_effect_model import (  # noqa: F401,E402
    compute_medicine_effect,
)

from app.medicine.simulation.combination_effect_model import (  # noqa: F401,E402
    compute_combination_effect,
)

from app.medicine.simulation.disease_direction_resolver import (  # noqa: F401,E402
    classify_disease,
    resolve_directions,
)

from app.medicine.simulation.cell_health_model import (  # noqa: F401,E402
    compute_disease_health,
    METHOD as HEALTH_MODEL_METHOD,
)

from app.medicine.simulation.function_mapper import (  # noqa: F401,E402
    derive_pair,
    MAPPER_VERSION,
)

__all__ = [
    "SimulationTask",
    "SimulationStatus",
    "StateKind",
    "DirectionOfBenefit",
    "ResponseDirection",
    "ResponseMethod",
    "OverallInterpretation",
    "InteractionClass",
    "CellContext",
    "DiseaseRef",
    "InterventionRef",
    "TargetRef",
    "FunctionalIndicator",
    "Measurement",
    "IndicatorValue",
    "BiologicalState",
    "Response",
    "ScenarioComparison",
    "ProvenanceRecord",
    "SourceStatus",
    "MedicineEvidence",
    "SimulationRun",
    "SimulationResult",
    "to_dict",
    "to_wire",
    # Service entry points
    "run_virtual_disease_simulation",
    "run_treatment_simulation",
    "run_combination_treatment_simulation",
    "PIPELINE_VERSION",
    # Resolvers
    "resolve_disease",
    "resolve_disease_with_status",
    "resolve_intervention",
    "resolve_intervention_with_status",
    # Vocabulary
    "FUNCTION_MAPPER_VERSION",
    "REFERENCE_PAIRS",
    "get_pair",
    "list_curated_diseases",
    # Comparison builders
    "build_w01_comparison",
    "build_w02_comparison",
    "build_w03_comparison",
    # Uncertainty helpers
    "from_source_status",
    "from_evidence_method",
    "combine_uncertainty",
    "compute_medicine_effect",
    "compute_combination_effect",
    "classify_disease",
    "resolve_directions",
    "compute_disease_health",
    "HEALTH_MODEL_METHOD",
    "derive_pair",
    "MAPPER_VERSION",
]
