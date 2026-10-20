"""
CureVerseAI — Drug Development
Workflow 02 — Reverse Disease Engineering
End-to-end test script.

Run with:

    /home/aatazazhussain/projects/cureverseai/ai-engine/.venv/bin/python \
        /home/aatazazhussain/projects/cureverseai/ai-engine/tests/test_reverse_disease.py

No pytest dependency. Plain assertion-style tests, matching
the W01 smoke_test.py convention.

Three test groups:

    1. Pure unit tests — no network
    2. Synthetic integration tests — no network
    3. Live smoke tests — real sources (tagged SLOW)

Live tests skip cleanly on RuntimeError (source unavailable)
rather than failing. All others must pass.

Exit code 0 on all-pass, 1 on any failure.
"""

import sys
import time
import traceback
from pathlib import Path

AI_ENGINE_ROOT = Path("/home/aatazazhussain/projects/cureverseai/ai-engine")
sys.path.insert(0, str(AI_ENGINE_ROOT))


# ---------------------------------------------------------------------------
# Minimal harness
# ---------------------------------------------------------------------------


_RESULTS = []


def _run(label, fn, skip_on_runtime_error=False):
    t0 = time.time()
    try:
        fn()
        elapsed = time.time() - t0
        _RESULTS.append((label, "PASS", None, elapsed))
        print(f"[PASS] {label}  ({elapsed:.2f}s)")
    except RuntimeError as exc:
        elapsed = time.time() - t0
        if skip_on_runtime_error:
            _RESULTS.append((label, "SKIP", str(exc), elapsed))
            print(f"[SKIP] {label}  ({elapsed:.2f}s)")
            print(f"       reason: {str(exc)[:200]}")
        else:
            _RESULTS.append((label, "FAIL", str(exc), elapsed))
            print(f"[FAIL] {label}  ({elapsed:.2f}s)")
            print(f"       {type(exc).__name__}: {str(exc)[:300]}")
            traceback.print_exc()
    except Exception as exc:
        elapsed = time.time() - t0
        _RESULTS.append((label, "FAIL", str(exc), elapsed))
        print(f"[FAIL] {label}  ({elapsed:.2f}s)")
        print(f"       {type(exc).__name__}: {str(exc)[:300]}")
        traceback.print_exc()


def _assert(cond, msg):
    if not cond:
        raise AssertionError(msg)


# ---------------------------------------------------------------------------
# 1. Pure unit tests
# ---------------------------------------------------------------------------


def test_schemas_default():
    from app.drug_development.reverse_disease.schemas import (
        ProvenanceRecord,
        Explanation,
        ReverseDiseaseResult,
    )

    p = ProvenanceRecord()
    _assert(p.sources_queried == [], "ProvenanceRecord.sources_queried")
    _assert(p.source_failures == [], "ProvenanceRecord.source_failures")
    _assert(p.records_retrieved == 0, "ProvenanceRecord.records_retrieved")
    _assert(p.metadata == {}, "ProvenanceRecord.metadata")

    r = ReverseDiseaseResult(query="x")
    _assert(r.resolution_status == "unresolved", "default status")
    _assert(r.failure_reason is None, "default failure_reason")
    _assert(r.explanations == [], "default explanations")
    _assert(r.uncertainties == [], "default uncertainties")

    e = Explanation(
        explanation_id="exp:1",
        target_kind="node",
        target_id="disease:X",
        text="ok",
    )
    _assert(e.support_class is None, "default support_class")
    _assert(e.evidence_ids == [], "default evidence_ids")


def test_opentargets_id_form():
    from app.drug_development.reverse_disease.utils import (
        to_opentargets_id,
        to_colon_form,
    )

    _assert(
        to_opentargets_id("MONDO:0004979") == "MONDO_0004979",
        "colon->underscore",
    )
    _assert(
        to_opentargets_id("MONDO_0004979") == "MONDO_0004979",
        "underscore->underscore",
    )
    _assert(to_opentargets_id("") == "", "empty")

    _assert(
        to_colon_form("MONDO_0004979") == "MONDO:0004979",
        "underscore->colon",
    )
    _assert(
        to_colon_form("MONDO:0004979") == "MONDO:0004979",
        "colon->colon",
    )
    _assert(to_colon_form("") == "", "empty")


def test_normalize_hp_id():
    from app.drug_development.reverse_disease.sources.hpo import (
        normalize_hp_id,
    )

    _assert(
        normalize_hp_id("HP_0002099") == "HP:0002099",
        "HP underscore -> colon",
    )
    _assert(
        normalize_hp_id("HP:0002099") == "HP:0002099",
        "HP colon preserved",
    )
    _assert(normalize_hp_id("") == "", "empty")


def test_graph_builder_disease_node():
    from app.drug_development.reverse_disease.causal_graph_builder import (
        CausalGraphBuilder,
    )
    from app.drug_development.schemas.disease import (
        DiseaseIdentity,
        DiseaseIdentifier,
    )

    d = DiseaseIdentity(
        query="asthma",
        canonical_name="asthma",
        identifiers=[
            DiseaseIdentifier(
                source="Open Targets",
                identifier="MONDO:0004979",
            )
        ],
        resolution_status="resolved",
    )

    node = CausalGraphBuilder._build_disease_node(d)
    _assert(node is not None, "disease node created")
    _assert(
        node.node_id == "disease:MONDO_0004979",
        "disease node id",
    )
    _assert(node.node_type == "disease", "node_type disease")
    _assert(node.identifier == "MONDO:0004979", "identifier colon form")


def test_graph_builder_dict_conversions():
    from app.drug_development.reverse_disease.causal_graph_builder import (
        CausalGraphBuilder,
    )

    raw_node = {
        "node_id": "gene:FLG",
        "node_type": "gene",
        "name": "FLG",
        "identifier": "ENSG00000143631",
        "description": "filaggrin",
        "evidence_ids": [],
        "metadata": {"source": "Open Targets"},
    }
    node = CausalGraphBuilder._dict_to_node(raw_node)
    _assert(node is not None, "node conversion")
    _assert(node.node_id == "gene:FLG", "node_id preserved")

    raw_rel = {
        "source_id": "disease:MONDO_0004979",
        "target_id": "gene:FLG",
        "relationship_type": "associated_with",
        "evidence_ids": ["ev:ot:gene:FLG"],
        "evidence_level": "association",
        "support_class": "supported_association",
        "description": "x",
        "metadata": {},
    }
    rel = CausalGraphBuilder._dict_to_relationship(raw_rel)
    _assert(rel is not None, "relationship conversion")
    _assert(
        rel.support_class == "supported_association",
        "support_class preserved",
    )

    raw_ev = {
        "evidence_id": "ev:ot:gene:FLG",
        "source": "Open Targets",
        "relationship_description": "x",
        "evidence_level": "association",
        "reference": {
            "source": "Open Targets",
            "source_id": "MONDO_0004979",
            "source_type": "database",
            "url": None,
            "metadata": {},
        },
        "identifiers": {},
        "metadata": {},
    }
    ev = CausalGraphBuilder._dict_to_evidence(raw_ev)
    _assert(ev is not None, "evidence conversion")
    _assert(ev.reference is not None, "reference rebuilt")


def test_ranker_synthetic():
    from app.drug_development.reverse_disease.mechanism_ranker import (
        MechanismRanker,
    )

    nodes = [
        {
            "node_id": "mechanism:evidence:literature",
            "node_type": "mechanism",
            "name": "Literature",
            "metadata": {
                "targets_supporting": 20,
                "mean_score": 0.60,
                "datatype_id": "literature",
            },
        },
        {
            "node_id": "mechanism:evidence:clinical",
            "node_type": "mechanism",
            "name": "Clinical",
            "metadata": {
                "targets_supporting": 5,
                "mean_score": 0.90,
                "datatype_id": "clinical",
            },
        },
        {
            "node_id": "pathway:R-HSA-1",
            "node_type": "pathway",
            "name": "P1",
            "identifier": "R-HSA-1",
            "metadata": {},
        },
        {
            "node_id": "pathway:R-HSA-2",
            "node_type": "pathway",
            "name": "P2",
            "identifier": "R-HSA-2",
            "metadata": {},
        },
    ]
    edges = [
        {
            "source_id": "disease:X",
            "target_id": "pathway:R-HSA-1",
            "relationship_type": "associated_with",
            "metadata": {"supporting_genes": ["A", "B", "C"]},
        },
    ]

    merged = {"graph": {"nodes": nodes, "edges": edges}}
    ranks = MechanismRanker().rank(merged)

    cats = ranks["ranked_mechanism_categories"]
    _assert(len(cats) == 2, "two categories ranked")
    _assert(cats[0]["rank"] == 1, "first rank")
    _assert(
        cats[0]["datatype_id"] == "literature",
        "literature first by count",
    )

    pws = ranks["ranked_pathways"]
    _assert(len(pws) == 2, "two pathways ranked")
    # R-HSA-1 has 3 supporting genes -> rank 1
    _assert(pws[0]["rank"] == 1, "pathway rank 1")
    _assert(
        pws[0]["supporting_gene_count"] == 3,
        "pathway 1 gene count",
    )


def test_explanation_builder_synthetic():
    from app.drug_development.reverse_disease.explanation_builder import (
        ExplanationBuilder,
    )

    nodes = [
        {
            "node_id": "disease:X",
            "node_type": "disease",
            "name": "Test",
            "identifier": "X",
            "description": "A test disease.",
            "evidence_ids": [],
            "metadata": {},
        },
        {
            "node_id": "phenotype:HP_1",
            "node_type": "phenotype",
            "name": "Feature 1",
            "identifier": "HP:1",
            "description": "Test feature.",
            "evidence_ids": [],
            "metadata": {},
        },
    ]
    edges = []

    merged = {"graph": {"nodes": nodes, "edges": edges}}
    segs = ExplanationBuilder().build(merged)

    _assert(len(segs) == 2, f"expected 2 segments, got {len(segs)}")
    for s in segs:
        _assert(s["target_kind"] in ("node", "edge"), "kind")
        _assert(s["explanation_id"].startswith("exp:"), "id prefix")
        _assert(isinstance(s["text"], str), "text is str")
        _assert(len(s["text"]) > 10, "text non-empty")


def test_service_unresolved():
    from app.drug_development.reverse_disease.service import (
        ReverseDiseaseService,
    )

    svc = ReverseDiseaseService(fetch_chembl=False)
    result = svc.run("")

    _assert(result["resolution_status"] == "unresolved", "status")
    _assert(result["graph"]["nodes"] == [], "empty nodes")
    _assert(result["graph"]["edges"] == [], "empty edges")
    _assert(result["failure_reason"] is not None, "reason present")
    _assert(
        "provenance" in result,
        "provenance block present",
    )


# ---------------------------------------------------------------------------
# 2. Synthetic integration tests
# ---------------------------------------------------------------------------


def test_synthetic_full_graph_build():
    """
    Build a full graph from hand-crafted layer dicts. This
    exercises CausalGraphBuilder + EvidenceIntegrator with
    no network access at all.
    """
    from app.drug_development.reverse_disease.causal_graph_builder import (
        CausalGraphBuilder,
    )
    from app.drug_development.reverse_disease.evidence_integrator import (
        EvidenceIntegrator,
    )
    from app.drug_development.schemas.disease import (
        DiseaseIdentity,
        DiseaseIdentifier,
    )

    disease = DiseaseIdentity(
        query="example",
        canonical_name="example disease",
        identifiers=[
            DiseaseIdentifier(
                source="Open Targets",
                identifier="MONDO:0000001",
            )
        ],
        resolution_status="resolved",
    )

    # Minimal but well-formed layer output
    phenotype_layer = {
        "disease_node_id": "disease:MONDO_0000001",
        "nodes": [
            {
                "node_id": "phenotype:HP_0000001",
                "node_type": "phenotype",
                "name": "Feature",
                "identifier": "HP:0000001",
                "description": "Test.",
                "evidence_ids": [],
                "metadata": {},
            }
        ],
        "relationships": [
            {
                "source_id": "disease:MONDO_0000001",
                "target_id": "phenotype:HP_0000001",
                "relationship_type": "associated_with",
                "evidence_ids": ["ev:ot:phenotype:HP_0000001"],
                "evidence_level": "association",
                "support_class": "supported_association",
                "description": "x",
                "metadata": {},
            }
        ],
        "evidence": [
            {
                "evidence_id": "ev:ot:phenotype:HP_0000001",
                "source": "Open Targets",
                "relationship_description": "x",
                "evidence_level": "association",
                "reference": None,
                "identifiers": {},
                "metadata": {},
            }
        ],
        "sources": ["Open Targets"],
        "found": True,
        "metadata": {},
        "reason": None,
    }

    empty_layer = {
        "disease_node_id": "disease:MONDO_0000001",
        "nodes": [],
        "relationships": [],
        "evidence": [],
        "sources": [],
        "found": False,
        "metadata": {},
        "reason": "no data",
    }

    layers = {
        "phenotypes": phenotype_layer,
        "mechanisms": empty_layer,
        "genes": empty_layer,
        "pathways": empty_layer,
    }

    merged = CausalGraphBuilder().build(disease, layers)
    _assert(merged["integrity"]["ok"], "integrity ok")
    _assert(
        len(merged["graph"]["nodes"]) == 2,
        f"expected 2 nodes, got {len(merged['graph']['nodes'])}",
    )
    _assert(
        len(merged["graph"]["edges"]) == 1,
        "one edge",
    )

    payload = EvidenceIntegrator().integrate(
        disease=disease,
        merged_graph=merged,
        layers=layers,
    )
    _assert("summary" in payload, "summary present")
    _assert("limitations" in payload, "limitations present")
    _assert(
        len(payload["limitations"]) >= 6,
        "at least 6 fixed limitations",
    )


# ---------------------------------------------------------------------------
# 3. Live smoke tests
# ---------------------------------------------------------------------------


def test_live_asthma():
    from app.drug_development.reverse_disease.service import (
        run_reverse_disease,
    )

    result = run_reverse_disease("asthma", fetch_chembl=False)

    _assert(
        result["resolution_status"] == "resolved",
        f"status: {result['resolution_status']}",
    )
    _assert(result["failure_reason"] is None, "no failure")

    _assert(
        len(result["graph"]["nodes"]) >= 50,
        f"expected >=50 nodes, got {len(result['graph']['nodes'])}",
    )
    _assert(
        len(result["graph"]["edges"]) >= 80,
        f"expected >=80 edges, got {len(result['graph']['edges'])}",
    )
    _assert(
        len(result["evidence"]) >= 80,
        f"expected >=80 evidence records, got {len(result['evidence'])}",
    )

    _assert(
        result["integrity"]["ok"] is True,
        f"integrity failed: {result['integrity']}",
    )

    mi = result["mechanistic_investigation"]
    _assert(len(mi["phenotypes"]) > 0, "phenotypes present")
    _assert(len(mi["mechanisms"]) > 0, "mechanisms present")
    _assert(len(mi["genes"]) > 0, "genes present")
    _assert(len(mi["pathways"]) > 0, "pathways present")
    _assert(mi["variants"] == [], "variants empty in Phase 1")
    _assert(
        mi["manifestations"] == [],
        "manifestations empty in Phase 1",
    )

    sources = result["provenance"]["sources_queried"]
    _assert("Open Targets" in sources, "OT in sources")
    _assert("Reactome" in sources, "Reactome in sources")

    types = [u["type"] for u in result["uncertainties"]]
    _assert(
        "missing_variant_layer" in types,
        "variant uncertainty present",
    )
    _assert(
        "missing_manifestations_layer" in types,
        "manifestation uncertainty present",
    )

    # All edges carry support_class
    for edge in result["graph"]["edges"]:
        _assert(
            edge.get("support_class") is not None,
            f"edge missing support_class: {edge.get('relationship_type')}",
        )

    # All explanations reference real targets
    for exp in result["explanations"]:
        _assert(
            exp["target_kind"] in ("node", "edge"),
            "explanation kind",
        )
        _assert(exp["target_id"], "explanation target_id")


def test_live_blank_query():
    from app.drug_development.reverse_disease.service import (
        run_reverse_disease,
    )

    result = run_reverse_disease("")
    _assert(
        result["resolution_status"] == "unresolved",
        "blank -> unresolved",
    )
    _assert(result["graph"]["nodes"] == [], "empty graph")


def test_live_ambiguous():
    from app.drug_development.reverse_disease.service import (
        run_reverse_disease,
    )

    result = run_reverse_disease("ca", fetch_chembl=False)
    _assert(
        result["resolution_status"] == "partial",
        f"status: {result['resolution_status']}",
    )
    _assert(result["graph"]["nodes"] == [], "no auto-selected graph")
    _assert(
        len(result["disease"].get("candidates", [])) > 0,
        "candidates preserved",
    )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------


def main():
    print("=" * 78)
    print("CureVerseAI — W02 Reverse Disease Engineering — Test Suite")
    print("=" * 78)
    print()

    print("--- 1. Unit tests (no network) ---")
    _run("test_schemas_default", test_schemas_default)
    _run("test_opentargets_id_form", test_opentargets_id_form)
    _run("test_normalize_hp_id", test_normalize_hp_id)
    _run("test_graph_builder_disease_node", test_graph_builder_disease_node)
    _run(
        "test_graph_builder_dict_conversions",
        test_graph_builder_dict_conversions,
    )
    _run("test_ranker_synthetic", test_ranker_synthetic)
    _run(
        "test_explanation_builder_synthetic",
        test_explanation_builder_synthetic,
    )
    _run("test_service_unresolved", test_service_unresolved)

    print()
    print("--- 2. Synthetic integration tests (no network) ---")
    _run(
        "test_synthetic_full_graph_build",
        test_synthetic_full_graph_build,
    )

    print()
    print("--- 3. Live smoke tests (real sources, SLOW) ---")
    _run(
        "test_live_blank_query",
        test_live_blank_query,
    )
    _run(
        "test_live_asthma",
        test_live_asthma,
        skip_on_runtime_error=True,
    )
    _run(
        "test_live_ambiguous",
        test_live_ambiguous,
        skip_on_runtime_error=True,
    )

    print()
    print("=" * 78)

    passed = sum(1 for _, s, _, _ in _RESULTS if s == "PASS")
    skipped = sum(1 for _, s, _, _ in _RESULTS if s == "SKIP")
    failed = sum(1 for _, s, _, _ in _RESULTS if s == "FAIL")
    total = len(_RESULTS)
    elapsed = sum(e for _, _, _, e in _RESULTS)

    print(f"Results: {passed} passed, {skipped} skipped, {failed} failed, "
          f"{total} total  ({elapsed:.1f}s)")

    if failed:
        print()
        print("Failures:")
        for label, status, reason, _ in _RESULTS:
            if status == "FAIL":
                print(f"  - {label}: {reason}")
        print("=" * 78)
        sys.exit(1)

    print("=" * 78)
    sys.exit(0)


if __name__ == "__main__":
    main()
