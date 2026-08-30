# Validacao Live Mais Recente

As evidencias live machine-readable do NanoJuris ficam em
[`validation/runs/`](validation/runs/). O catalogo de cobertura le os arquivos
JSON desse diretorio e seleciona a observacao mais recente de cada provider;
ele nao deriva disponibilidade de edicao manual em Markdown.

A ultima rodada de referencia com rede limpa esta registrada em
[`validation/runs/20260816T020958Z-unified-reference-no-env-proxy.json`](validation/runs/20260816T020958Z-unified-reference-no-env-proxy.json)
e em sua [versao legivel](validation/runs/20260816T020958Z-unified-reference-no-env-proxy.md).

Para registrar uma nova rodada autenticada com inventario de rotas, resultados
por provider e checklist de redacao, use o
[template de rodada Playwright](validation/runs/playwright-live-run-template.md).

A auditoria ampla do Studio permanece em
[qa/studio-provider-audit-2026-08-15.md](qa/studio-provider-audit-2026-08-15.md),
e a rodada historica anterior em
[live-validation-2026-08-15.md](live-validation-2026-08-15.md).

Cada artefato registra a consulta, seu hash, fontes chamadas, estado
operacional, totais observados, paginação, latencia, estado de acesso quando
observado e limitações. Nenhuma rodada representa monitoramento continuo ou
garantia de disponibilidade futura.

## Validacao integrada da plataforma

Em `2026-08-28`, uma sessao autenticada da plataforma em producao consultou o
catalogo de 45 providers em quatro janelas. O resultado foi parcial: 31 fontes
retornaram dados, 10 tiveram falha classificada e 4 foram ignoradas por nao
declararem suporte a busca unificada. A paginacao e o reader foram exercitados.

O assistente retornou HTTP 502 nessa execucao, sem resposta textual ou citacoes.
Os logs de execucao OCI classificaram a causa: o Gemini terminou com
`finish_reason=max_tokens` antes de fechar o JSON. A correcao local configura
`reasoning_effort=MINIMAL`, preservando a validacao estrita do envelope; ela
ainda precisa ser empacotada e publicada antes de uma nova chamada live.
Essa evidencia pertence a integracao da plataforma, nao e uma nova validacao
isolada de cada endpoint externo. Veja o resumo sanitizado em
[`validation/runs/20260828T010539Z-platform-live-summary.md`](validation/runs/20260828T010539Z-platform-live-summary.md)
e o JSON correspondente.

### Inventario de rotas observado

O trace registrou apenas as rotas emitidas pelo navegador: `GET`
`/auth/login/oracle`, `/auth/callback` e `/auth/session`; `GET`
`/api/v1/sources`, `/api/v1/keys`, `/api/v1/admin/access`,
`/api/v1/admin/users` e `/api/v1/admin/audit`; `POST` `/api/v1/search` e
`/bff/assistant`. Queries administrativas e parâmetros de busca foram
redigidos. A tabela não representa rotas apenas documentadas ou descobertas em
JavaScript.
