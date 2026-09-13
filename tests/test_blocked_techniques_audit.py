"""Regression tests for bounded, non-bypass blocked-source rechecks."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).parents[1]


def _load(name: str) -> dict:
    return json.loads((ROOT / "docs" / "provider-discovery" / name).read_text(encoding="utf-8"))


def test_template_audit_does_not_authorize_bypass_components() -> None:
    audit = _load("lib-template-technique-audit-20260907.json")
    forbidden = {
        "CAPTCHA or Turnstile solving",
        "fingerprint or canvas spoofing",
        "proxy rotation",
        "cookie or session replay",
        "TLS verification disabling",
        "rate-limit or WAF evasion",
        "challenge token generation or reuse",
    }
    assert forbidden.issubset(set(audit["explicitly_not_applied"]))
    restricted = (
        item for item in audit["components"] if "stealth" in item["path"] or "proxy" in item["path"]
    )
    assert all(item["classification"] != "usable" for item in restricted)


def test_blocked_recheck_preserves_external_access_states() -> None:
    recheck = _load("legitimate-blocked-techniques-20260907.json")
    results = {item["provider"]: item["result"] for item in recheck["results"]}
    assert results["tjap_tucujuris"] == "blocked"
    assert results["tjma_jurisconsult"] == "blocked"
    assert results["trf3_jurisprudencia"] == "blocked_transport"
    assert results["tjmg_jurisprudencia"] == "unblocked_by_official_alternative"
    assert results["tjsc_eproc_jurisprudencia"] == "temporary_portal_block"
    assert recheck["safety"] == {
        "captcha_solved": False,
        "tokens_reused": False,
        "cookies_replayed": False,
        "tls_verification_disabled": False,
        "proxy_rotation": False,
        "rate_limit_bypass": False,
    }


def test_tjsc_eproc_does_not_claim_first_degree_from_route_name() -> None:
    evidence = _load("tjsc-first-degree-eproc-boundary-live-20260907.json")
    first = evidence["queries"][0]
    second = evidence["queries"][1]
    assert first["classification"] == "contract_rejected"
    assert second["identity"]["degree"] == "second"
    assert evidence["detail_probe"]["classification"] == "access_controlled"


def test_first_degree_route_inventory_is_discovery_only() -> None:
    inventory = _load("first-degree-route-inventory-20260907.json")
    assert len(inventory["results"]) == 27
    assert all(item["promotion_decision"] == "discovery_only" for item in inventory["results"])


def test_tjma_catalog_separates_degrees_without_promoting_gated_results() -> None:
    inventory = _load("tjma-public-route-inventory-live-20260907.json")
    catalog = next(
        item for item in inventory["routes"] if item["path"].endswith("lista_relatorios")
    )
    surfaces = {item["surface"] for item in catalog["items"]}
    assert {"CJSG", "CJPG"}.issubset(surfaces)
    gated = [item for item in inventory["routes"] if item["classification"] == "captcha_required"]
    assert gated
    assert all(item["status"] == 400 for item in gated)
    assert "retrievable records" in inventory["decision"]


def test_tjsc_first_degree_route_preserves_temporary_portal_block() -> None:
    evidence = _load("tjsc-cjpg-route-live-20260907.json")
    assert evidence["classification"] == "temporary_portal_block"
    assert evidence["status"] == 200
    assert evidence["observed"]["query_form_present"] is False
    assert evidence["observed"]["first_degree_contract_proven"] is False
    assert evidence["safety"]["captcha_solved"] is False


def test_tjsc_eprocwebcon_candidate_route_remains_blocked() -> None:
    evidence = _load("tjsc-cjpg-eprocwebcon-recheck-20260907.json")
    assert evidence["http_status"] == 298
    assert evidence["classification"] == "temporary_portal_block"
    assert evidence["observed"]["first_degree_contract_proven"] is False
    assert evidence["bypass_attempted"] is False


def test_tjto_get_fallback_keeps_intermitent_waf_explicit() -> None:
    evidence = _load("tjto-get-route-live-20260907.json")
    assert any(item["classification"] == "public_html_reachable" for item in evidence["methods"])
    assert any(item["classification"] == "access_controlled_waf" for item in evidence["methods"])
    assert evidence["safety"]["tokens_reused"] is False
    assert "do not promote" in evidence["decision"]


def test_tjdf_public_api_recheck_is_reproducible_without_bypass() -> None:
    evidence = _load("tjdf-api-live-recheck-20260907.json")
    assert evidence["credentials_used"] is False
    assert evidence["bypass_attempted"] is False
    assert evidence["endpoint"].endswith("/api/v1/pesquisa")
    assert evidence["requests"][0]["http_status"] == 200
    assert evidence["requests"][1]["pagina"] == 1
    assert evidence["requests"][2]["total"] == 0
    assert "second_degree_markers" in evidence["contract_observations"]


def test_third_party_indexes_remain_research_only() -> None:
    evidence = _load("third-party-index-alternative-audit-20260907.json")
    assert evidence["credentials_used"] is False
    assert evidence["bypass_attempted"] is False
    assert all(
        item["classification"] == "third_party_index_research_only"
        for item in evidence["candidates"]
    )
    assert "Do not use third-party indexes" in evidence["decision"]


def test_falcao_and_trt2_recheck_keeps_candidates_out_of_runtime() -> None:
    evidence = _load("falcao-trt2-live-recheck-20260907.json")
    assert evidence["credentials_used"] is False
    assert evidence["bypass_attempted"] is False
    falcao_requests = [item for item in evidence["requests"] if item["provider"] == "falcao_jt"]
    assert any(item["classification"] == "official_landing_page" for item in falcao_requests)
    assert any(
        item["classification"] == "public_shell_only_intermittent" for item in falcao_requests
    )
    assert any(item["http_status"] == 403 for item in falcao_requests)
    assert all(
        item.get("observed", {}).get("result_contract_present") is not True
        for item in falcao_requests
    )
    options = next(
        item
        for item in evidence["requests"]
        if item["provider"] == "trt2_pje_jurisprudencia"
        and item["classification"] == "public_options_with_captcha"
    )
    assert options["observed"]["result_contract_present"] is False


def test_official_alternative_surface_recheck_does_not_overclaim_jurisprudence() -> None:
    evidence = _load("official-alternative-surface-recheck-20260907.json")
    assert evidence["credentials_used"] is False
    assert evidence["bypass_attempted"] is False
    checks = {(item["authority"], item["classification"]): item for item in evidence["checks"]}
    assert ("TJAP", "access_controlled_method_not_supported") in checks
    assert ("TJAP", "production_process_consultation_only") in checks
    assert ("TJAP", "process_consultation_only") in checks
    assert ("TJAP", "specialized_summaries_only") in checks
    assert ("TJMA", "official_application_bundle") in checks
    assert ("TJMA", "portal_link_to_challenge_gated_app") in checks
    assert checks[("TJAP", "process_consultation_only")]["observed"]["jurisprudence_markers"] == 0
    assert "no blocked source" in evidence["conclusion"]


def test_state_eproc_first_degree_recheck_does_not_count_host_name_as_cjpg() -> None:
    evidence = _load("state-first-degree-eproc-recheck-20260907.json")

    assert evidence["credentials_used"] is False
    assert evidence["bypass_attempted"] is False
    results = {entry["authority"]: entry for entry in evidence["results"]}
    assert set(results) == {"TJRJ", "TJSC"}
    for entry in results.values():
        assert entry["second_degree"]["classification"] == "valid_second_degree"
        assert entry["first_degree"]["classification"] == (
            "contract_rejected_source_returned_second_degree"
        )
        assert "Do not promote" in entry["first_degree"]["decision"]
    assert "explicit CJPG gaps" in evidence["conclusion"]


def test_state_eproc_current_boundary_preserves_contract_error() -> None:
    evidence = _load("state-eproc-first-degree-boundary-live-20260908.json")

    assert evidence["credentials_used"] is False
    assert evidence["bypass_used"] is False
    assert evidence["raw_content_persisted"] is False
    assert evidence["query"]["degree"] == "first"
    assert evidence["query"]["instance"] == "first"
    assert {item["authority"] for item in evidence["results"]} == {"TJRJ", "TJSC"}
    for item in evidence["results"]:
        assert item["classification"] == "mixed_degree_rejected"
        assert item["error_type"] == "ParserContractChangedError"
        assert item["converted_to_empty"] is False
    assert evidence["route_assessment"]["distinct_first_degree_origin_for_tjrj_or_tjsc"] is False


def test_tjdft_public_api_recheck_proves_second_degree_text_and_full_text() -> None:
    evidence = _load("tjdf-jurisdf-api-live-20260907.json")
    assert evidence["credentials_used"] is False
    assert evidence["bypass_attempted"] is False
    assert evidence["response"]["http_status"] == 200
    assert evidence["response"]["records"] > 0
    assert evidence["response"]["first_record"]["full_text_present"] is True
    assert evidence["classification"]["degree"] == "second"
    assert evidence["classification"]["collection"] == "CJSG"


def test_tjrs_public_tiff_route_is_available_without_bypass() -> None:
    evidence = _load("tjrs-solr-fulltext-live-20260907.json")
    assert evidence["credentials_used"] is False
    assert evidence["bypass_attempted"] is False
    assert evidence["response"]["http_status"] == 200
    assert evidence["response"]["decoded_content_type"] == "image/tiff"
    assert evidence["classification"]["document_status"] == "available"
    assert evidence["classification"]["extraction_status"] == "unsupported_format_without_ocr"
