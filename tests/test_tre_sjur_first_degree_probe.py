from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from tools.probe_tre_sjur_first_degree import MAX_RESPONSE_BYTES

ROOT = Path(__file__).parents[1]
EVIDENCE = ROOT / "docs" / "provider-discovery" / "tre-sjur-type-filter-live-20260912.json"
SECOND_EVIDENCE = (
    ROOT / "docs" / "provider-discovery" / "tre-sjur-second-degree-type-filter-live-20260912.json"
)
MULTI_UF_EVIDENCE = (
    ROOT / "docs" / "provider-discovery" / "tre-sjur-first-degree-multi-uf-live-20260912.json"
)


def test_first_degree_probe_bound_matches_tre_transport() -> None:
    assert MAX_RESPONSE_BYTES == 16_000_000


def test_tre_type_filter_evidence_is_complete_and_sanitized() -> None:
    payload = json.loads(EVIDENCE.read_text(encoding="utf-8"))
    results = payload["results"]

    assert len(results) == 27
    assert payload["response_bodies_persisted"] is False
    assert payload["credentials_used"] is False
    assert payload["bypass_attempted"] is False
    assert payload["safety"]["spacing_seconds"] >= 2
    assert all(
        item["route"].startswith("https://sjur-pesquisa-api.tse.jus.br/tre-") for item in results
    )
    assert Counter(item["classification"] for item in results) == Counter(
        {"success_filtered_window": 1, "authoritative_empty": 26}
    )

    non_empty = [item for item in results if item["classification"] == "success_filtered_window"]
    assert [item["tribunal"] for item in non_empty] == ["TRE-MG"]
    assert non_empty[0]["contains_requested_type"] is True
    assert non_empty[0]["decision_types"] == {"Sentença": 1000}


def test_tre_second_degree_type_filter_evidence_is_complete_and_sanitized() -> None:
    payload = json.loads(SECOND_EVIDENCE.read_text(encoding="utf-8"))
    results = payload["results"]

    assert len(results) == 27
    assert payload["degree_scope"] == "second"
    assert payload["requested_types"] == [
        "Acórdão",
        "Decisão monocrática",
        "Resolução",
        "Decisão sem resolução",
    ]
    assert payload["response_bodies_persisted"] is False
    assert payload["credentials_used"] is False
    assert payload["bypass_attempted"] is False
    assert payload["safety"]["spacing_seconds"] >= 2
    assert all(
        item["route"].startswith("https://sjur-pesquisa-api.tse.jus.br/tre-") for item in results
    )
    assert all(item.get("unexpected_types") == [] for item in results if item.get("decision_types"))
    assert Counter(item["classification"] for item in results) == Counter(
        {"success_filtered_window": 24, "authoritative_empty": 1, "response_too_large": 2}
    )
    non_empty = [item for item in results if item["classification"] == "success_filtered_window"]
    assert all(item["contains_requested_type"] is True for item in non_empty)


def test_first_degree_multi_uf_evidence_respects_bound_and_degree_labels() -> None:
    payload = json.loads(MULTI_UF_EVIDENCE.read_text(encoding="utf-8"))
    results = payload["results"]
    assert len(results) == 27
    assert payload["response_bodies_persisted"] is False
    assert payload["safety"]["max_response_bytes"] == MAX_RESPONSE_BYTES
    assert all(item["bypass_attempted"] is False for item in results)
    assert all(item["classification"] != "response_too_large" for item in results)
    mg = next(item for item in results if item["tribunal"] == "TRE-MG")
    assert mg["classification"] == "success_with_explicit_first_degree_label"
    assert mg["degree_labels"]["first"] > 0
