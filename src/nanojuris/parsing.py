"""Shared, bounded HTML/JSON parsing primitives for provider adapters.

The public API intentionally stays smaller than a general scraping framework:
it provides reusable node operations for jurisprudence parsers while keeping
selector recovery and similarity as reviewable suggestions.
"""

from __future__ import annotations

import json
import re
from collections.abc import Callable, Iterable
from dataclasses import dataclass, field
from hashlib import sha256
from typing import Any, Literal
from urllib.parse import urljoin

from bs4 import BeautifulSoup, Tag

try:  # Optional performance backend.
    from lxml import etree, html as lxml_html
except ImportError:  # pragma: no cover - exercised in minimal installations
    etree = None  # type: ignore[assignment]
    lxml_html = None  # type: ignore[assignment]

try:  # cssselect is optional even when lxml is present.
    from lxml.cssselect import CSSSelector
except ImportError:  # pragma: no cover - environment dependent
    CSSSelector = None  # type: ignore[assignment,misc]


Backend = Literal["lxml", "beautifulsoup"]
_SAFE_SELECTOR_PART = re.compile(r"^[A-Za-z_][A-Za-z0-9_-]*$")


@dataclass(slots=True)
class HtmlDocument:
    """Parsed HTML document with a stable provider-facing interface."""

    raw: bytes
    base_url: str = ""
    max_bytes: int = 10_000_000
    _backend: Backend = field(init=False)
    _root: Any = field(init=False, repr=False)
    _soup: BeautifulSoup | None = field(init=False, default=None, repr=False)

    def __post_init__(self) -> None:
        if len(self.raw) > self.max_bytes:
            raise ValueError("HTML excede o limite de bytes do parser")
        if lxml_html is not None:
            parser = etree.HTMLParser(recover=True, no_network=True, huge_tree=False)
            try:
                source: str | bytes = self.raw.decode("utf-8")
            except UnicodeDecodeError:
                source = self.raw
            # lxml rejects a Unicode string that still contains an XML encoding
            # declaration. Remove only that declaration; the page content is
            # already decoded and no external resource is consulted.
            if isinstance(source, str):
                source = re.sub(r"^\s*<\?xml[^>]*\?>", "", source, count=1, flags=re.I)
            if not source or not source.strip():
                source = "<html></html>"
            try:
                self._root = lxml_html.fromstring(source, parser=parser)
                self._backend = "lxml"
            except (etree.ParserError, ValueError):
                # Some public endpoints return malformed/empty fragments with
                # a successful status. Keep the observation usable through
                # the permissive fallback instead of dropping the provider.
                fallback = source if isinstance(source, str) else source.decode("utf-8", errors="replace")
                self._soup = BeautifulSoup(fallback, "html.parser")
                self._root = self._soup
                self._backend = "beautifulsoup"
        else:
            try:
                source = self.raw.decode("utf-8")
            except UnicodeDecodeError:
                source = self.raw
            self._soup = BeautifulSoup(source, "html.parser")
            self._root = self._soup
            self._backend = "beautifulsoup"

    @classmethod
    def from_text(
        cls,
        text: str,
        *,
        base_url: str = "",
        max_bytes: int = 10_000_000,
        encoding: str = "utf-8",
    ) -> "HtmlDocument":
        return cls(text.encode(encoding, errors="replace"), base_url=base_url, max_bytes=max_bytes)

    @property
    def backend(self) -> Backend:
        """Return the active parser backend."""

        return self._backend

    @property
    def sha256(self) -> str:
        """Return the fingerprint of the exact captured bytes."""

        return sha256(self.raw).hexdigest()

    def text(self, separator: str = " ") -> str:
        return _clean_text(self._root_text(self._root), separator=separator)

    def get_text(self, separator: str = " ", strip: bool = True) -> str:
        value = self.text(separator=separator)
        return value.strip() if strip else value

    def visible_text(self, separator: str = " ") -> str:
        """Return visible text while excluding script/style-like containers."""

        soup = BeautifulSoup(self._markup(), "html.parser")
        for node in soup(("script", "style", "noscript", "template")):
            node.decompose()
        return _clean_text(soup.get_text(separator, strip=True), separator=separator)

    @property
    def title(self) -> str | None:
        node = self.select_one("title")
        return node.text(strip=True) if node is not None else None

    def css(self, selector: str) -> "HtmlNodes":
        """Select nodes with CSS, using lxml when cssselect is installed."""

        if not selector or not selector.strip():
            return HtmlNodes([], self)
        if self._backend == "lxml" and CSSSelector is not None:
            try:
                elements = CSSSelector(selector)(self._root)
            except (etree.XPathError, ValueError) as exc:
                raise ValueError(f"Seletor CSS inválido: {selector}") from exc
            return HtmlNodes([self._wrap(item) for item in elements], self)
        soup = self._get_soup()
        try:
            return HtmlNodes([self._wrap(item) for item in soup.select(selector)], self)
        except Exception as exc:  # BeautifulSoup exposes multiple selector errors.
            raise ValueError(f"Seletor CSS inválido: {selector}") from exc

    def select(self, selector: str) -> "HtmlNodes":
        """BeautifulSoup-compatible alias used by migrated provider parsers."""

        return self.css(selector)

    def select_one(self, selector: str) -> "HtmlNode | None":
        return self.css(selector).first

    def xpath(self, expression: str) -> "HtmlNodes":
        """Select nodes with XPath when the optional lxml backend is active."""

        if self._backend != "lxml" or etree is None:
            raise RuntimeError("XPath exige a dependência opcional lxml")
        try:
            values = self._root.xpath(expression)
        except etree.XPathError as exc:
            raise ValueError(f"XPath inválido: {expression}") from exc
        return HtmlNodes([self._wrap(value) for value in values if _is_node(value)], self)

    def find_by_text(
        self,
        text: str,
        *,
        exact: bool = False,
        case_sensitive: bool = False,
        limit: int | None = None,
    ) -> "HtmlNodes":
        """Find the smallest structural elements containing a text label."""

        needle = _clean_text(text)
        if not needle:
            return HtmlNodes([], self)
        if not case_sensitive:
            needle = needle.casefold()
        matches: list[HtmlNode] = []
        for node in self._all_nodes():
            value = node.text()
            comparable = value if case_sensitive else value.casefold()
            found = comparable == needle if exact else needle in comparable
            if found:
                matches.append(node)
        matches.sort(key=lambda item: (len(item.text()), -item.depth, 0 if item.get("id") else 1))
        return HtmlNodes(matches[:limit] if limit is not None else matches, self)

    def find_by_regex(
        self,
        pattern: str | re.Pattern[str],
        *,
        flags: int = 0,
        limit: int | None = None,
    ) -> "HtmlNodes":
        compiled = re.compile(pattern, flags) if isinstance(pattern, str) else pattern
        matches = [node for node in self._all_nodes() if compiled.search(node.text())]
        return HtmlNodes(matches[:limit] if limit is not None else matches, self)

    def links(self) -> "HtmlNodes":
        return self.css("a[href]")

    def forms(self) -> "HtmlNodes":
        return self.css("form")

    def json(self) -> Any:
        return json.loads(self.raw.decode("utf-8", errors="replace"))

    def _get_soup(self) -> BeautifulSoup:
        if self._soup is None:
            self._soup = BeautifulSoup(self._markup(), "html.parser")
        return self._soup

    def _markup(self) -> str:
        if self._backend == "lxml" and etree is not None:
            # Re-serialize as Unicode so a legacy source charset declared in
            # the original markup cannot reinterpret already-decoded text.
            return etree.tostring(self._root, encoding="unicode", method="html")
        return str(self._root)

    def _wrap(self, value: Any) -> "HtmlNode":
        return HtmlNode(value, self)

    def _all_nodes(self) -> list["HtmlNode"]:
        if self._backend == "lxml":
            return [self._wrap(item) for item in self._root.iter() if _is_node(item)]
        soup = self._get_soup()
        return [self._wrap(item) for item in soup.find_all(True)]

    @staticmethod
    def _root_text(value: Any) -> str:
        if callable(getattr(value, "text_content", None)):
            return str(value.text_content())
        if callable(getattr(value, "itertext", None)):
            return " ".join(str(item) for item in value.itertext())
        if hasattr(value, "get_text"):
            return str(value.get_text(" ", strip=True))
        return str(value or "")


@dataclass(slots=True)
class HtmlNode:
    """Wrapper around one lxml or BeautifulSoup element."""

    element: Any
    document: HtmlDocument

    @property
    def tag(self) -> str:
        return str(getattr(self.element, "tag", None) or getattr(self.element, "name", ""))

    @property
    def depth(self) -> int:
        if hasattr(self.element, "iterancestors"):
            return sum(1 for _ in self.element.iterancestors())
        return sum(1 for _ in getattr(self.element, "parents", ()))

    def text(self, separator: str = " ", strip: bool = True) -> str:
        if callable(getattr(self.element, "text_content", None)):
            value = str(self.element.text_content())
        elif callable(getattr(self.element, "itertext", None)):
            value = separator.join(str(item) for item in self.element.itertext())
        elif hasattr(self.element, "get_text"):
            value = str(self.element.get_text(separator, strip=strip))
        else:
            value = str(self.element or "")
        return _clean_text(value, separator=separator) if strip else value

    def get_text(self, separator: str = " ", strip: bool = True) -> str:
        return self.text(separator=separator, strip=strip)

    def visible_text(self, separator: str = " ") -> str:
        """Return visible text for this node, excluding script-like children."""

        return parse_html(self.html, max_bytes=max(len(self.html.encode("utf-8")), 1)).visible_text(separator)

    def get(self, attribute: str, default: str | None = None) -> str | None:
        value = self.element.get(attribute) if hasattr(self.element, "get") else None
        return str(value) if value is not None else default

    def __getitem__(self, attribute: str) -> str:
        value = self.get(attribute)
        if value is None:
            raise KeyError(attribute)
        return value

    @property
    def html(self) -> str:
        if isinstance(self.element, Tag):
            return str(self.element)
        if hasattr(self.element, "getroottree"):
            return etree.tostring(self.element, encoding="unicode", method="html")
        return str(self.element)

    @property
    def parent(self) -> "HtmlNode | None":
        getparent = getattr(self.element, "getparent", None)
        parent = getparent() if callable(getparent) else None
        if parent is None:
            parent = getattr(self.element, "parent", None)
        return self.document._wrap(parent) if parent is not None and _is_node(parent) else None

    def find_parent(self, tag: str | None = None) -> "HtmlNode | None":
        """Return the closest ancestor matching an optional tag name."""

        current = self.parent
        expected = tag.casefold() if tag else None
        while current is not None:
            if expected is None or current.tag.casefold() == expected:
                return current
            current = current.parent
        return None

    @property
    def children(self) -> "HtmlNodes":
        if hasattr(self.element, "iterchildren"):
            items = list(self.element.iterchildren())
        else:
            items = [item for item in self.element.children if _is_node(item)]
        return HtmlNodes([self.document._wrap(item) for item in items], self.document)

    def css(self, selector: str) -> "HtmlNodes":
        if isinstance(self.element, Tag):
            return HtmlNodes(
                [self.document._wrap(item) for item in self.element.select(selector)],
                self.document,
            )
        if self.document._backend == "lxml" and CSSSelector is not None:
            return HtmlNodes(
                [self.document._wrap(item) for item in CSSSelector(selector)(self.element)],
                self.document,
            )
        soup = BeautifulSoup(self.html, "html.parser")
        return HtmlNodes(
            [self.document._wrap(item) for item in soup.select(selector)],
            self.document,
        )

    def select(self, selector: str) -> "HtmlNodes":
        return self.css(selector)

    def select_one(self, selector: str) -> "HtmlNode | None":
        return self.css(selector).first

    def xpath(self, expression: str) -> "HtmlNodes":
        if not hasattr(self.element, "xpath"):
            return self.document.xpath(expression)
        return HtmlNodes(
            [
                self.document._wrap(item)
                for item in self.element.xpath(expression)
                if _is_node(item)
            ],
            self.document,
        )

    def urljoin(self, value: str | None) -> str | None:
        return urljoin(self.document.base_url, value) if value else None

    def generate_css_selector(self) -> str:
        """Generate a compact structural selector for review or memory."""

        parts: list[str] = []
        current: HtmlNode | None = self
        while current is not None and current.tag and current.tag not in {"html", "[document]"}:
            part = _selector_part(current)
            parts.append(part)
            if current.get("id"):
                break
            current = current.parent
        return " > ".join(reversed(parts)) or self.tag

    def signature(self) -> dict[str, Any]:
        classes = tuple(sorted((self.get("class") or "").split()))
        return {
            "tag": self.tag.lower(),
            "id": self.get("id"),
            "classes": classes,
            "attributes": tuple(sorted(_attribute_names(self.element))),
            "parent_tag": self.parent.tag.lower() if self.parent else None,
            "text_length": len(self.text()),
        }

    def find_similar(
        self,
        *,
        threshold: float = 0.65,
        limit: int = 10,
        within: HtmlDocument | None = None,
    ) -> "HtmlNodes":
        """Suggest structurally similar nodes without changing a parser."""

        reference = self.signature()
        document = within or self.document
        scored = [
            (score, node)
            for node in document._all_nodes()
            if (score := _similarity(reference, node.signature())) >= threshold
        ]
        scored.sort(key=lambda item: (-item[0], len(item[1].text()), item[1].depth))
        return HtmlNodes([node for _, node in scored[:limit]], document)


class HtmlNodes(list[HtmlNode]):
    """List-like selector result with parser-friendly conveniences."""

    def __init__(self, values: Iterable[HtmlNode], document: HtmlDocument):
        super().__init__(values)
        self.document = document

    @property
    def first(self) -> HtmlNode | None:
        return self[0] if self else None

    @property
    def last(self) -> HtmlNode | None:
        return self[-1] if self else None

    def get(self, default: str | None = None) -> str | None:
        return self.first.text() if self.first is not None else default

    def getall(self) -> list[str]:
        return [item.text() for item in self]

    def attrs(self, name: str) -> list[str | None]:
        return [item.get(name) for item in self]

    def css(self, selector: str) -> "HtmlNodes":
        return HtmlNodes(
            [child for item in self for child in item.css(selector)],
            self.document,
        )

    def xpath(self, expression: str) -> "HtmlNodes":
        return HtmlNodes(
            [child for item in self for child in item.xpath(expression)],
            self.document,
        )

    def filter(self, predicate: Callable[[HtmlNode], bool]) -> "HtmlNodes":
        return HtmlNodes((item for item in self if predicate(item)), self.document)


def parse_html(
    content: bytes | str,
    *,
    base_url: str = "",
    max_bytes: int = 10_000_000,
    encoding: str = "utf-8",
) -> HtmlDocument:
    """Parse HTML with bounded input and an optional high-performance backend."""

    raw = content.encode(encoding, errors="replace") if isinstance(content, str) else bytes(content)
    return HtmlDocument(raw, base_url=base_url, max_bytes=max_bytes)


def _clean_text(value: str, *, separator: str = " ") -> str:
    return separator.join(value.replace("\xa0", " ").split()).strip()


def _is_node(value: Any) -> bool:
    if isinstance(value, Tag):
        return True
    tag = getattr(value, "tag", None)
    # lxml comments/PIs expose a non-string callable tag and are not HTML
    # elements. Excluding them prevents selector and text traversal crashes.
    return isinstance(tag, str)


def _attribute_names(element: Any) -> Iterable[str]:
    attrs = getattr(element, "attrib", None)
    if attrs is not None:
        return attrs.keys()
    return getattr(element, "attrs", {}).keys()


def _selector_part(node: HtmlNode) -> str:
    tag = node.tag.lower() or "*"
    identifier = node.get("id")
    if identifier and _SAFE_SELECTOR_PART.fullmatch(identifier):
        return f"#{identifier}"
    classes = [
        item
        for item in (node.get("class") or "").split()
        if _SAFE_SELECTOR_PART.fullmatch(item)
    ]
    part = tag + "".join(f".{item}" for item in classes[:3])
    if node.parent is not None:
        siblings = [item for item in node.parent.children if item.tag.lower() == tag]
        if len(siblings) > 1:
            index = next(
                (idx for idx, item in enumerate(siblings, 1) if item.element is node.element),
                1,
            )
            part += f":nth-of-type({index})"
    return part


def _similarity(reference: dict[str, Any], candidate: dict[str, Any]) -> float:
    score = 0.0
    if reference["tag"] == candidate["tag"]:
        score += 0.25
    if reference["id"] and reference["id"] == candidate["id"]:
        score += 0.25
    reference_classes = set(reference["classes"])
    candidate_classes = set(candidate["classes"])
    if reference_classes or candidate_classes:
        union = reference_classes | candidate_classes
        score += 0.25 * (len(reference_classes & candidate_classes) / len(union) if union else 0)
    reference_attrs = set(reference["attributes"])
    candidate_attrs = set(candidate["attributes"])
    if reference_attrs or candidate_attrs:
        union = reference_attrs | candidate_attrs
        score += 0.15 * (len(reference_attrs & candidate_attrs) / len(union) if union else 0)
    if reference["parent_tag"] == candidate["parent_tag"]:
        score += 0.05
    if abs(reference["text_length"] - candidate["text_length"]) <= max(
        20, reference["text_length"] * 0.2
    ):
        score += 0.05
    return min(score, 1.0)


__all__ = ["HtmlDocument", "HtmlNode", "HtmlNodes", "parse_html"]
