from __future__ import annotations

import json
from pathlib import Path
from uuid import uuid4

import pytest

from nanojuris.discovery.draft import build_sdd_artifacts, write_sdd_artifacts
from nanojuris.discovery.crawler import DiscoveryCrawler
from nanojuris.discovery.cache import DiscoveryCache
from nanojuris.discovery.extract import extract_filter_candidates, extract_route_candidates, suggest_selector_candidates
from nanojuris.discovery.models import (
    DiscoveryEvidence,
    DiscoveryPolicy,
    DiscoveryRequest,
    DiscoveryResponse,
    DiscoveryRun,
    DiscoveryStatus,
)
from nanojuris.discovery.policy import assert_allowed_url, redact_headers
from nanojuris.discovery.replay import replay_analysis
from nanojuris.models import AccessStatus, ExtractionStatus


def _evidence(body: bytes = b"<html><body><p>Ementa decisao</p></body></html>") -> DiscoveryEvidence:
    response = DiscoveryResponse(
        status_code=200,
        url="https://example.test/jurisprudencia",
        final_url="https://example.test/jurisprudencia",
        content_type="text/html; charset=utf-8",
        body=body,
    )
    return DiscoveryEvidence(
        run_id="run-1",
        captured_at="2026-08-20T00:00:00+00:00",
        seed_url=response.url,
        request=DiscoveryRequest("GET", response.url),
        response=response,
        status=DiscoveryStatus.VALID,
        access_status=AccessStatus.PUBLIC,
        extraction_status=ExtractionStatus.COMPLETE,
    )


def test_policy_accepts_subdomains_and_rejects_private_destinations():
    policy = DiscoveryPolicy(allowed_domains=("example.test",))
    assert_allowed_url("https://www.example.test/jurisprudencia", policy)
    with pytest.raises(ValueError):
        assert_allowed_url("http://127.0.0.1:8080", policy)
    with pytest.raises(ValueError):
        assert_allowed_url("https://other.test", policy)


def test_redact_headers_removes_authentication_material():
    assert redact_headers({"Authorization": "Bearer secret", "Content-Type": "text/html"}) == {
        "Authorization": "<redacted>",
        "Content-Type": "text/html",
    }


def test_extract_routes_from_html_forms_scripts_and_links():
    html = b"""
    <a href="/jurisprudencia/1">detalhe</a>
    <form method="post" action="/api/search"></form>
    <script>fetch('/api/results?page=2')</script>
    """
    candidates = extract_route_candidates("https://example.test/home", html, "text/html")
    assert {candidate.url for candidate in candidates} == {
        "https://example.test/jurisprudencia/1",
        "https://example.test/api/search",
        "https://example.test/api/results?page=2",
    }
    assert next(candidate for candidate in candidates if candidate.url.endswith("/api/search")).method == "POST"


def test_selector_candidates_are_suggestions_with_confidence():
    html = b'<main><section id="ementa">Ementa: texto da decisao</section></main>'
    candidates = suggest_selector_candidates(html, {"decision_text": ("ementa",)})
    assert candidates[0].selector == "#ementa"
    assert candidates[0].confidence == 0.75


def test_extract_filter_candidates_preserves_html_contract_fields_and_options():
    html = b'''
    <form action="/search" method="post">
      <input name="texto" placeholder="Termos" required>
      <select name="tipo"><option value="AC">Acordao</option><option value="SV">Sumula</option></select>
    </form>
    '''
    candidates = extract_filter_candidates("https://example.test", html, "text/html")
    by_name = {candidate.name: candidate for candidate in candidates}
    assert by_name["texto"].required is True
    assert by_name["tipo"].values == ["AC", "SV"]


def test_replay_analysis_does_not_need_network():
    draft_dir = Path(".tmp") / f"provider-discovery-test-{uuid4().hex}"
    try:
        write_sdd_artifacts(
            DiscoveryRun("run-1", "2026-08-20T00:00:00+00:00", DiscoveryPolicy(("example.test",)), [_evidence()]),
            draft_dir,
        )
        result = replay_analysis(draft_dir / "evidence.json")
        assert result["probe"]["status_code"] == 200
        assert result["probe"]["content_sha256"]
    finally:
        for child in draft_dir.glob("*"):
            child.unlink()
        draft_dir.rmdir()


def test_sdd_drafts_contain_traceable_run_and_required_sections():
    run = DiscoveryRun("run-1", "2026-08-20T00:00:00+00:00", DiscoveryPolicy(("example.test",)), [_evidence()])
    artifacts = build_sdd_artifacts(run)
    assert {"research.md", "spec.md", "design.md", "tasks.md", "verification.md", "threat-model.md"} <= set(
        artifacts
    )
    assert "run-1" in artifacts["spec.md"]


def test_crawler_continues_after_controlled_route_and_follows_allowed_candidates():
    class StubClient:
        policy = DiscoveryPolicy(("example.test",), max_pages=3, max_depth=1, delay_seconds=0)

        def fetch(self, *, run_id, seed_url, request):
            from nanojuris.discovery.models import RouteCandidate

            current = _evidence()
            current.run_id = run_id
            current.request = request
            if request.url.endswith("/start"):
                current.route_candidates = [RouteCandidate("https://example.test/next", depth=1)]
            return current

    run = DiscoveryCrawler(StubClient()).crawl("https://example.test/start")
    assert [evidence.request.url for evidence in run.evidences] == [
        "https://example.test/start",
        "https://example.test/next",
    ]


def test_discovery_cache_replays_evidence_by_request_fingerprint():
    cache_dir = Path(".tmp") / f"provider-discovery-cache-{uuid4().hex}"
    try:
        cache = DiscoveryCache(cache_dir)
        evidence = _evidence()
        cache.put(evidence)
        loaded = cache.get(evidence.request)
        assert loaded is not None
        assert loaded.response.content_sha256 == evidence.response.content_sha256
        assert loaded.response.body == evidence.response.body
    finally:
        for child in cache_dir.glob("*"):
            child.unlink()
        cache_dir.rmdir()
