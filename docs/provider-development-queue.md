# Provider Development Queue

Este documento organiza a fila de novos providers do NanoJuris. Ele separa
fontes ja implementadas, candidatos prontos para fixture/parser e rotas que
dependem de investigacao adicional.

Regra de produto: nenhum provider deve ser implementado antes de existir um
dossie canonico em `docs/providers/<provider>/README.md`, uma entrada no
registro central e uma copia de compatibilidade em `docs/source-contracts/`,
com contrato publico observado, limites, fixtures esperadas e decisao de uso
via MCP.

## Status

| Status | Significado | Pode virar codigo? |
| --- | --- | --- |
| `implemented` | Provider existe em `src/nanojuris/providers` e tem dossie proprio. | ja existe |
| `candidate_ready` | Rota publica retornou conteudo juridico valido em sessao limpa. | sim, apos fixture |
| `candidate_needs_har` | Portal oficial existe, mas falta payload/postback/header publico. | nao ainda |
| `documental` | Conteudo publico util, mas nao e busca decisoria geral. | somente catalogo |
| `blocked_or_inconclusive` | Timeout, desafio, captcha, 404 ou contrato insuficiente. | nao |

## Fila Recomendada

| Ordem | Fonte | Status | Dossie | Proximo passo |
| --- | --- | --- | --- | --- |
| 1 | TST pesquisa textual | `implemented` | [tst_jurisprudencia.md](providers/tst_jurisprudencia/README.md) | monitorar contrato live e ampliar filtros |
| 2 | TJRS AJAX/SOLR | `implemented` | [tjrs_solr.md](providers/tjrs_solr/README.md) | validar detalhe/inteiro teor antes de promovê-los |
| 3 | TJBA GraphQL | `candidate_ready` | [route-mapping-results-2026-08-07.md](route-mapping-results-2026-08-07.md) | salvar fixture GraphQL e validar detalhe por UUID |
| 4 | TJPR HTML | `candidate_ready` | [route-mapping-results-2026-08-07.md](route-mapping-results-2026-08-07.md) | salvar fixture publica e implementar parser/paginacao |
| 5 | TJRJ/eproc | `implemented` | [tjrj_eproc_jurisprudencia.md](providers/tjrj_eproc_jurisprudencia/README.md) | adicionar fixtures especificas e monitorar labels |
| 6 | CJF/TRF1 Jurisprudencia | `implemented` | [cjf_jurisprudencia.md](providers/cjf_jurisprudencia/README.md) | validar detalhe externo e superfície unificada separadamente |
| 7 | TRF5 Jurisprudencia | `implemented` | [trf5_jurisprudencia.md](providers/trf5_jurisprudencia/README.md) | ampliar fixtures e validar paginacao/detalhe |
| 8 | Falcao/Justica do Trabalho | `blocked_or_inconclusive` | [falcao_jt.md](providers/falcao_jt/README.md) | repetir GET controlado; HAR publico se disponivel |
| 9 | TJPI/JusPI | `implemented` | [tjpi_juspi.md](providers/tjpi_juspi/README.md) | monitorar live opt-in e ampliar filtros catalogados |
| 10 | TJGO/Projudi | `implemented` | [tjgo_projudi_jurisprudencia.md](providers/tjgo_projudi_jurisprudencia/README.md) | validar paginacao live opt-in e numero de processo |
| 11 | TNU/TRF2/TRF6 eproc federal | `implemented` | [eproc_jurisprudencia_federal.md](providers/eproc_jurisprudencia_federal/README.md) | validar inteiro teor live por instancia e ampliar filtros |
| 12 | TJRR/Juris JSF | `candidate_ready` | [tjrr_juris.md](providers/tjrr_juris/README.md) | salvar fixture sanitizada e mapear paginacao |
| 13 | TJMT/Jurisprudencia API | `blocked_or_inconclusive` | [tjmt_jurisprudencia_api.md](providers/tjmt_jurisprudencia_api/README.md) | repetir apenas se surgir nova superficie publica; nao usar login |
| 14 | TJPA/Jurisprudencia BFF | `implemented` | [tjpa_jurisprudencia_bff.md](providers/tjpa_jurisprudencia_bff/README.md) | validar detalhe e filtros adicionais |
| 15 | TJSC/eproc | `implemented` | [tjsc_eproc_jurisprudencia.md](providers/tjsc_eproc_jurisprudencia/README.md) | adicionar fixtures especificas e monitorar paginacao |
| 16 | TJPB/PJe Jurisprudencia | `implemented` | [tjpb_pje_jurisprudencia.md](providers/tjpb_pje_jurisprudencia/README.md) | monitorar token, WAF e contrato de detalhe |
| 17 | TJMG Jurisprudencia | `blocked_or_inconclusive` | ainda sem ficha propria | nao automatizar enquanto a busca exigir captcha HTTP 401 |
| 18 | TJRJ/eJURIS legado | `candidate_needs_har` | ainda sem ficha propria | mapear WebForms e confirmar reCAPTCHA na busca |
| 19 | TSE/SJUR beta | `candidate_needs_har` | [justica_eleitoral_sjur.md](providers/justica_eleitoral_sjur/README.md) | HAR da nova SPA e endpoint de resultados |
| 20 | TJCE/e-SAJ CJSG | `candidate_needs_har` | [tjce_cjsg.md](providers/tjce_cjsg/README.md) | capturar HAR limpo e reproduzir formulario; nao forcar reset TLS |
| 21 | TJPE Consulta Jurisprudencia | `candidate_ready` | [tjpe_jurisprudencia.md](providers/tjpe_jurisprudencia/README.md) | capturar fixtures REST e implementar parser/paginacao |
| 22 | TJSE Jurisprudencia Judicial | `blocked_or_inconclusive` | [tjse_jurisprudencia.md](providers/tjse_jurisprudencia/README.md) | HAR limpo com token normal; nao contornar captcha |
| 23 | TJRO/LIAME | `documental` | [tjro_liame.md](providers/tjro_liame/README.md) | tratar como precedentes/catalogo |
| 24 | TJES | `candidate_needs_har` | [tjes_jurisprudencia.md](providers/tjes_jurisprudencia/README.md) | capturar fluxo legado ou validar portal atual |
| 25 | TCU Jurisprudencia e dados abertos | `implemented` | [tcu_jurisprudencia.md](providers/tcu_jurisprudencia/README.md) | cache incremental e adapters de outros datasets |
| 26 | CNJ Informativos de Jurisprudencia | `candidate_ready` | [cnj_jurisprudencia.md](providers/cnj_jurisprudencia/README.md) | fixture HTML, parser de itens e links PDF |
| 27 | TST Jurisprudencia | `implemented` | [tst_jurisprudencia.md](providers/tst_jurisprudencia/README.md) | monitorar contrato live e ampliar filtros |
| 28 | TJCE Informativos | `candidate_ready` | [tjce_informativos.md](providers/tjce_informativos/README.md) | salvar fixture HTML, parser de itens e links PDF |
| 29 | TRF3 Jurisprudencia | `candidate_needs_har` | [trf3_jurisprudencia.md](providers/trf3_jurisprudencia/README.md) | captura automatica da busca; testar acordao por processo separadamente |
| 30 | TJAP/Tucujuris | `blocked_or_inconclusive` | [tjap_tucujuris.md](providers/tjap_tucujuris/README.md) | nova superficie publica sem desafio |
| 31 | TJMG Espelho de Acordao | `blocked_or_inconclusive` | [tjmg_jurisprudencia.md](providers/tjmg_jurisprudencia/README.md) | nao automatizar captcha; buscar superficie oficial alternativa |
| 32 | TJRN Jurisprudencia | `blocked_or_inconclusive` | [tjrn_jurisprudencia.md](providers/tjrn_jurisprudencia/README.md) | HAR publico da busca unificada |
| 33 | TJTO Jurisprudencia | `candidate_needs_har` | [tjto_jurisprudencia.md](providers/tjto_jurisprudencia/README.md) | reproduzir query, filtros, detalhe e inteiro teor |
| 34 | TJBA GraphQL | `candidate_ready` | [tjba_graphql.md](providers/tjba_graphql/README.md) | fixture GraphQL, parser e detalhe |
| 35 | TJPR HTML | `candidate_ready` | [tjpr_jurisprudencia.md](providers/tjpr_jurisprudencia/README.md) | fixture de sucesso/vazio e parser |
| 36 | TJRS AJAX/SOLR | `implemented` | [tjrs_solr.md](providers/tjrs_solr/README.md) | fixture live opt-in e detalhe/inteiro teor |

## Checklist De Entrada Para Implementar

Antes de criar `src/nanojuris/providers/<provider>.py`:

- [ ] A fonte e oficial ou institucionalmente confiavel.
- [ ] A rota publica foi reproduzida sem cookie pessoal, login, captcha ou
  desafio.
- [ ] Existe HTML/JSON real com conteudo juridico valido.
- [ ] Existe fixture real de sucesso representativa do contrato observado.
- [ ] Existe fixture de vazio ou erro esperado.
- [ ] O dossie define campos canonicos e lacunas.
- [ ] O dossie define quando o MCP deve usar ou pular a fonte.
- [ ] O provider declara `ProviderCapabilities`.
- [ ] O parser funciona offline antes do teste live.

## Ordem De Desenvolvimento Recomendada

1. **TJBA, TJPR e CJF/TRF1**: fechar fixtures e implementar os candidatos que
   ja retornaram conteudo decisorio em sessao limpa. TJPB, TJPA e TJRS agora
   possuem adapters iniciais e devem receber aprofundamento incremental. O TST
   ja possui provider e dossie; o registro de descoberta esta em
   [public-provider-discovery-2026-08-10.md](public-provider-discovery-2026-08-10.md).
2. **TRF5 e TJRR**: implementar os fluxos HTML/JSF com fixtures proprias e
   classificacao explicita de paginacao e controles de acesso.
3. **Falcao/JT**: somente avancar se a consulta publica normal deixar de
   retornar bloqueio; ele pode reduzir a necessidade de providers isolados de
   TRTs.
4. **TJRR/Juris JSF**: alto potencial, mas exige entender `ViewState` e
   postback PrimeFaces sem usar sessao privada.
5. **TJPA e TCU**: aprofundar detalhe, cache incremental e datasets adicionais;
   a busca inicial ja esta implementada com limites documentados.
6. **TJMT API**: somente avancar se surgir uma nova superficie publica
   reproduzivel; a revalidacao atual encontrou login e HTTP 401.
7. **TJPB/TJSC/TJRJ**: manter monitoramento live opt-in e adicionar fixtures
   especificas, sem contornar WAF, captcha ou limites.
8. **Documentais e dados abertos**: TJSE e TJRO podem virar providers de
   catalogo; o TJPE ja possui candidato REST decisorio e o TCU possui um
   dataset publico pronto para adapter streaming.

## Regra Para Promover Status

- `candidate_ready -> implemented`: fixture, parser, provider, testes e
  `ProviderCapabilities`.
- `candidate_needs_har -> candidate_ready`: HAR limpo e chamada reproduzida por
  `requests` com headers minimos.
- `documental -> candidate_ready`: rota de resultados decisorios localizada.
- `blocked_or_inconclusive -> candidate_needs_har`: portal responde e mostra
  formulario/fluxo publico reproduzivel.
