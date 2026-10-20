from typing import Any, Dict

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from app.services.ai_engine import analyze, get_medicine_curated


router = APIRouter(prefix="/analyze", tags=["AI Analysis"])


class AnalyzeRequest(BaseModel):
    domain: str = Field(..., min_length=1)
    task: str = Field(..., min_length=1)
    input: Dict[str, Any] = Field(default_factory=dict)


@router.get("/domains")
async def domains():
    return {
        "domains": [
            "research",
            "drug_development",
            "medicine",
            "biotechnology",
            "education",
        ],
        "count": 5,
    }


#: Maximum accepted length of the `disease` string for
#: W02 requests. Real disease names are far shorter;
#: anything above this is almost certainly an accidental
#: paste or a bad client.
_W02_MAX_DISEASE_LENGTH = 500


def _validate_w02_request(request: AnalyzeRequest) -> None:
    """
    Validate a reverse_disease_engineering request.

    Raises HTTPException(400) on failure. Called only for
    W02 requests; other tasks keep the existing passthrough
    behavior.
    """

    disease = request.input.get("disease")

    if not isinstance(disease, str) or not disease.strip():
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid W02 request.",
                "message": (
                    "input.disease must be a non-empty string."
                ),
            },
        )

    if len(disease) > _W02_MAX_DISEASE_LENGTH:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid W02 request.",
                "message": (
                    "input.disease exceeds the maximum length "
                    f"of {_W02_MAX_DISEASE_LENGTH} characters."
                ),
            },
        )


#: Maximum accepted length of the `disease` string for
#: W03 requests. Matches the W02 limit for consistency.
_W03_MAX_DISEASE_LENGTH = 500

#: Maximum accepted length of `mechanism_id` and
#: `target_id`. These are identifiers, not free text;
#: anything above this is a malformed client.
_W03_MAX_ID_LENGTH = 200


def _validate_w03_request(request: AnalyzeRequest) -> None:
    """
    Validate a therapeutic_discovery request.

    Raises HTTPException(400) on failure.

    `disease` must be a non-empty string <= 500 chars.
    `mechanism_id` and `target_id` are optional; when
    supplied they must be non-empty strings <= 200 chars.
    """

    disease = request.input.get("disease")

    if not isinstance(disease, str) or not disease.strip():
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid W03 request.",
                "message": (
                    "input.disease must be a non-empty string."
                ),
            },
        )

    if len(disease) > _W03_MAX_DISEASE_LENGTH:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid W03 request.",
                "message": (
                    "input.disease exceeds the maximum length "
                    f"of {_W03_MAX_DISEASE_LENGTH} characters."
                ),
            },
        )

    for field_name in ("mechanism_id", "target_id"):
        value = request.input.get(field_name)

        # Missing or None are both valid — these fields
        # are optional.
        if value is None:
            continue

        if not isinstance(value, str) or not value.strip():
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Invalid W03 request.",
                    "message": (
                        f"input.{field_name} must be a "
                        "non-empty string when supplied."
                    ),
                },
            )

        if len(value) > _W03_MAX_ID_LENGTH:
            raise HTTPException(
                status_code=400,
                detail={
                    "error": "Invalid W03 request.",
                    "message": (
                        f"input.{field_name} exceeds the "
                        f"maximum length of "
                        f"{_W03_MAX_ID_LENGTH} characters."
                    ),
                },
            )


#: Maximum accepted lengths for Medicine inputs.
_MED_MAX_DISEASE_LENGTH = 500
_MED_MAX_INTERVENTION_LENGTH = 300
_MED_MAX_CELL_TYPE_LENGTH = 200
_MED_MAX_CONTEXT_LENGTH = 200
_MED_MAX_BASELINE_ID_LENGTH = 200

#: Medicine task names, mirrored from the AI Engine vocabulary.
_MED_W01_TASK = "virtual_disease_simulation"
_MED_W02_TASK = "treatment_simulation"
_MED_W03_TASK = "combination_treatment_simulation"


def _med_require_nonempty_str(
    request: AnalyzeRequest,
    field_name: str,
    max_length: int,
    task_label: str,
) -> str:
    """
    Validate that input.<field_name> is a non-empty string
    within the maximum length. Returns the stripped value.

    Raises HTTPException(400) with a shape consistent with the
    existing W02/W03 validators.
    """
    value = request.input.get(field_name)

    if not isinstance(value, str) or not value.strip():
        raise HTTPException(
            status_code=400,
            detail={
                "error": f"Invalid {task_label} request.",
                "message": (
                    f"input.{field_name} must be a non-empty "
                    "string."
                ),
            },
        )

    stripped = value.strip()

    if len(stripped) > max_length:
        raise HTTPException(
            status_code=400,
            detail={
                "error": f"Invalid {task_label} request.",
                "message": (
                    f"input.{field_name} exceeds the maximum "
                    f"length of {max_length} characters."
                ),
            },
        )

    return stripped


def _med_optional_str(
    request: AnalyzeRequest,
    field_name: str,
    max_length: int,
    task_label: str,
) -> None:
    """
    Validate an optional string field: if present, it must be a
    non-empty string within the maximum length. Missing or None
    is valid.
    """
    value = request.input.get(field_name)

    if value is None:
        return

    if not isinstance(value, str) or not value.strip():
        raise HTTPException(
            status_code=400,
            detail={
                "error": f"Invalid {task_label} request.",
                "message": (
                    f"input.{field_name} must be a non-empty "
                    "string when supplied."
                ),
            },
        )

    if len(value.strip()) > max_length:
        raise HTTPException(
            status_code=400,
            detail={
                "error": f"Invalid {task_label} request.",
                "message": (
                    f"input.{field_name} exceeds the maximum "
                    f"length of {max_length} characters."
                ),
            },
        )


def _validate_medicine_w01_request(request: AnalyzeRequest) -> None:
    """
    Validate a virtual_disease_simulation request.

    Required: input.disease.
    Optional: input.cell_type, input.context.
    """
    _med_require_nonempty_str(
        request, "disease", _MED_MAX_DISEASE_LENGTH, "Medicine W01"
    )
    _med_optional_str(
        request, "cell_type", _MED_MAX_CELL_TYPE_LENGTH, "Medicine W01"
    )
    _med_optional_str(
        request, "context", _MED_MAX_CONTEXT_LENGTH, "Medicine W01"
    )


def _validate_medicine_w02_request(request: AnalyzeRequest) -> None:
    """
    Validate a treatment_simulation request.

    Required: input.disease, input.intervention_id.
    Optional: input.baseline_id.
    """
    _med_require_nonempty_str(
        request, "disease", _MED_MAX_DISEASE_LENGTH, "Medicine W02"
    )
    _med_require_nonempty_str(
        request,
        "intervention_id",
        _MED_MAX_INTERVENTION_LENGTH,
        "Medicine W02",
    )
    _med_optional_str(
        request, "baseline_id", _MED_MAX_BASELINE_ID_LENGTH, "Medicine W02"
    )


def _normalize_intervention_id(value: str) -> str:
    """
    Light normalization for duplicate detection only.

    Strips, uppercases, and drops an optional ``chembl:``
    prefix. This is NOT the AI Engine's canonical resolver;
    it only catches obvious duplicates before dispatch.
    """
    v = (value or "").strip().upper()
    if v.startswith("CHEMBL:"):
        v = v[len("CHEMBL:"):]
    return v


def _validate_medicine_w03_request(request: AnalyzeRequest) -> None:
    """
    Validate a combination_treatment_simulation request.

    Required: input.disease, input.intervention_a_id,
              input.intervention_b_id.
    Optional: input.baseline_id.

    Rejects duplicate intervention ids after light
    normalization, per the specification's rule that the same
    intervention must not be selected twice without an
    explicitly documented reason.
    """
    _med_require_nonempty_str(
        request, "disease", _MED_MAX_DISEASE_LENGTH, "Medicine W03"
    )
    _med_require_nonempty_str(
        request,
        "intervention_a_id",
        _MED_MAX_INTERVENTION_LENGTH,
        "Medicine W03",
    )
    _med_require_nonempty_str(
        request,
        "intervention_b_id",
        _MED_MAX_INTERVENTION_LENGTH,
        "Medicine W03",
    )
    _med_optional_str(
        request, "baseline_id", _MED_MAX_BASELINE_ID_LENGTH, "Medicine W03"
    )

    a = _normalize_intervention_id(
        str(request.input.get("intervention_a_id") or "")
    )
    b = _normalize_intervention_id(
        str(request.input.get("intervention_b_id") or "")
    )

    if a and a == b:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "Invalid Medicine W03 request.",
                "message": (
                    "input.intervention_a_id and "
                    "input.intervention_b_id must refer to "
                    "different interventions."
                ),
            },
        )


def _mirror_medicine_status(payload: Any, task: str) -> Any:
    """
    Mirror the scientific status to data.status for medicine
    responses, per Phase 1 decision 8c.

    The mirrored value is the run's scientific status
    (success / partial / not_found / unsupported / error).
    It is additive: the original payload is preserved
    unchanged, including data.result.run.status.

    No-ops for non-medicine payloads or unexpected shapes.
    """
    try:
        if not isinstance(payload, dict):
            return payload
        data = payload.get("data")
        if not isinstance(data, dict):
            return payload
        result = data.get("result")
        if not isinstance(result, dict):
            return payload
        run = result.get("run")
        if not isinstance(run, dict):
            return payload
        status = run.get("status")
        if isinstance(status, str):
            data["status"] = status
    except Exception:
        # Never let the mirror break a response.
        return payload

    return payload


@router.get("/medicine/curated")
async def medicine_curated():
    """
    Proxy the AI Engine's curated Medicine vocabulary.

    Returns the AI Engine's JSON verbatim on success. Maps
    transport failures to the standard backend error codes:
    502 for HTTP errors from the AI Engine, 504 for timeout,
    502 for connection failures, 500 for anything else.
    """
    try:
        return await get_medicine_curated()
    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=504,
            detail={
                "error": "AI Engine timed out.",
                "message": str(exc),
            },
        ) from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "error": "AI Engine returned an error.",
                "message": (
                    f"Upstream status "
                    f"{exc.response.status_code}: "
                    f"{exc.response.text[:500]}"
                ),
            },
        ) from exc
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "error": "AI Engine unreachable.",
                "message": str(exc),
            },
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "CureVerseAI Medicine curated lookup failed.",
                "message": str(exc),
            },
        ) from exc


@router.post("")
async def run_analysis(request: AnalyzeRequest):
    if request.domain == "medicine":
        task_norm = request.task.strip().lower()
        if task_norm == _MED_W01_TASK:
            _validate_medicine_w01_request(request)
        elif task_norm == _MED_W02_TASK:
            _validate_medicine_w02_request(request)
        elif task_norm == _MED_W03_TASK:
            _validate_medicine_w03_request(request)

    if (
        request.domain == "drug_development"
        and request.task == "reverse_disease_engineering"
    ):
        _validate_w02_request(request)

    if (
        request.domain == "drug_development"
        and request.task == "therapeutic_discovery"
    ):
        _validate_w03_request(request)

    try:
        payload = await analyze(
            {
                "domain": request.domain,
                "task": request.task,
                "input": request.input,
            }
        )

        if request.domain == "medicine":
            payload = _mirror_medicine_status(
                payload, request.task
            )

        return payload
    except HTTPException:
        # Never wrap our own HTTPException in a 500.
        raise
    except httpx.TimeoutException as exc:
        raise HTTPException(
            status_code=504,
            detail={
                "error": "AI Engine timed out.",
                "message": str(exc),
            },
        ) from exc
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "error": "AI Engine returned an error.",
                "message": (
                    f"Upstream status "
                    f"{exc.response.status_code}: "
                    f"{exc.response.text[:500]}"
                ),
            },
        ) from exc
    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "error": "AI Engine unreachable.",
                "message": str(exc),
            },
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail={
                "error": "CureVerseAI analysis failed.",
                "message": str(exc),
            },
        ) from exc
