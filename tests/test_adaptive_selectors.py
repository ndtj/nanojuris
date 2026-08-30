from __future__ import annotations

from nanojuris.adaptive_selectors import (
    SelectorMemory,
    element_fingerprint,
    resilient_select,
    similarity_score,
)
from nanojuris.parsing import parse_html

_V1 = """
<html><body><section class="results">
  <article class="card acordao" data-kind="row"><h2>Alfa</h2>
    <p class="ementa">RESPONSABILIDADE CIVIL. Dano moral in re ipsa.</p></article>
  <article class="card acordao" data-kind="row"><h2>Beta</h2>
    <p class="ementa">CONTRATO. Rescisao unilateral.</p></article>
</section></body></html>
"""

# Same page after a layout revision: wrapper and row class renamed, tags kept.
_V2 = """
<html><body><section class="lista-resultados">
  <article class="cartao-julgado" data-kind="row"><h2>Gama</h2>
    <p class="texto-ementa">APELACAO CIVEL. Indenizacao por dano moral.</p></article>
  <article class="cartao-julgado" data-kind="row"><h2>Delta</h2>
    <p class="texto-ementa">EXECUCAO FISCAL. Nulidade da CDA.</p></article>
</section></body></html>
"""


class _Trace:
    def __init__(self) -> None:
        self.transformations: list[str] = []
        self.limitations: list[str] = []


def test_fingerprint_captures_structure() -> None:
    node = parse_html(_V1).select("article.card").first
    fingerprint = element_fingerprint(node)

    assert fingerprint["tag"] == "article"
    assert fingerprint["attributes"]["class"] == "card acordao"
    assert fingerprint["attributes"]["data-kind"] == "row"
    assert fingerprint["path"][-1] == "article"
    assert fingerprint["parent_name"] == "section"
    assert "h2" in fingerprint["children"] and "p" in fingerprint["children"]


def test_similarity_score_is_high_for_a_renamed_class_same_structure() -> None:
    reference = element_fingerprint(parse_html(_V1).select("article.card").first)
    moved = element_fingerprint(parse_html(_V2).select("article.cartao-julgado").first)
    unrelated = element_fingerprint(parse_html(_V1).select("h2").first)

    assert similarity_score(reference, moved) > 0.55
    assert similarity_score(reference, moved) > similarity_score(reference, unrelated)


def test_selector_memory_round_trips_and_seeds_from_package() -> None:
    memory = SelectorMemory(":memory:", seed=False)
    assert memory.load("demo", "row") is None
    memory.save("demo", "row", {"tag": "article", "attributes": {}})
    assert memory.load("demo", "row")["tag"] == "article"

    seeded = SelectorMemory(":memory:")
    # The shipped seed carries the wired tjdf selector.
    assert seeded.load("tjdf_juris", "acordao_link") is not None


def test_resilient_select_relocates_after_a_layout_change() -> None:
    memory = SelectorMemory(":memory:", seed=False)

    hit = resilient_select(
        parse_html(_V1), "article.card.acordao", name="row", source="demo", memory=memory
    )
    assert len(hit) == 2

    trace = _Trace()
    recovered = resilient_select(
        parse_html(_V2),
        "article.card.acordao",  # no longer matches anything
        name="row",
        source="demo",
        memory=memory,
        trace=trace,
    )
    assert len(recovered) == 2
    assert {node.select_one("h2").text() for node in recovered} == {"Gama", "Delta"}
    assert (
        trace.transformations and "relocated by structural similarity" in trace.transformations[0]
    )
    assert trace.limitations == []


def test_resilient_select_reports_an_unrecoverable_layout_change() -> None:
    memory = SelectorMemory(":memory:", seed=False)
    resilient_select(
        parse_html(_V1), "article.card.acordao", name="row", source="demo", memory=memory
    )

    trace = _Trace()
    result = resilient_select(
        parse_html("<html><body><table><tr><td>x</td></tr></table></body></html>"),
        "article.card.acordao",
        name="row",
        source="demo",
        memory=memory,
        trace=trace,
    )
    assert list(result) == []
    assert trace.transformations == []
    assert trace.limitations and "layout likely changed" in trace.limitations[0]


def test_resilient_select_without_memory_is_a_plain_selector() -> None:
    trace = _Trace()
    result = resilient_select(
        parse_html(_V2),
        "article.card.acordao",
        name="row",
        source="demo",
        memory=None,
        trace=trace,
    )
    assert list(result) == []
    assert trace.transformations == [] and trace.limitations == []
