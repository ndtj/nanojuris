"""Resilient selectors: relocate an element when a portal changes its HTML.

Court portals rewrite their markup without notice. A hard-coded CSS selector then
returns nothing and the provider silently looks "empty". This module ports the
adaptive-relocation technique from the Scrapling library
(``_StorageTools.element_to_dict`` plus ``Selector.__calculate_similarity_score``)
onto the NanoJuris parsing wrapper:

- ``element_fingerprint`` captures a structural signature of a node (tag,
  attributes, direct text, ancestor path, parent, siblings, children).
- ``similarity_score`` compares two fingerprints with ``difflib.SequenceMatcher``
  the same way Scrapling does, returning ``0.0``..``1.0``.
- ``SelectorMemory`` persists fingerprints to SQLite, keyed by ``(source, name)``.
- ``resilient_select`` runs the CSS selector; on a miss it relocates the closest
  structural match from the remembered fingerprint and records an **auditable**
  entry on the ``SourceTrace`` (``transformations`` when it recovers,
  ``limitations`` when it cannot). It never bypasses an access control and never
  fails silently.

No new dependencies: standard-library ``sqlite3`` and ``difflib`` only.
"""

from __future__ import annotations

import json
import sqlite3
import threading
from collections.abc import Mapping, Sequence
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

from nanojuris.parsing import HtmlDocument, HtmlNode, HtmlNodes

__all__ = [
    "element_fingerprint",
    "similarity_score",
    "SelectorMemory",
    "resilient_select",
    "resilient_find_all",
    "default_memory",
    "USE_DEFAULT_MEMORY",
    "DEFAULT_RELOCATE_THRESHOLD",
]

DEFAULT_RELOCATE_THRESHOLD = 0.40
_SEED_PATH = Path(__file__).parent / "data" / "selector_fingerprints.json"

_DEFAULT_MEMORY: SelectorMemory | None = None
_DEFAULT_MEMORY_LOCK = threading.Lock()
#: Passed as ``memory=`` to mean "use the shared process memory" (vs. an
#: explicit ``None``, which disables relocation).
USE_DEFAULT_MEMORY = object()
_USE_DEFAULT_MEMORY = USE_DEFAULT_MEMORY  # backwards-compatible internal alias


def default_memory() -> SelectorMemory:
    """Return the lazily-created process-wide selector memory."""

    global _DEFAULT_MEMORY
    if _DEFAULT_MEMORY is None:
        with _DEFAULT_MEMORY_LOCK:
            if _DEFAULT_MEMORY is None:
                _DEFAULT_MEMORY = SelectorMemory.open_default()
    return _DEFAULT_MEMORY


# --------------------------------------------------------------------------- #
# Fingerprint
# --------------------------------------------------------------------------- #
def _direct_text(node: HtmlNode) -> str:
    """Return only the text owned directly by ``node`` (not its descendants)."""

    element = node.element
    own = getattr(element, "text", None)
    if isinstance(own, str):  # lxml: leading text before the first child
        return own.strip()
    find_all = getattr(element, "find_all", None)  # BeautifulSoup
    if callable(find_all):
        try:
            parts = [str(item) for item in element.find_all(string=True, recursive=False)]
        except TypeError:  # pragma: no cover - very old bs4
            parts = [str(item) for item in element.find_all(text=True, recursive=False)]
        return " ".join(" ".join(parts).split())
    return ""


def _clean_attributes(node: HtmlNode) -> dict[str, str]:
    attrs = getattr(node.element, "attrib", None) or getattr(node.element, "attrs", {}) or {}
    result: dict[str, str] = {}
    for key, value in dict(attrs).items():
        if isinstance(value, (list, tuple)):
            value = " ".join(str(item) for item in value)
        text = str(value).strip()
        if text:
            result[str(key)] = text
    return result


def _ancestor_path(node: HtmlNode) -> tuple[str, ...]:
    path: list[str] = []
    current: HtmlNode | None = node
    while current is not None:
        tag = current.tag.lower()
        if not tag or tag in {"[document]", "html"}:
            break
        path.append(tag)
        current = current.parent
    return tuple(reversed(path))


def element_fingerprint(node: HtmlNode) -> dict[str, Any]:
    """Structural signature of a node, comparable across markup revisions."""

    parent = node.parent
    fingerprint: dict[str, Any] = {
        "tag": node.tag.lower(),
        "attributes": _clean_attributes(node),
        "text": _direct_text(node)[:500],
        "path": list(_ancestor_path(node)),
        "children": [child.tag.lower() for child in node.children if child.tag],
    }
    if parent is not None:
        siblings = [
            child.tag.lower()
            for child in parent.children
            if child.tag and child.element is not node.element
        ]
        fingerprint.update(
            parent_name=parent.tag.lower(),
            parent_attributes=_clean_attributes(parent),
            parent_text=_direct_text(parent)[:500],
            siblings=siblings,
        )
    return fingerprint


# --------------------------------------------------------------------------- #
# Similarity (faithful to Scrapling's __calculate_similarity_score)
# --------------------------------------------------------------------------- #
def _ratio(left: Sequence[Any] | str, right: Sequence[Any] | str) -> float:
    return SequenceMatcher(None, left, right).ratio()


def _dict_diff(left: Mapping[str, str], right: Mapping[str, str]) -> float:
    keys = _ratio(tuple(left.keys()), tuple(right.keys())) * 0.5
    values = _ratio(tuple(left.values()), tuple(right.values())) * 0.5
    return keys + values


def similarity_score(reference: Mapping[str, Any], candidate: Mapping[str, Any]) -> float:
    """Return how similar ``candidate`` is to ``reference`` on a 0..1 scale."""

    ref_attrs: Mapping[str, str] = reference.get("attributes") or {}
    cand_attrs: Mapping[str, str] = candidate.get("attributes") or {}

    score = 0.0
    checks = 0

    score += 1.0 if reference.get("tag") == candidate.get("tag") else 0.0
    checks += 1

    if reference.get("text"):
        score += _ratio(reference["text"], candidate.get("text") or "")
        checks += 1

    score += _dict_diff(ref_attrs, cand_attrs)
    checks += 1

    for attribute in ("class", "id", "href", "src"):
        if ref_attrs.get(attribute):
            score += _ratio(ref_attrs[attribute], cand_attrs.get(attribute) or "")
            checks += 1

    score += _ratio(tuple(reference.get("path") or ()), tuple(candidate.get("path") or ()))
    checks += 1

    if reference.get("parent_name"):
        if candidate.get("parent_name"):
            score += _ratio(reference["parent_name"], candidate.get("parent_name") or "")
            checks += 1
            score += _dict_diff(
                reference.get("parent_attributes") or {},
                candidate.get("parent_attributes") or {},
            )
            checks += 1
            if reference.get("parent_text"):
                score += _ratio(reference["parent_text"], candidate.get("parent_text") or "")
                checks += 1

    if reference.get("siblings"):
        score += _ratio(
            tuple(reference["siblings"]),
            tuple(candidate.get("siblings") or ()),
        )
        checks += 1

    return round(score / checks, 4) if checks else 0.0


# --------------------------------------------------------------------------- #
# Persistence
# --------------------------------------------------------------------------- #
class SelectorMemory:
    """SQLite-backed fingerprint store, keyed by ``(source, name)``.

    Seeded from ``data/selector_fingerprints.json`` so a fresh install can
    already relocate the wired selectors. Pass ``path=":memory:"`` for tests or
    an ephemeral cache.
    """

    def __init__(self, path: str | Path = ":memory:", *, seed: bool = True) -> None:
        self._lock = threading.RLock()
        self._path = str(path)
        self._connection = sqlite3.connect(self._path, check_same_thread=False)
        self._connection.execute(
            "CREATE TABLE IF NOT EXISTS selector_fingerprints ("
            "source TEXT NOT NULL, name TEXT NOT NULL, fingerprint TEXT NOT NULL, "
            "updated_at TEXT NOT NULL DEFAULT (datetime('now')), "
            "PRIMARY KEY (source, name))"
        )
        self._connection.commit()
        if seed:
            self._load_seed()

    @classmethod
    def open_default(cls) -> SelectorMemory:
        """Persistent memory under the user home, falling back to in-memory."""

        try:
            directory = Path.home() / ".nanojuris"
            directory.mkdir(parents=True, exist_ok=True)
            return cls(directory / "selectors.db")
        except OSError:
            return cls(":memory:")

    def _load_seed(self) -> None:
        if not _SEED_PATH.is_file():
            return
        try:
            seed = json.loads(_SEED_PATH.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return
        for source, names in seed.items():
            for name, fingerprint in names.items():
                self._connection.execute(
                    "INSERT OR IGNORE INTO selector_fingerprints (source, name, fingerprint) "
                    "VALUES (?, ?, ?)",
                    (source, name, json.dumps(fingerprint, sort_keys=True)),
                )
        self._connection.commit()

    def save(self, source: str, name: str, fingerprint: Mapping[str, Any]) -> None:
        payload = json.dumps(fingerprint, sort_keys=True)
        with self._lock:
            self._connection.execute(
                "INSERT INTO selector_fingerprints (source, name, fingerprint) VALUES (?, ?, ?) "
                "ON CONFLICT(source, name) DO UPDATE SET "
                "fingerprint = excluded.fingerprint, updated_at = datetime('now')",
                (source, name, payload),
            )
            self._connection.commit()

    def load(self, source: str, name: str) -> dict[str, Any] | None:
        with self._lock:
            row = self._connection.execute(
                "SELECT fingerprint FROM selector_fingerprints WHERE source = ? AND name = ?",
                (source, name),
            ).fetchone()
        if not row:
            return None
        try:
            return json.loads(row[0])
        except ValueError:  # pragma: no cover - corrupt row
            return None

    def close(self) -> None:
        with self._lock:
            self._connection.close()


# --------------------------------------------------------------------------- #
# Orchestration
# --------------------------------------------------------------------------- #
def resilient_select(
    document: HtmlDocument,
    selector: str,
    *,
    name: str,
    source: str,
    memory: Any = _USE_DEFAULT_MEMORY,
    threshold: float = DEFAULT_RELOCATE_THRESHOLD,
    trace: Any | None = None,
) -> HtmlNodes:
    """Run ``selector``; relocate the closest structural match on a miss.

    ``name`` identifies the selector for the fingerprint store (for example
    ``"result_row"``). When the selector matches, the first hit's fingerprint is
    remembered. When it does not, the remembered fingerprint drives a structural
    search; a recovery is recorded on ``trace.transformations`` and a total miss
    on ``trace.limitations``.
    """

    memory = _resolve_memory(memory)
    nodes = document.select(selector)
    if nodes:
        _remember(memory, source, name, nodes.first, element_fingerprint)
        return nodes
    if memory is None or not (reference := memory.load(source, name)):
        return nodes

    relocated = _relocate(
        list(document._all_nodes()),
        reference,
        fingerprint_fn=element_fingerprint,
        threshold=threshold,
        name=name,
        trace=trace,
    )
    return HtmlNodes(relocated, document) if relocated else nodes


def resilient_find_all(
    soup: Any,
    selector: str,
    *,
    name: str,
    source: str,
    memory: Any = _USE_DEFAULT_MEMORY,
    threshold: float = DEFAULT_RELOCATE_THRESHOLD,
    trace: Any | None = None,
) -> list[Any]:
    """BeautifulSoup-native ``resilient_select``.

    For providers that already hold a ``BeautifulSoup``/``Tag`` and parse rows
    with bs4. Returns a list of ``Tag`` objects, relocating by structure when the
    CSS selector stops matching. Same auditing contract on ``trace``.
    """

    memory = _resolve_memory(memory)
    hits = list(soup.select(selector))
    if hits:
        _remember(memory, source, name, hits[0], _bs4_fingerprint)
        return hits
    if memory is None or not (reference := memory.load(source, name)):
        return hits

    root = soup if getattr(soup, "name", None) else getattr(soup, "root", soup)
    candidates = [tag for tag in root.find_all(True)]
    return _relocate(
        candidates,
        reference,
        fingerprint_fn=_bs4_fingerprint,
        threshold=threshold,
        name=name,
        trace=trace,
    )


def _resolve_memory(memory: Any) -> SelectorMemory | None:
    if memory is _USE_DEFAULT_MEMORY:
        try:
            return default_memory()
        except Exception:  # pragma: no cover - never fatal
            return None
    return memory


def _remember(
    memory: SelectorMemory | None,
    source: str,
    name: str,
    element: Any,
    fingerprint_fn: Any,
) -> None:
    if memory is None or element is None:
        return
    try:
        memory.save(source, name, fingerprint_fn(element))
    except (sqlite3.Error, AttributeError, TypeError):  # pragma: no cover - never fatal
        pass


def _relocate(
    candidates: list[Any],
    reference: Mapping[str, Any],
    *,
    fingerprint_fn: Any,
    threshold: float,
    name: str,
    trace: Any | None,
) -> list[Any]:
    if not candidates:
        return []
    fingerprints = [fingerprint_fn(candidate) for candidate in candidates]
    scores = [similarity_score(reference, fingerprint) for fingerprint in fingerprints]
    best_index = max(range(len(scores)), key=scores.__getitem__)
    best_score = scores[best_index]

    if best_score < threshold:
        if trace is not None and hasattr(trace, "limitations"):
            trace.limitations.append(
                f"Selector '{name}' matched nothing and no element scored above "
                f"{threshold:.2f} for structural relocation (best {best_score:.2f}); "
                "the source layout likely changed."
            )
        return []

    best_fingerprint = fingerprints[best_index]
    sibling_threshold = max(threshold, 0.6)
    matched_indexes = [best_index]
    matched_indexes.extend(
        index
        for index in range(len(candidates))
        if index != best_index
        and similarity_score(best_fingerprint, fingerprints[index]) >= sibling_threshold
    )
    matched_indexes.sort()  # keep document order
    matches = [candidates[index] for index in matched_indexes]
    if trace is not None and hasattr(trace, "transformations"):
        trace.transformations.append(
            f"Selector '{name}' relocated by structural similarity "
            f"(score {best_score:.2f}, {len(matches)} node(s)); update the hard-coded selector."
        )
    return matches


def _bs4_fingerprint(tag: Any) -> dict[str, Any]:
    """``element_fingerprint`` for a raw BeautifulSoup ``Tag``."""

    def attrs(node: Any) -> dict[str, str]:
        result: dict[str, str] = {}
        for key, value in (getattr(node, "attrs", {}) or {}).items():
            if isinstance(value, (list, tuple)):
                value = " ".join(str(item) for item in value)
            text = str(value).strip()
            if text:
                result[str(key)] = text
        return result

    def direct_text(node: Any) -> str:
        find_all = getattr(node, "find_all", None)
        if not callable(find_all):
            return ""
        try:
            parts = [str(item) for item in node.find_all(string=True, recursive=False)]
        except TypeError:  # pragma: no cover
            parts = [str(item) for item in node.find_all(text=True, recursive=False)]
        return " ".join(" ".join(parts).split())[:500]

    path: list[str] = []
    current = tag
    _stop = (None, "[document]", "html")
    while current is not None and getattr(current, "name", None) not in _stop:
        path.append(str(current.name).lower())
        current = current.parent
    path.reverse()

    fingerprint: dict[str, Any] = {
        "tag": str(tag.name).lower(),
        "attributes": attrs(tag),
        "text": direct_text(tag),
        "path": path,
        "children": [str(child.name).lower() for child in tag.find_all(True, recursive=False)],
    }
    parent = tag.parent
    if parent is not None and getattr(parent, "name", None):
        fingerprint.update(
            parent_name=str(parent.name).lower(),
            parent_attributes=attrs(parent),
            parent_text=direct_text(parent),
            siblings=[
                str(sib.name).lower()
                for sib in parent.find_all(True, recursive=False)
                if sib is not tag
            ],
        )
    return fingerprint
