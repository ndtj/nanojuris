# Provider Documentation Audit

Snapshot local: `2026-09-13`. Este relatorio e uma fotografia reproduzivel do estado documental;
nao afirma que uma rota nao observada exista nem que um provider esteja disponivel em qualquer rede.

## Como Ler

- `implemented`: existe no runtime; o nivel e risco vem de `source_contracts`.
- `candidate`: existe pesquisa documental, mas nao existe provider runtime.
- `family`: contrato compartilhado de implementacao, nao uma fonte executavel isolada.
- `needs_deepening`: provider implementado com lacunas documentais ou checklist aberto.
- `research_incomplete`: candidato ainda sem alguma secao obrigatoria.
- `research_ready`: candidato documentado para a proxima fase, ainda sem autorizacao para codigo.

## Resumo

- Dossies auditados: **85** (80 implemented, 5 candidates, 0 family).
- Dossies com secoes estruturais: **78/85**.
- Canonical/legacy em paridade: **85/85**.
- Prontidao: `implementation_ready`=66, `needs_deepening`=14, `research_incomplete`=1, `research_ready`=4.

A paridade confirma preservacao de informacao durante a migracao. Ela nao substitui a revisao
do contrato: itens `[ ]`, estados `pendente` e rotas apenas observadas continuam sendo bloqueios reais.

A evidencia live mais recente esta em [live-validation-latest.md](live-validation-latest.md).
A evidencia historica das 28 fontes candidatas esta em [candidate-live-validation-2026-08-11.md](candidate-live-validation-2026-08-11.md).

## Matriz Por Provider

| Provider | Ciclo | Prontidao | Nivel | Risco | Secoes faltantes | Pendencias | Fixtures referenciadas |
| --- | --- | --- | ---: | --- | --- | ---: | ---: |
| [`bnp_pangea`](providers/bnp_pangea/README.md) | implemented | `implementation_ready` | 4 | medio | - | 0 | 3 |
| [`cjf_jurisprudencia`](providers/cjf_jurisprudencia/README.md) | implemented | `needs_deepening` | 4 | medio | - | 2 | 8 |
| [`cnj_jurisprudencia`](providers/cnj_jurisprudencia/README.md) | implemented | `implementation_ready` | 4 | medio | - | 0 | 3 |
| [`eproc_jurisprudencia_federal`](providers/eproc_jurisprudencia_federal/README.md) | implemented | `implementation_ready` | 4 | medio | - | 0 | 3 |
| [`falcao_jt`](providers/falcao_jt/README.md) | candidate | `research_ready` | - | research | - | 0 | 2 |
| [`justica_eleitoral_sjur`](providers/justica_eleitoral_sjur/README.md) | implemented | `needs_deepening` | 4 | medio | - | 2 | 4 |
| [`stf_informativo`](providers/stf_informativo/README.md) | implemented | `needs_deepening` | 5 | baixo | - | 3 | 4 |
| [`stf_juris`](providers/stf_juris/README.md) | implemented | `needs_deepening` | 4 | alto | - | 3 | 6 |
| [`stj_dados_abertos_jurisprudencia`](providers/stj_dados_abertos_jurisprudencia/README.md) | implemented | `implementation_ready` | 4 | medio | - | 0 | 5 |
| [`stj_informativo`](providers/stj_informativo/README.md) | implemented | `implementation_ready` | 5 | medio | - | 0 | 5 |
| [`stj_scon`](providers/stj_scon/README.md) | implemented | `implementation_ready` | 4 | alto | - | 0 | 7 |
| [`stm_jurisprudencia`](providers/stm_jurisprudencia/README.md) | implemented | `implementation_ready` | 4 | medio | - | 0 | 4 |
| [`tce_pr_viajuris`](providers/tce_pr_viajuris/README.md) | implemented | `implementation_ready` | 4 | medio | - | 0 | 3 |
| [`tce_sp_jurisprudencia`](providers/tce_sp_jurisprudencia/README.md) | implemented | `implementation_ready` | 4 | alto | - | 0 | 6 |
| [`tcu_jurisprudencia`](providers/tcu_jurisprudencia/README.md) | implemented | `implementation_ready` | 4 | medio | - | 0 | 8 |
| [`tjac_banco_sentencas`](providers/tjac_banco_sentencas/README.md) | implemented | `implementation_ready` | 4 | medio | - | 0 | 1 |
| [`tjac_cjsg`](providers/tjac_cjsg/README.md) | implemented | `implementation_ready` | 4 | alto | - | 0 | 3 |
| [`tjac_ementario_jurisprudencia`](providers/tjac_ementario_jurisprudencia/README.md) | implemented | `implementation_ready` | 4 | medio | - | 0 | 4 |
| [`tjal_cjsg`](providers/tjal_cjsg/README.md) | implemented | `implementation_ready` | 4 | alto | - | 0 | 4 |
| [`tjal_esmal_banco_sentencas`](providers/tjal_esmal_banco_sentencas/README.md) | implemented | `implementation_ready` | 4 | medio | - | 0 | 7 |
| [`tjal_turma_recursal_ementario`](providers/tjal_turma_recursal_ementario/README.md) | implemented | `implementation_ready` | 4 | medio | - | 0 | 7 |
| [`tjam_cjsg`](providers/tjam_cjsg/README.md) | implemented | `implementation_ready` | 4 | alto | - | 0 | 4 |
| [`tjap_banco_sentencas`](providers/tjap_banco_sentencas/README.md) | implemented | `implementation_ready` | 4 | medio | - | 0 | 4 |
| [`tjap_tucujuris`](providers/tjap_tucujuris/README.md) | candidate | `research_ready` | - | research | - | 0 | 2 |
| [`tjba_graphql`](providers/tjba_graphql/README.md) | implemented | `implementation_ready` | 5 | medio | - | 0 | 3 |
| [`tjce_cjsg`](providers/tjce_cjsg/README.md) | implemented | `implementation_ready` | 4 | alto | - | 0 | 4 |
| [`tjce_informativos`](providers/tjce_informativos/README.md) | implemented | `needs_deepening` | 4 | medio | - | 5 | 1 |
| [`tjce_sjuris`](providers/tjce_sjuris/README.md) | implemented | `implementation_ready` | 4 | medio | - | 0 | 3 |
| [`tjdf_juris`](providers/tjdf_juris/README.md) | implemented | `implementation_ready` | 5 | baixo | - | 0 | 3 |
| [`tjes_cjpg`](providers/tjes_cjpg/README.md) | implemented | `implementation_ready` | 4 | alto | - | 0 | 7 |
| [`tjes_jurisprudencia`](providers/tjes_jurisprudencia/README.md) | implemented | `implementation_ready` | 4 | alto | - | 0 | 4 |
| [`tjes_turma_recursal`](providers/tjes_turma_recursal/README.md) | implemented | `implementation_ready` | 4 | alto | - | 0 | 4 |
| [`tjgo_projudi_jurisprudencia`](providers/tjgo_projudi_jurisprudencia/README.md) | implemented | `implementation_ready` | 4 | alto | - | 0 | 5 |
| [`tjma_informativos`](providers/tjma_informativos/README.md) | implemented | `implementation_ready` | 4 | medio | - | 0 | 1 |
| [`tjma_jurisconsult`](providers/tjma_jurisconsult/README.md) | implemented | `implementation_ready` | 4 | alto | - | 0 | 1 |
| [`tjmg_dspace_jurisprudencia`](providers/tjmg_dspace_jurisprudencia/README.md) | implemented | `implementation_ready` | 4 | medio | - | 0 | 3 |
| [`tjmg_ejef_boletim_jurisprudencia`](providers/tjmg_ejef_boletim_jurisprudencia/README.md) | implemented | `implementation_ready` | 4 | medio | - | 0 | 6 |
| [`tjmg_jurisprudencia`](providers/tjmg_jurisprudencia/README.md) | implemented | `implementation_ready` | 4 | alto | - | 0 | 5 |
| [`tjmmg_jurisprudencia_api`](providers/tjmmg_jurisprudencia_api/README.md) | implemented | `implementation_ready` | 4 | medio | - | 0 | 1 |
| [`tjmrs_jurisprudencia`](providers/tjmrs_jurisprudencia/README.md) | implemented | `needs_deepening` | 4 | medio | data, mcp, next_steps | 0 | 2 |
| [`tjms_cjpg`](providers/tjms_cjpg/README.md) | implemented | `implementation_ready` | 4 | alto | - | 0 | 4 |
| [`tjms_cjsg`](providers/tjms_cjsg/README.md) | implemented | `implementation_ready` | 4 | alto | - | 0 | 5 |
| [`tjmsp_jurisprudencia`](providers/tjmsp_jurisprudencia/README.md) | candidate | `research_incomplete` | - | research | data, states, fixtures, mcp, next_steps | 0 | 0 |
| [`tjmt_jurisprudencia_api`](providers/tjmt_jurisprudencia_api/README.md) | implemented | `implementation_ready` | 4 | medio | - | 0 | 4 |
| [`tjpa_jurisprudencia_bff`](providers/tjpa_jurisprudencia_bff/README.md) | implemented | `implementation_ready` | 5 | medio | - | 0 | 7 |
| [`tjpb_pje_jurisprudencia`](providers/tjpb_pje_jurisprudencia/README.md) | implemented | `implementation_ready` | 5 | medio | - | 0 | 5 |
| [`tjpe_jurisprudencia`](providers/tjpe_jurisprudencia/README.md) | implemented | `implementation_ready` | 4 | medio | - | 0 | 5 |
| [`tjpi_juspi`](providers/tjpi_juspi/README.md) | implemented | `implementation_ready` | 5 | medio | - | 0 | 6 |
| [`tjpr_jurisprudencia`](providers/tjpr_jurisprudencia/README.md) | implemented | `implementation_ready` | 5 | medio | - | 0 | 4 |
| [`tjrj_banco_sentencas`](providers/tjrj_banco_sentencas/README.md) | implemented | `implementation_ready` | 4 | medio | - | 0 | 1 |
| [`tjrj_ejuris`](providers/tjrj_ejuris/README.md) | implemented | `implementation_ready` | 4 | medio | - | 0 | 5 |
| [`tjrj_eproc_jurisprudencia`](providers/tjrj_eproc_jurisprudencia/README.md) | implemented | `implementation_ready` | 4 | medio | - | 0 | 6 |
| [`tjrn_jurisprudencia`](providers/tjrn_jurisprudencia/README.md) | implemented | `implementation_ready` | 4 | alto | - | 0 | 4 |
| [`tjro_jurisprudencia`](providers/tjro_jurisprudencia/README.md) | implemented | `implementation_ready` | 4 | medio | - | 0 | 7 |
| [`tjro_liame`](providers/tjro_liame/README.md) | implemented | `implementation_ready` | 4 | medio | - | 0 | 3 |
| [`tjrr_juris`](providers/tjrr_juris/README.md) | implemented | `implementation_ready` | 5 | medio | - | 0 | 3 |
| [`tjrs_solr`](providers/tjrs_solr/README.md) | implemented | `implementation_ready` | 5 | medio | - | 0 | 5 |
| [`tjsc_eproc_jurisprudencia`](providers/tjsc_eproc_jurisprudencia/README.md) | implemented | `implementation_ready` | 4 | medio | - | 0 | 7 |
| [`tjse_boletim_jurisprudencia`](providers/tjse_boletim_jurisprudencia/README.md) | implemented | `implementation_ready` | 4 | medio | - | 0 | 4 |
| [`tjse_jurisprudencia`](providers/tjse_jurisprudencia/README.md) | candidate | `research_ready` | - | research | - | 0 | 0 |
| [`tjsp_cjpg`](providers/tjsp_cjpg/README.md) | implemented | `implementation_ready` | 4 | alto | - | 0 | 7 |
| [`tjsp_cjsg`](providers/tjsp_cjsg/README.md) | implemented | `implementation_ready` | 4 | alto | - | 0 | 7 |
| [`tjsp_eproc_jurisprudencia`](providers/tjsp_eproc_jurisprudencia/README.md) | implemented | `implementation_ready` | 4 | medio | - | 0 | 3 |
| [`tjsp_nugepnac`](providers/tjsp_nugepnac/README.md) | implemented | `implementation_ready` | 4 | medio | - | 0 | 5 |
| [`tjto_jurisprudencia`](providers/tjto_jurisprudencia/README.md) | implemented | `implementation_ready` | 4 | medio | - | 0 | 4 |
| [`tnu_eproc_jurisprudencia`](providers/tnu_eproc_jurisprudencia/README.md) | implemented | `implementation_ready` | 5 | baixo | - | 0 | 6 |
| [`tre_sjur_first_degree`](providers/tre_sjur_first_degree/README.md) | implemented | `needs_deepening` | 4 | medio | - | 3 | 1 |
| [`tre_sjur_jurisprudencia`](providers/tre_sjur_jurisprudencia/README.md) | implemented | `needs_deepening` | 4 | medio | data, states, fixtures, mcp, next_steps | 0 | 0 |
| [`tre_sp_temas`](providers/tre_sp_temas/README.md) | implemented | `needs_deepening` | 4 | medio | - | 5 | 2 |
| [`trf2_eproc_jurisprudencia`](providers/trf2_eproc_jurisprudencia/README.md) | implemented | `implementation_ready` | 5 | baixo | - | 0 | 3 |
| [`trf3_jurisprudencia`](providers/trf3_jurisprudencia/README.md) | implemented | `needs_deepening` | 4 | medio | - | 2 | 3 |
| [`trf4_eproc_jurisprudencia`](providers/trf4_eproc_jurisprudencia/README.md) | implemented | `implementation_ready` | 5 | baixo | - | 0 | 7 |
| [`trf5_jurisprudencia`](providers/trf5_jurisprudencia/README.md) | implemented | `implementation_ready` | 4 | medio | - | 0 | 7 |
| [`trf6_eproc_jurisprudencia`](providers/trf6_eproc_jurisprudencia/README.md) | implemented | `implementation_ready` | 5 | baixo | - | 0 | 3 |
| [`trt15_jurisprudencia`](providers/trt15_jurisprudencia/README.md) | implemented | `implementation_ready` | 4 | alto | - | 0 | 6 |
| [`trt2_basis_jurisprudencia`](providers/trt2_basis_jurisprudencia/README.md) | implemented | `needs_deepening` | 4 | medio | contract, data, states, fixtures, mcp, next_steps | 0 | 0 |
| [`trt2_ementario_jurisprudencia`](providers/trt2_ementario_jurisprudencia/README.md) | implemented | `implementation_ready` | 4 | medio | - | 0 | 4 |
| [`trt2_pje_jurisprudencia`](providers/trt2_pje_jurisprudencia/README.md) | candidate | `research_ready` | - | research | - | 4 | 4 |
| [`trt3_ementario_jurisprudencia`](providers/trt3_ementario_jurisprudencia/README.md) | implemented | `needs_deepening` | 4 | medio | identity, contract, data, states, fixtures, mcp, next_steps | 0 | 0 |
| [`trt4_sumulas_jurisprudencia`](providers/trt4_sumulas_jurisprudencia/README.md) | implemented | `needs_deepening` | 4 | medio | identity, contract, data, states, fixtures, mcp, next_steps | 0 | 0 |
| [`trt6_jurisprudencia`](providers/trt6_jurisprudencia/README.md) | implemented | `implementation_ready` | 4 | medio | - | 0 | 3 |
| [`trt8_pje_jurisprudencia`](providers/trt8_pje_jurisprudencia/README.md) | implemented | `implementation_ready` | 4 | medio | - | 0 | 6 |
| [`trt9_nugepnac_jurisprudencia`](providers/trt9_nugepnac_jurisprudencia/README.md) | implemented | `needs_deepening` | 4 | medio | identity, contract, data, states, fixtures, mcp, next_steps | 0 | 0 |
| [`tse_sjur_jurisprudencia`](providers/tse_sjur_jurisprudencia/README.md) | implemented | `implementation_ready` | 5 | médio | - | 0 | 3 |
| [`tst_jurisprudencia`](providers/tst_jurisprudencia/README.md) | implemented | `implementation_ready` | 5 | medio | - | 0 | 3 |

## Gate De Desenvolvimento

Antes de implementar um candidato, o mantenedor deve fechar, no dossie e em fixture, os itens abaixo:

1. rota e metodo reproduzidos com sessao publica limpa;
2. payload, filtros, paginacao, ordenacao e limites confirmados;
3. sucesso, vazio, erro, controle de acesso e timeout classificados;
4. campos canonicos e campos ausentes/variaveis mapeados;
5. fixture pequena, teste offline e teste de contrato;
6. decisao explicita para documento, MCP, rate limit e uso responsavel.

O proximo passo de cada fonte esta no proprio dossie. Para atualizar este relatorio:

```bash
python tools/audit_provider_docs.py --write
```

A especificacao completa esta em [provider-dossier-template.md](provider-dossier-template.md).
