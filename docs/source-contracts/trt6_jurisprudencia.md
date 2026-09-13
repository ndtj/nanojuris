# TRT6 — Jurisprudência

Status: `implemented`; evidência nível A para a rota legada pública e nível B
para a SPA PJe challenge-gated. Última verificação: `2026-09-12`.

## Identidade e escopo

- Fonte oficial: Tribunal Regional do Trabalho da 6ª Região.
- Entrada legada: `https://apps.trt6.jus.br/acordaos/`.
- A superfície retorna acórdãos trabalhistas de segundo grau.
- Identidade canônica: `authority=TRT6`, `branch=labor`, `degree=second`,
  `instance=second`, `collection=JURISPRUDENCIA`, `document_type=acordao`.
- A consulta processual vinculada é apenas URL auxiliar e não substitui a
  decisão de jurisprudência.

## Contrato HTTP observado

| Rota | Método | Finalidade | Estado | Evidência |
|---|---|---|---|---|
| `/acordaos/` | GET | formulário público | operacional | live/fixture |
| `/acordaos/pesquisar` | POST | busca textual/CNJ | operacional | live/fixture |
| `/acordaos/exibirInteiroTeor?documento=<id>` | GET | leitura do documento | link público observado | live |
| `/acordaos/baixarInteiroTeor?documento=<id>` | GET | download do documento | link público observado | live |
| `/juris-backend/api/documentos` | POST | busca SPA PJe | challenge-gated, opt-in | fixture |

O formulário legado aceita `texto`, `numeroCnj`, `numeroTst`, `redator`,
`orgaoJulgador`, `dataInicio`, `dataFim` e `pagina`. A resposta é HTML UTF-8
legado, com dez cards por página, ementa, decisão, metadados e links oficiais.
Pesquisas amplas informam o total e limitam a janela aos primeiros 1.000
registros; consultas exatas podem não informar total autoritativo.

## Dados e mapeamento canônico

Cada card preserva processo CNJ, classe, redator, órgão colegiado, data de
publicação, data de julgamento, ementa, decisão, identificador de documento,
URL de leitura e URL de download. A ementa é `summary`; ementa + decisão são
`full_text`; campos de origem não mapeados ficam em `raw` e `SourceTrace`.

## Estados e falhas

| Estado | Tratamento |
|---|---|
| HTTP 200 com cards | normalizar e preservar trace |
| HTTP 200 vazio autoritativo | `total=0`, `extraction_status=empty` |
| total ausente em consulta exata | `total_known=false`, nunca completar implicitamente |
| HTTP 403/429, CAPTCHA, WAF ou login | erro explícito, nunca lista vazia |
| timeout/TLS/5xx | `SourceUnavailableError` |
| HTML sem cards e sem mensagem de vazio | `ParserContractChangedError` |

A SPA PJe continua exigindo reCAPTCHA. NanoJuris não gera, resolve, reproduz
ou armazena tokens; a federação utiliza somente a rota legada pública.

## Fixtures e testes

- Sucesso legado: `tests/fixtures/trt6_legacy_search_success.html`.
- Desafio PJe: `tests/fixtures/trt6_pje_recaptcha_error.json`.
- Busca PJe autorizada sanitizada: `tests/fixtures/trt6_pje_authorized_success.json`.
- Testes: `tests/test_trt6_jurisprudencia.py`.
- Evidência live: `docs/provider-discovery/trt6-legacy-search-live-20260912.json`.

As páginas 1 e 2 do endpoint legado foram observadas com IDs distintos; uma
consulta exata por CNJ retornou um único card. Nenhum corpo live é versionado.

## MCP e uso seguro

O provider pode ser roteado na busca federada para jurisprudência trabalhista
de segundo grau. O MCP deve informar total conhecido/desconhecido, janela,
filtros aplicados e `SourceTrace`. A rota PJe é diagnóstica/opt-in. Não são
persistidos cookies, credenciais, tokens ou inteiro teor bruto fora do fluxo
autorizado.

## Próximos passos

- Monitorar periodicamente a estabilidade do HTML e da paginação.
- Validar explicitamente páginas vazias e erro de parâmetro em nova sonda bounded.
- Reavaliar a rota PJe somente se publicar API oficial sem desafio.
