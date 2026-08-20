"""Bounded breadth-first discovery over candidate public routes."""

from __future__ import annotations

import time
import uuid
from collections import deque
from datetime import datetime, timezone

from nanojuris.discovery.http import HttpDiscoveryClient
from nanojuris.discovery.models import DiscoveryRun
from nanojuris.discovery.policy import is_allowed_url


class DiscoveryCrawler:
    """Follow GET candidates while preserving per-run bounds and evidence."""

    def __init__(self, client: HttpDiscoveryClient) -> None:
        self.client = client

    def crawl(self, seed_url: str) -> DiscoveryRun:
        policy = self.client.policy
        run = DiscoveryRun(run_id=uuid.uuid4().hex, started_at=_utc_now(), policy=policy)
        queue: deque[tuple[str, int]] = deque([(seed_url, 0)])
        visited: set[str] = set()
        total_bytes = 0

        while (
            queue and len(run.evidences) < policy.max_pages and total_bytes < policy.max_total_bytes
        ):
            url, depth = queue.popleft()
            if url in visited or depth > policy.max_depth or not is_allowed_url(url, policy):
                continue
            visited.add(url)
            if policy.delay_seconds:
                time.sleep(policy.delay_seconds)
            evidence = self.client.fetch(
                run_id=run.run_id,
                seed_url=seed_url,
                request=self._request_for(url),
            )
            run.evidences.append(evidence)
            total_bytes += evidence.response.response_bytes
            if evidence.response.response_bytes >= policy.max_bytes_per_response:
                continue
            for candidate in evidence.route_candidates:
                if candidate.method != "GET" or candidate.depth > policy.max_depth:
                    continue
                if candidate.url not in visited and is_allowed_url(candidate.url, policy):
                    queue.append((candidate.url, candidate.depth))
        run.finished_at = _utc_now()
        return run

    @staticmethod
    def _request_for(url: str):
        from nanojuris.discovery.models import DiscoveryRequest

        return DiscoveryRequest(method="GET", url=url)


def _utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()
