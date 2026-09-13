# Mapa nacional de lacunas de cobertura

Gerado em `2026-09-08` a partir da matriz nacional, do registro de superfícies e do catálogo de providers.

## Leitura correta

Este documento mapeia disponibilidade e evidência; não declara que uma fonte possui acervo integral. Bloqueios permanecem bloqueios e não são convertidos em resultados vazios.

## Resumo

- Superfícies: **249** (155 core, 94 condicionais).
- Core pronto no estado `federated_live`: **68**.
- Core ainda não pronto: **87**.
- Providers do catálogo sem binding na matriz: **24** de **85**.
- Superfícies com todos os gates GOLD explícitos: **68**.
- Matriz estadual CJPG/CJSG: **8/27** CJPG e **25/27** CJSG em estado GOLD; **7/27** tribunais com as duas trilhas.

| Prioridade | Quantidade |
|---|---:|
| P0 | 42 |
| P1 | 45 |
| P2 | 93 |
| P3 | 69 |

| Frente | Quantidade |
|---|---:|
| blocked_recheck_or_official_alternative | 12 |
| continuous_monitoring | 68 |
| contract_hardening | 30 |
| official_discovery | 137 |
| promotion_gates | 2 |

## Autoridades prioritárias

- `blocked_recheck_or_official_alternative`: STF, STJ, TJAP, TJMA, TJMSP, TRESP, TRES_AGGREGATE, TRF1, TRT2, TRT3, TRT4, TRT6
- `contract_hardening`: TJMMG, TREAC, TREAL, TREAM, TREAP, TREBA, TRECE, TREDF, TREES, TREGO, TREMA, TREMG, TREMS, TREMT, TREPA, TREPB, TREPE, TREPI, TREPR, TRERJ, TRERN, TRERO, TRERR, TRERS, TRESC, TRESE, TRESP, TRETO, TRF3, TSE
- `official_discovery`: CJF, CNJ, CSJT, ELECTORAL_FIRST_DEGREE_UNITS, FEDERAL_FIRST_DEGREE_UNITS, LABOR_FIRST_DEGREE_UNITS, MILITARY_FIRST_DEGREE_UNITS, TCDF, TCEAC, TCEAL, TCEAM, TCEAP, TCEBA, TCECE, TCEES, TCEGO, TCEMA, TCEMG, TCEMS, TCEMT, TCEPA, TCEPB, TCEPE, TCEPI, TCEPR, TCERJ, TCERN, TCERO, TCERR, TCERS, TCESC, TCESE, TCESP, TCETO, TCMBA, TCMGO, TCMPA, TCMSP, TJAC, TJAL, TJAM, TJAP, TJBA, TJCE, TJDFT, TJES, TJGO, TJMA, TJMG, TJMS, TJMT, TJPA, TJPB, TJPE, TJPI, TJPR, TJRJ, TJRN, TJRO, TJRR, TJRS, TJSC, TJSE, TJSP, TJTO, TRF1, TRF3, TRF5, TRF6, TRT1, TRT10, TRT11, TRT12, TRT13, TRT14, TRT15, TRT16, TRT17, TRT18, TRT19, TRT20, TRT21, TRT22, TRT23, TRT24, TRT5, TRT7, TRT9, TSE
- `promotion_gates`: STJ, TJMRS

## Fila executavel de descoberta e fechamento

A fila e derivada da matriz nacional. Execute em lotes de uma a tres superficies; bloqueios permanecem explicitos e nao viram resultados vazios.

| Lote | Autoridade | Ramo | Grau | Colecao | Provider | Estado | Lacunas | Proxima acao |
|---|---|---|---|---|---|---|---|---|
| `contract_hardening` | `TREAC` | `electoral` | `second` | `SJUR` | `tre_sjur_jurisprudencia` | `contract_pending` | degree_contract, federation, document_capability, human_legal_review | close_remote_pagination_and_document_gates |
| `contract_hardening` | `TREAL` | `electoral` | `second` | `SJUR` | `tre_sjur_jurisprudencia` | `contract_pending` | degree_contract, federation, document_capability, human_legal_review | close_remote_pagination_and_document_gates |
| `contract_hardening` | `TREAM` | `electoral` | `second` | `SJUR` | `tre_sjur_jurisprudencia` | `contract_pending` | degree_contract, federation, document_capability, human_legal_review | close_remote_pagination_and_document_gates |
| `contract_hardening` | `TREAP` | `electoral` | `second` | `SJUR` | `tre_sjur_jurisprudencia` | `contract_pending` | degree_contract, federation, document_capability, human_legal_review | close_remote_pagination_and_document_gates |
| `contract_hardening` | `TREBA` | `electoral` | `second` | `SJUR` | `tre_sjur_jurisprudencia` | `contract_pending` | degree_contract, federation, document_capability, human_legal_review | close_remote_pagination_and_document_gates |
| `contract_hardening` | `TRECE` | `electoral` | `second` | `SJUR` | `tre_sjur_jurisprudencia` | `contract_pending` | degree_contract, federation, document_capability, human_legal_review | close_remote_pagination_and_document_gates |
| `contract_hardening` | `TREDF` | `electoral` | `second` | `SJUR` | `tre_sjur_jurisprudencia` | `contract_pending` | degree_contract, federation, document_capability, human_legal_review | close_remote_pagination_and_document_gates |
| `contract_hardening` | `TREES` | `electoral` | `second` | `SJUR` | `tre_sjur_jurisprudencia` | `contract_pending` | degree_contract, federation, document_capability, human_legal_review | close_remote_pagination_and_document_gates |
| `contract_hardening` | `TREGO` | `electoral` | `second` | `SJUR` | `tre_sjur_jurisprudencia` | `contract_pending` | degree_contract, federation, document_capability, human_legal_review | close_remote_pagination_and_document_gates |
| `contract_hardening` | `TREMA` | `electoral` | `second` | `SJUR` | `tre_sjur_jurisprudencia` | `contract_pending` | degree_contract, federation, document_capability, human_legal_review | close_remote_pagination_and_document_gates |
| `contract_hardening` | `TREMG` | `electoral` | `second` | `SJUR` | `tre_sjur_jurisprudencia` | `contract_pending` | degree_contract, federation, document_capability, human_legal_review | close_remote_pagination_and_document_gates |
| `contract_hardening` | `TREMS` | `electoral` | `second` | `SJUR` | `tre_sjur_jurisprudencia` | `contract_pending` | degree_contract, federation, document_capability, human_legal_review | close_remote_pagination_and_document_gates |
| `contract_hardening` | `TREMT` | `electoral` | `second` | `SJUR` | `tre_sjur_jurisprudencia` | `contract_pending` | degree_contract, federation, document_capability, human_legal_review | close_remote_pagination_and_document_gates |
| `contract_hardening` | `TREPA` | `electoral` | `second` | `SJUR` | `tre_sjur_jurisprudencia` | `contract_pending` | degree_contract, federation, document_capability, human_legal_review | close_remote_pagination_and_document_gates |
| `contract_hardening` | `TREPB` | `electoral` | `second` | `SJUR` | `tre_sjur_jurisprudencia` | `contract_pending` | degree_contract, federation, document_capability, human_legal_review | close_remote_pagination_and_document_gates |
| `contract_hardening` | `TREPE` | `electoral` | `second` | `SJUR` | `tre_sjur_jurisprudencia` | `contract_pending` | degree_contract, federation, document_capability, human_legal_review | close_remote_pagination_and_document_gates |
| `contract_hardening` | `TREPI` | `electoral` | `second` | `SJUR` | `tre_sjur_jurisprudencia` | `contract_pending` | degree_contract, federation, document_capability, human_legal_review | close_remote_pagination_and_document_gates |
| `contract_hardening` | `TREPR` | `electoral` | `second` | `SJUR` | `tre_sjur_jurisprudencia` | `contract_pending` | degree_contract, federation, document_capability, human_legal_review | close_remote_pagination_and_document_gates |
| `contract_hardening` | `TRERJ` | `electoral` | `second` | `SJUR` | `tre_sjur_jurisprudencia` | `contract_pending` | degree_contract, federation, document_capability, human_legal_review | close_remote_pagination_and_document_gates |
| `contract_hardening` | `TRERN` | `electoral` | `second` | `SJUR` | `tre_sjur_jurisprudencia` | `contract_pending` | degree_contract, federation, document_capability, human_legal_review | close_remote_pagination_and_document_gates |
| `contract_hardening` | `TRERO` | `electoral` | `second` | `SJUR` | `tre_sjur_jurisprudencia` | `contract_pending` | degree_contract, federation, document_capability, human_legal_review | close_remote_pagination_and_document_gates |
| `contract_hardening` | `TRERR` | `electoral` | `second` | `SJUR` | `tre_sjur_jurisprudencia` | `contract_pending` | degree_contract, federation, document_capability, human_legal_review | close_remote_pagination_and_document_gates |
| `contract_hardening` | `TRERS` | `electoral` | `second` | `SJUR` | `tre_sjur_jurisprudencia` | `contract_pending` | degree_contract, federation, document_capability, human_legal_review | close_remote_pagination_and_document_gates |
| `contract_hardening` | `TRESC` | `electoral` | `second` | `SJUR` | `tre_sjur_jurisprudencia` | `contract_pending` | degree_contract, federation, document_capability, human_legal_review | close_remote_pagination_and_document_gates |
| `contract_hardening` | `TRESE` | `electoral` | `second` | `SJUR` | `tre_sjur_jurisprudencia` | `contract_pending` | degree_contract, federation, document_capability, human_legal_review | close_remote_pagination_and_document_gates |
| `contract_hardening` | `TRESP` | `electoral` | `second` | `SJUR` | `tre_sjur_jurisprudencia` | `contract_pending` | degree_contract, federation, document_capability, human_legal_review | close_remote_pagination_and_document_gates |
| `contract_hardening` | `TRETO` | `electoral` | `second` | `SJUR` | `tre_sjur_jurisprudencia` | `contract_pending` | degree_contract, federation, document_capability, human_legal_review | close_remote_pagination_and_document_gates |
| `contract_hardening` | `TSE` | `electoral` | `superior` | `SJUR` | `tse_sjur_jurisprudencia` | `contract_pending` | degree_contract, federation | close_contract_filters_pagination_and_fixtures |
| `contract_hardening` | `TRF3` | `federal` | `second` | `JURISPRUDENCIA` | `trf3_jurisprudencia` | `contract_pending` | degree_contract, live_status, federation, human_legal_review | close_contract_filters_pagination_and_fixtures |
| `contract_hardening` | `TJMMG` | `military` | `second` | `PORTAL` | `tjmmg_jurisprudencia_api` | `contract_pending` | degree_contract, live_status, federation, document_capability, human_legal_review | obtain_bounded_search_contract |
| `providerless_core` | `ELECTORAL_FIRST_DEGREE_UNITS` | `electoral` | `first` | `SJUR` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_core` | `TSE` | `electoral` | `superior` | `PORTAL` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_core` | `CJF` | `federal` | `superior` | `JURISPRUDENCIA` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_core` | `FEDERAL_FIRST_DEGREE_UNITS` | `federal` | `first` | `EPROC` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_core` | `LABOR_FIRST_DEGREE_UNITS` | `labor` | `first` | `PORTAL` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_core` | `TRT1` | `labor` | `second` | `JURISPRUDENCIA` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_core` | `TRT10` | `labor` | `second` | `JURISPRUDENCIA` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_core` | `TRT11` | `labor` | `second` | `JURISPRUDENCIA` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_core` | `TRT12` | `labor` | `second` | `JURISPRUDENCIA` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_core` | `TRT13` | `labor` | `second` | `JURISPRUDENCIA` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_core` | `TRT14` | `labor` | `second` | `JURISPRUDENCIA` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_core` | `TRT15` | `labor` | `second` | `JURISPRUDENCIA` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_core` | `TRT16` | `labor` | `second` | `JURISPRUDENCIA` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_core` | `TRT17` | `labor` | `second` | `JURISPRUDENCIA` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_core` | `TRT18` | `labor` | `second` | `JURISPRUDENCIA` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_core` | `TRT19` | `labor` | `second` | `JURISPRUDENCIA` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_core` | `TRT20` | `labor` | `second` | `JURISPRUDENCIA` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_core` | `TRT21` | `labor` | `second` | `JURISPRUDENCIA` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_core` | `TRT22` | `labor` | `second` | `JURISPRUDENCIA` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_core` | `TRT23` | `labor` | `second` | `JURISPRUDENCIA` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_core` | `TRT24` | `labor` | `second` | `JURISPRUDENCIA` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_core` | `TRT5` | `labor` | `second` | `JURISPRUDENCIA` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_core` | `TRT7` | `labor` | `second` | `JURISPRUDENCIA` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_core` | `TRT9` | `labor` | `second` | `JURISPRUDENCIA` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_core` | `TJAC` | `state` | `first` | `CJPG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_core` | `TJAM` | `state` | `first` | `CJPG` | `-` | `discovery_pending` | runtime, degree_contract, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_core` | `TJBA` | `state` | `first` | `CJPG` | `-` | `discovery_pending` | runtime, degree_contract, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_core` | `TJCE` | `state` | `first` | `CJPG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_core` | `TJDFT` | `state` | `first` | `CJPG` | `-` | `discovery_pending` | runtime, degree_contract, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_core` | `TJMA` | `state` | `first` | `CJPG` | `-` | `discovery_pending` | runtime, degree_contract, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_core` | `TJMA` | `state` | `second` | `CJSG` | `-` | `discovery_pending` | runtime, degree_contract, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_core` | `TJMG` | `state` | `first` | `CJPG` | `-` | `discovery_pending` | runtime, degree_contract, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_core` | `TJMT` | `state` | `first` | `CJPG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_core` | `TJPA` | `state` | `first` | `CJPG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_core` | `TJPB` | `state` | `first` | `CJPG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_core` | `TJPE` | `state` | `first` | `CJPG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_core` | `TJPI` | `state` | `first` | `CJPG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_core` | `TJPR` | `state` | `first` | `CJPG` | `-` | `discovery_pending` | runtime, degree_contract, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_core` | `TJRJ` | `state` | `first` | `CJPG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_core` | `TJRN` | `state` | `first` | `CJPG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_core` | `TJRR` | `state` | `first` | `CJPG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_core` | `TJRS` | `state` | `first` | `CJPG` | `-` | `discovery_pending` | runtime, degree_contract, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_core` | `TJSC` | `state` | `first` | `CJPG` | `-` | `discovery_pending` | runtime, degree_contract, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_core` | `TJSE` | `state` | `first` | `CJPG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `blocked_official_alternative` | `STF` | `constitutional` | `superior` | `PORTAL` | `stf_juris` | `blocked_or_unavailable` | degree_contract, live_status, federation, human_legal_review | recheck_official_alternative_or_record_block |
| `blocked_official_alternative` | `TRESP` | `electoral` | `second` | `TEMAS` | `tre_sp_temas` | `blocked_or_unavailable` | degree_contract, live_status, federation, human_legal_review | recheck_official_alternative_or_record_block |
| `blocked_official_alternative` | `TRES_AGGREGATE` | `electoral` | `second` | `SJUR` | `justica_eleitoral_sjur` | `blocked_or_unavailable` | degree_contract, live_status, federation, human_legal_review | recheck_official_alternative_or_record_block |
| `blocked_official_alternative` | `TRF1` | `federal` | `second` | `JURISPRUDENCIA` | `cjf_jurisprudencia` | `blocked_or_unavailable` | degree_contract, live_status, federation, human_legal_review | recheck_official_alternative_or_record_block |
| `blocked_official_alternative` | `TRT2` | `labor` | `second` | `JURISPRUDENCIA` | `trt2_pje_jurisprudencia` | `blocked_or_unavailable` | degree_contract, live_status, federation, human_legal_review | recheck_official_alternative_or_record_block |
| `providerless_core` | `TRT3` | `labor` | `second` | `JURISPRUDENCIA` | `-` | `blocked_or_unavailable` | runtime, degree_contract, live_status, federation, document_capability, human_legal_review | recheck_official_alternative_or_record_block |
| `providerless_core` | `TRT4` | `labor` | `second` | `JURISPRUDENCIA` | `-` | `blocked_or_unavailable` | runtime, degree_contract, live_status, federation, document_capability, human_legal_review | recheck_official_alternative_or_record_block |
| `blocked_official_alternative` | `TRT6` | `labor` | `second` | `JURISPRUDENCIA` | `trt6_jurisprudencia` | `blocked_or_unavailable` | degree_contract, live_status, federation, document_capability, human_legal_review | obtain_authorized_non_captcha_search_contract |
| `blocked_official_alternative` | `TJMSP` | `military` | `second` | `PORTAL` | `tjmsp_jurisprudencia` | `blocked_or_unavailable` | degree_contract, live_status, federation, document_capability, human_legal_review | obtain_official_allowlist_or_alternative |
| `blocked_official_alternative` | `TJAP` | `state` | `second` | `CJSG` | `tjap_tucujuris` | `blocked_or_unavailable` | degree_contract, live_status, federation, human_legal_review | recheck_official_alternative_or_record_block |
| `blocked_official_alternative` | `TJMA` | `state` | `unknown` | `CATALOG` | `tjma_jurisconsult` | `blocked_or_unavailable` | degree_contract, live_status, federation, human_legal_review | recheck_official_alternative_or_record_block |
| `blocked_official_alternative` | `STJ` | `superior` | `superior` | `PORTAL` | `stj_scon` | `blocked_or_unavailable` | degree_contract, live_status, federation, human_legal_review | recheck_official_alternative_or_record_block |
| `promotion_gate` | `TJMRS` | `military` | `second` | `PORTAL` | `tjmrs_jurisprudencia` | `live_not_federated` | degree_contract, federation, document_capability, human_legal_review | obtain_general_search_contract |
| `providerless_conditional` | `TCDF` | `control` | `second` | `JURISPRUDENCIA` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_conditional` | `TCEAC` | `control` | `second` | `JURISPRUDENCIA` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_conditional` | `TCEAL` | `control` | `second` | `JURISPRUDENCIA` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_conditional` | `TCEAM` | `control` | `second` | `JURISPRUDENCIA` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_conditional` | `TCEAP` | `control` | `second` | `JURISPRUDENCIA` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_conditional` | `TCEBA` | `control` | `second` | `JURISPRUDENCIA` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_conditional` | `TCECE` | `control` | `second` | `JURISPRUDENCIA` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_conditional` | `TCEES` | `control` | `second` | `JURISPRUDENCIA` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_conditional` | `TCEGO` | `control` | `second` | `JURISPRUDENCIA` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_conditional` | `TCEMA` | `control` | `second` | `JURISPRUDENCIA` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_conditional` | `TCEMG` | `control` | `second` | `JURISPRUDENCIA` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_conditional` | `TCEMS` | `control` | `second` | `JURISPRUDENCIA` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_conditional` | `TCEMT` | `control` | `second` | `JURISPRUDENCIA` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_conditional` | `TCEPA` | `control` | `second` | `JURISPRUDENCIA` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_conditional` | `TCEPB` | `control` | `second` | `JURISPRUDENCIA` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_conditional` | `TCEPE` | `control` | `second` | `JURISPRUDENCIA` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_conditional` | `TCEPI` | `control` | `second` | `JURISPRUDENCIA` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_conditional` | `TCEPR` | `control` | `second` | `JURISPRUDENCIA` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_conditional` | `TCERJ` | `control` | `second` | `JURISPRUDENCIA` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_conditional` | `TCERN` | `control` | `second` | `JURISPRUDENCIA` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_conditional` | `TCERO` | `control` | `second` | `JURISPRUDENCIA` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_conditional` | `TCERR` | `control` | `second` | `JURISPRUDENCIA` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_conditional` | `TCERS` | `control` | `second` | `JURISPRUDENCIA` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_conditional` | `TCESC` | `control` | `second` | `JURISPRUDENCIA` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_conditional` | `TCESE` | `control` | `second` | `JURISPRUDENCIA` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_conditional` | `TCESP` | `control` | `second` | `JURISPRUDENCIA` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_conditional` | `TCETO` | `control` | `second` | `JURISPRUDENCIA` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_conditional` | `TCMBA` | `control` | `second` | `JURISPRUDENCIA` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_conditional` | `TCMGO` | `control` | `second` | `JURISPRUDENCIA` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_conditional` | `TCMPA` | `control` | `second` | `JURISPRUDENCIA` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_conditional` | `TCMSP` | `control` | `second` | `JURISPRUDENCIA` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_conditional` | `CNJ` | `federal` | `superior` | `PORTAL` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_conditional` | `CSJT` | `federal` | `superior` | `PORTAL` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_conditional` | `TRF1` | `federal` | `unknown` | `CPOPG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | confirm_upstream_surface_semantics_before_adapter |
| `providerless_conditional` | `TRF1` | `federal` | `unknown` | `CPOSG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | confirm_upstream_surface_semantics_before_adapter |
| `providerless_conditional` | `TRF3` | `federal` | `unknown` | `CPOPG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | confirm_upstream_surface_semantics_before_adapter |
| `providerless_conditional` | `TRF3` | `federal` | `unknown` | `CPOSG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | confirm_upstream_surface_semantics_before_adapter |
| `providerless_conditional` | `TRF5` | `federal` | `unknown` | `CPOPG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | confirm_upstream_surface_semantics_before_adapter |
| `providerless_conditional` | `TRF5` | `federal` | `unknown` | `CPOSG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | confirm_upstream_surface_semantics_before_adapter |
| `providerless_conditional` | `TRF6` | `federal` | `unknown` | `CPOPG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | confirm_upstream_surface_semantics_before_adapter |
| `providerless_conditional` | `TRF6` | `federal` | `unknown` | `CPOSG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | confirm_upstream_surface_semantics_before_adapter |
| `providerless_conditional` | `MILITARY_FIRST_DEGREE_UNITS` | `military` | `first` | `PORTAL` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | discover_official_entry |
| `providerless_conditional` | `TJAC` | `state` | `unknown` | `CPOPG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | confirm_upstream_surface_semantics_before_adapter |
| `providerless_conditional` | `TJAC` | `state` | `unknown` | `CPOSG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | confirm_upstream_surface_semantics_before_adapter |
| `providerless_conditional` | `TJAL` | `state` | `unknown` | `CPOPG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | confirm_upstream_surface_semantics_before_adapter |
| `providerless_conditional` | `TJAL` | `state` | `unknown` | `CPOSG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | confirm_upstream_surface_semantics_before_adapter |
| `providerless_conditional` | `TJAM` | `state` | `unknown` | `CPOPG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | confirm_upstream_surface_semantics_before_adapter |
| `providerless_conditional` | `TJAM` | `state` | `unknown` | `CPOSG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | confirm_upstream_surface_semantics_before_adapter |
| `providerless_conditional` | `TJAP` | `state` | `unknown` | `CPOPG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | confirm_upstream_surface_semantics_before_adapter |
| `providerless_conditional` | `TJAP` | `state` | `unknown` | `CPOSG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | confirm_upstream_surface_semantics_before_adapter |
| `providerless_conditional` | `TJBA` | `state` | `unknown` | `CPOPG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | confirm_upstream_surface_semantics_before_adapter |
| `providerless_conditional` | `TJBA` | `state` | `unknown` | `CPOSG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | confirm_upstream_surface_semantics_before_adapter |
| `providerless_conditional` | `TJCE` | `state` | `unknown` | `CPOPG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | confirm_upstream_surface_semantics_before_adapter |
| `providerless_conditional` | `TJCE` | `state` | `unknown` | `CPOSG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | confirm_upstream_surface_semantics_before_adapter |
| `providerless_conditional` | `TJDFT` | `state` | `unknown` | `CPOPG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | confirm_upstream_surface_semantics_before_adapter |
| `providerless_conditional` | `TJDFT` | `state` | `unknown` | `CPOSG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | confirm_upstream_surface_semantics_before_adapter |
| `providerless_conditional` | `TJES` | `state` | `unknown` | `CPOPG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | confirm_upstream_surface_semantics_before_adapter |
| `providerless_conditional` | `TJES` | `state` | `unknown` | `CPOSG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | confirm_upstream_surface_semantics_before_adapter |
| `providerless_conditional` | `TJGO` | `state` | `unknown` | `CPOPG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | confirm_upstream_surface_semantics_before_adapter |
| `providerless_conditional` | `TJGO` | `state` | `unknown` | `CPOSG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | confirm_upstream_surface_semantics_before_adapter |
| `providerless_conditional` | `TJMG` | `state` | `unknown` | `CPOPG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | confirm_upstream_surface_semantics_before_adapter |
| `providerless_conditional` | `TJMG` | `state` | `unknown` | `CPOSG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | confirm_upstream_surface_semantics_before_adapter |
| `providerless_conditional` | `TJMS` | `state` | `unknown` | `CPOPG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | confirm_upstream_surface_semantics_before_adapter |
| `providerless_conditional` | `TJMS` | `state` | `unknown` | `CPOSG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | confirm_upstream_surface_semantics_before_adapter |
| `providerless_conditional` | `TJMT` | `state` | `unknown` | `CPOPG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | confirm_upstream_surface_semantics_before_adapter |
| `providerless_conditional` | `TJMT` | `state` | `unknown` | `CPOSG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | confirm_upstream_surface_semantics_before_adapter |
| `providerless_conditional` | `TJPA` | `state` | `unknown` | `CPOPG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | confirm_upstream_surface_semantics_before_adapter |
| `providerless_conditional` | `TJPA` | `state` | `unknown` | `CPOSG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | confirm_upstream_surface_semantics_before_adapter |
| `providerless_conditional` | `TJPB` | `state` | `unknown` | `CPOPG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | confirm_upstream_surface_semantics_before_adapter |
| `providerless_conditional` | `TJPB` | `state` | `unknown` | `CPOSG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | confirm_upstream_surface_semantics_before_adapter |
| `providerless_conditional` | `TJPE` | `state` | `unknown` | `CPOPG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | confirm_upstream_surface_semantics_before_adapter |
| `providerless_conditional` | `TJPE` | `state` | `unknown` | `CPOSG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | confirm_upstream_surface_semantics_before_adapter |
| `providerless_conditional` | `TJPI` | `state` | `unknown` | `CPOPG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | confirm_upstream_surface_semantics_before_adapter |
| `providerless_conditional` | `TJPI` | `state` | `unknown` | `CPOSG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | confirm_upstream_surface_semantics_before_adapter |
| `providerless_conditional` | `TJPR` | `state` | `unknown` | `CPOPG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | confirm_upstream_surface_semantics_before_adapter |
| `providerless_conditional` | `TJPR` | `state` | `unknown` | `CPOSG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | confirm_upstream_surface_semantics_before_adapter |
| `providerless_conditional` | `TJRJ` | `state` | `unknown` | `CPOPG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | confirm_upstream_surface_semantics_before_adapter |
| `providerless_conditional` | `TJRJ` | `state` | `unknown` | `CPOSG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | confirm_upstream_surface_semantics_before_adapter |
| `providerless_conditional` | `TJRN` | `state` | `unknown` | `CPOPG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | confirm_upstream_surface_semantics_before_adapter |
| `providerless_conditional` | `TJRN` | `state` | `unknown` | `CPOSG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | confirm_upstream_surface_semantics_before_adapter |
| `providerless_conditional` | `TJRO` | `state` | `unknown` | `CPOPG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | confirm_upstream_surface_semantics_before_adapter |
| `providerless_conditional` | `TJRO` | `state` | `unknown` | `CPOSG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | confirm_upstream_surface_semantics_before_adapter |
| `providerless_conditional` | `TJRR` | `state` | `unknown` | `CPOPG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | confirm_upstream_surface_semantics_before_adapter |
| `providerless_conditional` | `TJRR` | `state` | `unknown` | `CPOSG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | confirm_upstream_surface_semantics_before_adapter |
| `providerless_conditional` | `TJRS` | `state` | `unknown` | `CPOPG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | confirm_upstream_surface_semantics_before_adapter |
| `providerless_conditional` | `TJRS` | `state` | `unknown` | `CPOSG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | confirm_upstream_surface_semantics_before_adapter |
| `providerless_conditional` | `TJSC` | `state` | `unknown` | `CPOPG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | confirm_upstream_surface_semantics_before_adapter |
| `providerless_conditional` | `TJSC` | `state` | `unknown` | `CPOSG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | confirm_upstream_surface_semantics_before_adapter |
| `providerless_conditional` | `TJSP` | `state` | `unknown` | `CPOPG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | confirm_upstream_surface_semantics_before_adapter |
| `providerless_conditional` | `TJSP` | `state` | `unknown` | `CPOSG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | confirm_upstream_surface_semantics_before_adapter |
| `providerless_conditional` | `TJTO` | `state` | `unknown` | `CPOPG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | confirm_upstream_surface_semantics_before_adapter |
| `providerless_conditional` | `TJTO` | `state` | `unknown` | `CPOSG` | `-` | `discovery_pending` | runtime, degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | confirm_upstream_surface_semantics_before_adapter |
| `adapter_discovery` | `TJTO` | `state` | `unknown` | `DETAIL` | `tjto_jurisprudencia` | `discovery_pending` | degree_contract, fixtures_live_evidence, live_status, federation, document_capability, human_legal_review | confirm_upstream_surface_semantics_before_adapter |
| `promotion_gate` | `STJ` | `superior` | `superior` | `AGGREGATE` | `stj_dados_abertos_jurisprudencia` | `live_not_federated` | federation | complete_quality_and_promotion_gates |

## Inventário dos 27 tribunais estaduais

`GOLD` exige todos os gates técnicos; `federated_live` indica fonte ativa, mas não substitui a auditoria de qualidade. `not_mapped` significa que ainda não há contrato de superfície, e não significa resultado vazio.

| Tribunal | CJPG | Provider CJPG | CJSG | Provider CJSG | Próxima ação |
|---|---|---|---|---|---|
| `TJAC` | `discovery_pending` | `—` | `GOLD` | `tjac_cjsg` | discover_official_entry |
| `TJAL` | `GOLD` | `tjal_esmal_banco_sentencas` | `GOLD` | `tjal_cjsg` | monitoramento |
| `TJAM` | `discovery_pending` | `—` | `GOLD` | `tjam_cjsg` | discover_official_entry |
| `TJAP` | `GOLD` | `tjap_banco_sentencas` | `blocked_or_unavailable` | `tjap_tucujuris` | recheck_official_alternative_or_record_block |
| `TJBA` | `discovery_pending` | `—` | `GOLD` | `tjba_graphql` | discover_official_entry |
| `TJCE` | `discovery_pending` | `—` | `GOLD` | `tjce_cjsg` | discover_official_entry |
| `TJDFT` | `discovery_pending` | `—` | `GOLD` | `tjdf_juris` | discover_official_entry |
| `TJES` | `GOLD` | `tjes_cjpg` | `GOLD` | `tjes_jurisprudencia` | monitoramento |
| `TJGO` | `GOLD` | `tjgo_projudi_jurisprudencia` | `GOLD` | `tjgo_projudi_jurisprudencia` | monitoramento |
| `TJMA` | `discovery_pending` | `—` | `discovery_pending` | `—` | discover_official_entry |
| `TJMG` | `discovery_pending` | `—` | `GOLD` | `tjmg_dspace_jurisprudencia` | discover_official_entry |
| `TJMS` | `GOLD` | `tjms_cjpg` | `GOLD` | `tjms_cjsg` | monitoramento |
| `TJMT` | `discovery_pending` | `—` | `GOLD` | `tjmt_jurisprudencia_api` | discover_official_entry |
| `TJPA` | `discovery_pending` | `—` | `GOLD` | `tjpa_jurisprudencia_bff` | discover_official_entry |
| `TJPB` | `discovery_pending` | `—` | `GOLD` | `tjpb_pje_jurisprudencia` | discover_official_entry |
| `TJPE` | `discovery_pending` | `—` | `GOLD` | `tjpe_jurisprudencia` | discover_official_entry |
| `TJPI` | `discovery_pending` | `—` | `GOLD` | `tjpi_juspi` | discover_official_entry |
| `TJPR` | `discovery_pending` | `—` | `GOLD` | `tjpr_jurisprudencia` | discover_official_entry |
| `TJRJ` | `discovery_pending` | `—` | `GOLD` | `tjrj_eproc_jurisprudencia` | discover_official_entry |
| `TJRN` | `discovery_pending` | `—` | `GOLD` | `tjrn_jurisprudencia` | discover_official_entry |
| `TJRO` | `GOLD` | `tjro_jurisprudencia` | `GOLD` | `tjro_jurisprudencia` | monitoramento |
| `TJRR` | `discovery_pending` | `—` | `GOLD` | `tjrr_juris` | discover_official_entry |
| `TJRS` | `discovery_pending` | `—` | `GOLD` | `tjrs_solr` | discover_official_entry |
| `TJSC` | `discovery_pending` | `—` | `GOLD` | `tjsc_eproc_jurisprudencia` | discover_official_entry |
| `TJSE` | `discovery_pending` | `—` | `GOLD` | `tjse_boletim_jurisprudencia` | discover_official_entry |
| `TJSP` | `GOLD` | `tjsp_cjpg` | `GOLD` | `tjsp_cjsg` | monitoramento |
| `TJTO` | `GOLD` | `tjto_jurisprudencia` | `GOLD` | `tjto_jurisprudencia` | monitoramento |

## Critério de promoção

Uma superfície só pode ser promovida quando possuir:

- fonte oficial identificada;
- contrato específico de grau/coleção;
- adapter e fixture;
- chamada live bounded válida;
- qualidade canônica e inteiro teor conforme declarado;
- integração federada explícita.

A lista completa, com campos faltantes e gates por superfície, está no JSON desta mesma pasta.

## Providers do catalogo sem binding na matriz

Estas entradas continuam visiveis para reconciliacao, mas nao alteram as contagens de cobertura obrigatoria.

| Provider | Estado | Frente | Informacao faltante |
|---|---|---|---|
| `bnp_pangea` | `federated_live` | `catalog_reconciliation` | - |
| `cnj_jurisprudencia` | `federated_live` | `catalog_reconciliation` | - |
| `eproc_jurisprudencia_federal` | `contract_pending` | `catalog_reconciliation` | - |
| `falcao_jt` | `blocked_or_unavailable` | `catalog_reconciliation` | - |
| `stf_informativo` | `blocked_or_unavailable` | `catalog_reconciliation` | - |
| `stj_informativo` | `federated_live` | `catalog_reconciliation` | - |
| `tce_pr_viajuris` | `federated_live` | `catalog_reconciliation` | - |
| `tce_sp_jurisprudencia` | `live_not_federated` | `catalog_reconciliation` | - |
| `tcu_jurisprudencia` | `federated_live` | `catalog_reconciliation` | - |
| `tjac_banco_sentencas` | `live_not_federated` | `catalog_reconciliation` | - |
| `tjac_ementario_jurisprudencia` | `federated_live` | `catalog_reconciliation` | - |
| `tjal_turma_recursal_ementario` | `contract_pending` | `catalog_reconciliation` | - |
| `tjce_informativos` | `live_not_federated` | `catalog_reconciliation` | - |
| `tjma_informativos` | `live_not_federated` | `catalog_reconciliation` | - |
| `tjrj_banco_sentencas` | `contract_pending` | `catalog_reconciliation` | - |
| `tjse_jurisprudencia` | `discovery_pending` | `catalog_reconciliation` | - |
| `tjsp_nugepnac` | `contract_pending` | `catalog_reconciliation` | - |
| `tre_sjur_first_degree` | `live_not_federated` | `catalog_reconciliation` | - |
| `trt15_jurisprudencia` | `contract_pending` | `catalog_reconciliation` | - |
| `trt2_basis_jurisprudencia` | `contract_pending` | `catalog_reconciliation` | - |
| `trt2_ementario_jurisprudencia` | `federated_live` | `catalog_reconciliation` | - |
| `trt3_ementario_jurisprudencia` | `live_not_federated` | `catalog_reconciliation` | - |
| `trt4_sumulas_jurisprudencia` | `contract_pending` | `catalog_reconciliation` | - |
| `trt9_nugepnac_jurisprudencia` | `contract_pending` | `catalog_reconciliation` | - |
