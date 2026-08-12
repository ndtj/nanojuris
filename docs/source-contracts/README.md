# Dossies De Fonte

Esta pasta e a camada de compatibilidade dos dossies tecnicos. A documentacao
canonica por provider esta em
[docs/providers/](../providers/README.md), com um diretorio proprio para cada
fonte. Os arquivos desta pasta continuam completos e preservados para manter
links antigos, referencias externas e agentes que ja conhecem este caminho.

Cada arquivo registra contrato publico observado, lacunas, fixtures e
criterios de uso via MCP. O catalogo central esta em
[docs/registry/providers.json](../registry/providers.json).

Regra de manutencao: todo provider implementado em `src/nanojuris/providers`
deve possuir dossie canonico em `docs/providers/<id>/README.md` e copia legada
com o mesmo nome. Fontes ainda nao implementadas devem ficar marcadas como
`candidato` para nao serem confundidas com provider pronto.

Use `nanojuris contratos --fonte <provider>` para comparar o dossie com a
matriz viva declarada pelo codigo.

A validacao live mais recente dos candidatos esta em
`docs/candidate-live-validation-2026-08-11.md`.

## Providers Implementados

| Provider | Categoria | Dossie |
| --- | --- | --- |
| `bnp_pangea` | precedentes qualificados | [bnp_pangea.md](bnp_pangea.md) |
| `cnj_jurisprudencia` | jurisprudencia curada | [cnj_jurisprudencia.md](cnj_jurisprudencia.md) |
| `comunica_pje` | comunicacoes judiciais | [comunica_pje.md](comunica_pje.md) |
| `tnu_eproc_jurisprudencia` | jurisprudencia eproc federal | [tnu_eproc_jurisprudencia.md](tnu_eproc_jurisprudencia.md) |
| `stf_informativo` | jurisprudencia curada | [stf_informativo.md](stf_informativo.md) |
| `stf_juris` | jurisprudencia superior | [stf_juris.md](stf_juris.md) |
| `stj_informativo` | jurisprudencia curada | [stj_informativo.md](stj_informativo.md) |
| `stj_scon` | jurisprudencia superior | [stj_scon.md](stj_scon.md) |
| `stm_jurisprudencia` | jurisprudencia judicial | [stm_jurisprudencia.md](stm_jurisprudencia.md) |
| `tst_jurisprudencia` | jurisprudencia trabalhista superior | [tst_jurisprudencia.md](tst_jurisprudencia.md) |
| `tce_sp_jurisprudencia` | jurisprudencia administrativa | [tce_sp_jurisprudencia.md](tce_sp_jurisprudencia.md) |
| `tjce_informativos` | jurisprudencia curada | [tjce_informativos.md](tjce_informativos.md) |
| `tjac_cjsg` | jurisprudencia CJSG/e-SAJ | [tjac_cjsg.md](tjac_cjsg.md) |
| `tjac_esaj_cpopg` | consulta processual | [tjac_esaj_cpopg.md](tjac_esaj_cpopg.md) |
| `tjal_cjsg` | jurisprudencia CJSG/e-SAJ | [tjal_cjsg.md](tjal_cjsg.md) |
| `tjam_cjsg` | jurisprudencia CJSG/e-SAJ | [tjam_cjsg.md](tjam_cjsg.md) |
| `tjdf_juris` | jurisprudencia judicial | [tjdf_juris.md](tjdf_juris.md) |
| `tjgo_projudi_jurisprudencia` | jurisprudencia judicial | [tjgo_projudi_jurisprudencia.md](tjgo_projudi_jurisprudencia.md) |
| `tjms_cjsg` | jurisprudencia CJSG/e-SAJ | [tjms_cjsg.md](tjms_cjsg.md) |
| `tjpi_juspi` | jurisprudencia judicial | [tjpi_juspi.md](tjpi_juspi.md) |
| `tjpr_jurisprudencia` | jurisprudencia judicial | [tjpr_jurisprudencia.md](tjpr_jurisprudencia.md) |
| `tjsp_cjsg` | jurisprudencia CJSG/e-SAJ | [tjsp_cjsg.md](tjsp_cjsg.md) |
| `tjsp_eproc_jurisprudencia` | jurisprudencia eproc | [tjsp_eproc_jurisprudencia.md](tjsp_eproc_jurisprudencia.md) |
| `tjsp_esaj_cpopg` | consulta processual | [tjsp_esaj_cpopg.md](tjsp_esaj_cpopg.md) |
| `tjsp_nugepnac` | precedentes locais | [tjsp_nugepnac.md](tjsp_nugepnac.md) |
| `tre_sp_temas` | jurisprudencia eleitoral tematica | [tre_sp_temas.md](tre_sp_temas.md) |
| `trf2_eproc_jurisprudencia` | jurisprudencia eproc federal | [trf2_eproc_jurisprudencia.md](trf2_eproc_jurisprudencia.md) |
| `trf4_eproc_jurisprudencia` | jurisprudencia eproc federal | [trf4_eproc_jurisprudencia.md](trf4_eproc_jurisprudencia.md) |
| `trf6_eproc_jurisprudencia` | jurisprudencia eproc federal | [trf6_eproc_jurisprudencia.md](trf6_eproc_jurisprudencia.md) |

## Contratos De Pesquisa E Expansao

| Fonte | Status | Dossie |
| --- | --- | --- |
| Justica Eleitoral SJUR/TSE/TREs | contrato parcial | [justica_eleitoral_sjur.md](justica_eleitoral_sjur.md) |
| STJ Dados Abertos | candidato pronto para adapter de dataset | [stj_dados_abertos_jurisprudencia.md](stj_dados_abertos_jurisprudencia.md) |
| TJSE Pesquisa Judicial | formulario JSF, captcha na busca | [tjse_jurisprudencia.md](tjse_jurisprudencia.md) |
| TJPE Consulta Jurisprudencia | REST publico, candidato pronto para fixture | [tjpe_jurisprudencia.md](tjpe_jurisprudencia.md) |
| TJSC/eproc Jurisprudencia | formulario eproc publico, candidato pronto para fixture | [tjsc_eproc_jurisprudencia.md](tjsc_eproc_jurisprudencia.md) |
| TJMA JurisConsult | contrato parcial | [tjma_jurisconsult.md](tjma_jurisconsult.md) |
| TRT2 PJe Jurisprudencia | bloqueio/desafio documentado | [trt2_pje_jurisprudencia.md](trt2_pje_jurisprudencia.md) |
| TJRR/Juris JSF | postback publico reproduzido, candidato pronto para fixture | [tjrr_juris.md](tjrr_juris.md) |
| TJMT Jurisprudencia API | candidato precisa header/payload | [tjmt_jurisprudencia_api.md](tjmt_jurisprudencia_api.md) |
| TJPA Jurisprudencia BFF | BFF publico, busca textual JSON reproduzida; candidato pronto para fixture | [tjpa_jurisprudencia_bff.md](tjpa_jurisprudencia_bff.md) |
| TJCE Jurisprudencia CJSG | e-SAJ oficial documentado; contrato HTTP pendente apos reset TLS | [tjce_cjsg.md](tjce_cjsg.md) |
| TJCE SJURIS | SPA oficial PJe/SAJ; gateway preliminar observado, contrato de resultados pendente | [tjce_sjuris.md](tjce_sjuris.md) |
| TJCE Informativos | provider HTML curado implementado; links oficiais preservados | [tjce_informativos.md](tjce_informativos.md) |
| TRF3 Jurisprudencia | interface oficial rica; nivel B e timeout HTTP registrado | [trf3_jurisprudencia.md](trf3_jurisprudencia.md) |
| TJPB PJe Jurisprudencia | candidato com risco WAF | [tjpb_pje_jurisprudencia.md](tjpb_pje_jurisprudencia.md) |
| TJRJ/eproc Jurisprudencia | candidato pronto para fixture | [tjrj_eproc_jurisprudencia.md](tjrj_eproc_jurisprudencia.md) |
| Falcao/Justica do Trabalho | candidato prioritario bloqueado no probe | [falcao_jt.md](falcao_jt.md) |
| TRF5 Jurisprudencia | candidato pronto para fixture | [trf5_jurisprudencia.md](trf5_jurisprudencia.md) |
| CJF/TRF1 Jurisprudencia | candidato pronto para fixture | [cjf_jurisprudencia.md](cjf_jurisprudencia.md) |
| TCU Jurisprudencia e dados abertos | dataset publico pronto para adapter; pesquisa interativa protegida | [tcu_jurisprudencia.md](tcu_jurisprudencia.md) |
| CNJ Informativos de Jurisprudencia | provider HTML/PDF implementado; conteudo curado | [cnj_jurisprudencia.md](cnj_jurisprudencia.md) |
| TJAP/Tucujuris | superficie institucional identificada; desafio no acesso limpo | [tjap_tucujuris.md](tjap_tucujuris.md) |
| TJES Jurisprudencia | resultado legado indexado; portal atual instavel | [tjes_jurisprudencia.md](tjes_jurisprudencia.md) |
| TJMG Espelho de Acordao | formulario e ajuda oficiais; busca textual com captcha | [tjmg_jurisprudencia.md](tjmg_jurisprudencia.md) |
| TJRN Jurisprudencia | busca unificada anunciada; portal respondeu 403 | [tjrn_jurisprudencia.md](tjrn_jurisprudencia.md) |
| TJTO Jurisprudencia | consulta indexada com campos ricos; replay HTTP pendente | [tjto_jurisprudencia.md](tjto_jurisprudencia.md) |
| TJBA GraphQL | busca JSON estruturada validada; fixture pendente | [tjba_graphql.md](tjba_graphql.md) |
| TJPR Jurisprudencia | provider HTML implementado; busca e parser validados | [tjpr_jurisprudencia.md](tjpr_jurisprudencia.md) |
| TJRS AJAX/SOLR | resposta estruturada com facets validada; parser pendente | [tjrs_solr.md](tjrs_solr.md) |
| TJRO LIAME | catalogo publico de precedentes; sem busca geral de acordaos | [tjro_liame.md](tjro_liame.md) |

## Fila De Desenvolvimento

A ordem de implementacao dos proximos providers fica em
[provider-development-queue.md](../provider-development-queue.md).
