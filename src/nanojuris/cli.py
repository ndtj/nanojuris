"""Command line interface for NanoJuris."""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any, cast

from nanojuris import __version__
from nanojuris.brazil import list_courts
from nanojuris.client import NanoJurisClient
from nanojuris.exporters import (
    RUN_EXPORT_FORMATS,
    research_run_to_export,
    search_page_to_markdown,
    to_canonical_jsonl,
    to_csv,
    to_jsonl,
)
from nanojuris.health import check_sources
from nanojuris.route_probe import parse_json_payload, parse_key_value_pairs, probe_route
from nanojuris.source_contracts import summarize_contracts
from nanojuris.store import SQLiteStore
from nanojuris.validation import validate_sources, write_validation_artifacts


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="nanojuris",
        description="Busca e normalizacao de jurisprudencia publica brasileira.",
    )
    parser.add_argument("--version", action="version", version=f"nanojuris {__version__}")

    sub = parser.add_subparsers(dest="command", required=True)

    buscar = sub.add_parser("buscar", help="Buscar precedentes ou jurisprudencia publica")
    buscar.add_argument("texto", nargs="?", default="", help="Texto de busca")
    buscar.add_argument("--fonte", default="bnp_pangea", help="Provider de origem")
    buscar.add_argument("--orgaos", default="", help="Siglas separadas por virgula: STF,STJ,TST")
    buscar.add_argument("--tipos", default="", help="Tipos separados por virgula: RG,RR,IAC,IRDR")
    buscar.add_argument("--numero", default="", help="Numero de processo ou precedente")
    buscar.add_argument("--publicacao-de", default="", help="Data inicial de publicacao")
    buscar.add_argument("--publicacao-ate", default="", help="Data final de publicacao")
    buscar.add_argument("--parte", default="", help="Nome da parte, quando suportado pela fonte")
    buscar.add_argument("--documento-parte", default="", help="Documento da parte")
    buscar.add_argument("--advogado", default="", help="Nome do advogado")
    buscar.add_argument("--oab", default="", help="Numero de OAB")
    buscar.add_argument("--precatoria", default="", help="Numero da carta precatoria na origem")
    buscar.add_argument(
        "--documento-delegacia",
        default="",
        help="Numero do documento na delegacia",
    )
    buscar.add_argument("--cda", default="", help="Numero de CDA")
    buscar.add_argument(
        "--detalhar",
        action="store_true",
        help="Buscar detalhes dos processos listados quando a fonte suportar",
    )
    buscar.add_argument("--pagina", type=int, default=1)
    buscar.add_argument("--limite", type=int, default=10)
    buscar.add_argument(
        "--store",
        default="",
        help="Salvar resultados canonicos em um banco SQLite local",
    )
    buscar.add_argument("--label", default="", help="Rotulo opcional para a busca salva")
    buscar.add_argument(
        "--formato",
        choices=["json", "jsonl", "canonical-jsonl", "markdown", "csv"],
        default="json",
        help="Formato de saida",
    )

    buscar_unificada = sub.add_parser(
        "buscar-unificada",
        help="Pesquisar jurisprudencia em varias fontes com completude explicita",
    )
    buscar_unificada.add_argument("texto", nargs="?", default="", help="Texto de busca")
    buscar_unificada.add_argument(
        "--fontes",
        default="",
        help="Providers separados por virgula; vazio usa as fontes unificadas",
    )
    buscar_unificada.add_argument("--orgaos", default="", help="Siglas separadas por virgula")
    buscar_unificada.add_argument("--tipos", default="", help="Tipos separados por virgula")
    buscar_unificada.add_argument("--numero", default="", help="Numero de processo ou precedente")
    buscar_unificada.add_argument("--pagina", type=int, default=1)
    buscar_unificada.add_argument("--limite", type=int, default=10)
    buscar_unificada.add_argument(
        "--store",
        default="",
        help="Salvar a pagina canonical em um banco SQLite e criar um ResearchRun",
    )
    buscar_unificada.add_argument("--label", default="", help="Rotulo opcional para a busca salva")

    precedente = sub.add_parser("precedente", help="Obter decisoes vinculadas a um precedente")
    precedente.add_argument("id", help="ID do precedente, ex.: stf-rg-615")
    precedente.add_argument("--fonte", default="bnp_pangea")

    documento = sub.add_parser("documento", help="Obter inteiro teor publico como documento")
    documento.add_argument("id", help="ID do documento, ex.: tjsp-cjsg-20787558-0")
    documento.add_argument("--fonte", default="tjsp_cjsg")
    documento.add_argument(
        "--compacto",
        action="store_true",
        help="Omitir campos longos como texto bruto, raw e traces completos",
    )

    parametros = sub.add_parser("parametros", help="Listar parametros publicos do provider")
    parametros.add_argument("--fonte", default="bnp_pangea")
    parametros.add_argument(
        "--catalogo",
        action="store_true",
        help="Normalizar parametros em tribunais, especies e grupos",
    )

    sugestoes = sub.add_parser("sugestoes", help="Listar sugestoes publicas de busca")
    sugestoes.add_argument("texto", help="Texto inicial")
    sugestoes.add_argument("--fonte", default="bnp_pangea")

    fontes = sub.add_parser("fontes", help="Listar fontes e capacidades declaradas")
    fontes.add_argument("--fonte", default="", help="Detalhar apenas um provider")

    studio = sub.add_parser("studio", help="Iniciar o NanoJuris Studio local")
    studio.add_argument("--host", default="127.0.0.1")
    studio.add_argument("--port", type=int, default=8765)
    studio.add_argument("--no-browser", action="store_true")
    studio.add_argument(
        "--ignore-env-proxy",
        action="store_true",
        help="Ignorar HTTP_PROXY/HTTPS_PROXY/ALL_PROXY herdados do ambiente local.",
    )

    diagnostico = sub.add_parser(
        "diagnostico",
        help="Exibir diagnostico de capacidades e limites de uma fonte",
    )
    diagnostico.add_argument("--fonte", default="bnp_pangea")

    saude = sub.add_parser(
        "saude",
        help="Verificar ao vivo o estado operacional de fontes publicas",
    )
    saude.add_argument(
        "--fontes",
        default="",
        help="Providers separados por virgula; vazio usa as fontes unificadas",
    )
    saude.add_argument("--texto", default="responsabilidade civil")
    saude.add_argument("--timeout", type=float, default=None)

    validar = sub.add_parser(
        "validar",
        help="Validar ao vivo o contrato normalizado de fontes publicas",
    )
    validar.add_argument(
        "--fontes",
        default="",
        help="Providers separados por virgula; vazio usa as fontes unificadas",
    )
    validar.add_argument("--texto", default="responsabilidade civil")
    validar.add_argument("--timeout", type=float, default=None)
    validar.add_argument(
        "--artefatos-dir",
        default="",
        help="Diretorio para salvar evidencias JSON e Markdown da validacao live",
    )
    validar.add_argument(
        "--escopo",
        default="provider-validation",
        help="Identificador legivel da rodada de validacao",
    )

    contratos = sub.add_parser(
        "contratos",
        help="Auditar maturidade, lacunas e proximos passos dos providers",
    )
    contratos.add_argument("--fonte", default="", help="Detalhar apenas um provider")
    contratos.add_argument(
        "--resumo",
        action="store_true",
        help="Exibir apenas resumo de maturidade e riscos",
    )

    tribunais = sub.add_parser("tribunais", help="Listar tribunais brasileiros conhecidos")
    tribunais.add_argument("--ramo", default="", help="Filtrar por ramo: state, federal, labor")
    tribunais.add_argument("--uf", default="", help="Filtrar por UF, ex.: SP")
    tribunais.add_argument(
        "--sistema",
        default="",
        help="Filtrar por familia tecnica: esaj_cjsg, eproc, pje, datajud",
    )
    tribunais.add_argument(
        "--implementados",
        action="store_true",
        help="Listar apenas tribunais com provider implementado",
    )

    probe_rota = sub.add_parser(
        "probe-rota",
        help="Avaliar uma rota publica candidata antes de implementar provider",
    )
    probe_rota.add_argument("url", help="URL publica absoluta")
    probe_rota.add_argument("--metodo", choices=["GET", "POST"], default="GET")
    probe_rota.add_argument(
        "--expect",
        action="append",
        default=[],
        help="Texto esperado na resposta. Pode ser repetido.",
    )
    probe_rota.add_argument(
        "--data",
        action="append",
        default=[],
        metavar="CHAVE=VALOR",
        help="Campo de formulario para POST. Pode ser repetido.",
    )
    probe_rota.add_argument(
        "--json",
        default="",
        help='Payload JSON como objeto ou array. Ex.: \'{"q":"idpj"}\' ou \'["TSE"]\'',
    )
    probe_rota.add_argument(
        "--json-file",
        default="",
        help="Caminho de arquivo JSON com payload do probe.",
    )
    probe_rota.add_argument("--timeout", type=float, default=30.0)
    probe_rota.add_argument(
        "--connect-timeout",
        type=float,
        default=None,
        help="Timeout separado para conexao; por padrao usa no maximo 10s.",
    )
    probe_rota.add_argument(
        "--read-timeout",
        type=float,
        default=None,
        help="Timeout para receber dados; por padrao usa --timeout.",
    )
    probe_rota.add_argument(
        "--max-bytes",
        type=int,
        default=5_000_000,
        help="Limite de leitura para diagnostico; respostas maiores sao marcadas como parciais.",
    )
    probe_rota.add_argument(
        "--sem-verificar-ssl",
        action="store_true",
        help="Desabilitar verificacao SSL apenas para diagnostico local.",
    )

    store = sub.add_parser("store", help="Consultar um store SQLite local")
    store_sub = store.add_subparsers(dest="store_command", required=True)

    store_stats = store_sub.add_parser("stats", help="Exibir estatisticas do store")
    store_stats.add_argument("db", help="Caminho do banco SQLite")

    store_query = store_sub.add_parser("query", help="Consultar registros canonicos salvos")
    store_query.add_argument("db", help="Caminho do banco SQLite")
    store_query.add_argument("--kind", choices=["decision", "document", "precedent"])
    store_query.add_argument("--fonte", default="")
    store_query.add_argument("--tribunal", default="")
    store_query.add_argument("--numero", default="")
    store_query.add_argument("--assunto", default="")
    store_query.add_argument("--relator", default="")
    store_query.add_argument("--tipo-decisao", default="")
    store_query.add_argument("--tipo-precedente", default="")
    store_query.add_argument("--canonical-key", default="")
    store_query.add_argument("--publicacao-de", default="")
    store_query.add_argument("--publicacao-ate", default="")
    store_query.add_argument("--limite", type=int, default=100)
    store_query.add_argument(
        "--compacto",
        action="store_true",
        help="Omitir campos longos como texto bruto, raw e traces completos",
    )

    store_get = store_sub.add_parser("get", help="Obter um registro canonico por tipo e id")
    store_get.add_argument("db", help="Caminho do banco SQLite")
    store_get.add_argument("kind", choices=["decision", "document", "precedent"])
    store_get.add_argument("id", help="ID canonico do registro")
    store_get.add_argument(
        "--compacto",
        action="store_true",
        help="Omitir campos longos como texto bruto, raw e traces completos",
    )

    store_runs = store_sub.add_parser("runs", help="Listar buscas salvas")
    store_runs.add_argument("db", help="Caminho do banco SQLite")
    store_runs.add_argument("--limite", type=int, default=50)

    store_run = store_sub.add_parser("run", help="Obter metadados de uma busca salva")
    store_run.add_argument("db", help="Caminho do banco SQLite")
    store_run.add_argument("id", help="ID da busca salva")

    store_records = store_sub.add_parser("records", help="Listar registros de uma busca salva")
    store_records.add_argument("db", help="Caminho do banco SQLite")
    store_records.add_argument("id", help="ID da busca salva")
    store_records.add_argument("--limite", type=int, default=100)
    store_records.add_argument("--offset", type=int, default=0)
    store_records.add_argument(
        "--compacto",
        action="store_true",
        help="Omitir campos longos como texto bruto, raw e traces completos",
    )

    store_export = store_sub.add_parser("export", help="Exportar uma busca salva")
    store_export.add_argument("db", help="Caminho do banco SQLite")
    store_export.add_argument("id", help="ID da busca salva")
    store_export.add_argument(
        "--formato",
        choices=sorted(RUN_EXPORT_FORMATS),
        default="jsonl",
        help="Formato de exportacao da busca salva",
    )
    store_export.add_argument("--limite", type=int, default=100)
    store_export.add_argument("--offset", type=int, default=0)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    client = NanoJurisClient()

    try:
        if args.command == "buscar":
            courts = _split_csv(args.orgaos)
            types = _split_csv(args.tipos)
            if args.store:
                run = client.search_and_store_run(
                    args.texto,
                    source=args.fonte,
                    courts=courts,
                    types=types,
                    page=args.pagina,
                    page_size=args.limite,
                    store=args.store,
                    label=args.label or None,
                    number=args.numero,
                    published_from=args.publicacao_de,
                    published_to=args.publicacao_ate,
                    party_name=args.parte,
                    party_document=args.documento_parte,
                    lawyer_name=args.advogado,
                    oab=args.oab,
                    precatory_number=args.precatoria,
                    police_document=args.documento_delegacia,
                    cda=args.cda,
                    fetch_details=args.detalhar,
                )
                print(
                    json.dumps(
                        {
                            "run_id": run.id,
                            "stored": run.record_count,
                            "store": args.store,
                            "source": args.fonte,
                            "label": run.label,
                        },
                        ensure_ascii=False,
                        indent=2,
                    )
                )
                return 0
            page = client.search(
                args.texto,
                source=args.fonte,
                courts=courts,
                types=types,
                page=args.pagina,
                page_size=args.limite,
                number=args.numero,
                published_from=args.publicacao_de,
                published_to=args.publicacao_ate,
                party_name=args.parte,
                party_document=args.documento_parte,
                lawyer_name=args.advogado,
                oab=args.oab,
                precatory_number=args.precatoria,
                police_document=args.documento_delegacia,
                cda=args.cda,
                fetch_details=args.detalhar,
            )
            print(_format_search(page, args.formato))
            return 0

        if args.command == "buscar-unificada":
            sources = _split_csv(args.fontes)
            courts = _split_csv(args.orgaos)
            types = _split_csv(args.tipos)
            if args.store:
                run = client.search_many_and_store_run(
                    args.texto,
                    sources=sources or None,
                    courts=courts,
                    types=types,
                    number=args.numero,
                    page=args.pagina,
                    page_size=args.limite,
                    store=args.store,
                    label=args.label or None,
                )
                print(
                    json.dumps(
                        {"run_id": run.id, "stored": run.record_count, "source": run.source},
                        ensure_ascii=False,
                        indent=2,
                    )
                )
                return 0
            search_payload = client.search_many(
                args.texto,
                sources=sources or None,
                courts=courts,
                types=types,
                number=args.numero,
                page=args.pagina,
                page_size=args.limite,
            )
            print(json.dumps(search_payload, ensure_ascii=False, indent=2, default=_json_default))
            return 0

        if args.command == "precedente":
            bundle = client.get_decisions(args.id, source=args.fonte)
            print(json.dumps(bundle.to_dict(), ensure_ascii=False, indent=2))
            return 0

        if args.command == "documento":
            document = client.get_document(args.id, source=args.fonte)
            document_payload = document.to_dict()
            if args.compacto:
                document_payload = _compact_record(document_payload)
            print(json.dumps(document_payload, ensure_ascii=False, indent=2))
            return 0

        if args.command == "parametros":
            params = (
                client.get_catalog(source=args.fonte).to_dict()
                if args.catalogo
                else client.get_parameters(source=args.fonte)
            )
            print(json.dumps(params, ensure_ascii=False, indent=2))
            return 0

        if args.command == "sugestoes":
            suggestions = client.list_suggestions(args.texto, source=args.fonte)
            print(json.dumps(suggestions, ensure_ascii=False, indent=2))
            return 0

        if args.command == "fontes":
            sources_payload: Any = (
                client.get_capabilities(source=args.fonte).to_dict()
                if args.fonte
                else [capability.to_dict() for capability in client.list_sources()]
            )
            print(json.dumps(sources_payload, ensure_ascii=False, indent=2))
            return 0

        if args.command == "studio":
            from nanojuris.web.server import main as studio_main

            studio_args = ["--host", args.host, "--port", str(args.port)]
            if args.no_browser:
                studio_args.append("--no-browser")
            if args.ignore_env_proxy:
                studio_args.append("--ignore-env-proxy")
            return studio_main(studio_args)

        if args.command == "diagnostico":
            capability = client.get_capabilities(source=args.fonte)
            print(json.dumps(capability.to_dict(), ensure_ascii=False, indent=2))
            return 0

        if args.command == "saude":
            health_payload = check_sources(
                client,
                sources=_split_csv(args.fontes) or None,
                text=args.texto,
                timeout=args.timeout,
            )
            print(json.dumps(health_payload, ensure_ascii=False, indent=2))
            return 0

        if args.command == "validar":
            validation_payload = validate_sources(
                client,
                sources=_split_csv(args.fontes) or None,
                text=args.texto,
                timeout=args.timeout,
            )
            if args.artefatos_dir:
                json_path, markdown_path = write_validation_artifacts(
                    validation_payload,
                    output_dir=args.artefatos_dir,
                    scope=args.escopo,
                )
                validation_payload["artifacts"] = {
                    "json": str(json_path),
                    "markdown": str(markdown_path),
                }
            print(json.dumps(validation_payload, ensure_ascii=False, indent=2))
            return 0 if validation_payload["passed"] else 1

        if args.command == "contratos":
            contracts = (
                [client.get_source_contract(source=args.fonte)]
                if args.fonte
                else client.list_source_contracts()
            )
            payload: Any = (
                summarize_contracts(contracts)
                if args.resumo
                else {
                    "summary": summarize_contracts(contracts),
                    "contracts": [contract.to_dict() for contract in contracts],
                }
            )
            print(json.dumps(payload, ensure_ascii=False, indent=2))
            return 0

        if args.command == "tribunais":
            court_rows = list_courts(
                branch=cast(Any, args.ramo or None),
                state=args.uf or None,
                source_system=cast(Any, args.sistema or None),
                implemented=True if args.implementados else None,
            )
            print(
                json.dumps([court.to_dict() for court in court_rows], ensure_ascii=False, indent=2)
            )
            return 0

        if args.command == "probe-rota":
            json_payload = None
            if args.json and args.json_file:
                raise ValueError("Use apenas um entre --json e --json-file")
            if args.json:
                json_payload = parse_json_payload(args.json)
            if args.json_file:
                json_payload = parse_json_payload(_read_text_file(args.json_file))
            result = probe_route(
                args.url,
                method=args.metodo,
                expected_texts=args.expect,
                timeout=args.timeout,
                connect_timeout=args.connect_timeout,
                read_timeout=args.read_timeout,
                max_bytes=args.max_bytes,
                user_agent=client.config.user_agent,
                data=parse_key_value_pairs(args.data),
                json_payload=json_payload,
                verify_ssl=not args.sem_verificar_ssl,
            )
            print(json.dumps(result.to_dict(), ensure_ascii=False, indent=2))
            return 0 if result.ok else 2

        if args.command == "store":
            with SQLiteStore(args.db) as store:
                if args.store_command == "stats":
                    print(json.dumps(store.stats().to_dict(), ensure_ascii=False, indent=2))
                    return 0
                if args.store_command == "query":
                    records = store.query_records(
                        kind=args.kind,
                        source=args.fonte or None,
                        court=args.tribunal or None,
                        case_number=args.numero or None,
                        subject=args.assunto or None,
                        rapporteur=args.relator or None,
                        decision_type=args.tipo_decisao or None,
                        precedent_type=args.tipo_precedente or None,
                        canonical_key=args.canonical_key or None,
                        publication_date_from=args.publicacao_de or None,
                        publication_date_to=args.publicacao_ate or None,
                        limit=args.limite,
                    )
                    if args.compacto:
                        records = [_compact_record(record) for record in records]
                    print(json.dumps(records, ensure_ascii=False, indent=2))
                    return 0
                if args.store_command == "get":
                    stored_record = store.get(cast(Any, args.kind), args.id)
                    if stored_record is None:
                        raise ValueError("Registro nao encontrado")
                    if args.compacto:
                        stored_record = _compact_record(stored_record)
                    print(json.dumps(stored_record, ensure_ascii=False, indent=2))
                    return 0
                if args.store_command == "runs":
                    runs = store.list_research_runs(limit=args.limite)
                    print(json.dumps(runs, ensure_ascii=False, indent=2))
                    return 0
                if args.store_command == "run":
                    saved_run = store.get_research_run(args.id)
                    if saved_run is None:
                        raise ValueError("Busca salva nao encontrada")
                    print(json.dumps(saved_run, ensure_ascii=False, indent=2))
                    return 0
                if args.store_command == "records":
                    records = store.get_research_run_records(
                        args.id,
                        limit=args.limite,
                        offset=args.offset,
                    )
                    if args.compacto:
                        records = [_compact_record(record) for record in records]
                    print(json.dumps(records, ensure_ascii=False, indent=2))
                    return 0
                if args.store_command == "export":
                    export_run = store.get_research_run(args.id)
                    if export_run is None:
                        raise ValueError("Busca salva nao encontrada")
                    records = store.get_research_run_records(
                        args.id,
                        limit=args.limite,
                        offset=args.offset,
                    )
                    print(research_run_to_export(export_run, records, args.formato))
                    return 0
    except Exception as exc:  # noqa: BLE001 - CLI boundary
        print(f"erro: {exc}", file=sys.stderr)
        return 2

    parser.error("Comando invalido")
    return 2


def _split_csv(value: str) -> list[str]:
    return [part.strip() for part in value.split(",") if part.strip()]


def _format_search(page: Any, output_format: str) -> str:
    if output_format == "csv":
        return to_csv(page)
    if output_format == "jsonl":
        return to_jsonl(page)
    if output_format == "canonical-jsonl":
        return to_canonical_jsonl(page)
    if output_format == "markdown":
        return search_page_to_markdown(page)
    return json.dumps(page.to_dict(), ensure_ascii=False, indent=2)


def _json_default(value: Any) -> Any:
    if hasattr(value, "to_dict"):
        return value.to_dict()
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serializable")


def _read_text_file(path: str) -> str:
    with open(path, encoding="utf-8") as file:
        return file.read()


def _compact_record(record: dict[str, Any]) -> dict[str, Any]:
    omitted = []
    compact: dict[str, Any] = {}
    for key, value in record.items():
        if key in {"raw", "text", "full_text", "source_trace", "extraction_trace"}:
            if value:
                omitted.append(key)
            continue
        if key == "raw_metadata" and isinstance(value, dict):
            nested = _compact_metadata(value)
            compact[key] = nested
            nested_omitted = nested.pop("omitted_fields", [])
            omitted.extend(f"raw_metadata.{field}" for field in nested_omitted)
            continue
        compact[key] = value
    if omitted:
        compact["omitted_fields"] = omitted
    return compact


def _compact_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    omitted = []
    compact: dict[str, Any] = {}
    for key, value in metadata.items():
        if key in {"parties_text", "movements_text"}:
            if value:
                omitted.append(key)
            continue
        compact[key] = value
    if omitted:
        compact["omitted_fields"] = omitted
    return compact


if __name__ == "__main__":
    raise SystemExit(main())
