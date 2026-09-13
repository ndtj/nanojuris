from __future__ import annotations

import json
from pathlib import Path

FIXTURES = Path(__file__).parent / "fixtures"


def test_trt2_public_options_and_filter_catalog_are_sanitized() -> None:
    options = json.loads((FIXTURES / "trt2_pje_opcoes.json").read_text(encoding="utf-8"))
    filters = json.loads((FIXTURES / "trt2_pje_filtros.json").read_text(encoding="utf-8"))

    assert options["version"] == "1.5.0-i1"
    assert options["captchaOption"] == "2"
    assert options["recaptchaSecretKey"] is None
    assert filters["documents"] == []
    assert filters["hits"] > 0
    assert "classeJudicial" in filters["aggregation_fields"]
    assert filters["sanitized"] is True


def test_trt2_document_challenge_is_never_an_empty_result() -> None:
    challenge = json.loads((FIXTURES / "trt2_pje_challenge.json").read_text(encoding="utf-8"))

    assert challenge["documents"] == []
    assert challenge["classification"] == "access_blocked"
    assert challenge["tokenDesafio"].startswith("[redacted")
    assert challenge["imagem"].startswith("[redacted")
