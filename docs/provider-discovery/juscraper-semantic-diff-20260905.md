# Juscraper x NanoJuris - semantic diff (2026-09-01)

Auditoria estatica por AST do checkout fixado. Nao executa Juscraper,
nao chama a rede e nao promove adapters.

- Commit upstream: `604c1dd70d6f313011cc1079790febe6c71807e2`
- Pacotes: **29**; registros de superficie: **87**
- Estados: `{"covered_requires_differential_fixture": 25, "detail_contract_unverified": 1, "no_runtime_equivalent": 3, "out_of_scope": 58}`

| Tribunal | Superficie | Equivalente | Estado | Evidencia estatica |
| --- | --- | --- | --- | --- |
| `tjac` | `cjsg` | `tjac_cjsg` | `covered_requires_differential_fixture` | - |
| `tjac` | `cpopg` | - | `out_of_scope` | - |
| `tjac` | `cposg` | - | `out_of_scope` | - |
| `tjal` | `cjsg` | `tjal_cjsg` | `covered_requires_differential_fixture` | - |
| `tjal` | `cpopg` | - | `out_of_scope` | - |
| `tjal` | `cposg` | - | `out_of_scope` | - |
| `tjam` | `cjsg` | `tjam_cjsg` | `covered_requires_differential_fixture` | - |
| `tjam` | `cpopg` | - | `out_of_scope` | - |
| `tjam` | `cposg` | - | `out_of_scope` | - |
| `tjap` | `cjsg` | - | `no_runtime_equivalent` | `client.py` |
| `tjap` | `cpopg` | - | `out_of_scope` | `client.py` |
| `tjap` | `cposg` | - | `out_of_scope` | `client.py` |
| `tjba` | `cjsg` | `tjba_graphql` | `covered_requires_differential_fixture` | `client.py`, `download.py`, `parse.py` |
| `tjba` | `cpopg` | - | `out_of_scope` | `client.py` |
| `tjba` | `cposg` | - | `out_of_scope` | `client.py` |
| `tjce` | `cjsg` | `tjce_cjsg` | `covered_requires_differential_fixture` | - |
| `tjce` | `cpopg` | - | `out_of_scope` | - |
| `tjce` | `cposg` | - | `out_of_scope` | - |
| `tjdft` | `cjsg` | `tjdf_juris` | `covered_requires_differential_fixture` | `client.py`, `download.py`, `parse.py` |
| `tjdft` | `cpopg` | - | `out_of_scope` | `client.py` |
| `tjdft` | `cposg` | - | `out_of_scope` | `client.py` |
| `tjes` | `cjsg` | `tjes_jurisprudencia` | `covered_requires_differential_fixture` | `client.py`, `download.py`, `parse.py` |
| `tjes` | `cpopg` | - | `out_of_scope` | `client.py` |
| `tjes` | `cposg` | - | `out_of_scope` | `client.py` |
| `tjes` | `cjpg` | `tjes_cjpg` | `covered_requires_differential_fixture` | `client.py` |
| `tjgo` | `cjsg` | `tjgo_projudi_jurisprudencia` | `covered_requires_differential_fixture` | `client.py`, `download.py`, `parse.py` |
| `tjgo` | `cpopg` | - | `out_of_scope` | `client.py` |
| `tjgo` | `cposg` | - | `out_of_scope` | `client.py` |
| `tjmg` | `cjsg` | - | `no_runtime_equivalent` | `client.py`, `download.py`, `parse.py` |
| `tjmg` | `cpopg` | - | `out_of_scope` | `client.py` |
| `tjmg` | `cposg` | - | `out_of_scope` | `client.py` |
| `tjms` | `cjsg` | `tjms_cjsg` | `covered_requires_differential_fixture` | - |
| `tjms` | `cpopg` | - | `out_of_scope` | - |
| `tjms` | `cposg` | - | `out_of_scope` | - |
| `tjmt` | `cjsg` | `tjmt_jurisprudencia_api` | `covered_requires_differential_fixture` | `client.py`, `download.py`, `parse.py` |
| `tjmt` | `cpopg` | - | `out_of_scope` | `client.py` |
| `tjmt` | `cposg` | - | `out_of_scope` | `client.py` |
| `tjpa` | `cjsg` | `tjpa_jurisprudencia_bff` | `covered_requires_differential_fixture` | `client.py` |
| `tjpa` | `cpopg` | - | `out_of_scope` | `client.py` |
| `tjpa` | `cposg` | - | `out_of_scope` | `client.py` |
| `tjpb` | `cjsg` | `tjpb_pje_jurisprudencia` | `covered_requires_differential_fixture` | `client.py` |
| `tjpb` | `cpopg` | - | `out_of_scope` | `client.py` |
| `tjpb` | `cposg` | - | `out_of_scope` | `client.py` |
| `tjpe` | `cjsg` | `tjpe_jurisprudencia` | `covered_requires_differential_fixture` | `client.py`, `download.py`, `parse.py` |
| `tjpe` | `cpopg` | - | `out_of_scope` | `client.py` |
| `tjpe` | `cposg` | - | `out_of_scope` | `client.py` |
| `tjpi` | `cjsg` | `tjpi_juspi` | `covered_requires_differential_fixture` | `client.py` |
| `tjpi` | `cpopg` | - | `out_of_scope` | `client.py` |
| `tjpi` | `cposg` | - | `out_of_scope` | `client.py` |
| `tjpr` | `cjsg` | `tjpr_jurisprudencia` | `covered_requires_differential_fixture` | `client.py`, `download.py`, `parse.py` |
| `tjpr` | `cpopg` | - | `out_of_scope` | `client.py` |
| `tjpr` | `cposg` | - | `out_of_scope` | `client.py` |
| `tjrj` | `cjsg` | `tjrj_eproc_jurisprudencia` | `covered_requires_differential_fixture` | `client.py`, `download.py`, `parse.py` |
| `tjrj` | `cpopg` | - | `out_of_scope` | `client.py` |
| `tjrj` | `cposg` | - | `out_of_scope` | `client.py` |
| `tjrn` | `cjsg` | `tjrn_jurisprudencia` | `covered_requires_differential_fixture` | `client.py` |
| `tjrn` | `cpopg` | - | `out_of_scope` | `client.py` |
| `tjrn` | `cposg` | - | `out_of_scope` | `client.py` |
| `tjro` | `cjsg` | `tjro_jurisprudencia` | `covered_requires_differential_fixture` | `client.py` |
| `tjro` | `cpopg` | - | `out_of_scope` | `client.py` |
| `tjro` | `cposg` | - | `out_of_scope` | `client.py` |
| `tjrr` | `cjsg` | `tjrr_juris` | `covered_requires_differential_fixture` | `client.py` |
| `tjrr` | `cpopg` | - | `out_of_scope` | `client.py` |
| `tjrr` | `cposg` | - | `out_of_scope` | `client.py` |
| `tjrs` | `cjsg` | `tjrs_solr` | `covered_requires_differential_fixture` | `client.py` |
| `tjrs` | `cpopg` | - | `out_of_scope` | `client.py` |
| `tjrs` | `cposg` | - | `out_of_scope` | `client.py` |
| `tjsc` | `cjsg` | `tjsc_eproc_jurisprudencia` | `covered_requires_differential_fixture` | `client.py` |
| `tjsc` | `cpopg` | - | `out_of_scope` | `client.py` |
| `tjsc` | `cposg` | - | `out_of_scope` | `client.py` |
| `tjsp` | `cjsg` | `tjsp_cjsg` | `covered_requires_differential_fixture` | `client.py` |
| `tjsp` | `cpopg` | - | `out_of_scope` | `client.py` |
| `tjsp` | `cposg` | - | `out_of_scope` | `client.py` |
| `tjsp` | `cjpg` | `tjsp_cjpg` | `covered_requires_differential_fixture` | `cjpg_download.py`, `client.py` |
| `tjto` | `cjsg` | `tjto_jurisprudencia` | `covered_requires_differential_fixture` | `client.py` |
| `tjto` | `cpopg` | - | `out_of_scope` | `client.py` |
| `tjto` | `cposg` | - | `out_of_scope` | `client.py` |
| `tjto` | `cjpg` | - | `no_runtime_equivalent` | `client.py` |
| `tjto` | `detail` | `tjto_jurisprudencia` | `detail_contract_unverified` | `client.py` |
| `trf1` | `cpopg` | - | `out_of_scope` | - |
| `trf1` | `cposg` | - | `out_of_scope` | - |
| `trf3` | `cpopg` | - | `out_of_scope` | - |
| `trf3` | `cposg` | - | `out_of_scope` | - |
| `trf5` | `cpopg` | - | `out_of_scope` | - |
| `trf5` | `cposg` | - | `out_of_scope` | - |
| `trf6` | `cpopg` | - | `out_of_scope` | `client.py` |
| `trf6` | `cposg` | - | `out_of_scope` | - |

## Regra de leitura

- AST extraction does not prove the HTTP payload or live availability.
- Field and filter names are not equivalent until a source-specific replay maps behavior.
- Process surfaces remain out of scope for NanoJuris and are not adapters.
- No upstream code, fixture, cookie, credential or response body is copied.
