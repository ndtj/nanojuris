# Roadmap

NanoJuris passa a seguir uma estrategia extraction-first: busca, aquisicao,
parsing, normalizacao, persistencia e exposicao via MCP. A camada de
interpretacao juridica fica fora do escopo do core.

A validacao pratica por persona e caso de uso esta em
[use-case-validation-matrix.md](use-case-validation-matrix.md).
O mapa de cobertura nacional e oportunidades de providers esta em
[provider-coverage-map.md](provider-coverage-map.md).
O ultimo relatorio aplicado de validacao esta em
[validation-report-2026-08-02.md](validation-report-2026-08-02.md).

## 0.1

- Provider BNP/Pangea.
- Modelos tipados.
- Cliente Python.
- CLI.
- Exportadores.
- Testes automatizados.

## 0.2

- TJSP/CJSG.
- Parser HTML para resultados.
- Detector de captcha/controle de acesso.
- Inteiro teor publico quando disponivel.

## 0.3

- STJ.
- Pesquisa de jurisprudencia.
- Repetitivos e sumulas.
- Pesquisa tecnica inicial registrada em [stj-provider-research.md](stj-provider-research.md).
- Ficha publica de fonte registrada em [stj-source-profile.md](stj-source-profile.md).

## 0.4

- Modelos canonicos de decisao, precedente e documento.
- Traces de extracao com status, hash e versao de parser.
- Status padronizados de acesso e extracao.

## 0.5

- STF.
- Repercussao geral, sumulas, acordaos e monocraticas.

## 0.6

- Store SQLite local.
- CLI de store com `stats`, `query` e `get`.
- Deduplicacao por `canonical_key` no store local.
- Buscas salvas por `ResearchRun` e retomada por `run_id`.
- Exportacao de `ResearchRun` em `json`, `jsonl`, `csv` e `markdown`.
- Paginacao de records/export de `ResearchRun` por `offset`.
- `get_document` para inteiro teor publico do TJSP/CJSG como `CanonicalDocument`.
- Catalogo brasileiro de tribunais com filtros por ramo, UF e provider implementado.
- Exportacao CSV orientada a dados juridicos objetivos.
- Diagnostico de fontes e capacidades.
- Estudos de caso por publico alvo em [case-studies.md](case-studies.md).
- Busca canonica nativa, busca com persistencia e consultas estruturadas no store.
- Exportacao canonica JSONL, CSVs por tipo de registro e contrato `CanonicalStore`.
- Exemplo SDK offline em [../examples/sdk_workflow.py](../examples/sdk_workflow.py).

## 0.6-publicacao

- Guia de provider novo em [provider-development.md](provider-development.md).
- Checklist de release em [release-checklist.md](release-checklist.md).
- Validacao por casos de uso em
	[validation-report-2026-08-02.md](validation-report-2026-08-02.md).

## 0.7

- MCP local.
- Ferramentas para busca, documento, fontes, diagnostico e exportacao.
- Camada `mcp_tools` testavel sem servidor e wrapper opcional `nanojuris-mcp`.
- Tools MCP de store local: `store_stats`, `store_query` e `store_get`.
- Tools MCP para buscas salvas: `store_runs`, `store_run` e `store_run_records`.
- Tool MCP `store_export_run` para entregar runs salvos a agentes e pipelines.
- Metadados MCP de paginacao: `total`, `has_more` e `next_offset`.
- Tool MCP `get_document` para inteiro teor publico auditavel.
- Tool MCP `list_courts` para descoberta do contexto judiciario brasileiro.

## 0.8+

- TST, TSE, TRFs e tribunais estaduais priorizados por estabilidade da fonte.
- Benchmark publico de cobertura e qualidade de extracao.
