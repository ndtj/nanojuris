"""Filesystem cache for bounded discovery responses."""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import time
from pathlib import Path
from typing import Any

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
            with temporary_path.open("r+b") as stream:
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary_path, path)
        finally:
            temporary_path.unlink(missing_ok=True)
        return path

    def cleanup(
        self,
        *,
        max_age_seconds: float | None = None,
        max_bytes: int | None = None,
        now: float | None = None,
    ) -> dict[str, Any]:
        """Remove expired/old cache entries within this cache directory only.

        Cleanup is opt-in and bounded to direct ``*.json`` files created by
        this cache.  Entries are removed oldest-first when the byte budget is
        exceeded.  The return value is an audit summary; filesystem races are
        reported instead of aborting the rest of the cleanup.
        """

        if max_age_seconds is not None and max_age_seconds < 0:
            raise ValueError("max_age_seconds deve ser não negativo")
        if max_bytes is not None and max_bytes < 0:
            raise ValueError("max_bytes deve ser não negativo")
        current_time = time.time() if now is None else now
        root = self.directory.resolve()
        entries: list[tuple[Path, float, int]] = []
        errors: list[str] = []
        for path in self.directory.glob("*.json"):
            try:
                if path.is_symlink() or path.resolve().parent != root:
                    continue
                stat = path.stat()
                entries.append((path, stat.st_mtime, stat.st_size))
            except OSError as exc:
                errors.append(f"{path.name}: {type(exc).__name__}")

        entries.sort(key=lambda item: (item[1], item[0].name))
        selected: list[tuple[Path, float, int]] = []
        if max_age_seconds is not None:
            cutoff = current_time - max_age_seconds
            selected.extend(item for item in entries if item[1] < cutoff)
        selected_paths = {item[0] for item in selected}
        remaining = [item for item in entries if item[0] not in selected_paths]
        if max_bytes is not None:
            total = sum(item[2] for item in remaining)
            for item in remaining:
                if total <= max_bytes:
                    break
                selected.append(item)
                selected_paths.add(item[0])
                total -= item[2]

        deleted_files = 0
        deleted_bytes = 0
        for path, _mtime, size in selected:
            try:
                path.unlink()
            except FileNotFoundError:
                continue
            except OSError as exc:
                errors.append(f"{path.name}: {type(exc).__name__}")
                continue
            deleted_files += 1
            deleted_bytes += size

        remaining_files = 0
        remaining_bytes = 0
        for path in self.directory.glob("*.json"):
            try:
                if path.is_symlink() or path.resolve().parent != root:
                    continue
                remaining_files += 1
                remaining_bytes += path.stat().st_size
            except OSError as exc:
                errors.append(f"{path.name}: {type(exc).__name__}")
        return {
            "deleted_files": deleted_files,
            "deleted_bytes": deleted_bytes,
            "remaining_files": remaining_files,
            "remaining_bytes": remaining_bytes,
            "errors": errors,
        }
