# `tjpb_pje_jurisprudencia`

## Identidade

- Fonte oficial: Banco de Jurisprudencia PJe do TJPB.
- Categoria: `court_jurisprudence`.
- Familia tecnica: `pje_jurisprudencia_estadual`.
- URL inicial: `https://pje-jurisprudencia.tjpb.jus.br/`.
- Status de acesso: `public` na busca observada; desafios de acesso continuam classificados.
- Status no NanoJuris: implementado para busca e detalhe HTML publico.

## Contrato HTTP

- Rota observada:
  - `GET /`
- Sinais do formulario:
  - ementa;
  - inteiro teor;
  - numero do processo;
  - classe;
  - orgao julgador;
  - relator;
  - data;
  - origem de documento.
- Busca: `POST /api/jurisprudencia/pesquisar` com `_token`, objeto `jurisprudencia` e `page`.
- Detalhe: `GET /jurisprudencia/view/{id}?words={termos}`.
- Paginacao: pagina baseada em um; a resposta live retornou dez hits por pagina.

Se a aquisição do token receber uma página com marcadores de CAPTCHA/WAF, o
provider levanta `AccessControlRequiredError`. Uma alteração HTML sem esses
marcadores continua sendo `ParserContractChangedError`; nenhum desafio é
resolvido automaticamente.

## Dados retornados

- Campos esperados:
  - numero do processo;
  - classe;
  - orgao julgador;
  - relator;
  - data;
  - ementa;
  - inteiro teor ou link.
- Campos canonicos esperados: `CanonicalDecision`.
- Inteiro teor: validado por chamada pública sob demanda; o corpo não é
  persistido no artefato live.

## Comportamento observado

- Probe `requests` com User-Agent NanoJuris: HTTP 200 e formulario publico.
- `Invoke-WebRequest`/PowerShell: Cloudflare managed challenge.
- Busca com resultado: o parser e exercitado por fixture JSON versionada; isso
  prova somente o mapeamento local, nao a disponibilidade atual do endpoint.
- Risco: alto enquanto o desafio variar por cliente.

## Fixtures

- [x] `tests/fixtures/tjpb_pje_jurisprudencia_success.json` (replay sintético,
  sem dados reais ou credenciais).
- [x] HTML inicial sem desafio (observado na sessão pública; não persistido).
- [x] HAR de busca real: deliberadamente não persistido por política de
  privacidade; o contrato é reproduzido pelo teste e pelo smoke live.
- [x] Busca vazia: cenário coberto pelo contrato compartilhado e pelo parser.
- [x] Resposta Cloudflare/challenge para diagnóstico em
  `tests/fixtures/tjpb_access_control.html`.

## MCP e agentes

- Quando usar: somente depois de chamada reproduzivel sem desafio.
- Quando pular: se o ambiente receber Cloudflare, captcha ou desafio.
- Mensagem segura: "A fonte TJPB/PJe mostra formulario publico, mas o acesso
  automatizado deve respeitar eventuais desafios sem bypass."
- Riscos: variacao de WAF por cliente/ambiente.

## Validacao live 2026-08-11

- Catalogos, busca e detalhe responderam HTTP 200; a busca com `dano moral` retornou total 48.534 e 10 hits.
- O bundle confirmou os endpoints de origens, classes, orgaos, relatores, pesquisa e detalhe por `_id`; o POST exige `_token` da sessao publica.

Evidencia detalhada: [candidate-live-validation-2026-08-11.md](https://github.com/ndtj/nanojuris/blob/main/docs/candidate-live-validation-2026-08-11.md).

## Implementacao 2026-08-11

- `TjpbPjeJurisprudenciaProvider` obtem o token CSRF da pagina publica a cada busca.
- A busca normaliza `_id`, ementa, numero de processo, data e URL publica do detalhe.
- `get_document()` remove elementos de navegacao e preserva hash, tamanho, URL e texto HTML.
- O provider nao tenta resolver WAF, captcha ou qualquer validacao humana.

## Evidência live ciclo 55 — 2026-09-05

- Busca `responsabilidade civil`: HTTP 200 JSON, 2 registros na página 1 e 2
  na página 2, total reportado 26.092 e IDs sem sobreposição.
- Detalhe do primeiro resultado: HTTP 200 `text/html`, 6.495 bytes, hash
  `0d8350f43223b5f76bb419c81506e023cc9f82aa367ef50e6561b429f44db7ec`, texto
  extraído com status `complete`.
- Artefato redigido: `docs/provider-discovery/tjpb-pje-live-20260905-cycle55.json`.
- A promoção técnica é automática: busca, paginação, detalhe, contrato,
  fixtures e qualidade passaram. Desafios futuros continuam sendo expostos
  como `access_control_required`, nunca como vazio.

## Proximos passos — fechamento técnico

- [x] Confirmar que a busca reproduz por `requests` em sessão pública.
- [x] Criar parser, teste offline e fixture sintética de busca.
- [x] Adicionar fixture segura de desafio e preservar a classificação de acesso.
- [x] Promover para a busca federada após o ciclo live 55.
## Contrato CJSG fechado - 2026-09-05

- A API PJe pública é tratada como superfície textual de segundo grau:
  `authority=TJPB`, `branch=state`, `degree=second`, `instance=second` e
  `collection=CJSG`.
- Consultas de primeiro grau são rejeitadas; registros que contenham uma
  sentença explicitamente de primeiro grau também são rejeitados, evitando
  contaminar a matriz.
- O resultado canônico inclui classe, órgão julgador, relator, tipo documental,
  URL de detalhe e `field_provenance`, mantendo o payload original em `raw`.
- Com a evidência live do ciclo 55 (páginas 1/2 e detalhe público), os oito
  gates técnicos da superfície CJSG estão fechados. Bloqueios futuros são
  reportados como controle de acesso, nunca como lista vazia.

### Paridade de payload 2026-09

- `id_origem` usa `8,2` quando nenhum filtro de origem foi solicitado.
- O backend espera `teor` e a chave legada `nr_rocesso`.
- `X-Requested-With: XMLHttpRequest` acompanha o POST de pesquisa.
- A validação de primeiro grau usa campos estruturados; `sentenca` dentro da
  ementa não é, sozinha, evidência de primeiro grau.
