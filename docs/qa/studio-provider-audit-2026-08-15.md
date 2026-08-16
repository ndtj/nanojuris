# Auditoria QA do Studio e dos providers - 2026-08-15

## Escopo

Auditoria manual do Studio real com Chromium, em desktop `1440x1000` e mobile
`390x844`, seguida de verificacao live controlada dos 40 providers registrados.
A consulta usada foi `responsabilidade civil`, `page_size=1`, concorrencia
limitada a seis workers e timeout global de 120 segundos.

A rodada nao tentou contornar captcha, WAF, login, geoblock ou validacao TLS.
Cada status representa o comportamento observado nesta rede e neste instante.

## Resultado do Studio

- catalogo carregado: **40 providers**;
- selecao inicial: **7 fontes estaveis**;
- perfil recomendado: **34 fontes**;
- selecao de catalogo completo: **40/40**;
- filtro local por provider: aprovado, sem alterar a selecao;
- mobile sem overflow horizontal: aprovado;
- console/page errors: nenhum;
- validacao live do perfil estavel: **4 validas e 3 indisponiveis**.

Prints gerados localmente em `artifacts/studio/`:

- `qa-real-final-initial-desktop.png` - estado inicial;
- `qa-real-final-filter-tjdft.png` - filtro do catalogo por TJDFT;
- `qa-real-final-validation-desktop.png` - painel live concluido;
- `qa-real-final-initial-mobile.png` - estado inicial em viewport mobile.

## Matriz live dos 40 providers

| Provider | Status observado | Leitura QA | Proxima acao |
| --- | --- | --- | --- |
| `bnp_pangea` | `query_rejected` | A fonte rejeitou a consulta generica HTTP 400. | Promover teste com expressao/parametros aceitos e documentar o minimo exigido. |
| `cjf_jurisprudencia` | `valid` | Retornou resultado e total observado. | Validar pagina seguinte e detalhe. |
| `cnj_jurisprudencia` | `empty` | Respondeu sem linhas para o termo. | Confirmar busca com termo existente e manter como fonte curada. |
| `comunica_pje` | `valid` | Retornou comunicacao publica. | Manter separado de jurisprudencia decisoria. |
| `stf_informativo` | `source_unavailable` | Falha de verificacao SSL nesta rede. | Repetir em rede limpa e registrar cadeia TLS; nao desabilitar SSL. |
| `stf_juris` | `source_unavailable` | Falha de verificacao SSL nesta rede. | Repetir em rede limpa e separar WAF de TLS. |
| `stj_dados_abertos_jurisprudencia` | `unsupported_query` | Catalogo/dataset, sem busca jurisprudencial online. | Manter como ingestao local, nao como busca remota. |
| `stj_informativo` | `valid` | Retornou informativo com janela parcial. | Validar detalhes e completude da janela. |
| `stj_scon` | `valid` | Retornou resultado do SCON. | Validar paginacao, campos e inteiro teor. |
| `stm_jurisprudencia` | `valid` | Retornou resultado Solr/HTML. | Validar filtros e detalhe. |
| `tce_sp_jurisprudencia` | `empty` | Respondeu sem resultado para o termo. | Testar termo especifico de sumula/boletim. |
| `tcu_jurisprudencia` | `valid` | Retornou registro do dataset publico. | Documentar que e dataset e validar atualizacao incremental. |
| `tjac_cjsg` | `valid` | Retornou ementa/metadados CJSG. | Validar detalhe e inteiro teor. |
| `tjac_esaj_cpopg` | `unsupported_query` | Consulta exige numero CNJ; provider esta correto. | Usar somente no fluxo de documento/processo. |
| `tjal_cjsg` | `valid` | Retornou resultado CJSG. | Validar detalhe e campos canonicos. |
| `tjam_cjsg` | `valid` | Retornou resultado CJSG. | Validar detalhe e campos canonicos. |
| `tjba_graphql` | `valid` | Retornou resultado GraphQL com total alto. | Validar cursor/paginacao e inteiro teor. |
| `tjce_informativos` | `valid` | Retornou informativo curado. | Manter categoria documental e ampliar filtros editoriais. |
| `tjdf_juris` | `valid` | Retornou resultado e total autoritativo. | Promover como provider de referencia do Studio. |
| `tjgo_projudi_jurisprudencia` | `valid` | Retornou resultado HTML. | Validar paginas seguintes e detalhe. |
| `tjms_cjsg` | `valid` | Retornou resultado CJSG. | Validar detalhe e inteiro teor. |
| `tjpa_jurisprudencia_bff` | `valid` | Retornou resultado BFF com janela parcial. | Ampliar filtros e validar detalhe. |
| `tjpb_pje_jurisprudencia` | `valid` | Retornou resultado PJe. | Validar token/sessao, paginacao e detalhe. |
| `tjpi_juspi` | `valid` | Retornou resultado e total. | Validar inteiro teor e filtros. |
| `tjpr_jurisprudencia` | `valid` | Retornou resultado HTML e total. | Validar paginacao e detalhe. |
| `tjrj_eproc_jurisprudencia` | `valid` | Retornou primeira janela e conteudo. | Comprovar paginacao remota. |
| `tjrr_juris` | `valid` | Retornou 20 itens; provider normaliza page size minimo. | Preservar limite observado e validar pagina JSF seguinte. |
| `tjrs_solr` | `valid` | Retornou resultado AJAX/SOLR. | Validar detalhe, inteiro teor e offset. |
| `tjsc_eproc_jurisprudencia` | `source_changed` | Resposta nao produziu numero de processo esperado. | Capturar fixture live e separar vazio de mudanca de parser. |
| `tjsp_cjsg` | `blocked` | CAPTCHA/controle de acesso observado. | Manter bloqueado, sem bypass; procurar superficie oficial alternativa. |
| `tjsp_eproc_jurisprudencia` | `valid` | Retornou resultado eproc. | Comprovar paginacao e detalhe. |
| `tjsp_esaj_cpopg` | `valid` | Retornou consulta processual publica. | Manter fora da busca decisoria unificada. |
| `tjsp_nugepnac` | `empty` | Fonte respondeu sem resultado para termo livre. | Validar busca por tema/IRDR/IAC. |
| `tnu_eproc_jurisprudencia` | `source_unavailable` | Timeout do portal eproc TNU. | Repetir em janela controlada; nao aumentar indefinidamente o timeout. |
| `tre_sp_temas` | `source_unavailable` | HTTP 403 na rota observada. | Classificar controle de acesso e documentar rota alternativa, se houver. |
| `trf2_eproc_jurisprudencia` | `valid` | Retornou resultado eproc. | Comprovar paginacao e detalhe. |
| `trf4_eproc_jurisprudencia` | `source_unavailable` | HTTP 503 na rota observada. | Repetir live e investigar disponibilidade do portal. |
| `trf5_jurisprudencia` | `valid` | Retornou resultado HTML. | Validar paginacao e inteiro teor. |
| `trf6_eproc_jurisprudencia` | `valid` | Retornou resultado eproc. | Comprovar paginacao e detalhe. |
| `tst_jurisprudencia` | `valid` | Retornou resultado e total alto. | Promover como provider de referencia e validar offsets. |

Resumo apos a correcao da taxonomia:

| Estado | Quantidade |
| --- | ---: |
| `valid` | 27 |
| `empty` | 3 |
| `query_rejected` | 1 |
| `unsupported_query` | 2 |
| `source_changed` | 1 |
| `blocked` | 1 |
| `source_unavailable` | 5 |
| **total** | **40** |

## Achados de produto e UX

### Corrigidos nesta onda

1. O catalogo agora possui filtro local por nome, id ou categoria.
2. Filtrar providers nao modifica a selecao da busca.
3. Nomes e identificadores longos quebram em vez de serem cortados.
4. Mensagens operacionais sao curtas; erros tecnicos ficam em detalhes
   expansiveis.
5. A validacao respeita providers que retornam page size maior que o pedido.
6. A taxonomia separa consulta rejeitada, consulta nao aplicavel e mudanca de
   contrato.

### Riscos ainda abertos

- A busca real ainda nao exibe uma barra de progresso por provider; o usuario
  pode esperar sem saber qual fonte esta lenta.
- O Studio mostra a ultima validacao, mas ainda nao persiste historico local de
  saude por provider.
- A selecao de 40 fontes pode produzir latencia alta e precisa de um deadline
  visivel antes da busca ampla.
- `valid` comprova apenas o contrato minimo de uma pagina, nao a completude de
  toda a jurisprudencia da fonte.

## Proxima onda recomendada

### P0 - Integridade e experiencia de consulta

1. Adicionar estado de progresso por provider na busca e na validacao.
2. Exibir ultima verificacao, latencia e status na ficha expandida da fonte.
3. Criar um modo `amostra rapida` que consulta no maximo 8 providers por vez.
4. Impedir que `todas` seja selecionado silenciosamente em uma busca pesada;
   exigir confirmacao visual com deadline estimado.

### P1 - Promocao tecnica

1. Comprovar paginacao e detalhe para os 27 providers validos.
2. Criar fixture live controlada para TJSC/eproc e decidir entre parser alterado
   ou resposta vazia.
3. Criar testes de contrato parametrizados para page size, pagina, identidade,
   vazio, controle de acesso e detalhe.
4. Promover TJDFT, TST, STJ/SCON, TJRS, TJBA, TJPA e TJPB como primeiro grupo
   de referencia documentado para o Studio.

### P2 - Cobertura madura

1. Separar visualmente jurisprudencia, precedentes, informativos, datasets,
   comunicacoes e consulta processual.
2. Adicionar filtros dinamicos por provider, sem apresentar filtros que a fonte
   nao suporta.
3. Persistir snapshots de validacao com hash da resposta e versao do parser.
4. Medir cobertura de campos canonicos e nao apenas quantidade de resultados.

## Criterio de promocao

Um provider so deve ser promovido para o perfil `maduras` quando possuir:

- contrato documentado e fixture de sucesso;
- fixture de vazio e erro classificado;
- identidade estavel;
- paginacao comprovada ou declarada como nao suportada;
- detalhe/inteiro teor testado quando anunciado;
- validacao live recente sem controle de acesso inesperado;
- limites e lacunas expostos no Studio, CLI e MCP.
