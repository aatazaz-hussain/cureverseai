"""
CureVerseAI — Medicine domain
Phase 4 backend route test matrix.

Runnable with:

    cd /home/aatazazhussain/projects/cureverseai/backend
    .venv/bin/python -m tests.test_medicine_routes

Uses FastAPI's TestClient against the mounted app, so no
separate server needs to start. Valid-request tests require
the AI Engine to be running on :8001. Validator-only tests
(the 400 cases) do not require the AI Engine.

Coverage:
    01  W01 valid                         -> 200, data.status == success
    02  W01 missing disease               -> 400
    03  W01 disease too long              -> 400
    04  W01 cell_type too long            -> 400
    05  W02 valid                         -> 200
    06  W02 missing intervention_id       -> 400
    07  W02 baseline_id too long          -> 400
    08  W03 valid                         -> 200, interaction_class
    09  W03 missing intervention_b_id     -> 400
    10  W03 duplicate intervention ids    -> 400
    11  W03 intervention_id too long      -> 400
    12  GET /medicine/curated             -> 200, count == 3
    13  GET /domains includes medicine    -> 200
    14  data.status mirrors run.status
    15  Regression: education passthrough
    16  Regression: W02 drug_development validation still enforced

The envelope is asserted here. Scientific correctness is
asserted in ai-engine/tests/test_medicine.py.
"""

from __future__ import annotations

import sys
from typing import Callable, List, Tuple

from fastapi.testclient import TestClient

from app.main import app


CLIENT = TestClient(app)

RESULTS: List[Tuple[str, bool, str]] = []


def _run(name: str, fn: Callable[[], None]) -> None:
    try:
        fn()
        RESULTS.append((name, True, ""))
        print(f"PASS  {name}")
    except AssertionError as exc:
        RESULTS.append((name, False, f"assertion: {exc}"))
        print(f"FAIL  {name}: {exc}")
    except Exception as exc:
        RESULTS.append((name, False, f"exception: {type(exc).__name__}: {exc}"))
        print(f"FAIL  {name}: {type(exc).__name__}: {exc}")


ANALYZE = "/api/v1/analyze"


def _post(body: dict):
    return CLIENT.post(ANALYZE, json=body)


# ---------------------------------------------------------------------------
# W01
# ---------------------------------------------------------------------------


def test_w01_valid() -> None:
    r = _post({
        "domain": "medicine",
        "task": "virtual_disease_simulation",
        "input": {"disease": "asthma"},
    })
    assert r.status_code == 200, r.text[:300]
    body = r.json()
    assert body.get("success") is True
    assert body.get("domain") == "medicine"
    assert isinstance(body.get("data"), dict)
    data = body["data"]
    assert data.get("status") == "success"
    assert isinstance(data.get("result"), dict)
    result = data["result"]
    assert result["run"]["status"] == "success"
    assert len(result["indicators"]) == 4
    assert len(result["states"]) == 2


def test_w01_missing_disease() -> None:
    r = _post({
        "domain": "medicine",
        "task": "virtual_disease_simulation",
        "input": {},
    })
    assert r.status_code == 400
    detail = r.json().get("detail") or {}
    assert "disease" in detail.get("message", "").lower()


def test_w01_disease_too_long() -> None:
    r = _post({
        "domain": "medicine",
        "task": "virtual_disease_simulation",
        "input": {"disease": "a" * 501},
    })
    assert r.status_code == 400


def test_w01_cell_type_too_long() -> None:
    r = _post({
        "domain": "medicine",
        "task": "virtual_disease_simulation",
        "input": {"disease": "asthma", "cell_type": "x" * 201},
    })
    assert r.status_code == 400


# ---------------------------------------------------------------------------
# W02
# ---------------------------------------------------------------------------


def test_w02_valid() -> None:
    r = _post({
        "domain": "medicine",
        "task": "treatment_simulation",
        "input": {
            "disease": "asthma",
            "intervention_id": "chembl:CHEMBL787",
        },
    })
    assert r.status_code == 200, r.text[:300]
    body = r.json()
    assert body.get("domain") == "medicine"
    data = body["data"]
    assert data.get("status") == "success"
    assert len(data["result"]["states"]) == 3


def test_w02_missing_intervention_id() -> None:
    r = _post({
        "domain": "medicine",
        "task": "treatment_simulation",
        "input": {"disease": "asthma"},
    })
    assert r.status_code == 400
    detail = r.json().get("detail") or {}
    assert "intervention_id" in detail.get("message", "")


def test_w02_baseline_id_too_long() -> None:
    r = _post({
        "domain": "medicine",
        "task": "treatment_simulation",
        "input": {
            "disease": "asthma",
            "intervention_id": "chembl:CHEMBL787",
            "baseline_id": "y" * 201,
        },
    })
    assert r.status_code == 400


# ---------------------------------------------------------------------------
# W03
# ---------------------------------------------------------------------------


def test_w03_valid() -> None:
    r = _post({
        "domain": "medicine",
        "task": "combination_treatment_simulation",
        "input": {
            "disease": "asthma",
            "intervention_a_id": "chembl:CHEMBL787",
            "intervention_b_id": "chembl:CHEMBL1200681",
        },
    })
    assert r.status_code == 200, r.text[:300]
    body = r.json()
    data = body["data"]
    assert data.get("status") == "success"
    result = data["result"]
    assert len(result["states"]) == 5
    comparison = result["comparison"]
    assert comparison["interaction_class"] == "insufficient_evidence"
    assert comparison["overall_interpretation"] == "not_modelled"


def test_w03_missing_intervention_b_id() -> None:
    r = _post({
        "domain": "medicine",
        "task": "combination_treatment_simulation",
        "input": {
            "disease": "asthma",
            "intervention_a_id": "chembl:CHEMBL787",
        },
    })
    assert r.status_code == 400
    detail = r.json().get("detail") or {}
    assert "intervention_b_id" in detail.get("message", "")


def test_w03_duplicate_intervention_ids() -> None:
    # Normalization: chembl:CHEMBL787 and CHEMBL787 are the same.
    r = _post({
        "domain": "medicine",
        "task": "combination_treatment_simulation",
        "input": {
            "disease": "asthma",
            "intervention_a_id": "chembl:CHEMBL787",
            "intervention_b_id": "CHEMBL787",
        },
    })
    assert r.status_code == 400
    detail = r.json().get("detail") or {}
    assert "different interventions" in detail.get("message", "")


def test_w03_intervention_id_too_long() -> None:
    r = _post({
        "domain": "medicine",
        "task": "combination_treatment_simulation",
        "input": {
            "disease": "asthma",
            "intervention_a_id": "a" * 301,
            "intervention_b_id": "b",
        },
    })
    assert r.status_code == 400


# ---------------------------------------------------------------------------
# Curated endpoint
# ---------------------------------------------------------------------------


def test_medicine_curated_route() -> None:
    r = CLIENT.get("/api/v1/analyze/medicine/curated")
    assert r.status_code == 200, r.text[:300]
    body = r.json()
    assert body.get("success") is True
    assert body.get("count") == 3
    pairs = body.get("curated") or []
    assert len(pairs) == 3
    for p in pairs:
        assert p.get("disease_id")
        assert p.get("disease_name")
        assert p.get("cell_context_id")
        assert p.get("cell_context_name")


def test_domains_endpoint() -> None:
    r = CLIENT.get("/api/v1/analyze/domains")
    assert r.status_code == 200
    domains = r.json().get("domains") or []
    assert "medicine" in domains
    assert "research" in domains
    assert "education" in domains


# ---------------------------------------------------------------------------
# data.status mirror
# ---------------------------------------------------------------------------


def test_status_mirror_present_for_medicine() -> None:
    r = _post({
        "domain": "medicine",
        "task": "virtual_disease_simulation",
        "input": {"disease": "asthma"},
    })
    assert r.status_code == 200
    data = r.json()["data"]
    # Mirror is present and equals the run's status.
    assert data.get("status") == data["result"]["run"]["status"]


# ---------------------------------------------------------------------------
# Regression
# ---------------------------------------------------------------------------


def test_regression_education_passthrough() -> None:
    # The education domain is not validated by the medicine
    # validators; its request shape is unchanged.
    r = _post({
        "domain": "education",
        "task": "explanation",
        "input": {"topic": "photosynthesis"},
    })
    assert r.status_code == 200, r.text[:300]
    body = r.json()
    assert body.get("domain") == "education"


def test_regression_drug_development_w02_validation() -> None:
    # The existing W02 validator must still fire: missing disease -> 400.
    r = _post({
        "domain": "drug_development",
        "task": "reverse_disease_engineering",
        "input": {},
    })
    assert r.status_code == 400
    detail = r.json().get("detail") or {}
    assert "disease" in detail.get("message", "").lower()


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


TESTS: List[Tuple[str, Callable[[], None]]] = [
    ("01_w01_valid", test_w01_valid),
    ("02_w01_missing_disease", test_w01_missing_disease),
    ("03_w01_disease_too_long", test_w01_disease_too_long),
    ("04_w01_cell_type_too_long", test_w01_cell_type_too_long),
    ("05_w02_valid", test_w02_valid),
    ("06_w02_missing_intervention_id", test_w02_missing_intervention_id),
    ("07_w02_baseline_id_too_long", test_w02_baseline_id_too_long),
    ("08_w03_valid", test_w03_valid),
    ("09_w03_missing_intervention_b_id", test_w03_missing_intervention_b_id),
    ("10_w03_duplicate_intervention_ids", test_w03_duplicate_intervention_ids),
    ("11_w03_intervention_id_too_long", test_w03_intervention_id_too_long),
    ("12_medicine_curated_route", test_medicine_curated_route),
    ("13_domains_endpoint", test_domains_endpoint),
    ("14_status_mirror_present_for_medicine", test_status_mirror_present_for_medicine),
    ("15_regression_education_passthrough", test_regression_education_passthrough),
    ("16_regression_drug_development_w02_validation", test_regression_drug_development_w02_validation),
]


def main() -> int:
    print("=== Medicine Phase 4 backend test matrix ===")
    print()
    for name, fn in TESTS:
        _run(name, fn)
    print()
    passed = sum(1 for _, ok, _ in RESULTS if ok)
    failed = len(RESULTS) - passed
    print(f"{passed}/{len(RESULTS)} passed, {failed} failed")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
