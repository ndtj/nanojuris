# Programa nacional de segundo grau dos TJs

Gerado em `2026-09-13`. Nao editar a tabela manualmente.

Cobertura significa oito gates comprovados por superficie; provider existente ou HTTP 200 isolado nao basta.

## Resumo

- Tribunais: **27/27** mapeados.
- Workpacks completos: **25/27**.
- Workpacks incompletos: **2**.

## Workpacks

| TJ | Provider | Estado | Acao | Gates | Proxima tarefa |
| --- | --- | --- | --- | ---: | --- |
| `TJAC` | `tjac_cjsg` | `live_validated` | `maintenance` | 8/8 | Revalidacao periodica |
| `TJAL` | `tjal_cjsg` | `live_validated` | `maintenance` | 8/8 | Revalidacao periodica |
| `TJAM` | `tjam_cjsg` | `live_validated` | `maintenance` | 8/8 | Revalidacao periodica |
| `TJAP` | `tjap_tucujuris` | `blocked_access` | `blocked_recheck` | 1/8 | Provar contrato especifico de segundo grau/CJSG |
| `TJBA` | `tjba_graphql` | `live_validated` | `maintenance` | 8/8 | Revalidacao periodica |
| `TJCE` | `tjce_cjsg` | `live_validated` | `maintenance` | 8/8 | Revalidacao periodica |
| `TJDFT` | `tjdf_juris` | `live_validated` | `maintenance` | 8/8 | Revalidacao periodica |
| `TJES` | `tjes_jurisprudencia` | `live_validated` | `maintenance` | 8/8 | Revalidacao periodica |
| `TJGO` | `tjgo_projudi_jurisprudencia` | `live_validated` | `maintenance` | 8/8 | Revalidacao periodica |
| `TJMA` | `-` | `candidate` | `blocked_recheck` | 0/8 | Confirmar fonte oficial, rota publica e limites |
| `TJMG` | `tjmg_dspace_jurisprudencia` | `live_validated` | `maintenance` | 8/8 | Revalidacao periodica |
| `TJMS` | `tjms_cjsg` | `live_validated` | `maintenance` | 8/8 | Revalidacao periodica |
| `TJMT` | `tjmt_jurisprudencia_api` | `live_validated` | `maintenance` | 8/8 | Revalidacao periodica |
| `TJPA` | `tjpa_jurisprudencia_bff` | `live_validated` | `maintenance` | 8/8 | Revalidacao periodica |
| `TJPB` | `tjpb_pje_jurisprudencia` | `live_validated` | `maintenance` | 8/8 | Revalidacao periodica |
| `TJPE` | `tjpe_jurisprudencia` | `live_validated` | `maintenance` | 8/8 | Revalidacao periodica |
| `TJPI` | `tjpi_juspi` | `live_validated` | `maintenance` | 8/8 | Revalidacao periodica |
| `TJPR` | `tjpr_jurisprudencia` | `live_validated` | `maintenance` | 8/8 | Revalidacao periodica |
| `TJRJ` | `tjrj_eproc_jurisprudencia` | `live_validated` | `maintenance` | 8/8 | Revalidacao periodica |
| `TJRN` | `tjrn_jurisprudencia` | `live_validated` | `maintenance` | 8/8 | Revalidacao periodica |
| `TJRO` | `tjro_jurisprudencia` | `live_validated` | `maintenance` | 8/8 | Revalidacao periodica |
| `TJRR` | `tjrr_juris` | `live_validated` | `maintenance` | 8/8 | Revalidacao periodica |
| `TJRS` | `tjrs_solr` | `live_validated` | `maintenance` | 8/8 | Revalidacao periodica |
| `TJSC` | `tjsc_eproc_jurisprudencia` | `live_validated` | `maintenance` | 8/8 | Revalidacao periodica |
| `TJSE` | `tjse_boletim_jurisprudencia` | `live_validated` | `maintenance` | 8/8 | Revalidacao periodica |
| `TJSP` | `tjsp_cjsg` | `live_validated` | `maintenance` | 8/8 | Revalidacao periodica |
| `TJTO` | `tjto_jurisprudencia` | `live_validated` | `maintenance` | 8/8 | Revalidacao periodica |

## Definicao dos gates

1. `official_source` - Confirmar fonte oficial, rota publica e limites.
2. `degree_contract` - Provar contrato especifico de segundo grau/CJSG.
3. `adapter` - Implementar e registrar adapter com erros explicitos.
4. `fixtures` - Cobrir sucesso, vazio, parametro invalido e schema drift.
5. `pagination_filters` - Validar pagina 2, ordenacao e filtros.
6. `live_validation` - Executar chamada live bounded com conteudo juridico.
7. `quality` - Validar identidade, grau, trace e deduplicacao.
8. `federation` - Habilitar federacao somente apos todos os gates.

Bloqueios de acesso/transporte permanecem explicitos e nunca sao convertidos em resultado vazio. Os detalhes executaveis de cada tribunal estao no array `workpacks` do JSON correspondente.
