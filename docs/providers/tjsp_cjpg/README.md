# TJSP CJPG (jurisprudencia de primeiro grau)

Status: `implemented`, `live_validated`, `federation_enabled`.

Promotion addendum (2026-09-05): the operator approved local/federated use
after the technical contract, fixtures, quality checks and bounded live check
passed. This does not authorize deployment or redistribution. The default
federation preserves the explicit CJPG/first-degree discriminator.

O provider `tjsp_cjpg` consulta a busca publica CJPG do e-SAJ do Tribunal de
Justica de Sao Paulo. CJPG e uma colecao de decisoes de primeiro grau e fica
separada de CJSG, precedentes qualificados e consulta processual. Por isso,
nao participa da busca unificada por padrao.

## Identidade

Fonte oficial: Tribunal de Justica do Estado de Sao Paulo (TJSP), colecao
publica CJPG de decisoes de primeiro grau no e-SAJ.

## Contrato observado

- Portal oficial: <https://esaj.tjsp.jus.br/>.
- Busca: `GET /cjpg/pesquisar.do`.
- Paginacao: `GET /cjpg/trocarDePagina.do?pagina=<n>&conversationId=` apos a
  busca inicial na mesma sessao publica.
- Parametros reproduzidos: `dadosConsulta.pesquisaLivre`, numero CNJ,
  `dadosConsulta.dtInicio`, `dadosConsulta.dtFim`, classe, assunto, vara e
  ordenacao.
- Limite remoto observado: 10 resultados por pagina.
- Resposta: HTML com `divDadosResultado`, linhas `tr.fundocinza1`, metadados
  rotulados e texto de decisao oculto no proprio resultado.

## Dados e normalizacao

O adapter mapeia numero CNJ, classe, assunto, magistrado, comarca, foro, vara,
data de disponibilizacao e inteiro teor para `JurisprudenceResult` e
`CanonicalDecision`. A data de disponibilizacao fica em `updated_at` e em
`raw.data_disponibilizacao`; nao e apresentada como data de julgamento. O
identificador tecnico do portal (`name` da ancora) e preservado em
`raw.source_id`/`raw.cd_processo`. Campos de origem e texto integral ficam em
`raw` para auditoria.

Cada chamada cria `SourceTrace` com URL final, status HTTP, tipo, bytes, tempo
e SHA-256. Respostas vazias, erros HTTP, bloqueios e mudancas de layout sao
estados distintos; nenhum erro vira lista vazia.

## Uso

```python
from nanojuris import NanoJurisClient

client = NanoJurisClient()
page = client.search("responsabilidade civil", source="tjsp_cjpg", page_size=10)
```

O provider pode ser selecionado explicitamente pelo CLI, MCP ou Studio. A
capability usa `collection=first_degree;route=cjpg` e
`supports_unified_search=False` para impedir mistura semantica com CJSG.

## Limites e seguranca

- O adapter respeita timeout, SSL e `rate_limit_interval` compartilhados.
- Nao contorna CAPTCHA, WAF, login, sessao, robots ou rate limit.
- O inteiro teor e inline; nao foi promovida uma rota de detalhe independente.
- A evidencia de acesso publico nao autoriza coleta ou redistribuicao em massa;
  revisao juridica de termos, LGPD, retencao e licenca continua obrigatoria.
- Fixtures sao sinteticas e nao contem corpo live ou dados pessoais reais.

## MCP

O provider pode ser consultado explicitamente por MCP com `source="tjsp_cjpg"`.
O trace e a completude devem ser exibidos ao consumidor; erros de acesso nunca
devem ser apresentados como ausencia de jurisprudencia.

## Fixtures e teste live

- `tests/fixtures/tjsp_cjpg_success.html`: duas decisoes sinteticas;
- `tests/fixtures/tjsp_cjpg_empty.html`: busca sem resultados;
- `tests/fixtures/tjsp_cjpg_access_control.html`: captcha sem bypass;
- `tests/fixtures/tjsp_cjpg_schema_drift.html`: linha sem tabela;
- `tests/test_tjsp_cjpg_live.py`: chamada bounded, somente com
  `NANOJURIS_RUN_TJSP_CJPG_LIVE=1`.

## Proximos passos

1. repetir a chamada bounded em ciclos de atualizacao;
2. fechar revisao de reuso, retencao e licenciamento;
3. criar fixtures diferenciais quando o layout evoluir;
4. avaliar promocao para federacao somente apos autorizacao humana.

## Evidencia live

Em 2026-09-01, uma chamada publica limitada a `q=responsabilidade` retornou
HTTP 200, HTML valido, 10 linhas e total declarado de 4.658.921 registros.
O corpo foi analisado em memoria; somente metadados e hash foram registrados
em `docs/provider-discovery/tjsp-cjpg-live-20260901.json`.
