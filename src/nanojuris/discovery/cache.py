"""Filesystem cache for bounded discovery responses."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
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
        # A process may be interrupted while a cache file is being replaced.
        # Cache corruption must never turn an optional replay into a discovery
        # failure: treat it as a miss and let the caller fetch fresh evidence.
        try:
            return load_evidence(path)
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
            return None

    def put(self, evidence: DiscoveryEvidence) -> Path:
        path = self.path_for(evidence.request)
        # Write-and-replace keeps readers from observing a partially written
        # JSON envelope.  This follows the same safe persistence pattern as
        # the reference template while retaining NanoJuris' synchronous API.
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
        temporary_path = Path(temporary)
        try:
            os.close(fd)
            write_evidence(evidence, temporary_path)
            os.replace(temporary_path, path)
        finally:
            temporary_path.unlink(missing_ok=True)
        return path
