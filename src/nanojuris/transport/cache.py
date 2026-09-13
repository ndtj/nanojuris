"""Atomic filesystem cache for immutable transport responses."""

from __future__ import annotations

import base64
import json
import os
import tempfile
import time
from dataclasses import asdict
from pathlib import Path

from nanojuris.transport.models import TransportResponse, TransportStatus


class ContentResponseCache:
    """Cache GET/HEAD response envelopes without persisting request secrets."""

    def __init__(
        self,
        directory: str | Path,
        *,
        ttl_seconds: float | None = None,
        max_body_bytes: int | None = 4_000_000,
        max_total_bytes: int | None = 64_000_000,
    ) -> None:
        self.directory = Path(directory)
        self.directory.mkdir(parents=True, exist_ok=True)
        if ttl_seconds is not None and ttl_seconds < 0:
            raise ValueError("ttl_seconds must be non-negative")
        if max_body_bytes is not None and max_body_bytes < 1:
            raise ValueError("max_body_bytes must be positive")
        if max_total_bytes is not None and max_total_bytes < 1:
            raise ValueError("max_total_bytes must be positive")
        self.ttl_seconds = ttl_seconds
        self.max_body_bytes = max_body_bytes
        self.max_total_bytes = max_total_bytes

    def _path(self, key: str) -> Path:
        if len(key) != 64 or any(char not in "0123456789abcdef" for char in key):
            raise ValueError("cache key must be a SHA-256 hex digest")
        return self.directory / key[:2] / f"{key}.json"

    def get(self, key: str, *, now: float | None = None) -> TransportResponse | None:
        return self._read(key, now=now, allow_expired=False)

    def get_stale(
        self,
        key: str,
        *,
        max_age_seconds: float,
        now: float | None = None,
    ) -> TransportResponse | None:
        """Return an expired response only inside an explicit stale budget.

        Stale data is never returned by :meth:`get`.  Callers must opt in with
        a finite budget, which keeps ``stale-if-error`` observable and bounded.
        """

        if max_age_seconds < 0:
            raise ValueError("max_age_seconds must be non-negative")
        return self._read(
            key,
            now=now,
            allow_expired=True,
            max_stale_age=max_age_seconds,
        )

    def _read(
        self,
        key: str,
        *,
        now: float | None,
        allow_expired: bool,
        max_stale_age: float | None = None,
    ) -> TransportResponse | None:
        path = self._path(key)
        try:
            age = (time.time() if now is None else now) - path.stat().st_mtime
            if self.ttl_seconds is None:
                expired = False
            elif self.ttl_seconds == 0:
                # A zero TTL means "never fresh".  Do not compare mtimes to
                # the wall clock here: filesystem timestamp granularity and
                # clock skew can otherwise make a just-written entry appear
                # fresh for one request.
                expired = True
            else:
                expired = age > self.ttl_seconds
            if expired and not allow_expired:
                return None
            if allow_expired and max_stale_age is not None and age > max_stale_age:
                return None
            payload = json.loads(path.read_text(encoding="utf-8"))
            body = base64.b64decode(payload.pop("body_base64"), validate=True)
            if self.max_body_bytes is not None and len(body) > self.max_body_bytes:
                return None
            payload["body"] = body
            payload["redirects"] = tuple(payload.get("redirects") or ())
            payload["headers"] = dict(payload.get("headers") or {})
            payload["status"] = TransportStatus(payload.get("status", "complete"))
            return TransportResponse(**payload)
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError):
            return None

    def put(self, key: str, response: TransportResponse) -> Path:
        if self.max_body_bytes is not None and len(response.body) > self.max_body_bytes:
            raise ValueError("response body exceeds cache max_body_bytes")
        path = self._path(key)
        path.parent.mkdir(parents=True, exist_ok=True)
        payload = asdict(response)
        payload.pop("body", None)
        payload["body_base64"] = base64.b64encode(response.body).decode("ascii")
        payload["redirects"] = list(response.redirects)
        payload["status"] = response.status.value
        fd, temporary = tempfile.mkstemp(prefix=f".{path.name}.", suffix=".tmp", dir=path.parent)
        temporary_path = Path(temporary)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                json.dump(payload, stream, ensure_ascii=False, sort_keys=True)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary_path, path)
        finally:
            temporary_path.unlink(missing_ok=True)
        if self.max_total_bytes is not None:
            self.cleanup(max_bytes=self.max_total_bytes)
        return path

    def invalidate(self, key: str) -> bool:
        """Remove one cache entry and report whether it existed."""

        path = self._path(key)
        try:
            path.unlink()
        except FileNotFoundError:
            return False
        return True

    def cleanup(
        self,
        *,
        max_age_seconds: float | None = None,
        max_bytes: int | None = None,
        now: float | None = None,
    ) -> dict[str, int | list[str]]:
        """Bound cache growth by age and total bytes, oldest entries first."""

        if max_age_seconds is not None and max_age_seconds < 0:
            raise ValueError("max_age_seconds must be non-negative")
        if max_bytes is not None and max_bytes < 0:
            raise ValueError("max_bytes must be non-negative")
        current = time.time() if now is None else now
        entries: list[tuple[Path, float, int]] = []
        errors: list[str] = []
        for path in self.directory.glob("**/*.json"):
            try:
                if path.is_symlink() or path.resolve().parent == self.directory.resolve():
                    # Entries are sharded below the cache root; root-level
                    # files are ignored to avoid deleting unrelated data.
                    continue
                stat = path.stat()
                entries.append((path, stat.st_mtime, stat.st_size))
            except OSError as exc:
                errors.append(f"{path.name}: {type(exc).__name__}")
        entries.sort(key=lambda item: (item[1], str(item[0])))
        selected: set[Path] = set()
        if max_age_seconds is not None:
            cutoff = current - max_age_seconds
            selected.update(path for path, mtime, _size in entries if mtime < cutoff)
        remaining = [item for item in entries if item[0] not in selected]
        if max_bytes is not None:
            total = sum(size for _path, _mtime, size in remaining)
            for path, _mtime, size in remaining:
                if total <= max_bytes:
                    break
                selected.add(path)
                total -= size
        deleted_files = deleted_bytes = 0
        for path, _mtime, size in entries:
            if path not in selected:
                continue
            try:
                path.unlink()
                deleted_files += 1
                deleted_bytes += size
            except FileNotFoundError:
                continue
            except OSError as exc:
                errors.append(f"{path.name}: {type(exc).__name__}")
        return {
            "deleted_files": deleted_files,
            "deleted_bytes": deleted_bytes,
            "errors": errors,
        }
