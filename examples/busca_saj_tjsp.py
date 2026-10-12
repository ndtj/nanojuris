#!/usr/bin/env python3
"""Consulta publica CJSG/TJSP com sessao efemera.

Dependencias: ``pip install requests beautifulsoup4``.

    O fluxo usa o formulario publico, inicializa a sessao publica quando o
    proprio formulario declara essa etapa, envia o POST declarado pelo formulario
    e continua na mesma sessao. Se a fonte devolver resultados no POST, eles sao
    usados diretamente; se devolver uma resposta intermediaria publica, o script
    tenta a primeira pagina por ``trocaDePagina.do``. CAPTCHA, login, sessao
    ausente e outras telas de controle nunca sao tratados como busca vazia.
"""

from __future__ import annotations

import argparse
import json
import re
import time
from collections.abc import Iterable
from typing import Any
from urllib.parse import urljoin, urlsplit

import requests
from bs4 import BeautifulSoup, Tag

BASE = "https://esaj.tjsp.jus.br/cjsg/"
RESULT_SELECTOR = "a.downloadEmenta[cdacordao][cdforo]"
CONTROL_SELECTOR = '.g-recaptcha,[name="recaptcha_response_token"],[name="uuidCaptcha"]'


def consultar(
    texto: str, origem: str = "T", tipo: str = "A", perfil: str = "courts"
) -> dict[str, Any]:
    """Run one bounded public search without persisting cookies or credentials."""

    with requests.Session() as session:
        session.headers["User-Agent"] = "ConsultaPublicaTJSP/1.0 (Python requests)"
        initial_path = "resultadoCompleta.do" if perfil == "courts" else "consultaCompleta.do"
        initial = session.get(urljoin(BASE, initial_path), timeout=45)
        initial.raise_for_status()
        initial_soup = BeautifulSoup(initial.content, "html.parser")
        form = next(
            (
                item
                for item in initial_soup.select("form")
                if "resultadoCompleta.do" in item.get("action", "")
            ),
            None,
        )
        if form is None:
            return _base_result(
                texto, origem, tipo, perfil, initial.status_code, "formulario_indisponivel"
            )

        data = _form_data(form)
        overrides = {
            "dados.buscaInteiroTeor": texto,
            "dados.origensSelecionadas": origem,
            "tipoDecisaoSelecionados": tipo,
            "dados.ordenarPor": "dtPublicacao",
        }
        data = [(key, value) for key, value in data if key not in overrides]
        data.extend(overrides.items())
        data = _initialize_public_access_session(session, initial, data)
        submit = form.select_one('input[name="pbSubmit"]')
        if submit is not None:
            data.append(("pbSubmit", submit.get("value", "Pesquisar")))

        destination = urljoin(initial.url, form["action"])
        if urlsplit(destination).hostname != "esaj.tjsp.jus.br":
            raise ValueError("Destino do formulario nao pertence ao SAJ TJSP")

        # Esta e a unica submissao automatizada: o POST do formulario publico.
        # A rota captchaControleAcesso.do e deliberadamente excluida: e uma
        # rota de controle, nao uma etapa de extracao nem um desbloqueio.
        posted = session.post(
            destination,
            data=data,
            headers={"Referer": initial.url},
            timeout=60,
        )
        posted.raise_for_status()
        posted_soup = BeautifulSoup(posted.content, "html.parser")
        base = _base_result(texto, origem, tipo, perfil, posted.status_code, None)

        post_root = _find_result_root(posted_soup, tipo)
        if post_root is not None:
            return _with_results(base, post_root, posted_soup, tipo)
        if _has_empty_session(posted.text):
            return _with_state(base, "sessao_ausente", posted_soup)
        if _looks_empty(posted_soup.get_text(" ", strip=True)) and not _has_access_control(
            posted_soup, posted.text
        ):
            return _with_state(base, "sem_resultados", posted_soup)

        # Algumas versões públicas retornam uma resposta intermediária, inclusive
        # uma tela de controle, antes do fragmento de resultados. A primeira
        # página deve ser buscada na mesma sessão.
        time.sleep(0.5)
        first_page = session.get(
            urljoin(BASE, "trocaDePagina.do"),
            params={"tipoDeDecisao": tipo, "pagina": 1},
            headers={"Referer": destination, "Accept": "text/html"},
            timeout=60,
        )
        first_page.raise_for_status()
        page_soup = BeautifulSoup(first_page.content, "html.parser")
        page_root = _find_result_root(page_soup, tipo)
        if page_root is not None:
            base["http"] = first_page.status_code
            return _with_results(base, page_root, page_soup, tipo)
        if _has_empty_session(first_page.text):
            return _with_state(base, "sessao_ausente", page_soup, first_page.status_code)
        if _has_access_control(page_soup, first_page.text):
            return _with_state(base, "access_control_required", page_soup, first_page.status_code)
        state = (
            "sem_resultados"
            if _looks_empty(page_soup.get_text(" ", strip=True))
            else "retorno_sem_resultados_validaveis"
        )
        return _with_state(base, state, page_soup, first_page.status_code)


def _form_data(form: Tag) -> list[tuple[str, str]]:
    data: list[tuple[str, str]] = []
    for field in form.select("input[name], select[name], textarea[name]"):
        name = str(field["name"])
        field_type = field.get("type", "").lower()
        if field.has_attr("disabled") or field_type in {
            "button",
            "submit",
            "reset",
            "file",
            "image",
        }:
            continue
        if field_type in {"checkbox", "radio"} and not field.has_attr("checked"):
            continue
        if field.name == "select":
            options = field.select("option[selected]") or field.select("option")[:1]
            data.extend((name, str(option.get("value", option.get_text()))) for option in options)
        else:
            value = field.get("value", "") if field.name == "input" else field.get_text()
            data.append((name, str(value)))
    return data


def _initialize_public_access_session(
    session: requests.Session,
    initial: requests.Response,
    data: list[tuple[str, str]],
) -> list[tuple[str, str]]:
    """Refresh the public SAJ UUID using the source-declared session flow."""

    uuid_values = [value for key, value in data if key == "uuidCaptcha"]
    if not uuid_values:
        return data
    uuid_value = uuid_values[0]

    control = session.post(
        urljoin(BASE, "captchaControleAcesso.do"),
        data={"uuidCaptcha": uuid_value},
        headers={"Referer": initial.url},
        timeout=45,
    )
    control.raise_for_status()
    try:
        refreshed_uuid = control.json().get("uuidCaptcha")
    except (ValueError, AttributeError, TypeError):
        refreshed_uuid = None
    if not refreshed_uuid:
        return data

    return [(key, value) for key, value in data if key != "uuidCaptcha"] + [
        ("uuidCaptcha", str(refreshed_uuid))
    ]


def _find_result_root(soup: BeautifulSoup, tipo: str) -> Tag | BeautifulSoup | None:
    container = soup.select_one(f"#divDadosResultado-{tipo}")
    if container is not None:
        return container
    return soup if soup.select(RESULT_SELECTOR) else None


def _with_results(
    result: dict[str, Any], root: Tag | BeautifulSoup, soup: BeautifulSoup, tipo: str
) -> dict[str, Any]:
    seen: set[tuple[str, str]] = set()
    records: list[dict[str, Any]] = []
    for anchor in root.select(RESULT_SELECTOR):
        identity = (str(anchor.get("cdacordao")), str(anchor.get("cdforo")))
        if identity in seen or not identity[0] or not identity[1]:
            continue
        seen.add(identity)
        summary = soup.find(id=f"textAreaDados_{identity[0]}")
        records.append(
            {
                "cdAcordao": identity[0],
                "cdForo": identity[1],
                "rotulo": anchor.get_text(" ", strip=True),
                "ementa": summary.get_text(" ", strip=True) if summary else None,
                "documento": urljoin(
                    BASE,
                    f"getArquivo.do?cdAcordao={identity[0]}&cdForo={identity[1]}",
                ),
            }
        )
    pagination = soup.select_one(f"#paginacaoSuperior-{tipo}")
    result.update(
        estado="resultados" if records else "container_sem_documentos",
        quantidade_pagina=len(records),
        paginacao=pagination.get_text(" ", strip=True) if pagination else None,
        resultados=records,
    )
    return result


def _base_result(
    texto: str, origem: str, tipo: str, perfil: str, http: int, state: str | None
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "consulta": texto,
        "origem": origem,
        "tipo": tipo,
        "http": http,
        "perfil": perfil,
        "resultados": [],
    }
    if state:
        result["estado"] = state
    return result


def _with_state(
    result: dict[str, Any], state: str, soup: BeautifulSoup, http: int | None = None
) -> dict[str, Any]:
    if http is not None:
        result["http"] = http
    result.update(
        estado=state,
        formulario_retorno=soup.find("input", {"name": "dados.buscaInteiroTeor"}) is not None,
        captcha_presente=bool(soup.select(CONTROL_SELECTOR)),
    )
    return result


def _has_empty_session(text: str) -> bool:
    return "emptysession" in text.lower()


def _has_access_control(soup: BeautifulSoup, text: str) -> bool:
    lowered = text.lower()
    return bool(
        soup.select(CONTROL_SELECTOR)
        or "captchacontroleacesso" in lowered
        or "recaptcha" in lowered
        or any(value in lowered for value in ("acesso negado", "validacao de acesso", "login"))
    )


def _looks_empty(text: str) -> bool:
    return bool(re.search(r"nenhum\s+(?:registro|resultado)|nao\s+foram\s+encontrad", text, re.I))


def main(argv: Iterable[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("texto", nargs="?", default="dano moral")
    parser.add_argument("--origem", choices=["T", "R"], default="T")
    parser.add_argument("--tipo", choices=["A", "D", "H"], default="A")
    parser.add_argument("--saida")
    parser.add_argument("--perfil", choices=["courts", "juscraper"], default="courts")
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        result = consultar(args.texto, args.origem, args.tipo, args.perfil)
    except requests.RequestException as exc:
        result = {"estado": "erro_http", "classe_erro": type(exc).__name__, "resultados": []}
    serialized = json.dumps(result, ensure_ascii=False, indent=2)
    if args.saida:
        with open(args.saida, "w", encoding="utf-8") as handle:
            handle.write(serialized + "\n")
    print(serialized)
    return 0 if result.get("estado") in {"resultados", "sem_resultados"} else 2


if __name__ == "__main__":
    raise SystemExit(main())
