from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest
from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT / "tools") not in sys.path:
    sys.path.insert(0, str(ROOT / "tools"))

from build_selector_fingerprints import REGISTRY, build  # noqa: E402

from nanojuris.adaptive_selectors import (  # noqa: E402
    SelectorMemory,
    resilient_find_all,
    resilient_select,
    similarity_score,
)
from nanojuris.parsing import parse_html  # noqa: E402

FIXTURES = ROOT / "tests" / "fixtures"
SEED = ROOT / "src" / "nanojuris" / "data" / "selector_fingerprints.json"

_IDS = [f"{source}:{name}" for source, name, *_ in REGISTRY]


def _fixture(name: str) -> str:
    return (FIXTURES / name).read_text(encoding="utf-8", errors="replace")


def _discriminating_token(selector: str) -> str:
    """The class or id token a relocation should be able to survive losing."""

    tokens = re.findall(r"[#.]([A-Za-z0-9_-]+)", selector.split(",")[0])
    assert tokens, selector
    return tokens[-1]


def test_seed_file_matches_the_registry() -> None:
    on_disk = json.loads(SEED.read_text(encoding="utf-8"))
    expected = build()
    assert on_disk == expected, "run: python tools/build_selector_fingerprints.py --write"


def test_seed_fingerprints_are_self_consistent() -> None:
    catalog = json.loads(SEED.read_text(encoding="utf-8"))
    for source, names in catalog.items():
        for name, fingerprint in names.items():
            score = similarity_score(fingerprint, fingerprint)
            assert score >= 0.99, f"{source}:{name} scored {score} against itself"


@pytest.mark.parametrize(("source", "name", "fixture", "selector", "backend"), REGISTRY, ids=_IDS)
def test_wired_selector_relocates_when_its_token_is_removed(
    source: str, name: str, fixture: str, selector: str, backend: str
) -> None:
    html = _fixture(fixture)
    memory = SelectorMemory(":memory:", seed=False)

    class _Trace:
        transformations: list[str] = []
        limitations: list[str] = []

    if backend == "bs4":
        baseline = list(BeautifulSoup(html, "html.parser").select(selector))
    else:
        baseline = list(parse_html(html).select(selector))
    assert baseline, f"fixture {fixture} no longer matches {selector!r}"

    # Prime the fingerprint from the working page.
    if backend == "bs4":
        resilient_find_all(
            BeautifulSoup(html, "html.parser"), selector, name=name, source=source, memory=memory
        )
    else:
        resilient_select(parse_html(html), selector, name=name, source=source, memory=memory)

    token = _discriminating_token(selector)
    # A replacement that shares no substring, so ``[attr*=token]`` also stops matching.
    changed = html.replace(token, "wxyzRelocated")
    trace = _Trace()
    if backend == "bs4":
        assert not BeautifulSoup(changed, "html.parser").select(selector)
        recovered = resilient_find_all(
            BeautifulSoup(changed, "html.parser"),
            selector,
            name=name,
            source=source,
            memory=memory,
            trace=trace,
        )
    else:
        assert not parse_html(changed).select(selector)
        recovered = list(
            resilient_select(
                parse_html(changed),
                selector,
                name=name,
                source=source,
                memory=memory,
                trace=trace,
            )
        )

    assert recovered, f"{source}:{name} could not be relocated after losing {token!r}"
    assert (
        trace.transformations and "relocated by structural similarity" in trace.transformations[0]
    )
