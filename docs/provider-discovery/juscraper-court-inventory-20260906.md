# Inventário Juscraper × NanoJuris — 2026-09-01

Inventário estático reproduzível do checkout correto `jtrecenti/juscraper`.
Nenhum código upstream é executado, copiado ou promovido; a matriz serve
para priorização SDD.

- Commit upstream: `604c1dd70d6f313011cc1079790febe6c71807e2`
- Pacotes estaduais: **25**
- Pacotes TRF: **4**
- Providers runtime NanoJuris no cruzamento: **58**
- Tribunais no catálogo NanoJuris: **94**
- Sobreposição de códigos com Juscraper: **29**
- Evidências institucionais/live: `cnj-tribunal-register-20260901.json`, `court-catalog-url-probe-20260901.json`

| Pacote | Superfícies Juscraper | Equivalentes NanoJuris | Classificação | Prioridade |
| --- | --- | --- | --- | --- |
| `tjac` | `cjsg`, `cpopg`, `cposg` | `tjac_cjsg` | `covered_by_existing_runtime` | `maintenance` |
| `tjal` | `cjsg`, `cpopg`, `cposg` | `tjal_cjsg` | `covered_by_existing_runtime` | `maintenance` |
| `tjam` | `cjsg`, `cpopg`, `cposg` | `tjam_cjsg` | `covered_by_existing_runtime` | `maintenance` |
| `tjap` | `cjsg`, `cpopg`, `cposg` | `tjap_tucujuris` | `runtime_overlap_blocked` | `P0_access_or_transport` |
| `tjba` | `cjsg`, `cpopg`, `cposg` | `tjba_graphql` | `covered_by_existing_runtime` | `maintenance` |
| `tjce` | `cjsg`, `cpopg`, `cposg` | `tjce_cjsg` | `covered_by_existing_runtime` | `maintenance` |
| `tjdft` | `cjsg`, `cpopg`, `cposg` | `tjdf_juris` | `covered_by_existing_runtime` | `maintenance` |
| `tjes` | `cjsg`, `cjpg`, `cpopg`, `cposg` | `tjes_cjpg`, `tjes_jurisprudencia` | `covered_by_existing_runtime` | `maintenance` |
| `tjgo` | `cjsg`, `cpopg`, `cposg` | `tjgo_projudi_jurisprudencia` | `covered_by_existing_runtime` | `maintenance` |
| `tjmg` | `cjsg`, `cpopg`, `cposg` | `tjmg_jurisprudencia` | `runtime_overlap_blocked` | `P0_access_or_transport` |
| `tjms` | `cjsg`, `cpopg`, `cposg` | `tjms_cjsg` | `covered_by_existing_runtime` | `maintenance` |
| `tjmt` | `cjsg`, `cpopg`, `cposg` | `tjmt_jurisprudencia_api` | `covered_by_existing_runtime` | `maintenance` |
| `tjpa` | `cjsg`, `cpopg`, `cposg` | `tjpa_jurisprudencia_bff` | `covered_by_existing_runtime` | `maintenance` |
| `tjpb` | `cjsg`, `cpopg`, `cposg` | `tjpb_pje_jurisprudencia` | `covered_by_existing_runtime` | `maintenance` |
| `tjpe` | `cjsg`, `cpopg`, `cposg` | `tjpe_jurisprudencia` | `covered_by_existing_runtime` | `maintenance` |
| `tjpi` | `cjsg`, `cpopg`, `cposg` | `tjpi_juspi` | `covered_by_existing_runtime` | `maintenance` |
| `tjpr` | `cjsg`, `cpopg`, `cposg` | `tjpr_jurisprudencia` | `covered_by_existing_runtime` | `maintenance` |
| `tjrj` | `cjsg`, `cpopg`, `cposg` | `tjrj_eproc_jurisprudencia` | `partial_overlap_review` | `P2_compare_contracts` |
| `tjrn` | `cjsg`, `cpopg`, `cposg` | `tjrn_jurisprudencia` | `covered_by_existing_runtime` | `maintenance` |
| `tjro` | `cjsg`, `cpopg`, `cposg` | `tjro_jurisprudencia` | `covered_by_existing_runtime` | `maintenance` |
| `tjrr` | `cjsg`, `cpopg`, `cposg` | `tjrr_juris` | `covered_by_existing_runtime` | `maintenance` |
| `tjrs` | `cjsg`, `cpopg`, `cposg` | `tjrs_solr` | `covered_by_existing_runtime` | `maintenance` |
| `tjsc` | `cjsg`, `cpopg`, `cposg` | `tjsc_eproc_jurisprudencia` | `partial_overlap_review` | `P2_compare_contracts` |
| `tjsp` | `cjsg`, `cjpg`, `cpopg`, `cposg` | `tjsp_cjpg`, `tjsp_cjsg` | `covered_by_existing_runtime` | `maintenance` |
| `tjto` | `cjsg`, `cjpg`, `detail`, `cpopg`, `cposg` | `tjto_jurisprudencia` | `covered_by_existing_runtime` | `maintenance` |
| `trf1` | `cpopg`, `cposg` | — | `out_of_scope_process_surface` | `out_of_scope` |
| `trf3` | `cpopg`, `cposg` | — | `out_of_scope_process_surface` | `out_of_scope` |
| `trf5` | `cpopg`, `cposg` | — | `out_of_scope_process_surface` | `out_of_scope` |
| `trf6` | `cpopg`, `cposg` | — | `out_of_scope_process_surface` | `out_of_scope` |

## Leitura da matriz

- **21** pacotes possuem equivalentes runtime com evidência live válida para todas as superfícies jurisprudenciais mapeadas.
- **2** pacotes possuem ao menos uma superfície bloqueada; continuam fora da contagem de cobertura.
- **0** pacotes possuem runtime, mas carecem de evidência live válida atual.
- **0** lacunas não têm equivalente runtime; devem ser pesquisadas individualmente, sem assumir que o upstream funciona hoje.
- **2** pacotes têm apenas sobreposição parcial (por exemplo, eSAJ/eproc); nomes semelhantes não provam equivalência.
- **4** pacotes TRF expõem consulta processual (`cpopg`/`cposg`) e permanecem fora da NanoJuris, conforme a fronteira com a NanoJud.
- O catálogo NanoJuris possui mais autoridades que o checkout Juscraper; `courts_not_in_juscraper` explicita essas lacunas sem inferir indisponibilidade.
- A lista nacional foi reconciliada com um snapshot do diretório de tribunais do CNJ; ela cobre autoridades de tribunal, não cada unidade judicial ou órgão administrativo.

O estado live é lido do catálogo gerado do NanoJuris; o inventário não executa rede nem transforma runtime em evidência de disponibilidade.

## Autoridades no catálogo NanoJuris sem pacote Juscraper

Estas autoridades fazem parte do catálogo nacional local, mas não foram encontradas no checkout auditado. A ausência de pacote upstream não é uma afirmação de indisponibilidade da fonte oficial.

| Código | Situação |
| --- | --- |
| `cnj` | `not_in_juscraper_catalog_gap` |
| `stf` | `not_in_juscraper_catalog_gap` |
| `stj` | `not_in_juscraper_catalog_gap` |
| `stm` | `not_in_juscraper_catalog_gap` |
| `tjma` | `not_in_juscraper_catalog_gap` |
| `tjmmg` | `not_in_juscraper_catalog_gap` |
| `tjmrs` | `not_in_juscraper_catalog_gap` |
| `tjmsp` | `not_in_juscraper_catalog_gap` |
| `tjse` | `not_in_juscraper_catalog_gap` |
| `tnu` | `not_in_juscraper_catalog_gap` |
| `treac` | `not_in_juscraper_catalog_gap` |
| `treal` | `not_in_juscraper_catalog_gap` |
| `tream` | `not_in_juscraper_catalog_gap` |
| `treap` | `not_in_juscraper_catalog_gap` |
| `treba` | `not_in_juscraper_catalog_gap` |
| `trece` | `not_in_juscraper_catalog_gap` |
| `tredf` | `not_in_juscraper_catalog_gap` |
| `trees` | `not_in_juscraper_catalog_gap` |
| `trego` | `not_in_juscraper_catalog_gap` |
| `trema` | `not_in_juscraper_catalog_gap` |
| `tremg` | `not_in_juscraper_catalog_gap` |
| `trems` | `not_in_juscraper_catalog_gap` |
| `tremt` | `not_in_juscraper_catalog_gap` |
| `trepa` | `not_in_juscraper_catalog_gap` |
| `trepb` | `not_in_juscraper_catalog_gap` |
| `trepe` | `not_in_juscraper_catalog_gap` |
| `trepi` | `not_in_juscraper_catalog_gap` |
| `trepr` | `not_in_juscraper_catalog_gap` |
| `trerj` | `not_in_juscraper_catalog_gap` |
| `trern` | `not_in_juscraper_catalog_gap` |
| `trero` | `not_in_juscraper_catalog_gap` |
| `trerr` | `not_in_juscraper_catalog_gap` |
| `trers` | `not_in_juscraper_catalog_gap` |
| `tresc` | `not_in_juscraper_catalog_gap` |
| `trese` | `not_in_juscraper_catalog_gap` |
| `tresp` | `not_in_juscraper_catalog_gap` |
| `treto` | `not_in_juscraper_catalog_gap` |
| `trf2` | `not_in_juscraper_catalog_gap` |
| `trf4` | `not_in_juscraper_catalog_gap` |
| `trt1` | `not_in_juscraper_catalog_gap` |
| `trt10` | `not_in_juscraper_catalog_gap` |
| `trt11` | `not_in_juscraper_catalog_gap` |
| `trt12` | `not_in_juscraper_catalog_gap` |
| `trt13` | `not_in_juscraper_catalog_gap` |
| `trt14` | `not_in_juscraper_catalog_gap` |
| `trt15` | `not_in_juscraper_catalog_gap` |
| `trt16` | `not_in_juscraper_catalog_gap` |
| `trt17` | `not_in_juscraper_catalog_gap` |
| `trt18` | `not_in_juscraper_catalog_gap` |
| `trt19` | `not_in_juscraper_catalog_gap` |
| `trt2` | `not_in_juscraper_catalog_gap` |
| `trt20` | `not_in_juscraper_catalog_gap` |
| `trt21` | `not_in_juscraper_catalog_gap` |
| `trt22` | `not_in_juscraper_catalog_gap` |
| `trt23` | `not_in_juscraper_catalog_gap` |
| `trt24` | `not_in_juscraper_catalog_gap` |
| `trt3` | `not_in_juscraper_catalog_gap` |
| `trt4` | `not_in_juscraper_catalog_gap` |
| `trt5` | `not_in_juscraper_catalog_gap` |
| `trt6` | `not_in_juscraper_catalog_gap` |
| `trt7` | `not_in_juscraper_catalog_gap` |
| `trt8` | `not_in_juscraper_catalog_gap` |
| `trt9` | `not_in_juscraper_catalog_gap` |
| `tse` | `not_in_juscraper_catalog_gap` |
| `tst` | `not_in_juscraper_catalog_gap` |
