from nanojuris.normalization import (
    first_nonempty,
    normalize_cnj_number,
    normalize_date_value,
    normalize_decision_type,
    normalize_text,
    normalize_url,
)


def test_normalize_text_and_first_nonempty() -> None:
    assert normalize_text("  Ementa\xa0\n sobre   tema ") == "Ementa sobre tema"
    assert first_nonempty("", None, "  valor ") == "valor"


def test_normalize_dates_preserves_unknown_as_none() -> None:
    assert normalize_date_value("31/12/2025") == "2025-12-31"
    assert normalize_date_value("10 de março de 2024") == "2024-03-10"
    assert normalize_date_value("sem data") is None


def test_normalize_cnj_and_decision_type() -> None:
    assert normalize_cnj_number("00000001234520201234") == "0000000-12.3452.0.20.1234"
    assert normalize_decision_type("Acórdão") == "acordao"
    assert normalize_decision_type("Decisão monocrática") == "decisao_monocratica"


def test_normalize_url_removes_fragment_and_resolves_relative() -> None:
    assert normalize_url("/decisao/1#top", base_url="https://example.test/pesquisa") == (
        "https://example.test/decisao/1"
    )
