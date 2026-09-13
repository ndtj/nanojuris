# Juscraper x NanoJuris - semantic diff (2026-09-01)

Auditoria estatica por AST do checkout fixado. Nao executa Juscraper,
nao chama a rede e nao promove adapters.

- Commit upstream: `604c1dd70d6f313011cc1079790febe6c71807e2`
- Pacotes: **29**; registros de superficie: **87**
- Estados: `{"covered_requires_differential_fixture": 27, "detail_contract_unverified": 1, "out_of_scope": 58, "runtime_overlap_blocked": 1}`

| Tribunal | Superficie | Equivalente | Estado | Evidencia estatica |
| --- | --- | --- | --- | --- |
| `tjac` | `cjsg` | `tjac_cjsg` | `covered_requires_differential_fixture` | - |
| `tjac` | `cpopg` | `tjac_cjsg` | `out_of_scope` | - |
| `tjac` | `cposg` | `tjac_cjsg` | `out_of_scope` | - |
| `tjal` | `cjsg` | `tjal_cjsg` | `covered_requires_differential_fixture` | - |
| `tjal` | `cpopg` | `tjal_cjsg` | `out_of_scope` | - |
| `tjal` | `cposg` | `tjal_cjsg` | `out_of_scope` | - |
| `tjam` | `cjsg` | `tjam_cjsg` | `covered_requires_differential_fixture` | - |
| `tjam` | `cpopg` | `tjam_cjsg` | `out_of_scope` | - |
| `tjam` | `cposg` | `tjam_cjsg` | `out_of_scope` | - |
| `tjap` | `cjsg` | `tjap_tucujuris` | `runtime_overlap_blocked` | `client.py` |
| `tjap` | `cpopg` | `tjap_tucujuris` | `out_of_scope` | `client.py` |
| `tjap` | `cposg` | `tjap_tucujuris` | `out_of_scope` | `client.py` |
| `tjba` | `cjsg` | `tjba_graphql` | `covered_requires_differential_fixture` | `client.py`, `download.py`, `parse.py` |
| `tjba` | `cpopg` | `tjba_graphql` | `out_of_scope` | `client.py` |
| `tjba` | `cposg` | `tjba_graphql` | `out_of_scope` | `client.py` |
| `tjce` | `cjsg` | `tjce_cjsg` | `covered_requires_differential_fixture` | - |
| `tjce` | `cpopg` | `tjce_cjsg` | `out_of_scope` | - |
| `tjce` | `cposg` | `tjce_cjsg` | `out_of_scope` | - |
| `tjdft` | `cjsg` | `tjdf_juris` | `covered_requires_differential_fixture` | `client.py`, `download.py`, `parse.py` |
| `tjdft` | `cpopg` | `tjdf_juris` | `out_of_scope` | `client.py` |
| `tjdft` | `cposg` | `tjdf_juris` | `out_of_scope` | `client.py` |
| `tjes` | `cjsg` | `tjes_jurisprudencia` | `covered_requires_differential_fixture` | `client.py`, `download.py`, `parse.py` |
| `tjes` | `cjpg` | `tjes_jurisprudencia` | `covered_requires_differential_fixture` | `client.py` |
| `tjes` | `cpopg` | `tjes_jurisprudencia` | `out_of_scope` | `client.py` |
| `tjes` | `cposg` | `tjes_jurisprudencia` | `out_of_scope` | `client.py` |
| `tjgo` | `cjsg` | `tjgo_projudi_jurisprudencia` | `covered_requires_differential_fixture` | `client.py`, `download.py`, `parse.py` |
| `tjgo` | `cpopg` | `tjgo_projudi_jurisprudencia` | `out_of_scope` | `client.py` |
| `tjgo` | `cposg` | `tjgo_projudi_jurisprudencia` | `out_of_scope` | `client.py` |
| `tjmg` | `cjsg` | `tjmg_jurisprudencia` | `covered_requires_differential_fixture` | `client.py`, `download.py`, `parse.py` |
| `tjmg` | `cpopg` | `tjmg_jurisprudencia` | `out_of_scope` | `client.py` |
| `tjmg` | `cposg` | `tjmg_jurisprudencia` | `out_of_scope` | `client.py` |
| `tjms` | `cjsg` | `tjms_cjsg` | `covered_requires_differential_fixture` | - |
| `tjms` | `cpopg` | `tjms_cjsg` | `out_of_scope` | - |
| `tjms` | `cposg` | `tjms_cjsg` | `out_of_scope` | - |
| `tjmt` | `cjsg` | `tjmt_jurisprudencia_api` | `covered_requires_differential_fixture` | `client.py`, `download.py`, `parse.py` |
| `tjmt` | `cpopg` | `tjmt_jurisprudencia_api` | `out_of_scope` | `client.py` |
| `tjmt` | `cposg` | `tjmt_jurisprudencia_api` | `out_of_scope` | `client.py` |
| `tjpa` | `cjsg` | `tjpa_jurisprudencia_bff` | `covered_requires_differential_fixture` | `client.py` |
| `tjpa` | `cpopg` | `tjpa_jurisprudencia_bff` | `out_of_scope` | `client.py` |
| `tjpa` | `cposg` | `tjpa_jurisprudencia_bff` | `out_of_scope` | `client.py` |
| `tjpb` | `cjsg` | `tjpb_pje_jurisprudencia` | `covered_requires_differential_fixture` | `client.py` |
| `tjpb` | `cpopg` | `tjpb_pje_jurisprudencia` | `out_of_scope` | `client.py` |
| `tjpb` | `cposg` | `tjpb_pje_jurisprudencia` | `out_of_scope` | `client.py` |
| `tjpe` | `cjsg` | `tjpe_jurisprudencia` | `covered_requires_differential_fixture` | `client.py`, `download.py`, `parse.py` |
| `tjpe` | `cpopg` | `tjpe_jurisprudencia` | `out_of_scope` | `client.py` |
| `tjpe` | `cposg` | `tjpe_jurisprudencia` | `out_of_scope` | `client.py` |
| `tjpi` | `cjsg` | `tjpi_juspi` | `covered_requires_differential_fixture` | `client.py` |
| `tjpi` | `cpopg` | `tjpi_juspi` | `out_of_scope` | `client.py` |
| `tjpi` | `cposg` | `tjpi_juspi` | `out_of_scope` | `client.py` |
| `tjpr` | `cjsg` | `tjpr_jurisprudencia` | `covered_requires_differential_fixture` | `client.py`, `download.py`, `parse.py` |
| `tjpr` | `cpopg` | `tjpr_jurisprudencia` | `out_of_scope` | `client.py` |
| `tjpr` | `cposg` | `tjpr_jurisprudencia` | `out_of_scope` | `client.py` |
| `tjrj` | `cjsg` | `tjrj_ejuris` | `covered_requires_differential_fixture` | `client.py`, `download.py`, `parse.py` |
| `tjrj` | `cpopg` | `tjrj_ejuris` | `out_of_scope` | `client.py` |
| `tjrj` | `cposg` | `tjrj_ejuris` | `out_of_scope` | `client.py` |
| `tjrn` | `cjsg` | `tjrn_jurisprudencia` | `covered_requires_differential_fixture` | `client.py` |
| `tjrn` | `cpopg` | `tjrn_jurisprudencia` | `out_of_scope` | `client.py` |
| `tjrn` | `cposg` | `tjrn_jurisprudencia` | `out_of_scope` | `client.py` |
| `tjro` | `cjsg` | `tjro_jurisprudencia` | `covered_requires_differential_fixture` | `client.py` |
| `tjro` | `cpopg` | `tjro_jurisprudencia` | `out_of_scope` | `client.py` |
| `tjro` | `cposg` | `tjro_jurisprudencia` | `out_of_scope` | `client.py` |
| `tjrr` | `cjsg` | `tjrr_juris` | `covered_requires_differential_fixture` | `client.py` |
| `tjrr` | `cpopg` | `tjrr_juris` | `out_of_scope` | `client.py` |
| `tjrr` | `cposg` | `tjrr_juris` | `out_of_scope` | `client.py` |
| `tjrs` | `cjsg` | `tjrs_solr` | `covered_requires_differential_fixture` | `client.py` |
| `tjrs` | `cpopg` | `tjrs_solr` | `out_of_scope` | `client.py` |
| `tjrs` | `cposg` | `tjrs_solr` | `out_of_scope` | `client.py` |
| `tjsc` | `cjsg` | `tjsc_eproc_jurisprudencia` | `covered_requires_differential_fixture` | `client.py` |
| `tjsc` | `cpopg` | `tjsc_eproc_jurisprudencia` | `out_of_scope` | `client.py` |
| `tjsc` | `cposg` | `tjsc_eproc_jurisprudencia` | `out_of_scope` | `client.py` |
| `tjsp` | `cjsg` | `tjsp_cjsg` | `covered_requires_differential_fixture` | `client.py` |
| `tjsp` | `cjpg` | `tjsp_cjsg` | `covered_requires_differential_fixture` | `cjpg_download.py`, `client.py` |
| `tjsp` | `cpopg` | `tjsp_cjsg` | `out_of_scope` | `client.py` |
| `tjsp` | `cposg` | `tjsp_cjsg` | `out_of_scope` | `client.py` |
| `tjto` | `cjsg` | `tjto_jurisprudencia` | `covered_requires_differential_fixture` | `client.py` |
| `tjto` | `cjpg` | `tjto_jurisprudencia` | `covered_requires_differential_fixture` | `client.py` |
| `tjto` | `detail` | `tjto_jurisprudencia` | `detail_contract_unverified` | `client.py` |
| `tjto` | `cpopg` | `tjto_jurisprudencia` | `out_of_scope` | `client.py` |
| `tjto` | `cposg` | `tjto_jurisprudencia` | `out_of_scope` | `client.py` |
| `trf1` | `cpopg` | - | `out_of_scope` | - |
| `trf1` | `cposg` | - | `out_of_scope` | - |
| `trf3` | `cpopg` | - | `out_of_scope` | - |
| `trf3` | `cposg` | - | `out_of_scope` | - |
| `trf5` | `cpopg` | `trf5_jurisprudencia` | `out_of_scope` | - |
| `trf5` | `cposg` | `trf5_jurisprudencia` | `out_of_scope` | - |
| `trf6` | `cpopg` | `trf6_eproc_jurisprudencia` | `out_of_scope` | `client.py` |
| `trf6` | `cposg` | `trf6_eproc_jurisprudencia` | `out_of_scope` | - |

## Regra de leitura

- AST extraction does not prove the HTTP payload or live availability.
- Field and filter names are not equivalent until a source-specific replay maps behavior.
- Process surfaces remain out of scope for NanoJuris and are not adapters.
- No upstream code, fixture, cookie, credential or response body is copied.
