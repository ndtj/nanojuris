# TJRO LIAME Precedentes Qualificados

Status: `runtime_live_validated` | papel: `qualified_precedents`

Provider do catalogo de precedentes qualificados do TJRO. Ele nao representa
o acervo geral de acordaos e permanece fora da busca textual unificada.

## Identidade E Escopo

- `source_id`: `tjro_liame`.
- Portal: <https://liame.tjro.jus.br/>.
- Busca: <https://liame.tjro.jus.br/pesquisa/precedentes>.
- Escopo: IRDR/IAC e precedentes qualificados publicados pelo LIAME.
- Fora do escopo: jurisprudencia geral, consulta processual e comunicacoes.

## Contrato HTTP Observado

- `POST /api/pesquisa/precedentes`.
- Content-Type: `application/json`.
- Campos: `siglas`, `especies`, `texto`, `numero`,
  `numero_processo_paradigma`, `assuntos`, `data_inicio`, `data_final`,
  `situacao`, `ordenacao`, `page` e `page_size`.
- Especies TJRO observadas: `incidente_assuncao_competencia` e
  `incidente_demanda_repetitiva`.
- Resposta: `data.total`, `data.page`, `data.page_size`, `data.total_pages`,
  `data.has_next` e `data.results`.

## Dados Retornados

O registro preserva numero, questao, tese, relator, situacao, datas, assuntos,
referencia legislativa, limite de suspensao e processos paradigma em `raw`.
Processos paradigma sao normalizados como `ParadigmCase`.

## Filtros E Paginaçao

Implementados na query comum: texto, numero, tipos e datas de publicacao como
janela de `data_inicio`/`data_final`, alem de pagina e tamanho. A API tambem
possui situacao, assuntos e numero de processo paradigma; esses campos ainda
aguardam extensao tipada da query comum.

## Inteiro Teor E Documentos

O registro pode conter URLs externas de decisoes de admissao ou merito. Elas
permanecem referencias observadas e nao sao anunciadas como documento carregado.

## Estados E Falhas

- HTTP 200 com `data.results`: resultados publicos de precedentes.
- HTTP 400/422: `QueryRejectedError`.
- HTTP 401/403: `AccessControlRequiredError`.
- HTTP 429: `RateLimitDetectedError`.
- 5xx, rede ou contrato JSON alterado: falha observavel.

## Evidencias, Fixtures E Testes

- Fixture: `tests/fixtures/tjro_liame_results.json`.
- Testes: `tests/test_tjro_liame.py`.
- Evidencia live: `docs/validation/runs/20260816T125603Z-tjto-tjma-tjro-live.json`.
- Rodada: consulta `empreitada` retornou um precedente qualificado.

## Implementaçao E Integraçao

- Modulo: `src/nanojuris/providers/tjro_liame.py`.
- Classe: `TjroLiameProvider`.
- Registro canonico: `CanonicalPrecedent` por meio do mapeamento de resultados.
- Interfaces: Python, CLI, Studio e MCP; nao participa da busca textual unificada.

## MCP E Agentes

O agente deve rotular cada resultado como precedente qualificado TJRO e nunca
apresenta-lo como amostra geral de acordaos. Deve preservar questao, tese,
situacao, processo paradigma e links externos.

## Promocao

Provider no maximo comprovado para precedentes qualificados. Gold contextual
depende de rodadas live adicionais, testes dos filtros restantes e contrato
documental separado para documentos vinculados.

## Proximos Passos

- validar filtros de situacao, assunto e processo paradigma;
- repetir a consulta live com pagina 2;
- documentar separadamente documentos vinculados quando forem reproduzidos;
- manter o provider fora da busca textual geral.
