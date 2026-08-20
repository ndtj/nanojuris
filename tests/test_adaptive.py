import sqlite3

from nanojuris.adaptive import SelectorMemory
from nanojuris.parsing import parse_html


def test_selector_memory_requires_approval_before_resolution() -> None:
    document = parse_html(b'<main><p id="ementa">Texto da ementa</p></main>')
    with SelectorMemory(sqlite3.connect(":memory:")) as memory:
        entry = memory.remember(
            document,
            source="fixture",
            field="summary",
            selector="#ementa",
            matches=1,
            confidence=0.9,
            evidence="fixture local",
        )
        assert memory.resolve(document, source="fixture", field="summary") == []
        approved = memory.approve(entry.id)
        assert approved.approved is True
        assert [node.text() for node in memory.resolve(document, source="fixture", field="summary")] == [
            "Texto da ementa"
        ]
