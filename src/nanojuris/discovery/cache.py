"""Filesystem cache for bounded discovery responses."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

from nanojuris.discovery.models import DiscoveryEvidence, DiscoveryRequest
from nanojuris.discovery.policy import redact_mapping, redact_payload
from nanojuris.discovery.replay import load_evidence, write_evidence


class DiscoveryCache:
    """Cache keyed by method, URL, query and redacted request body."""

    def __init__(self, directory: str | Path) -> None:
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)

    def path_for(self, request: DiscoveryRequest) -> Path:
        material = json.dumps(
            {
                "method": request.method.upper(),
                "url": request.url,
                "query": redact_mapping(request.query),
                "body": redact_payload(request.body),
            },
            ensure_ascii=False,
            sort_keys=True,
            default=str,
        ).encode("utf-8")
        fingerprint = hashlib.sha256(material).hexdigest()
        return self.directory / f"{fingerprint}.json"

    def get(self, request: DiscoveryRequest) -> DiscoveryEvidence | None:
        path = self.path_for(request)
        if not path.exists():
            return None
        return load_evidence(path)

    def put(self, evidence: DiscoveryEvidence) -> Path:
        path = self.path_for(evidence.request)
        write_evidence(evidence, path)
        return path
