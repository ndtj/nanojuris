"""Contract regressions for the TJGO/Projudi adapter."""

from __future__ import annotations

from nanojuris.config import NanoJurisConfig
from nanojuris.models import JurisprudenceQuery
from nanojuris.providers.tjgo_projudi_jurisprudencia import (
    TjgoProjudiJurisprudenciaProvider,
    _build_payload,
)


def test_tjgo_payload_translates_appellate_scope_and_available_filters() -> None:
    payload = _build_payload(
        JurisprudenceQuery(
            text="dano moral",
            exact_phrase="responsabilidade civil",
            number="0000001-01.2020.8.09.0001",
            source_origin="segundo grau",
            types=["acordao"],
            published_from="2024-01-01",
            published_to="2024-12-31",
            page=2,
            page_size=3,
        )
    )

    # Projudi has one text field; an exact phrase is used when no broader text
    # is supplied.  The official second-degree selector is Id_Instancia=15.
    assert payload["Texto"] == "dano moral"
    assert payload["Id_Instancia"] == "15"
    assert payload["Id_ArquivoTipo"] == "1"
    assert payload["ProcessoNumero"] == "0000001-01.2020.8.09.0001"
    assert payload["DataInicial"] == "2024-01-01"
    assert payload["DataFinal"] == "2024-12-31"
    assert payload["PosicaoPaginaAtual"] == "1"


def test_tjgo_capability_classifies_every_common_filter() -> None:
    capability = TjgoProjudiJurisprudenciaProvider(
        NanoJurisConfig(rate_limit_interval=0)
    ).get_capabilities()
    common = {
        "text",
        "courts",
        "types",
        "all_words",
        "any_words",
        "without_words",
        "exact_phrase",
        "rapporteur",
        "updated_from",
        "updated_to",
        "published_from",
        "published_to",
        "number",
        "party_name",
        "party_document",
        "lawyer_name",
        "oab",
        "precatory_number",
        "police_document",
        "cda",
        "source_origin",
        "source_origins",
        "fetch_details",
        "case_class",
        "judging_body",
        "degree",
        "instance",
        "branch",
        "legal_area",
        "authority",
        "collection",
        "document_type",
        "decision_type",
        "judgment_date_from",
        "judgment_date_to",
    }
    assert common <= set(capability.filter_semantics)
    assert all(capability.filter_status(name) != "unverified" for name in common)
    assert capability.filter_status("degree") == "translated"
    assert capability.filter_status("case_class") == "unsupported"
