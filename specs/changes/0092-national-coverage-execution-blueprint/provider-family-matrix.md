# Matriz de famílias e lacunas

Esta matriz é um roteiro de descoberta, não uma declaração de funcionamento.
O estado real vem dos inventários gerados e de evidências live recentes.

## Tribunais estaduais

| Autoridade | CJPG (1º grau) | CJSG (2º grau) | Ordem de trabalho |
| --- | --- | --- | --- |
| TJAC | descobrir/validar | revalidar `tjac_cjsg` | Onda A + CJPG |
| TJAL | descobrir/validar | revalidar `tjal_cjsg` | Onda A + CJPG |
| TJAP | rota oficial ou bloqueio | rota oficial ou bloqueio | não contornar Turnstile |
| TJAM | descobrir/validar | revalidar `tjam_cjsg` | Onda A + CJPG |
| TJBA | Banco de Sentenças a classificar | `tjba_graphql` | B1 + CJPG |
| TJCE | rota oficial ou bloqueio | `tjce_cjsg`/alternativa | bloqueio de transporte explícito |
| TJDFT | descobrir/validar | `tjdf_juris` | B1 + primeiro grau separado |
| TJES | `tjes_cjpg` | `tjes_jurisprudencia` PJe2G | revalidar grau |
| TJGO | descobrir/validar | `tjgo_projudi_jurisprudencia` | B2 |
| TJMA | `tjma_jurisconsult` contextual | rota geral a descobrir | não promover contexto |
| TJMG | `tjmg_dspace_jurisprudencia`/rota oficial | `tjmg_jurisprudencia` | validar desafio e grau |
| TJMS | `tjms_cjpg` | `tjms_cjsg` | Onda A + CJPG |
| TJMT | descobrir/validar | `tjmt_jurisprudencia_api` | B1 + CJPG |
| TJPA | banco restrito/alternativa | `tjpa_jurisprudencia_bff` | B1 + CJPG |
| TJPB | descobrir/validar | `tjpb_pje_jurisprudencia` | B1 + CJPG |
| TJPE | rota JSF/alternativa | rota oficial ou bloqueio | não converter 403 em vazio |
| TJPI | descobrir/validar | `tjpi_juspi` | B2 + CJPG |
| TJPR | descobrir/validar | `tjpr_jurisprudencia` | B2 + CJPG |
| TJRJ | banco/rota separada | `tjrj_eproc_jurisprudencia` | B3 + CJPG |
| TJRN | descobrir/validar | `tjrn_jurisprudencia` | B1 + CJPG |
| TJRO | rota própria, não Liame | `tjro_jurisprudencia` | B3 + CJPG |
| TJRR | descobrir/validar | `tjrr_juris` | B2 + CJPG |
| TJRS | descobrir/validar | `tjrs_solr` | B2 + CJPG |
| TJSC | descobrir/validar | `tjsc_eproc_jurisprudencia` | B3 + CJPG |
| TJSE | boletim curado separado | rota geral a descobrir | não promover boletim como geral |
| TJSP | `tjsp_cjpg` condicionado | CJSG controlado | rota oficial/apoio institucional |
| TJTO | `tjto_cjpg` | `tjto_jurisprudencia` | B2 + validar `tip_criterio_inst=2` |

## Outras famílias

| Família | Superfícies | Regra de classificação |
| --- | --- | --- |
| Federal | TRF1–6, TNU, CJF | separar EPROC/JURIS/PORTAL e grau |
| Superior | STJ, STF, TST, STM | informativo não é acórdão geral |
| Trabalho | TRT1–24, TST | ementário, PJe e jurisprudência têm papéis distintos |
| Eleitoral | TSE, TREs, SJUR | boletim/tema não substitui decisão textual |
| Militar | STM e tribunais estaduais militares | confirmar coleção e instância |
| Controle | TCU, TCEs | fonte especializada, não contar como TJ |

## Critério de “coberto”

Uma célula só muda para `covered` quando o registro de promoção comprovar os
oito gates. `implemented`, `live_validated` e `federation_enabled` continuam
sendo dimensões distintas.
