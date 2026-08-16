# TJMA JurisConsult

Status: `runtime_live_validated_catalog` | papel: `catalog_context`

Provider de catalogos publicos do JurisConsult/TJMA. A busca de resultados
jurisprudenciais permanece controlada por captcha e nao e automatizada.

## Identidade E Escopo

- `source_id`: `tjma_jurisconsult`.
- Portal: <https://jurisconsult.tjma.jus.br/>.
- API: <https://apijuris.tjma.jus.br/v1>.
- Escopo implementado: especies de relatorio, tipos de pesquisa, classes,
  magistrados, camaras, comarcas e links de sumulas/precedentes.
- Fora do escopo: coleta automatica de acordaos, decisoes e sentencas.

## Contrato HTTP Observado

Endpoints publicos de catalogo, todos reproduzidos com HTTP 200:

- `GET /jurisprudencia/lista_relatorios`.
- `GET /jurisprudencia/lista_todos_tipos_pesquisa?tipoRelatorio=<id>`.
- `GET /jurisprudencia/lista_todos_classes?tipoRelatorio=<id>`.
- `GET /jurisprudencia/lista_todos_magistrados?tipoRelatorio=<id>`.
- `GET /jurisprudencia/lista_todos_camaras?tipoRelatorio=<id>`.
- `GET /jurisprudencia/lista_todos_comarcas?tipoRelatorio=<id>`.
- `GET /jurisprudencia/links_pesquisa_sumulas`.

As rotas de resultados usam variantes de `/jurisprudencia/processos` e exigem
`tokenG` e `keyId` de captcha. O provider retorna
`AccessControlRequiredError` sem tentar criar ou reutilizar desafio.

## Dados Retornados

`ProviderCatalog.species` recebe os relatorios oficiais. O payload bruto
preserva classes, magistrados, camaras, comarcas, tipos de pesquisa e links de
IRDR/IAC/sumulas em `catalog.raw`.

## Filtros E Paginaçao

O catalogo aceita o identificador `tipoRelatorio` nas rotas oficiais. Nao ha
paginaçao de resultados implementada porque a busca principal esta gated.

## Inteiro Teor E Documentos

Nao aplicavel nesta superficie. Nenhum link de catalogo e promovido como
documento carregado.

## Estados E Falhas

- Catalogos publicos: `access_status=public`.
- Busca principal: `access_control_required` por captcha.
- Falha de rede ou 5xx: `SourceUnavailableError`.
- HTTP 429: `RateLimitDetectedError`.

Captcha nao e convertido em vazio nem em provider textual funcional.

## Evidencias, Fixtures E Testes

- Fixture: `tests/fixtures/tjma_jurisconsult_catalog.json`.
- Testes: `tests/test_tjma_jurisconsult.py`.
- Evidencia live: `docs/validation/runs/20260816T125603Z-tjto-tjma-tjro-live.json`.
- Rodada: 7 especies, 135 classes e 313 magistrados observados.

## Implementaçao E Integraçao

- Modulo: `src/nanojuris/providers/tjma_jurisconsult.py`.
- Classe: `TjmaJurisconsultProvider`.
- Interfaces: catalogo Python, CLI, Studio e MCP; fora da busca unificada.

## MCP E Agentes

O agente pode usar o catalogo para desenho amostral e descoberta de filtros,
mas deve dizer que ele nao contem resultados coletados. A busca textual deve
ser reportada como controlada por captcha.

## Promocao

O provider esta no maximo comprovado para catalogo publico. So pode ganhar
busca textual quando existir uma superficie oficial sem captcha ou um fluxo
interativo explicitamente operado pelo usuario.

## Proximos Passos

- monitorar a disponibilidade dos catalogos publicos;
- registrar mudancas de vocabulário e relatorios;
- nao automatizar a busca enquanto o captcha continuar sendo requisito;
- investigar somente superficies oficiais alternativas sem desafio.
