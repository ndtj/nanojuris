"""Offline quality gates for provider evidence.

These checks deliberately inspect only checked-in documentation and fixtures.
They do not instantiate a network session and do not infer a live success from
the presence of a file.  The goal is to prevent the evidence catalogue from
silently regressing while a provider is being hardened.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from nanojuris.client import NanoJurisClient
from tools.audit_provider_discovery_offline import _fixture_refs, _test_files, _test_fixture_refs

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "docs" / "registry" / "provider-catalog.full.json"

# These providers are intentionally tracked as an evidence debt.  They have a
# parser/registration test, but no reviewed payload has been checked in yet.
# Keeping the list explicit makes new evidence debt fail loudly in review.
KNOWN_EVIDENCE_DEBT = {
    "stf_informativo",  # the XLSX is built in-memory by its parser tests
    "tjpb_pje_jurisprudencia",
    "tjrj_eproc_jurisprudencia",
}

SECRET_MARKERS = re.compile(
    # Header-shaped markers are intentionally anchored: JavaScript bundles
    # often contain harmless names such as ``srcookie=1``.
    r"(?im)(?:^|[\r\n])\s*(?:authorization|cookie|set-cookie)\s*:\s*[^\r\n]+|"
    r"bearer\s+[a-z0-9._-]{20,}|private\s+key|client[_ -]?secret\s*[:=]|"
    r"access[_ -]?token\s*[:=]\s*[A-Za-z0-9._-]{20,}"
)


def _runtime_sources() -> set[str]:
    catalog = json.loads(CATALOG.read_text(encoding="utf-8"))
    return {
        str(entry["source_id"])
        for entry in catalog["entries"]
        if entry.get("implementation_status") == "runtime"
    }


def _evidence_for(source_id: str) -> set[str]:
    refs = _fixture_refs(ROOT, source_id)
    tests = _test_files(ROOT, source_id)
    refs.update(_test_fixture_refs(ROOT, tests, source_id))
    return refs


def test_runtime_fixture_evidence_debt_is_explicit() -> None:
    runtime = {item.source for item in NanoJurisClient().list_sources()}
    assert runtime == _runtime_sources()

    evidence_debt = {source for source in runtime if not _evidence_for(source)}
    assert evidence_debt == KNOWN_EVIDENCE_DEBT

    # A provider with only a synthetic inline payload is still debt, rather
    # than being accidentally counted as a reviewed, replayable fixture.
    assert not _evidence_for("stf_informativo")


def test_every_referenced_fixture_exists_and_is_nonempty() -> None:
    for source_id in _runtime_sources():
        for name in sorted(_evidence_for(source_id)):
            path = ROOT / "tests" / "fixtures" / name
            assert path.is_file(), f"{source_id}: missing fixture {name}"
            assert path.stat().st_size > 0, f"{source_id}: empty fixture {name}"


def test_referenced_json_fixtures_are_valid_json() -> None:
    for source_id in _runtime_sources():
        for name in sorted(_evidence_for(source_id)):
            path = ROOT / "tests" / "fixtures" / name
            if path.suffix.lower() != ".json":
                continue
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
                raise AssertionError(f"{source_id}: invalid JSON fixture {name}") from exc
            assert payload is not None, f"{source_id}: null JSON fixture {name}"


def test_referenced_fixtures_contain_no_credential_material() -> None:
    for source_id in _runtime_sources():
        for name in sorted(_evidence_for(source_id)):
            path = ROOT / "tests" / "fixtures" / name
            text = path.read_text(encoding="utf-8", errors="replace")
            assert not SECRET_MARKERS.search(text), f"{source_id}: secret marker in {name}"


def test_unified_court_contracts_declare_minimum_data_quality() -> None:
    """Every textual court source must expose enough data for safe ranking."""

    identity_fields = {
        "case_number",
        "registry_number",
        "public_id",
        "source_record_id",
        "id",
        "number",
    }
    content_fields = {"summary", "full_text", "question", "thesis", "title"}
    date_fields = {"judgment_date", "publication_date", "updated_at", "source_updated_at"}

    gaps: dict[str, list[str]] = {}
    for capability in NanoJurisClient().list_sources():
        if capability.category != "court_jurisprudence" or not capability.supports_unified_search:
            continue
        fields = set(capability.extracted_fields)
        missing = [
            name
            for name, required in (
                ("identity", identity_fields),
                ("legal_content", content_fields),
                ("date", date_fields),
            )
            if not fields & required
        ]
        if not capability.endpoints:
            missing.append("source_trace_endpoint")
        if missing:
            gaps[capability.source] = missing

    assert gaps == {}, f"contratos judiciais sem campos mínimos: {gaps}"


def test_full_text_capability_contract_matches_the_declared_access_mode() -> None:
    """Avoid advertising detail/full text routes that the adapter cannot expose."""

    detail_modes = {"detail_call", "inline", "inline_result_text"}
    gaps: dict[str, list[str]] = {}
    for capability in NanoJurisClient().list_sources():
        fields = set(capability.extracted_fields)
        missing: list[str] = []
        if capability.supports_full_text and capability.full_text_access not in detail_modes:
            missing.append("full_text_access_mode")
        if capability.full_text_access == "detail_call" and not fields & {
            "document_url",
            "full_text_url",
        }:
            missing.append("detail_document_url")
        if capability.full_text_access in {"inline", "inline_result_text"} and not fields & {
            "full_text",
            "summary",
        }:
            missing.append("inline_content_field")
        if missing:
            gaps[capability.source] = missing

    assert gaps == {}, f"contratos de inteiro teor inconsistentes: {gaps}"
