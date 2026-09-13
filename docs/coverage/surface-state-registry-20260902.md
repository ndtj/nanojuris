# Registro canônico de estados das superfícies

Geração: `2026-09-01`; superfícies: **151**; obrigatórias: **125**.

Este artefato é a fonte de verdade para o estado por superfície. `lifecycle`, `contract_status`, `live_status`, `federation_status` e `legal_status` não são equivalentes.

## CJPG/CJSG

| Coleção | Live-validado | Esperado |
|---|---:|---:|
| CJPG | 9 | 27 |
| CJSG | 25 | 27 |

## Contagens por estado

| Dimensão | Contagens |
|---|---|
| `by_lifecycle` | `candidate`=50, `implemented`=101 |
| `by_contract_status` | `blocked_access`=4, `blocked_transport`=1, `candidate`=50, `live_validated`=66, `pending_contract`=29, `source_unavailable`=1 |
| `by_live_status` | `access_control_required`=3, `access_controlled`=3, `blocked_transport`=1, `not_observed`=47, `partial`=27, `source_unavailable`=2, `transport_error`=1, `valid`=67 |
| `by_federation_status` | `blocked`=6, `enabled`=63, `not_enabled`=82 |
| `by_legal_status` | `operator_approved`=65, `pending_human_review`=86 |

## Superfícies

| Superfície | Autoridade | Grau | Coleção | Provider | Contrato | Live | Federação | Legal |
|---|---|---|---|---|---|---|---|---|
| `surface:electoral-first-degree-units:sjur:first:gap` | `ELECTORAL_FIRST_DEGREE_UNITS` | `first` | `SJUR` | — | `candidate` | `not_observed` | `not_enabled` | `pending_human_review` |
| `surface:federal-first-degree-units:eproc:first:gap` | `FEDERAL_FIRST_DEGREE_UNITS` | `first` | `EPROC` | — | `candidate` | `not_observed` | `not_enabled` | `pending_human_review` |
| `surface:labor-first-degree-units:portal:first:gap` | `LABOR_FIRST_DEGREE_UNITS` | `first` | `PORTAL` | — | `candidate` | `not_observed` | `not_enabled` | `pending_human_review` |
| `surface:military-first-degree-units:portal:first:gap` | `MILITARY_FIRST_DEGREE_UNITS` | `first` | `PORTAL` | — | `candidate` | `not_observed` | `not_enabled` | `pending_human_review` |
| `surface:stf:portal:superior:stf-juris` | `STF` | `superior` | `PORTAL` | `stf_juris` | `blocked_transport` | `blocked_transport` | `blocked` | `pending_human_review` |
| `surface:stj:aggregate:superior:stj-dados-abertos-jurisprudencia` | `STJ` | `superior` | `AGGREGATE` | `stj_dados_abertos_jurisprudencia` | `live_validated` | `valid` | `not_enabled` | `operator_approved` |
| `surface:stj:portal:superior:stj-scon` | `STJ` | `superior` | `PORTAL` | `stj_scon` | `blocked_access` | `access_control_required` | `blocked` | `pending_human_review` |
| `surface:stm:portal:superior:stm-jurisprudencia` | `STM` | `superior` | `PORTAL` | `stm_jurisprudencia` | `live_validated` | `valid` | `enabled` | `operator_approved` |
| `surface:tjac:cjpg:first:tjac-banco-sentencas` | `TJAC` | `first` | `CJPG` | `tjac_banco_sentencas` | `live_validated` | `valid` | `not_enabled` | `pending_human_review` |
| `surface:tjac:cjsg:second:tjac-cjsg` | `TJAC` | `second` | `CJSG` | `tjac_cjsg` | `live_validated` | `valid` | `enabled` | `operator_approved` |
| `surface:tjal:cjpg:first:tjal-esmal-banco-sentencas` | `TJAL` | `first` | `CJPG` | `tjal_esmal_banco_sentencas` | `live_validated` | `valid` | `enabled` | `operator_approved` |
| `surface:tjal:cjsg:second:tjal-cjsg` | `TJAL` | `second` | `CJSG` | `tjal_cjsg` | `live_validated` | `valid` | `enabled` | `operator_approved` |
| `surface:tjam:cjpg:first:gap` | `TJAM` | `first` | `CJPG` | — | `candidate` | `not_observed` | `not_enabled` | `pending_human_review` |
| `surface:tjam:cjsg:second:tjam-cjsg` | `TJAM` | `second` | `CJSG` | `tjam_cjsg` | `live_validated` | `valid` | `enabled` | `operator_approved` |
| `surface:tjap:cjpg:first:tjap-banco-sentencas` | `TJAP` | `first` | `CJPG` | `tjap_banco_sentencas` | `live_validated` | `valid` | `enabled` | `operator_approved` |
| `surface:tjap:cjsg:second:tjap-tucujuris` | `TJAP` | `second` | `CJSG` | `tjap_tucujuris` | `blocked_access` | `access_controlled` | `blocked` | `pending_human_review` |
| `surface:tjba:cjpg:first:gap` | `TJBA` | `first` | `CJPG` | — | `candidate` | `not_observed` | `not_enabled` | `pending_human_review` |
| `surface:tjba:cjsg:second:tjba-graphql` | `TJBA` | `second` | `CJSG` | `tjba_graphql` | `live_validated` | `valid` | `enabled` | `operator_approved` |
| `surface:tjba:jurisprudencia:second:tjba-graphql` | `TJBA` | `second` | `JURISPRUDENCIA` | `tjba_graphql` | `live_validated` | `valid` | `enabled` | `operator_approved` |
| `surface:tjce:cjpg:first:gap` | `TJCE` | `first` | `CJPG` | — | `candidate` | `not_observed` | `not_enabled` | `pending_human_review` |
| `surface:tjce:cjsg:second:tjce-cjsg` | `TJCE` | `second` | `CJSG` | `tjce_cjsg` | `live_validated` | `valid` | `enabled` | `operator_approved` |
| `surface:tjce:sjur:second:tjce-sjuris` | `TJCE` | `second` | `SJUR` | `tjce_sjuris` | `live_validated` | `valid` | `enabled` | `operator_approved` |
| `surface:tjdft:cjpg:first:gap` | `TJDFT` | `first` | `CJPG` | — | `candidate` | `not_observed` | `not_enabled` | `pending_human_review` |
| `surface:tjdft:cjsg:second:tjdf-juris` | `TJDFT` | `second` | `CJSG` | `tjdf_juris` | `live_validated` | `valid` | `enabled` | `operator_approved` |
| `surface:tjdft:portal:second:tjdf-juris` | `TJDFT` | `second` | `PORTAL` | `tjdf_juris` | `live_validated` | `valid` | `enabled` | `operator_approved` |
| `surface:tjes:cjpg:first:tjes-cjpg` | `TJES` | `first` | `CJPG` | `tjes_cjpg` | `live_validated` | `valid` | `enabled` | `operator_approved` |
| `surface:tjes:cjsg:second:tjes-jurisprudencia` | `TJES` | `second` | `CJSG` | `tjes_jurisprudencia` | `live_validated` | `valid` | `enabled` | `operator_approved` |
| `surface:tjes:turma-recursal:recursal:tjes-turma-recursal` | `TJES` | `recursal` | `TURMA_RECURSAL` | `tjes_turma_recursal` | `live_validated` | `valid` | `enabled` | `operator_approved` |
| `surface:tjgo:cjpg:first:tjgo-projudi-jurisprudencia` | `TJGO` | `first` | `CJPG` | `tjgo_projudi_jurisprudencia` | `live_validated` | `valid` | `enabled` | `operator_approved` |
| `surface:tjgo:cjsg:second:tjgo-projudi-jurisprudencia` | `TJGO` | `second` | `CJSG` | `tjgo_projudi_jurisprudencia` | `live_validated` | `valid` | `enabled` | `operator_approved` |
| `surface:tjgo:pje:mixed:tjgo-projudi-jurisprudencia` | `TJGO` | `mixed` | `PJE` | `tjgo_projudi_jurisprudencia` | `live_validated` | `valid` | `enabled` | `operator_approved` |
| `surface:tjma:catalog:unknown:tjma-jurisconsult` | `TJMA` | `unknown` | `CATALOG` | `tjma_jurisconsult` | `blocked_access` | `access_controlled` | `blocked` | `pending_human_review` |
| `surface:tjma:cjpg:first:gap` | `TJMA` | `first` | `CJPG` | — | `candidate` | `not_observed` | `not_enabled` | `pending_human_review` |
| `surface:tjma:cjsg:second:gap` | `TJMA` | `second` | `CJSG` | — | `candidate` | `access_controlled` | `not_enabled` | `pending_human_review` |
| `surface:tjmg:cjpg:first:gap` | `TJMG` | `first` | `CJPG` | — | `candidate` | `not_observed` | `not_enabled` | `pending_human_review` |
| `surface:tjmg:cjsg-ejef-boletim:second:tjmg-ejef-boletim-jurisprudencia` | `TJMG` | `second` | `CJSG_EJEF_BOLETIM` | `tjmg_ejef_boletim_jurisprudencia` | `live_validated` | `valid` | `enabled` | `operator_approved` |
| `surface:tjmg:cjsg:second:tjmg-dspace-jurisprudencia` | `TJMG` | `second` | `CJSG` | `tjmg_dspace_jurisprudencia` | `live_validated` | `valid` | `enabled` | `operator_approved` |
| `surface:tjmg:jurisprudencia:second:tjmg-jurisprudencia` | `TJMG` | `second` | `JURISPRUDENCIA` | `tjmg_jurisprudencia` | `live_validated` | `valid` | `enabled` | `operator_approved` |
| `surface:tjmmg:portal:second:tjmmg-jurisprudencia-api` | `TJMMG` | `second` | `PORTAL` | `tjmmg_jurisprudencia_api` | `live_validated` | `valid` | `not_enabled` | `pending_human_review` |
| `surface:tjmrs:portal:second:gap` | `TJMRS` | `second` | `PORTAL` | — | `candidate` | `not_observed` | `not_enabled` | `pending_human_review` |
| `surface:tjms:cjpg:first:tjms-cjpg` | `TJMS` | `first` | `CJPG` | `tjms_cjpg` | `live_validated` | `valid` | `enabled` | `operator_approved` |
| `surface:tjms:cjsg:second:tjms-cjsg` | `TJMS` | `second` | `CJSG` | `tjms_cjsg` | `live_validated` | `valid` | `enabled` | `operator_approved` |
| `surface:tjmsp:portal:second:gap` | `TJMSP` | `second` | `PORTAL` | — | `candidate` | `not_observed` | `not_enabled` | `pending_human_review` |
| `surface:tjmt:cjpg:first:gap` | `TJMT` | `first` | `CJPG` | — | `candidate` | `not_observed` | `not_enabled` | `pending_human_review` |
| `surface:tjmt:cjsg:second:tjmt-jurisprudencia-api` | `TJMT` | `second` | `CJSG` | `tjmt_jurisprudencia_api` | `live_validated` | `valid` | `enabled` | `operator_approved` |
| `surface:tjmt:jurisprudencia:second:tjmt-jurisprudencia-api` | `TJMT` | `second` | `JURISPRUDENCIA` | `tjmt_jurisprudencia_api` | `live_validated` | `valid` | `enabled` | `operator_approved` |
| `surface:tjpa:cjpg:first:gap` | `TJPA` | `first` | `CJPG` | — | `candidate` | `not_observed` | `not_enabled` | `pending_human_review` |
| `surface:tjpa:cjsg:second:tjpa-jurisprudencia-bff` | `TJPA` | `second` | `CJSG` | `tjpa_jurisprudencia_bff` | `live_validated` | `valid` | `enabled` | `operator_approved` |
| `surface:tjpa:jurisprudencia:second:tjpa-jurisprudencia-bff` | `TJPA` | `second` | `JURISPRUDENCIA` | `tjpa_jurisprudencia_bff` | `live_validated` | `valid` | `enabled` | `operator_approved` |
| `surface:tjpb:cjpg:first:gap` | `TJPB` | `first` | `CJPG` | — | `candidate` | `not_observed` | `not_enabled` | `pending_human_review` |
| `surface:tjpb:cjsg:second:tjpb-pje-jurisprudencia` | `TJPB` | `second` | `CJSG` | `tjpb_pje_jurisprudencia` | `live_validated` | `valid` | `enabled` | `operator_approved` |
| `surface:tjpb:pje:second:tjpb-pje-jurisprudencia` | `TJPB` | `second` | `PJE` | `tjpb_pje_jurisprudencia` | `live_validated` | `valid` | `enabled` | `operator_approved` |
| `surface:tjpe:cjpg:first:gap` | `TJPE` | `first` | `CJPG` | — | `candidate` | `not_observed` | `not_enabled` | `pending_human_review` |
| `surface:tjpe:cjsg:second:tjpe-jurisprudencia` | `TJPE` | `second` | `CJSG` | `tjpe_jurisprudencia` | `live_validated` | `valid` | `enabled` | `operator_approved` |
| `surface:tjpe:jurisprudencia:second:tjpe-jurisprudencia` | `TJPE` | `second` | `JURISPRUDENCIA` | `tjpe_jurisprudencia` | `live_validated` | `valid` | `enabled` | `operator_approved` |
| `surface:tjpi:cjpg:first:gap` | `TJPI` | `first` | `CJPG` | — | `candidate` | `not_observed` | `not_enabled` | `pending_human_review` |
| `surface:tjpi:cjsg:second:tjpi-juspi` | `TJPI` | `second` | `CJSG` | `tjpi_juspi` | `live_validated` | `valid` | `enabled` | `operator_approved` |
| `surface:tjpi:portal:second:tjpi-juspi` | `TJPI` | `second` | `PORTAL` | `tjpi_juspi` | `live_validated` | `valid` | `enabled` | `operator_approved` |
| `surface:tjpr:cjpg:first:gap` | `TJPR` | `first` | `CJPG` | — | `candidate` | `not_observed` | `not_enabled` | `pending_human_review` |
| `surface:tjpr:cjsg:second:tjpr-jurisprudencia` | `TJPR` | `second` | `CJSG` | `tjpr_jurisprudencia` | `live_validated` | `valid` | `enabled` | `operator_approved` |
| `surface:tjpr:jurisprudencia:second:tjpr-jurisprudencia` | `TJPR` | `second` | `JURISPRUDENCIA` | `tjpr_jurisprudencia` | `live_validated` | `valid` | `enabled` | `operator_approved` |
| `surface:tjrj:cjpg:first:gap` | `TJRJ` | `first` | `CJPG` | — | `candidate` | `not_observed` | `not_enabled` | `pending_human_review` |
| `surface:tjrj:cjsg:second:tjrj-eproc-jurisprudencia` | `TJRJ` | `second` | `CJSG` | `tjrj_eproc_jurisprudencia` | `live_validated` | `valid` | `enabled` | `operator_approved` |
| `surface:tjrj:eproc:mixed:tjrj-eproc-jurisprudencia` | `TJRJ` | `mixed` | `EPROC` | `tjrj_eproc_jurisprudencia` | `live_validated` | `valid` | `enabled` | `operator_approved` |
| `surface:tjrj:jurisprudencia:mixed:tjrj-ejuris` | `TJRJ` | `mixed` | `JURISPRUDENCIA` | `tjrj_ejuris` | `live_validated` | `valid` | `enabled` | `operator_approved` |
| `surface:tjrn:cjpg:first:gap` | `TJRN` | `first` | `CJPG` | — | `candidate` | `not_observed` | `not_enabled` | `pending_human_review` |
| `surface:tjrn:cjsg:second:tjrn-jurisprudencia` | `TJRN` | `second` | `CJSG` | `tjrn_jurisprudencia` | `live_validated` | `valid` | `enabled` | `operator_approved` |
| `surface:tjrn:jurisprudencia:mixed:tjrn-jurisprudencia` | `TJRN` | `mixed` | `JURISPRUDENCIA` | `tjrn_jurisprudencia` | `live_validated` | `valid` | `enabled` | `operator_approved` |
| `surface:tjro:cjpg:first:tjro-jurisprudencia` | `TJRO` | `first` | `CJPG` | `tjro_jurisprudencia` | `live_validated` | `valid` | `enabled` | `operator_approved` |
| `surface:tjro:cjsg:second:tjro-jurisprudencia` | `TJRO` | `second` | `CJSG` | `tjro_jurisprudencia` | `live_validated` | `valid` | `enabled` | `operator_approved` |
| `surface:tjro:jurisprudencia:mixed:tjro-jurisprudencia` | `TJRO` | `mixed` | `JURISPRUDENCIA` | `tjro_jurisprudencia` | `live_validated` | `valid` | `enabled` | `operator_approved` |
| `surface:tjro:precedent:second:tjro-liame` | `TJRO` | `second` | `PRECEDENT` | `tjro_liame` | `live_validated` | `valid` | `enabled` | `operator_approved` |
| `surface:tjrr:cjpg:first:gap` | `TJRR` | `first` | `CJPG` | — | `candidate` | `not_observed` | `not_enabled` | `pending_human_review` |
| `surface:tjrr:cjsg:second:tjrr-juris` | `TJRR` | `second` | `CJSG` | `tjrr_juris` | `live_validated` | `valid` | `enabled` | `operator_approved` |
| `surface:tjrr:portal:second:tjrr-juris` | `TJRR` | `second` | `PORTAL` | `tjrr_juris` | `live_validated` | `valid` | `enabled` | `operator_approved` |
| `surface:tjrs:cjpg:first:gap` | `TJRS` | `first` | `CJPG` | — | `candidate` | `not_observed` | `not_enabled` | `pending_human_review` |
| `surface:tjrs:cjsg:second:tjrs-solr` | `TJRS` | `second` | `CJSG` | `tjrs_solr` | `live_validated` | `valid` | `enabled` | `operator_approved` |
| `surface:tjrs:portal:second:tjrs-solr` | `TJRS` | `second` | `PORTAL` | `tjrs_solr` | `live_validated` | `valid` | `enabled` | `operator_approved` |
| `surface:tjsc:cjpg:first:gap` | `TJSC` | `first` | `CJPG` | — | `candidate` | `not_observed` | `not_enabled` | `pending_human_review` |
| `surface:tjsc:cjsg:second:tjsc-eproc-jurisprudencia` | `TJSC` | `second` | `CJSG` | `tjsc_eproc_jurisprudencia` | `live_validated` | `valid` | `enabled` | `operator_approved` |
| `surface:tjsc:eproc:mixed:tjsc-eproc-jurisprudencia` | `TJSC` | `mixed` | `EPROC` | `tjsc_eproc_jurisprudencia` | `live_validated` | `valid` | `enabled` | `operator_approved` |
| `surface:tjse:cjpg:first:gap` | `TJSE` | `first` | `CJPG` | — | `candidate` | `not_observed` | `not_enabled` | `pending_human_review` |
| `surface:tjse:cjsg:second:tjse-boletim-jurisprudencia` | `TJSE` | `second` | `CJSG` | `tjse_boletim_jurisprudencia` | `live_validated` | `valid` | `enabled` | `operator_approved` |
| `surface:tjsp:cjpg:first:tjsp-cjpg` | `TJSP` | `first` | `CJPG` | `tjsp_cjpg` | `live_validated` | `valid` | `enabled` | `operator_approved` |
| `surface:tjsp:cjsg:second:tjsp-cjsg` | `TJSP` | `second` | `CJSG` | `tjsp_cjsg` | `live_validated` | `valid` | `enabled` | `operator_approved` |
| `surface:tjsp:eproc:mixed:tjsp-eproc-jurisprudencia` | `TJSP` | `mixed` | `EPROC` | `tjsp_eproc_jurisprudencia` | `live_validated` | `valid` | `enabled` | `operator_approved` |
| `surface:tjto:cjpg:first:tjto-jurisprudencia` | `TJTO` | `first` | `CJPG` | `tjto_jurisprudencia` | `live_validated` | `valid` | `enabled` | `operator_approved` |
| `surface:tjto:cjsg:second:tjto-jurisprudencia` | `TJTO` | `second` | `CJSG` | `tjto_jurisprudencia` | `live_validated` | `valid` | `enabled` | `operator_approved` |
| `surface:tjto:portal:mixed:tjto-jurisprudencia` | `TJTO` | `mixed` | `PORTAL` | `tjto_jurisprudencia` | `live_validated` | `valid` | `enabled` | `operator_approved` |
| `surface:tnu:eproc:superior:tnu-eproc-jurisprudencia` | `TNU` | `superior` | `EPROC` | `tnu_eproc_jurisprudencia` | `live_validated` | `valid` | `enabled` | `operator_approved` |
| `surface:treac:sjur:second:tre-sjur-jurisprudencia` | `TREAC` | `second` | `SJUR` | `tre_sjur_jurisprudencia` | `pending_contract` | `partial` | `not_enabled` | `pending_human_review` |
| `surface:treal:sjur:second:tre-sjur-jurisprudencia` | `TREAL` | `second` | `SJUR` | `tre_sjur_jurisprudencia` | `pending_contract` | `partial` | `not_enabled` | `pending_human_review` |
| `surface:tream:sjur:second:tre-sjur-jurisprudencia` | `TREAM` | `second` | `SJUR` | `tre_sjur_jurisprudencia` | `pending_contract` | `partial` | `not_enabled` | `pending_human_review` |
| `surface:treap:sjur:second:tre-sjur-jurisprudencia` | `TREAP` | `second` | `SJUR` | `tre_sjur_jurisprudencia` | `pending_contract` | `partial` | `not_enabled` | `pending_human_review` |
| `surface:treba:sjur:second:tre-sjur-jurisprudencia` | `TREBA` | `second` | `SJUR` | `tre_sjur_jurisprudencia` | `pending_contract` | `partial` | `not_enabled` | `pending_human_review` |
| `surface:trece:sjur:second:tre-sjur-jurisprudencia` | `TRECE` | `second` | `SJUR` | `tre_sjur_jurisprudencia` | `pending_contract` | `partial` | `not_enabled` | `pending_human_review` |
| `surface:tredf:sjur:second:tre-sjur-jurisprudencia` | `TREDF` | `second` | `SJUR` | `tre_sjur_jurisprudencia` | `pending_contract` | `partial` | `not_enabled` | `pending_human_review` |
| `surface:trees:sjur:second:tre-sjur-jurisprudencia` | `TREES` | `second` | `SJUR` | `tre_sjur_jurisprudencia` | `pending_contract` | `partial` | `not_enabled` | `pending_human_review` |
| `surface:trego:sjur:second:tre-sjur-jurisprudencia` | `TREGO` | `second` | `SJUR` | `tre_sjur_jurisprudencia` | `pending_contract` | `partial` | `not_enabled` | `pending_human_review` |
| `surface:trema:sjur:second:tre-sjur-jurisprudencia` | `TREMA` | `second` | `SJUR` | `tre_sjur_jurisprudencia` | `pending_contract` | `partial` | `not_enabled` | `pending_human_review` |
| `surface:tremg:sjur:second:tre-sjur-jurisprudencia` | `TREMG` | `second` | `SJUR` | `tre_sjur_jurisprudencia` | `pending_contract` | `partial` | `not_enabled` | `pending_human_review` |
| `surface:trems:sjur:second:tre-sjur-jurisprudencia` | `TREMS` | `second` | `SJUR` | `tre_sjur_jurisprudencia` | `pending_contract` | `partial` | `not_enabled` | `pending_human_review` |
| `surface:tremt:sjur:second:tre-sjur-jurisprudencia` | `TREMT` | `second` | `SJUR` | `tre_sjur_jurisprudencia` | `pending_contract` | `partial` | `not_enabled` | `pending_human_review` |
| `surface:trepa:sjur:second:tre-sjur-jurisprudencia` | `TREPA` | `second` | `SJUR` | `tre_sjur_jurisprudencia` | `pending_contract` | `partial` | `not_enabled` | `pending_human_review` |
| `surface:trepb:sjur:second:tre-sjur-jurisprudencia` | `TREPB` | `second` | `SJUR` | `tre_sjur_jurisprudencia` | `pending_contract` | `partial` | `not_enabled` | `pending_human_review` |
| `surface:trepe:sjur:second:tre-sjur-jurisprudencia` | `TREPE` | `second` | `SJUR` | `tre_sjur_jurisprudencia` | `pending_contract` | `partial` | `not_enabled` | `pending_human_review` |
| `surface:trepi:sjur:second:tre-sjur-jurisprudencia` | `TREPI` | `second` | `SJUR` | `tre_sjur_jurisprudencia` | `pending_contract` | `partial` | `not_enabled` | `pending_human_review` |
| `surface:trepr:sjur:second:tre-sjur-jurisprudencia` | `TREPR` | `second` | `SJUR` | `tre_sjur_jurisprudencia` | `pending_contract` | `partial` | `not_enabled` | `pending_human_review` |
| `surface:trerj:sjur:second:tre-sjur-jurisprudencia` | `TRERJ` | `second` | `SJUR` | `tre_sjur_jurisprudencia` | `pending_contract` | `partial` | `not_enabled` | `pending_human_review` |
| `surface:trern:sjur:second:tre-sjur-jurisprudencia` | `TRERN` | `second` | `SJUR` | `tre_sjur_jurisprudencia` | `pending_contract` | `partial` | `not_enabled` | `pending_human_review` |
| `surface:trero:sjur:second:tre-sjur-jurisprudencia` | `TRERO` | `second` | `SJUR` | `tre_sjur_jurisprudencia` | `pending_contract` | `partial` | `not_enabled` | `pending_human_review` |
| `surface:trerr:sjur:second:tre-sjur-jurisprudencia` | `TRERR` | `second` | `SJUR` | `tre_sjur_jurisprudencia` | `pending_contract` | `partial` | `not_enabled` | `pending_human_review` |
| `surface:trers:sjur:second:tre-sjur-jurisprudencia` | `TRERS` | `second` | `SJUR` | `tre_sjur_jurisprudencia` | `pending_contract` | `partial` | `not_enabled` | `pending_human_review` |
| `surface:tres-aggregate:sjur:second:justica-eleitoral-sjur` | `TRES_AGGREGATE` | `second` | `SJUR` | `justica_eleitoral_sjur` | `pending_contract` | `source_unavailable` | `not_enabled` | `pending_human_review` |
| `surface:tresc:sjur:second:tre-sjur-jurisprudencia` | `TRESC` | `second` | `SJUR` | `tre_sjur_jurisprudencia` | `pending_contract` | `partial` | `not_enabled` | `pending_human_review` |
| `surface:trese:sjur:second:tre-sjur-jurisprudencia` | `TRESE` | `second` | `SJUR` | `tre_sjur_jurisprudencia` | `pending_contract` | `partial` | `not_enabled` | `pending_human_review` |
| `surface:tresp:sjur:second:tre-sjur-jurisprudencia` | `TRESP` | `second` | `SJUR` | `tre_sjur_jurisprudencia` | `pending_contract` | `partial` | `not_enabled` | `pending_human_review` |
| `surface:tresp:temas:second:tre-sp-temas` | `TRESP` | `second` | `TEMAS` | `tre_sp_temas` | `source_unavailable` | `source_unavailable` | `blocked` | `pending_human_review` |
| `surface:treto:sjur:second:tre-sjur-jurisprudencia` | `TRETO` | `second` | `SJUR` | `tre_sjur_jurisprudencia` | `pending_contract` | `partial` | `not_enabled` | `pending_human_review` |
| `surface:trf1:jurisprudencia:second:cjf-jurisprudencia` | `TRF1` | `second` | `JURISPRUDENCIA` | `cjf_jurisprudencia` | `blocked_access` | `access_control_required` | `blocked` | `pending_human_review` |
| `surface:trf2:eproc:second:trf2-eproc-jurisprudencia` | `TRF2` | `second` | `EPROC` | `trf2_eproc_jurisprudencia` | `live_validated` | `valid` | `enabled` | `operator_approved` |
| `surface:trf3:jurisprudencia:second:trf3-jurisprudencia` | `TRF3` | `second` | `JURISPRUDENCIA` | `trf3_jurisprudencia` | `candidate` | `transport_error` | `not_enabled` | `pending_human_review` |
| `surface:trf4:eproc:second:trf4-eproc-jurisprudencia` | `TRF4` | `second` | `EPROC` | `trf4_eproc_jurisprudencia` | `live_validated` | `valid` | `enabled` | `operator_approved` |
| `surface:trf5:jurisprudencia:second:trf5-jurisprudencia` | `TRF5` | `second` | `JURISPRUDENCIA` | `trf5_jurisprudencia` | `live_validated` | `valid` | `enabled` | `operator_approved` |
| `surface:trf6:eproc:second:trf6-eproc-jurisprudencia` | `TRF6` | `second` | `EPROC` | `trf6_eproc_jurisprudencia` | `live_validated` | `valid` | `enabled` | `operator_approved` |
| `surface:trt10:jurisprudencia:second:gap` | `TRT10` | `second` | `JURISPRUDENCIA` | — | `candidate` | `not_observed` | `not_enabled` | `pending_human_review` |
| `surface:trt11:jurisprudencia:second:gap` | `TRT11` | `second` | `JURISPRUDENCIA` | — | `candidate` | `not_observed` | `not_enabled` | `pending_human_review` |
| `surface:trt12:jurisprudencia:second:gap` | `TRT12` | `second` | `JURISPRUDENCIA` | — | `candidate` | `not_observed` | `not_enabled` | `pending_human_review` |
| `surface:trt13:jurisprudencia:second:gap` | `TRT13` | `second` | `JURISPRUDENCIA` | — | `candidate` | `not_observed` | `not_enabled` | `pending_human_review` |
| `surface:trt14:jurisprudencia:second:gap` | `TRT14` | `second` | `JURISPRUDENCIA` | — | `candidate` | `not_observed` | `not_enabled` | `pending_human_review` |
| `surface:trt15:jurisprudencia:second:gap` | `TRT15` | `second` | `JURISPRUDENCIA` | — | `candidate` | `not_observed` | `not_enabled` | `pending_human_review` |
| `surface:trt16:jurisprudencia:second:gap` | `TRT16` | `second` | `JURISPRUDENCIA` | — | `candidate` | `not_observed` | `not_enabled` | `pending_human_review` |
| `surface:trt17:jurisprudencia:second:gap` | `TRT17` | `second` | `JURISPRUDENCIA` | — | `candidate` | `not_observed` | `not_enabled` | `pending_human_review` |
| `surface:trt18:jurisprudencia:second:gap` | `TRT18` | `second` | `JURISPRUDENCIA` | — | `candidate` | `not_observed` | `not_enabled` | `pending_human_review` |
| `surface:trt19:jurisprudencia:second:gap` | `TRT19` | `second` | `JURISPRUDENCIA` | — | `candidate` | `not_observed` | `not_enabled` | `pending_human_review` |
| `surface:trt1:jurisprudencia:second:gap` | `TRT1` | `second` | `JURISPRUDENCIA` | — | `candidate` | `not_observed` | `not_enabled` | `pending_human_review` |
| `surface:trt20:jurisprudencia:second:gap` | `TRT20` | `second` | `JURISPRUDENCIA` | — | `candidate` | `not_observed` | `not_enabled` | `pending_human_review` |
| `surface:trt21:jurisprudencia:second:gap` | `TRT21` | `second` | `JURISPRUDENCIA` | — | `candidate` | `not_observed` | `not_enabled` | `pending_human_review` |
| `surface:trt22:jurisprudencia:second:gap` | `TRT22` | `second` | `JURISPRUDENCIA` | — | `candidate` | `not_observed` | `not_enabled` | `pending_human_review` |
| `surface:trt23:jurisprudencia:second:gap` | `TRT23` | `second` | `JURISPRUDENCIA` | — | `candidate` | `not_observed` | `not_enabled` | `pending_human_review` |
| `surface:trt24:jurisprudencia:second:gap` | `TRT24` | `second` | `JURISPRUDENCIA` | — | `candidate` | `not_observed` | `not_enabled` | `pending_human_review` |
| `surface:trt2:jurisprudencia:second:trt2-pje-jurisprudencia` | `TRT2` | `second` | `JURISPRUDENCIA` | `trt2_pje_jurisprudencia` | `candidate` | `access_control_required` | `not_enabled` | `pending_human_review` |
| `surface:trt3:jurisprudencia:second:gap` | `TRT3` | `second` | `JURISPRUDENCIA` | — | `candidate` | `not_observed` | `not_enabled` | `pending_human_review` |
| `surface:trt4:jurisprudencia:second:gap` | `TRT4` | `second` | `JURISPRUDENCIA` | — | `candidate` | `not_observed` | `not_enabled` | `pending_human_review` |
| `surface:trt5:jurisprudencia:second:gap` | `TRT5` | `second` | `JURISPRUDENCIA` | — | `candidate` | `not_observed` | `not_enabled` | `pending_human_review` |
| `surface:trt6:jurisprudencia:second:gap` | `TRT6` | `second` | `JURISPRUDENCIA` | — | `candidate` | `not_observed` | `not_enabled` | `pending_human_review` |
| `surface:trt7:jurisprudencia:second:gap` | `TRT7` | `second` | `JURISPRUDENCIA` | — | `candidate` | `not_observed` | `not_enabled` | `pending_human_review` |
| `surface:trt8:jurisprudencia:second:gap` | `TRT8` | `second` | `JURISPRUDENCIA` | — | `candidate` | `not_observed` | `not_enabled` | `pending_human_review` |
| `surface:trt9:jurisprudencia:second:gap` | `TRT9` | `second` | `JURISPRUDENCIA` | — | `candidate` | `not_observed` | `not_enabled` | `pending_human_review` |
| `surface:tse:sjur:superior:tse-sjur-jurisprudencia` | `TSE` | `superior` | `SJUR` | `tse_sjur_jurisprudencia` | `pending_contract` | `valid` | `not_enabled` | `operator_approved` |
| `surface:tst:portal:superior:tst-jurisprudencia` | `TST` | `superior` | `PORTAL` | `tst_jurisprudencia` | `live_validated` | `valid` | `enabled` | `operator_approved` |

Estados de contrato, live, federação e legalidade são independentes. Aprovação legal nunca é inferida do catálogo ou de uma chamada pública.
