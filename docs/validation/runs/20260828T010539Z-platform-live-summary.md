# Validação live da plataforma — providers NanoJuris

Data da execução: `2026-08-28T01:05:39Z`  
Ambiente: **produção**  
Modo: busca autenticada, seleção `all_sources`.

Este documento é um resumo sanitizado do trace de produção. Credenciais, cookies, tokens, corpos de resposta e request IDs foram omitidos. O JSON de evidência é [20260828T010539Z-platform-live-summary.json](20260828T010539Z-platform-live-summary.json).

## Resultado executivo

- Sessão autenticada: **sim** (HTTP 200).
- Catálogo: **45 providers** (HTTP 200).
- Providers pesquisados: **41**.
- Providers com dados retornados: **31**.
- Providers com falha explícita: **10**.
- Providers ignorados por capability: **4**.
- Total agregado observado nas quatro janelas: **294**; não representa um total deduplicado global.

## Janelas de busca

| Janela | Providers | Resultados na página | Total informado | Erros |
|---:|---:|---:|---:|---:|
| 1 | 10 | 10 | 39 | 5 |
| 2 | 11 | 10 | 98 | 1 |
| 3 | 11 | 10 | 79 | 3 |
| 4 | 9 | 10 | 78 | 1 |

A paginação avançou com sucesso: **Pagina 2 de 30 (11-20 de 294)**. Reader e detalhe foram abertos/capturados, e a área administrativa foi aberta.

## Providers com dados

`cnj_jurisprudencia`, `stj_informativo`, `stm_jurisprudencia`, `tce_sp_jurisprudencia`, `tcu_jurisprudencia`, `tjac_cjsg`, `tjal_cjsg`, `tjam_cjsg`, `tjba_graphql`, `tjce_informativos`, `tjce_sjuris`, `tjdf_juris`, `tjgo_projudi_jurisprudencia`, `tjms_cjsg`, `tjmt_jurisprudencia_api`, `tjpa_jurisprudencia_bff`, `tjpi_juspi`, `tjpr_jurisprudencia`, `tjrj_eproc_jurisprudencia`, `tjrr_juris`, `tjrs_solr`, `tjsc_eproc_jurisprudencia`, `tjsp_eproc_jurisprudencia`, `tjsp_nugepnac`, `tjto_jurisprudencia`, `tnu_eproc_jurisprudencia`, `trf2_eproc_jurisprudencia`, `trf4_eproc_jurisprudencia`, `trf5_jurisprudencia`, `trf6_eproc_jurisprudencia`, `tst_jurisprudencia`

## Falhas classificadas

- `bnp_pangea`: QueryRejectedError
- `cjf_jurisprudencia`: AccessControlRequiredError
- `stf_informativo`: SslVerificationError
- `stf_juris`: SslVerificationError
- `stj_scon`: AccessControlRequiredError
- `tjce_cjsg`: AccessControlRequiredError
- `tjpb_pje_jurisprudencia`: AccessControlRequiredError
- `tjpe_jurisprudencia`: SslVerificationError
- `tjsp_cjsg`: AccessControlRequiredError
- `tre_sp_temas`: SourceUnavailableError

Falhas não foram convertidas em resultados vazios. Elas representam bloqueio, erro de transporte, TLS ou mudança/recusa da fonte conforme o envelope retornado pela plataforma.

## Providers ignorados

- `justica_eleitoral_sjur`
- `stj_dados_abertos_jurisprudencia`
- `tjma_jurisconsult`
- `tjro_liame`

Essas fontes foram omitidas da busca unificada porque a capability declarou ausência de suporte explícito; isso não significa indisponibilidade.

## Assistente de IA

- Endpoint: `/bff/assistant`.
- Resultado: **HTTP 502 — Bad Gateway**.
- Resposta textual: **0 caracteres**.
- Citações: **0**.
- Latência: **23297 ms**.

A falha do assistente é um problema operacional da integração live e permanece aberta. O trace não contém resposta da IA para documentar.

## Inventario de rotas observado

O navegador emitiu somente as rotas abaixo. Queries administrativas e
parametros de busca foram redigidos no artefato; rotas apenas documentadas ou
encontradas em JavaScript nao foram promovidas para este inventario.

| Metodo | Rota | Finalidade | Status observado | Tentativas |
|---|---|---|---|---:|
| `GET` | `/auth/login/oracle` | iniciar login Oracle | 303 | 1 |
| `GET` | `/auth/callback` | concluir retorno OAuth | 303 | 1 |
| `GET` | `/auth/session` | confirmar sessao | 200, 401, 404 | 12 |
| `GET` | `/api/v1/sources` | carregar catalogo | 200 | 2 |
| `POST` | `/api/v1/search` | busca federada e paginacao | 200 | 4 |
| `POST` | `/bff/assistant` | assistente contextual | 502 | 1 |
| `GET` | `/api/v1/keys` | area de chaves | 200 | 1 |
| `GET` | `/api/v1/admin/access` | autorizacao do painel | 200 | 1 |
| `GET` | `/api/v1/admin/users` | diretorio administrativo | 200 | 1 |
| `GET` | `/api/v1/admin/audit` | auditoria administrativa | 200 | 1 |

As rotas de busca, reader e paginacao foram exercitadas pela mesma superficie
`/api/v1/search`; o trace nao inventaria endpoints internos dos providers.

## Diagnóstico do navegador

- Falhas de requests registradas pelo runner: **0**.
- Erros de página: **0**.
- Erros de sessão: **1**.
- Sinais de console: {"401":12,"404":1,"502":1,"invalid_region":1,"password_form_warning":1,"unsafe_header":2}.

Os sinais 401 ocorreram durante a transição de autenticação e não impediram a sessão autenticada posterior. Os sinais 502/404 e o aviso de formulário devem ser acompanhados em uma rodada específica de diagnóstico.

## Conclusão

A produção disponibilizou o catálogo completo, a busca federada parcial, resultados de 31 providers, paginação e reader. A execução não comprova disponibilidade integral dos 45 providers nem funcionamento do assistente: 10 providers falharam explicitamente, 4 foram ignorados por capability e o assistente retornou 502. Nenhuma correção ou alteração de produção foi inferida a partir deste trace.
