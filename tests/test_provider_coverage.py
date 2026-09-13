from __future__ import annotations

import json
from pathlib import Path

from nanojuris.catalog import get_provider_catalog_entry, load_provider_catalog
from nanojuris.client import NanoJurisClient
from tools import build_provider_coverage as coverage_builder
from tools.build_provider_coverage import build_catalog, render_docs

ROOT = Path(__file__).resolve().parents[1]


def test_provider_coverage_catalog_is_current() -> None:
    catalog_path = ROOT / "docs" / "registry" / "provider-catalog.full.json"
    expected = build_catalog()
    actual = json.loads(catalog_path.read_text(encoding="utf-8"))

    assert actual == expected


def test_snapshot_date_advances_to_newer_checked_in_evidence(monkeypatch, tmp_path) -> None:
    stale_catalog = tmp_path / "provider-catalog.json"
    stale_catalog.write_text(json.dumps({"generated_at": "2026-08-15"}), encoding="utf-8")
    evidence = tmp_path / "live.json"
    evidence.write_text(json.dumps({"observed_at": "2026-09-02T03:35:54Z"}), encoding="utf-8")

    monkeypatch.setattr(coverage_builder, "CATALOG_PATH", stale_catalog)
    monkeypatch.setattr(coverage_builder, "DEDICATED_LIVE_PATHS", (evidence,))
    monkeypatch.setattr(coverage_builder, "VALIDATION_RUNS_DIR", tmp_path / "runs")

    assert coverage_builder._snapshot_date() == "2026-09-02"


def test_packaged_catalog_matches_documentation_catalog() -> None:
    documentation_catalog = json.loads(
        (ROOT / "docs" / "registry" / "provider-catalog.full.json").read_text(encoding="utf-8")
    )

    assert load_provider_catalog() == documentation_catalog
    assert get_provider_catalog_entry("tjdf_juris")["source_id"] == "tjdf_juris"


def test_provider_coverage_docs_are_current() -> None:
    catalog = build_catalog()

    for path, expected in render_docs(catalog).items():
        assert path.is_file(), str(path)
        assert path.read_text(encoding="utf-8") == expected, str(path)


def test_provider_coverage_catalog_matches_runtime_sources() -> None:
    catalog = build_catalog()
    entries = {entry["source_id"]: entry for entry in catalog["entries"]}
    runtime_sources = {item.source for item in NanoJurisClient().list_sources()}
    implemented = {
        source_id for source_id, entry in entries.items() if entry["lifecycle"] == "implemented"
    }

    assert implemented == runtime_sources

    for source_id in runtime_sources:
        entry = entries[source_id]
        assert entry["documentation"]["human_doc"] == f"docs/providers/{source_id}/README.md"
        assert (
            entry["input_contract"]["search_modes"]
            == (entry["source_contract"]["evidence"]["search_modes"])
        )
        assert (
            entry["output_contract"]["canonical_records"]
            == (entry["source_contract"]["evidence"]["canonical_records"])
        )


def test_catalog_entries_have_named_provider_modules() -> None:
    catalog = build_catalog()
    module_names = {
        path.stem
        for path in (ROOT / "src" / "nanojuris" / "providers").glob("*.py")
        if path.stem not in {"__init__", "base"}
    }

    assert {
        entry["source_id"] for entry in catalog["entries"] if entry["source_id"] not in module_names
    } == set()


def test_candidates_with_adapters_are_explicit_opt_in_bindings() -> None:
    entries = {entry["source_id"]: entry for entry in build_catalog()["entries"]}
    expected = {
        "falcao_jt",
        "tjap_tucujuris",
        "tjse_jurisprudencia",
        "trt2_pje_jurisprudencia",
        "tjmsp_jurisprudencia",
    }
    assert {
        source_id
        for source_id, entry in entries.items()
        if entry["runtime_binding_status"] == "available_opt_in"
    } == expected
    assert all(entries[source_id]["lifecycle"] == "candidate" for source_id in expected)
    assert all(
        entries[source_id]["interfaces"]["unified_search"] is False for source_id in expected
    )
    blocked_candidates = expected
    assert all(
        "aguardar rota publica/alternativa oficial" in entries[source_id]["next_action"]
        for source_id in blocked_candidates
    )


def test_trt6_legacy_surface_is_promoted_from_live_evidence() -> None:
    entry = next(
        item for item in build_catalog()["entries"] if item["source_id"] == "trt6_jurisprudencia"
    )
    assert entry["lifecycle"] == "implemented"
    assert entry["live_status"] == "valid"
    assert entry["live_validation"]["evidence"] == (
        "docs/provider-discovery/trt6-legacy-search-live-20260912.json"
    )
    assert entry["live_validation"]["access_status"] == "public"
    assert entry["interfaces"]["unified_search"] is True


def test_tjsc_eproc_recheck_keeps_prior_valid_health() -> None:
    entry = next(
        item
        for item in build_catalog()["entries"]
        if item["source_id"] == "tjsc_eproc_jurisprudencia"
    )
    assert entry["live_status"] == "valid"
    assert entry["live_validation"]["date"] == "2026-09-08"
    assert entry["live_validation"]["last_recheck"]["status"] == "source_unavailable"
    assert entry["live_validation"]["last_recheck"]["date"] == "2026-09-13"


def test_tre_first_degree_probe_is_reconciled_as_runtime_opt_in() -> None:
    entries = {entry["source_id"]: entry for entry in build_catalog()["entries"]}
    entry = entries["tre_sjur_first_degree"]

    assert entry["live_status"] == "valid"
    assert entry["live_validation"]["scope"] == "SJUR/TRE/first/decision_type_filter"
    assert entry["live_validation"]["returned"] > 0
    assert entry["lifecycle"] == "implemented"
    assert entry["runtime_binding_status"] == "available_default"
    assert entry["interfaces"]["unified_search"] is False
    assert entry["live_validation"]["date_partition_status"] == "valid"
    assert entry["live_validation"]["date_partition_total"] == 3
    assert entry["live_validation"]["date_partition_uf_sweep_status"] == ("valid_empty_window")
    assert entry["live_validation"]["date_partition_uf_sweep_checked"] == 27


def test_tre_second_degree_identity_is_not_left_unknown() -> None:
    entries = {entry["source_id"]: entry for entry in build_catalog()["entries"]}
    entry = entries["tre_sjur_jurisprudencia"]

    assert entry["surface_identity"] == {
        "authority": "TRE",
        "branch": "electoral",
        "degree": "second",
        "instance": "second",
        "collection": "SJUR",
        "document_scope": "electoral_jurisprudence",
    }
    assert entry["live_status"] == "partial"
    assert entry["live_validation"]["evidence"] == (
        "docs/provider-discovery/tre-sjur-pagination-recheck-live-20260913.json"
    )
    # The official endpoint's reported total is a live value and may change
    # between bounded probes; retain the invariant that a non-zero window was
    # observed while the remote page contract remains unresolved.
    assert entry["live_validation"]["reported_total"] > 0
    assert entry["live_validation"]["total_known"] is False
    assert entry["live_validation"]["full_text_status"] == "valid"
    assert entry["live_validation"]["document_evidence"] == (
        "docs/provider-discovery/tre-sp-sjur-document-live-20260912.json"
    )
    assert entry["live_validation"]["document_bytes"] == 161960
    assert entry["live_validation"]["date_partition_status"] == "valid"
    assert entry["live_validation"]["date_partition_total"] == 203
    assert entry["live_validation"]["uf_sweep_status"] == "valid"
    assert entry["live_validation"]["uf_sweep_checked"] == 27
    assert entry["live_validation"]["uf_sweep_complete"] == 27
    assert entry["live_validation"]["uf_sweep_evidence"] == (
        "docs/provider-discovery/tre-sjur-date-partition-uf-sweep-live-20260913.json"
    )
    assert entry["interfaces"]["unified_search"] is False


def test_tre_second_degree_separates_live_availability_from_completeness() -> None:
    entries = {entry["source_id"]: entry for entry in build_catalog()["entries"]}
    dimensions = entries["tre_sjur_jurisprudencia"]["live_dimensions"]

    # The bounded 27-UF sweep is publicly reachable and parsed, but the
    # general remote page contract is still unresolved.  Both facts must be
    # visible without promoting the source to default federation.
    assert dimensions["availability"] == "valid_partial"
    assert dimensions["completeness"] == "bounded_partition"
    assert dimensions["pagination"] == "unverified"
    assert dimensions["legacy_live_status"] == "partial"


def test_tre_family_runtime_instances_are_explicitly_reconciled() -> None:
    entries = {entry["source_id"]: entry for entry in build_catalog()["entries"]}
    for source_id, suffix in (
        ("tre_sjur_jurisprudencia", "jurisprudencia"),
        ("tre_sjur_first_degree", "first_degree"),
    ):
        expansion = entries[source_id]["runtime_expansion"]
        assert expansion["kind"] == "scoped_family_instances"
        assert expansion["catalog_identity"] == source_id
        assert expansion["instance_pattern"] == f"tre_<uf>_sjur_{suffix}"
        assert expansion["instance_count"] == 27
        assert expansion["authorities"] == [
            "TRE-AC",
            "TRE-AL",
            "TRE-AM",
            "TRE-AP",
            "TRE-BA",
            "TRE-CE",
            "TRE-DF",
            "TRE-ES",
            "TRE-GO",
            "TRE-MA",
            "TRE-MG",
            "TRE-MS",
            "TRE-MT",
            "TRE-PA",
            "TRE-PB",
            "TRE-PE",
            "TRE-PI",
            "TRE-PR",
            "TRE-RJ",
            "TRE-RN",
            "TRE-RO",
            "TRE-RR",
            "TRE-RS",
            "TRE-SC",
            "TRE-SE",
            "TRE-SP",
            "TRE-TO",
        ]
        assert expansion["federation_default"] is False


def test_surface_metadata_is_complete_and_explicit_about_unknown_scope() -> None:
    entries = build_catalog()["entries"]
    surface_ids = [entry["surface_id"] for entry in entries]

    assert len(surface_ids) == len(set(surface_ids))
    for entry in entries:
        assert entry["owner"] == "team:provider-engineering"
        assert entry["next_action"]
        assert entry["evidence_ids"]
        assert entry["evidence_ttl"] > 0
        identity = entry["surface_identity"]
        assert set(identity) == {
            "authority",
            "branch",
            "degree",
            "instance",
            "collection",
            "document_scope",
        }
        assert entry["surface_id"].endswith(f"/{entry['source_id']}")


def test_tjap_banco_sentencas_keeps_its_proven_cjpg_identity() -> None:
    entries = {entry["source_id"]: entry for entry in build_catalog()["entries"]}
    identity = entries["tjap_banco_sentencas"]["surface_identity"]

    assert identity["degree"] == "first"
    assert identity["instance"] == "first"
    assert identity["collection"] == "CJPG"


def test_tjma_jurisconsult_keeps_authorized_cjsg_identity_without_promotion() -> None:
    entries = {entry["source_id"]: entry for entry in build_catalog()["entries"]}
    entry = entries["tjma_jurisconsult"]
    assert entry["surface_identity"] == {
        "authority": "TJMA",
        "branch": "state",
        "degree": "second",
        "instance": "second",
        "collection": "CJSG",
        "document_scope": "court_catalog",
    }
    assert entry["live_status"] == "access_controlled"
    assert entry["interfaces"]["unified_search"] is False
    assert entry["coverage_role"] != "primary_textual_jurisprudence"


def test_cjf_trf1_keeps_the_canonical_trf1_appellate_identity() -> None:
    entries = {entry["source_id"]: entry for entry in build_catalog()["entries"]}
    identity = entries["cjf_jurisprudencia"]["surface_identity"]

    assert identity == {
        "authority": "TRF1",
        "branch": "federal",
        "degree": "second",
        "instance": "second",
        "collection": "JURISPRUDENCIA",
        "document_scope": "court_jurisprudence",
    }


def test_primary_textual_sources_are_suitable_for_unified_jurisprudence() -> None:
    catalog = build_catalog()
    primary = [
        entry
        for entry in catalog["entries"]
        if entry["coverage_role"] == "primary_textual_jurisprudence"
    ]

    assert primary
    for entry in primary:
        assert entry["lifecycle"] == "implemented"
        assert entry["interfaces"]["unified_search"] is True
        assert "CanonicalDecision" in entry["output_contract"]["canonical_records"]


def test_provider_coverage_scores_are_actionable() -> None:
    catalog = build_catalog()

    for entry in catalog["entries"]:
        score = entry["maturity_score"]
        assert 0 <= score["total"] <= 100, entry["source_id"]
        assert score["grade"] in {"A", "B", "C", "D"}, entry["source_id"]
        assert set(score["dimensions"]) == {
            "input",
            "output",
            "reliability",
            "documentation",
            "product",
        }
        assert score["next_actions"], entry["source_id"]


def test_reference_provider_scores_above_mapped_candidates() -> None:
    catalog = build_catalog()
    entries = {entry["source_id"]: entry for entry in catalog["entries"]}

    assert entries["tjdf_juris"]["maturity_score"]["total"] >= 85
    for entry in catalog["entries"]:
        if entry["lifecycle"] == "candidate":
            assert (
                entry["maturity_score"]["total"] < entries["tjdf_juris"]["maturity_score"]["total"]
            )


def test_standalone_document_evidence_is_consumed_by_catalog(monkeypatch, tmp_path) -> None:
    artifact = {
        "source": "stj_scon",
        "scope": "public_full_text_document",
        "checked_at": "2026-08-16T16:15:00-03:00",
        "document_id": "stj-scon-document-202502858982",
        "status": "valid",
        "http_status": 200,
        "access_status": "public",
        "retrieval_status": "ok",
        "extraction_status": "complete",
        "full_text_status": "loaded",
        "content_type": "application/pdf",
        "response_bytes": 270212,
        "sha256": "a" * 64,
        "parser": "stj_scon.get_document",
    }
    (tmp_path / "document.json").write_text(json.dumps(artifact), encoding="utf-8")
    monkeypatch.setattr(coverage_builder, "VALIDATION_RUNS_DIR", tmp_path)

    rows = coverage_builder._parse_validation_runs()

    assert rows["stj_scon"]["status"] == "valid"
    assert rows["stj_scon"]["scope"] == "public_full_text_document"
    assert rows["stj_scon"]["full_text_status"] == "loaded"
    assert rows["stj_scon"]["sha256"] == "a" * 64
    assert rows["stj_scon"]["evidence"].endswith("/document.json")


def test_validation_envelope_sources_are_consumed(monkeypatch, tmp_path) -> None:
    artifact = {
        "checked_at": "2026-08-16T12:56:03Z",
        "scope": "missing_state_providers_live",
        "sources": [
            {
                "source_id": "tjro_liame",
                "checked_at": "2026-08-16T12:56:03Z",
                "status": "valid",
                "http_status": 200,
                "access_status": "public",
                "retrieval_status": "ok",
                "extraction_status": "complete",
                "returned": 1,
                "reported_total": 1,
            }
        ],
    }
    path = tmp_path / "envelope.json"
    path.write_text(json.dumps(artifact), encoding="utf-8")
    monkeypatch.setattr(coverage_builder, "VALIDATION_RUNS_DIR", tmp_path)

    rows = coverage_builder._parse_validation_runs()

    assert rows["tjro_liame"]["status"] == "valid"
    assert rows["tjro_liame"]["access_status"] == "public"
    assert rows["tjro_liame"]["evidence"].endswith("/envelope.json")


def test_dedicated_live_keeps_primary_search_when_detail_surfaces_follow(
    monkeypatch, tmp_path
) -> None:
    artifact = {
        "observed_at": "2026-09-02T03:35:54Z",
        "results": [
            {
                "source_id": "tjro_jurisprudencia",
                "surface": "jurisprudencia",
                "classification": "reachable_valid_data",
                "http_status": 200,
                "record_count_observed": 1,
                "reported_total": 676011,
                "pagination_mode": "offset",
            },
            {
                "source_id": "tjro_jurisprudencia",
                "surface": "facets_and_filter_catalog",
                "classification": "reachable_valid_metadata_pending_canonical_facets",
                "http_status": 200,
                "record_count_observed": 0,
                "reported_total": 3480824,
            },
            {
                "source_id": "tjro_jurisprudencia",
                "surface": "related_documents_for_pjesg",
                "classification": "reachable_valid_data",
                "http_status": 200,
                "record_count_observed": 4,
                "reported_total": 4,
            },
        ],
    }
    path = tmp_path / "tjro-live.json"
    path.write_text(json.dumps(artifact), encoding="utf-8")
    monkeypatch.setattr(coverage_builder, "DEDICATED_LIVE_PATHS", (path,))

    rows = coverage_builder._parse_latest_live_validation()

    assert rows["tjro_jurisprudencia"]["status"] == "valid"
    assert rows["tjro_jurisprudencia"]["scope"] == "jurisprudencia"
    assert rows["tjro_jurisprudencia"]["returned"] == 1
    assert rows["tjro_jurisprudencia"]["reported_total"] == 676011


def test_dedicated_live_consumes_redacted_document_qa_envelope(monkeypatch, tmp_path):
    artifact = {
        "generated_at": "2026-09-07T22:00:00Z",
        "sources": [
            {
                "source": "tjms_cjsg",
                "status": "checked",
                "search": {"returned": 1, "reported_total": 230516},
                "result": {"access_status": "public", "extraction_status": "complete"},
                "provider_document": {
                    "status": "loaded",
                    "content_type": "application/pdf",
                },
                "public_url": {
                    "status": "reachable",
                    "http_status": 200,
                    "content_type": "application/pdf",
                    "response_bytes": 475946,
                    "sha256": "b" * 64,
                },
            }
        ],
    }
    path = tmp_path / "document-qa.json"
    path.write_text(json.dumps(artifact), encoding="utf-8")
    monkeypatch.setattr(coverage_builder, "DEDICATED_LIVE_PATHS", (path,))

    rows = coverage_builder._parse_latest_live_validation()

    assert rows["tjms_cjsg"]["status"] == "valid"
    assert rows["tjms_cjsg"]["scope"] == "public_full_text"
    assert rows["tjms_cjsg"]["response_bytes"] == 475946
    assert rows["tjms_cjsg"]["content_sha256"] == "b" * 64


def test_dedicated_live_flattens_nested_state_cjsg_primary_page(monkeypatch, tmp_path):
    """Nested two-page batch evidence must update provider health from page 1."""

    artifact = {
        "generated_at": "2026-09-08T05:00:00Z",
        "results": [
            {
                "source_id": "tjrr_juris",
                "surface": "cjsg",
                "first_page": {
                    "classification": "reachable_valid_data",
                    "returned": 1,
                    "reported_total": 42,
                    "trace": {
                        "http_status": 200,
                        "content_sha256": "c" * 64,
                        "response_bytes": 1234,
                    },
                },
                "second_page": {"classification": "reachable_valid_data", "returned": 1},
            }
        ],
    }
    path = tmp_path / "state-cjsg.json"
    path.write_text(json.dumps(artifact), encoding="utf-8")
    monkeypatch.setattr(coverage_builder, "DEDICATED_LIVE_PATHS", (path,))

    rows = coverage_builder._parse_latest_live_validation()

    assert rows["tjrr_juris"]["status"] == "valid"
    assert rows["tjrr_juris"]["returned"] == 1
    assert rows["tjrr_juris"]["reported_total"] == 42
    assert rows["tjrr_juris"]["http_status"] == 200


def test_dedicated_live_flattens_nested_pages_primary_page(monkeypatch, tmp_path):
    """B1 batch evidence uses a pages list and must feed page one health."""

    artifact = {
        "generated_at": "2026-09-08T05:00:00Z",
        "results": [
            {
                "source_id": "tjba_graphql",
                "surface": "cjsg",
                "pages": [
                    {
                        "classification": "reachable_valid_data",
                        "returned": 1,
                        "reported_total": 7,
                        "trace": {
                            "http_status": 200,
                            "content_sha256": "d" * 64,
                            "response_bytes": 456,
                        },
                    },
                    {"classification": "reachable_valid_data", "returned": 1},
                ],
            }
        ],
    }
    path = tmp_path / "state-b1.json"
    path.write_text(json.dumps(artifact), encoding="utf-8")
    monkeypatch.setattr(coverage_builder, "DEDICATED_LIVE_PATHS", (path,))

    rows = coverage_builder._parse_latest_live_validation()

    assert rows["tjba_graphql"]["status"] == "valid"
    assert rows["tjba_graphql"]["returned"] == 1
    assert rows["tjba_graphql"]["reported_total"] == 7
    assert rows["tjba_graphql"]["http_status"] == 200


def test_dedicated_live_uses_outer_classification_for_compact_pages(monkeypatch, tmp_path):
    """Compact pagination evidence may classify the envelope once."""

    artifact = {
        "observed_at": "2026-09-10T12:00:00Z",
        "results": [
            {
                "source_id": "tjrj_ejuris",
                "surface": "cjsg",
                "classification": "success_with_results_pagination_validated",
                "record_count_observed": 1,
                "reported_total": 46191,
                "pages": [
                    {"returned": 1, "reported_total": 46191},
                    {"returned": 1, "reported_total": 46191},
                ],
            }
        ],
    }
    path = tmp_path / "compact-pagination.json"
    path.write_text(json.dumps(artifact), encoding="utf-8")
    monkeypatch.setattr(coverage_builder, "DEDICATED_LIVE_PATHS", (path,))

    rows = coverage_builder._parse_latest_live_validation()

    assert rows["tjrj_ejuris"]["status"] == "valid"
    assert rows["tjrj_ejuris"]["reported_total"] == 46191


def test_dedicated_live_normalizes_semantic_success_classification(monkeypatch, tmp_path):
    """Provider-specific success labels must feed the common valid state."""

    artifact = {
        "observed_at": "2026-09-07T22:30:37Z",
        "source_id": "tjse_boletim_jurisprudencia",
        "surface": "cjsg",
        "status": "valid",
        "classification": "public_textual_second_degree",
        "record_count_observed": 10,
        "http_status": 200,
        "latency_ms": 18532.84,
    }
    path = tmp_path / "tjse-boletim.json"
    path.write_text(json.dumps(artifact), encoding="utf-8")
    monkeypatch.setattr(coverage_builder, "DEDICATED_LIVE_PATHS", (path,))

    rows = coverage_builder._parse_latest_live_validation()

    assert rows["tjse_boletim_jurisprudencia"]["status"] == "valid"
    assert rows["tjse_boletim_jurisprudencia"]["returned"] == 10
    assert rows["tjse_boletim_jurisprudencia"]["latency"] == 18532.84


def test_dedicated_live_normalizes_result_and_document_success(monkeypatch, tmp_path):
    """A bounded search plus a valid detail document remains a live success."""

    artifact = {
        "observed_at": "2026-09-10T12:00:00Z",
        "source_id": "tre_sjur_jurisprudencia",
        "surface": "SJUR",
        "classification": "success_with_results_and_document",
        "record_count_observed": 3,
        "reported_total": 10,
        "http_status": 200,
        "response_bytes": 91325,
        "latency_ms": 1152.58,
    }
    path = tmp_path / "tre-sp-sjur.json"
    path.write_text(json.dumps(artifact), encoding="utf-8")
    monkeypatch.setattr(coverage_builder, "DEDICATED_LIVE_PATHS", (path,))

    rows = coverage_builder._parse_latest_live_validation()

    assert rows["tre_sjur_jurisprudencia"]["status"] == "valid"
    assert rows["tre_sjur_jurisprudencia"]["returned"] == 3
    assert rows["tre_sjur_jurisprudencia"]["reported_total"] == 10
    assert rows["tre_sjur_jurisprudencia"]["response_bytes"] == 91325


def test_dedicated_live_consumes_federal_eproc_provider_envelope(monkeypatch, tmp_path):
    """Federal eproc search/detail probes feed each child provider health row."""

    artifact = {
        "generated_at": "2026-09-10T21:07:11-03:00",
        "providers": [
            {
                "source": "tnu_eproc_jurisprudencia",
                "search": {"http_status": 200, "returned": 1, "total": 11228, "total_known": True},
                "detail": {
                    "status": "valid",
                    "content_type": "text/html",
                    "byte_size": 137621,
                    "sha256": "a" * 64,
                },
            },
            {
                "source": "trf2_eproc_jurisprudencia",
                "search": {"http_status": 403, "returned": 0, "total_known": False},
                "detail": {"status": "blocked"},
            },
        ],
    }
    path = tmp_path / "federal-eproc.json"
    path.write_text(json.dumps(artifact), encoding="utf-8")
    monkeypatch.setattr(coverage_builder, "DEDICATED_LIVE_PATHS", (path,))

    rows = coverage_builder._parse_latest_live_validation()

    assert rows["tnu_eproc_jurisprudencia"]["status"] == "valid"
    assert rows["tnu_eproc_jurisprudencia"]["returned"] == 1
    assert rows["tnu_eproc_jurisprudencia"]["full_text_status"] == "valid"
    assert rows["tnu_eproc_jurisprudencia"]["response_bytes"] == 137621
    assert rows["trf2_eproc_jurisprudencia"]["status"] == "access_control_required"


def test_dedicated_live_keeps_valid_provider_when_empty_probe_follows(monkeypatch, tmp_path):
    """An explicit empty query must not erase a successful primary probe."""

    artifact = {
        "observed_at": "2026-09-05T11:00:00Z",
        "results": [
            {
                "source_id": "tjgo_projudi_jurisprudencia",
                "surface": "jurisprudencia",
                "classification": "reachable_valid_data",
                "http_status": 200,
                "record_count_observed": 3,
                "reported_total": 36060,
                "pagination_mode": "page",
            },
            {
                "source_id": "tjgo_projudi_jurisprudencia",
                "surface": "jurisprudencia",
                "classification": "reachable_empty_data",
                "http_status": 200,
                "record_count_observed": 0,
                "reported_total": None,
                "pagination_mode": "page",
            },
        ],
    }
    path = tmp_path / "tjgo-live.json"
    path.write_text(json.dumps(artifact), encoding="utf-8")
    monkeypatch.setattr(coverage_builder, "DEDICATED_LIVE_PATHS", (path,))

    rows = coverage_builder._parse_latest_live_validation()

    assert rows["tjgo_projudi_jurisprudencia"]["status"] == "valid"
    assert rows["tjgo_projudi_jurisprudencia"]["returned"] == 3
    assert rows["tjgo_projudi_jurisprudencia"]["reported_total"] == 36060


def test_dedicated_live_keeps_valid_provider_when_transient_recheck_fails(monkeypatch, tmp_path):
    """A timeout in a later health probe must not create a false outage."""

    artifact = {
        "observed_at": "2026-09-13T05:00:00Z",
        "results": [
            {
                "source_id": "tjsc_eproc_jurisprudencia",
                "classification": "source_unavailable",
                "http_status": None,
                "record_count_observed": 0,
            }
        ],
    }
    path = tmp_path / "eproc-recheck.json"
    path.write_text(json.dumps(artifact), encoding="utf-8")
    monkeypatch.setattr(coverage_builder, "DEDICATED_LIVE_PATHS", (path,))

    rows = {
        "tjsc_eproc_jurisprudencia": {
            "status": "valid",
            "scope": "cjsg",
            "_dedicated_evidence_date": "2026-09-08",
        }
    }
    coverage_builder._merge_dedicated_live(rows, path)

    assert rows["tjsc_eproc_jurisprudencia"]["status"] == "valid"
    assert rows["tjsc_eproc_jurisprudencia"]["last_recheck"] == {
        "date": "2026-09-13",
        "status": "source_unavailable",
        "evidence": path.as_posix(),
        "http_status": None,
    }


def test_tre_document_uf_sweep_enriches_document_capability_without_replacing_health(
    tmp_path,
):
    artifact = {
        "observed_at": "2026-09-13T05:52:07Z",
        "results": [
            {
                "authority": "TRE-AC",
                "classification": "success_with_document",
                "degree": "second",
                "collection": "SJUR",
                "document_access_status": "public",
                "document_extraction_status": "complete",
                "document_has_text": True,
            },
            {
                "authority": "TRE-AP",
                "classification": "source_unavailable",
                "degree": "second",
                "collection": "SJUR",
                "document_access_status": "unknown",
                "document_extraction_status": "unavailable",
                "document_has_text": False,
            },
        ],
    }
    path = tmp_path / "tre-sjur-document-uf-sweep-live-20260913.json"
    path.write_text(json.dumps(artifact), encoding="utf-8")
    rows = {
        "tre_sjur_jurisprudencia": {
            "status": "valid",
            "scope": "jurisprudencia",
        }
    }

    coverage_builder._merge_dedicated_live(rows, path)

    enriched = rows["tre_sjur_jurisprudencia"]
    assert enriched["status"] == "valid"
    assert enriched["document_uf_sweep_status"] == "partial"
    assert enriched["document_uf_sweep_checked"] == 2
    assert enriched["document_uf_sweep_valid"] == 1
    assert enriched["document_uf_sweep_failures"] == [
        {"authority": "TRE-AP", "classification": "source_unavailable"}
    ]


def test_tjam_detail_block_is_exposed_without_regressing_search_health(tmp_path):
    artifact = {
        "source_id": "tjam_cjsg",
        "checked_at": "2026-09-13",
        "response": {
            "http_status": 200,
            "content_type": "text/html;charset=UTF-8",
            "response_bytes": 10657,
            "content_sha256": "detail-hash",
            "access_status": "access_control_required",
        },
    }
    path = tmp_path / "tjam-cjsg-detail-live-20260913.json"
    path.write_text(json.dumps(artifact), encoding="utf-8")
    rows = {
        "tjam_cjsg": {
            "status": "valid",
            "scope": "cjsg",
            "date": "2026-09-13",
        }
    }

    coverage_builder._merge_dedicated_live(rows, path)

    enriched = rows["tjam_cjsg"]
    assert enriched["status"] == "valid"
    assert enriched["document_access_status"] == "access_control_required"
    assert enriched["document_extraction_status"] == "blocked"
    assert enriched["document_content_sha256"] == "detail-hash"


def test_tjce_detail_success_enriches_search_health(tmp_path):
    artifact = {
        "source_id": "tjce_cjsg",
        "checked_at": "2026-09-13",
        "response": {
            "http_status": 200,
            "content_type": "application/pdf;charset=UTF-8",
            "response_bytes": 530551,
            "content_sha256": "document-hash",
            "access_status": "public",
            "extraction_status": "complete",
            "detected_content_type": "application/pdf",
            "text_characters": 73244,
            "page_count": 33,
        },
    }
    path = tmp_path / "tjce-cjsg-detail-live-20260913.json"
    path.write_text(json.dumps(artifact), encoding="utf-8")
    rows = {
        "tjce_cjsg": {
            "status": "valid",
            "date": "2026-09-13",
            "scope": "cjsg",
        }
    }

    coverage_builder._merge_dedicated_live(rows, path)

    enriched = rows["tjce_cjsg"]
    assert enriched["status"] == "valid"
    assert enriched["full_text_status"] == "valid"
    assert enriched["document_extraction_status"] == "complete"
    assert enriched["document_page_count"] == 33
    assert enriched["document_content_sha256"] == "document-hash"


def test_tre_first_degree_text_probe_does_not_become_false_empty(tmp_path):
    artifact = {
        "observed_at": "2026-09-13T15:21:36Z",
        "results": [
            {
                "tribunal": "TRE-AC",
                "http_status": 200,
                "degree_labels": {"second": 1000},
                "classification": "success_without_first_degree_label",
            },
            {
                "tribunal": "TRE-AP",
                "http_status": 200,
                "degree_labels": {},
                "classification": "success_without_first_degree_label",
            },
        ],
    }
    path = tmp_path / "tre-sjur-first-degree-sweep-live-20260913.json"
    path.write_text(json.dumps(artifact), encoding="utf-8")
    rows = {
        "tre_sjur_first_degree": {
            "status": "valid",
            "date": "2026-09-12",
            "note": "filtro remoto validado",
        }
    }

    coverage_builder._merge_dedicated_live(rows, path)

    enriched = rows["tre_sjur_first_degree"]
    assert enriched["status"] == "valid"
    assert enriched["first_degree_text_probe_status"] == "second_degree_only_window"
    assert enriched["first_degree_text_probe_second_only"] == 1
    assert enriched["first_degree_text_probe_unknown"] == 1


def test_tre_first_degree_sample_enriches_family_without_replacing_filter_contract(tmp_path):
    artifact = {
        "source_id": "tre_sjur_first_degree",
        "authority": "TRE-MG",
        "checked_at": "2026-09-13",
        "observations": {
            "degree": "first",
            "returned": 1,
            "reported_total": 1,
            "source_id": "tre_mg_sjur_first_degree-1",
            "response_bytes": 10,
            "content_sha256": "sample-hash",
        },
    }
    path = tmp_path / "tre-mg-first-degree-live-20260913.json"
    path.write_text(json.dumps(artifact), encoding="utf-8")
    rows = {
        "tre_sjur_first_degree": {
            "status": "valid",
            "date": "2026-09-12",
            "scope": "decision_type_filter",
        }
    }

    coverage_builder._merge_dedicated_live(rows, path)

    enriched = rows["tre_sjur_first_degree"]
    assert enriched["status"] == "valid"
    assert enriched["scope"] == "decision_type_filter"
    assert enriched["first_degree_sample_authority"] == "TRE-MG"
    assert enriched["first_degree_sample_status"] == "valid"


def test_dedicated_live_does_not_overwrite_newer_evidence_with_stale_artifact(
    monkeypatch, tmp_path
):
    """Append-only evidence ordering must remain chronological per provider."""

    newer = {
        "observed_at": "2026-09-07T00:14:00Z",
        "source_id": "tjpe_jurisprudencia",
        "surface": "cjsg",
        "classification": "valid",
        "http_status": 200,
        "record_count_observed": 5,
        "reported_total": 5,
    }
    older = {
        "observed_at": "2026-09-06T12:00:00Z",
        "source_id": "tjpe_jurisprudencia",
        "surface": "cjsg",
        "classification": "blocked_transport",
        "http_status": None,
        "record_count_observed": 0,
    }
    newer_path = tmp_path / "newer.json"
    older_path = tmp_path / "older.json"
    newer_path.write_text(json.dumps(newer), encoding="utf-8")
    older_path.write_text(json.dumps(older), encoding="utf-8")
    monkeypatch.setattr(coverage_builder, "DEDICATED_LIVE_PATHS", (newer_path, older_path))

    rows = coverage_builder._parse_latest_live_validation()

    assert rows["tjpe_jurisprudencia"]["status"] == "valid"
    assert rows["tjpe_jurisprudencia"]["date"] == "2026-09-07"
    assert rows["tjpe_jurisprudencia"]["returned"] == 5


def test_nested_search_live_evidence_is_flattened_without_body_persistence(monkeypatch, tmp_path):
    """Nested redacted search envelopes update the provider health row."""

    artifact = {
        "observed_at": "2026-09-13T03:56:05Z",
        "provider": "tjmg_jurisprudencia",
        "surface": "CJSG",
        "classification": "success_with_results",
        "search": {
            "http_status": 200,
            "access_status": "public",
            "result_count": 1,
            "reported_total": 1000,
            "total_known": True,
            "elapsed_ms": 399.12,
            "content_type": "application/json",
            "response_bytes": 2046,
            "content_sha256": "abc123",
        },
        "detail": {
            "http_status": 200,
            "text_characters": 1200,
            "content_type": "application/json",
            "response_bytes": 8584,
            "content_sha256": "doc-sha",
            "access_status": "public",
        },
    }
    path = tmp_path / "nested-search.json"
    path.write_text(json.dumps(artifact), encoding="utf-8")
    monkeypatch.setattr(coverage_builder, "DEDICATED_LIVE_PATHS", (path,))

    rows = coverage_builder._parse_latest_live_validation()

    row = rows["tjmg_jurisprudencia"]
    assert row["status"] == "valid"
    assert row["date"] == "2026-09-13"
    assert row["returned"] == 1
    assert row["reported_total"] == 1000
    assert row["latency"] == 399.12
    assert row["full_text_status"] == "valid"
    assert row["access_status"] == "public"
    assert row["document_content_sha256"] == "doc-sha"
    assert row["document_response_bytes"] == 8584
    assert row["document_content_type"] == "application/json"
    assert row["document_text_characters"] == 1200
    assert row["document_access_status"] == "public"


def test_federated_smoke_consumes_only_explicit_public_rows(monkeypatch, tmp_path):
    """Redacted federation evidence must not turn unknown sources into empty ones."""

    artifact = {
        "generated_at": "2026-09-06T12:00:00Z",
        "source_completeness": {
            "tjrn_jurisprudencia": {
                "returned": 2,
                "reported_total": 12,
                "pagination_mode": "page",
            },
            "tjpe_jurisprudencia": {
                "returned": 0,
                "reported_total": None,
                "pagination_mode": "page",
            },
        },
        "source_access_status": {
            "tjrn_jurisprudencia": "public",
            "tjpe_jurisprudencia": None,
        },
    }
    path = tmp_path / "federated-smoke.json"
    path.write_text(json.dumps(artifact), encoding="utf-8")
    monkeypatch.setattr(coverage_builder, "DEDICATED_LIVE_PATHS", (path,))

    rows = coverage_builder._parse_latest_live_validation()

    assert rows["tjrn_jurisprudencia"]["status"] == "valid"
    assert rows["tjrn_jurisprudencia"]["returned"] == 2
    # An unknown row must not erase or downgrade earlier evidence for the same
    # source; importantly, it must not be interpreted as an empty result.
    assert rows["tjpe_jurisprudencia"]["status"] == "valid"
    assert rows["tjpe_jurisprudencia"]["returned"] != 0


def test_degree_binding_live_evidence_is_consumed_without_promoting_access_block(
    monkeypatch,
) -> None:
    """The current CJPG/CJSG evidence updates live status, not federation state."""

    evidence_path = (
        ROOT / "docs" / "provider-discovery" / "degree-bindings-live-20260902-cycle26.json"
    )
    monkeypatch.setattr(coverage_builder, "DEDICATED_LIVE_PATHS", (evidence_path,))

    rows = coverage_builder._parse_latest_live_validation()

    assert rows["tjes_cjpg"]["status"] == "valid"
    assert rows["tjes_jurisprudencia"]["status"] == "valid"
    assert rows["tjsp_cjpg"]["status"] == "valid"
    assert rows["tjsp_cjsg"]["status"] == "blocked_access"
    assert rows["tjsp_cjsg"]["returned"] == 0
