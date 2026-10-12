from __future__ import annotations

import ast
from pathlib import Path

from bs4 import BeautifulSoup

from examples.busca_saj_tjsp import (
    _find_result_root,
    _form_data,
    _has_access_control,
    _looks_empty,
    _with_results,
    _with_state,
)


def test_form_data_preserves_hidden_fields_and_selected_options() -> None:
    soup = BeautifulSoup(
        """
        <form>
          <input name="conversationId" value="abc">
          <input name="ignored" value="no" disabled>
          <input type="checkbox" name="checked" value="yes" checked>
          <input type="checkbox" name="unchecked" value="no">
          <select name="tipo"><option value="A" selected>Acordao</option></select>
        </form>
        """,
        "html.parser",
    )

    assert _form_data(soup.form) == [
        ("conversationId", "abc"),
        ("checked", "yes"),
        ("tipo", "A"),
    ]


def test_result_fragment_is_parsed_without_requiring_full_container() -> None:
    soup = BeautifulSoup(
        """
        <a class="downloadEmenta" cdAcordao="123" cdForo="0">0000000-00</a>
        <textarea id="textAreaDados_123">Ementa pública</textarea>
        """,
        "html.parser",
    )

    root = _find_result_root(soup, "A")
    assert root is not None
    result = _with_results({"resultados": []}, root, soup, "A")

    assert result["estado"] == "resultados"
    assert result["resultados"][0]["cdAcordao"] == "123"
    assert result["resultados"][0]["ementa"] == "Ementa pública"


def test_control_response_is_not_classified_as_empty() -> None:
    soup = BeautifulSoup(
        '<form><input name="dados.buscaInteiroTeor"><div class="g-recaptcha"></div></form>',
        "html.parser",
    )

    result = _with_state({"resultados": []}, "access_control_required", soup)

    assert result["estado"] == "access_control_required"
    assert result["formulario_retorno"] is True
    assert result["captcha_presente"] is True
    assert _has_access_control(soup, soup.decode()) is True
    assert _looks_empty("Nenhum resultado") is True


def test_standalone_flow_has_no_executable_control_route_call() -> None:
    path = Path(__file__).parents[1] / "examples" / "busca_saj_tjsp.py"
    tree = ast.parse(path.read_text(encoding="utf-8"))

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if not isinstance(node.func, ast.Attribute) or node.func.attr != "post":
            continue
        assert not any(
            isinstance(argument, ast.Constant) and "captchaControleAcesso.do" in str(argument.value)
            for argument in node.args
        )
