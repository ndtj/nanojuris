# Provider Documentation Audit

Snapshot local: `2026-08-12`. Este relatorio e uma fotografia reproduzivel do estado documental;
nao afirma que uma rota nao observada exista nem que um provider esteja disponivel em qualquer rede.

## Como Ler

- `implemented`: existe no runtime; o nivel e risco vem de `source_contracts`.
- `candidate`: existe pesquisa documental, mas nao existe provider runtime.
- `family`: contrato compartilhado de implementacao, nao uma fonte executavel isolada.
- `needs_deepening`: provider implementado com lacunas documentais ou checklist aberto.
- `research_incomplete`: candidato ainda sem alguma secao obrigatoria.
- `research_ready`: candidato documentado para a proxima fase, ainda sem autorizacao para codigo.

## Resumo

- Dossies auditados: **57** (35 implemented, 21 candidates, 1 family).
- Dossies com secoes estruturais: **45/57**.
- Canonical/legacy em paridade: **57/57**.
- Prontidao: `family_spec`=1, `implementation_ready`=2, `needs_deepening`=33, `research_ready`=21.

A paridade confirma preservacao de informacao durante a migracao. Ela nao substitui a revisao
do contrato: itens `[ ]`, estados `pendente` e rotas apenas observadas continuam sendo bloqueios reais.

A evidencia live mais recente esta em [live-validation-2026-08-11.md](live-validation-2026-08-11.md).
A evidencia historica das 28 fontes candidatas esta em [candidate-live-validation-2026-08-11.md](candidate-live-validation-2026-08-11.md).

## Matriz Por Provider

| Provider | Ciclo | Prontidao | Nivel | Risco | Secoes faltantes | Pendencias | Fixtures referenciadas |
| --- | --- | --- | ---: | --- | --- | ---: | ---: |
| [`bnp_pangea`](docs/providers/bnp_pangea/README.md) | implemented | `needs_deepening` | 4 | medio | data, next_steps | 0 | 0 |
| [`cjf_jurisprudencia`](docs/providers/cjf_jurisprudencia/README.md) | implemented | `needs_deepening` | 4 | medio | next_steps | 6 | 0 |
| [`cnj_jurisprudencia`](docs/providers/cnj_jurisprudencia/README.md) | candidate | `research_ready` | - | research | - | 6 | 0 |
| [`comunica_pje`](docs/providers/comunica_pje/README.md) | implemented | `needs_deepening` | 3 | medio | - | 8 | 0 |
| [`eproc_jurisprudencia_federal`](docs/providers/eproc_jurisprudencia_federal/README.md) | family | `family_spec` | - | research | - | 1 | 3 |
| [`falcao_jt`](docs/providers/falcao_jt/README.md) | candidate | `research_ready` | - | research | - | 0 | 0 |
| [`justica_eleitoral_sjur`](docs/providers/justica_eleitoral_sjur/README.md) | candidate | `research_ready` | - | research | - | 5 | 0 |
| [`stf_informativo`](docs/providers/stf_informativo/README.md) | implemented | `needs_deepening` | 5 | baixo | - | 3 | 0 |
| [`stf_juris`](docs/providers/stf_juris/README.md) | implemented | `needs_deepening` | 3 | alto | data | 3 | 1 |
| [`stj_dados_abertos_jurisprudencia`](docs/providers/stj_dados_abertos_jurisprudencia/README.md) | candidate | `research_ready` | - | research | - | 8 | 0 |
| [`stj_informativo`](docs/providers/stj_informativo/README.md) | implemented | `needs_deepening` | 4 | medio | - | 3 | 1 |
| [`stj_scon`](docs/providers/stj_scon/README.md) | implemented | `needs_deepening` | 3 | alto | data | 1 | 4 |
| [`stm_jurisprudencia`](docs/providers/stm_jurisprudencia/README.md) | implemented | `needs_deepening` | 4 | medio | mcp, next_steps | 3 | 0 |
| [`tce_sp_jurisprudencia`](docs/providers/tce_sp_jurisprudencia/README.md) | implemented | `needs_deepening` | 4 | alto | - | 7 | 0 |
| [`tcu_jurisprudencia`](docs/providers/tcu_jurisprudencia/README.md) | implemented | `needs_deepening` | 4 | medio | next_steps | 4 | 0 |
| [`tjac_cjsg`](docs/providers/tjac_cjsg/README.md) | implemented | `needs_deepening` | 4 | alto | - | 4 | 0 |
| [`tjac_esaj_cpopg`](docs/providers/tjac_esaj_cpopg/README.md) | implemented | `needs_deepening` | 4 | medio | - | 7 | 0 |
| [`tjal_cjsg`](docs/providers/tjal_cjsg/README.md) | implemented | `needs_deepening` | 4 | alto | - | 8 | 0 |
| [`tjam_cjsg`](docs/providers/tjam_cjsg/README.md) | implemented | `needs_deepening` | 4 | alto | - | 8 | 0 |
| [`tjap_tucujuris`](docs/providers/tjap_tucujuris/README.md) | candidate | `research_ready` | - | research | - | 0 | 0 |
| [`tjba_graphql`](docs/providers/tjba_graphql/README.md) | candidate | `research_ready` | - | research | - | 0 | 0 |
| [`tjce_cjsg`](docs/providers/tjce_cjsg/README.md) | candidate | `research_ready` | - | research | - | 7 | 0 |
| [`tjce_informativos`](docs/providers/tjce_informativos/README.md) | candidate | `research_ready` | - | research | - | 5 | 0 |
| [`tjce_sjuris`](docs/providers/tjce_sjuris/README.md) | candidate | `research_ready` | - | research | - | 0 | 0 |
| [`tjdf_juris`](docs/providers/tjdf_juris/README.md) | implemented | `needs_deepening` | 5 | baixo | data | 0 | 0 |
| [`tjes_jurisprudencia`](docs/providers/tjes_jurisprudencia/README.md) | candidate | `research_ready` | - | research | - | 0 | 0 |
| [`tjgo_projudi_jurisprudencia`](docs/providers/tjgo_projudi_jurisprudencia/README.md) | implemented | `needs_deepening` | 4 | alto | - | 3 | 2 |
| [`tjma_jurisconsult`](docs/providers/tjma_jurisconsult/README.md) | candidate | `research_ready` | - | research | - | 4 | 0 |
| [`tjmg_jurisprudencia`](docs/providers/tjmg_jurisprudencia/README.md) | candidate | `research_ready` | - | research | - | 0 | 0 |
| [`tjms_cjsg`](docs/providers/tjms_cjsg/README.md) | implemented | `needs_deepening` | 4 | alto | - | 8 | 0 |
| [`tjmt_jurisprudencia_api`](docs/providers/tjmt_jurisprudencia_api/README.md) | candidate | `research_ready` | - | research | - | 9 | 0 |
| [`tjpa_jurisprudencia_bff`](docs/providers/tjpa_jurisprudencia_bff/README.md) | implemented | `needs_deepening` | 4 | medio | - | 14 | 0 |
| [`tjpb_pje_jurisprudencia`](docs/providers/tjpb_pje_jurisprudencia/README.md) | implemented | `needs_deepening` | 4 | medio | - | 6 | 0 |
| [`tjpe_jurisprudencia`](docs/providers/tjpe_jurisprudencia/README.md) | candidate | `research_ready` | - | research | - | 0 | 0 |
| [`tjpi_juspi`](docs/providers/tjpi_juspi/README.md) | implemented | `needs_deepening` | 4 | medio | - | 4 | 3 |
| [`tjpr_jurisprudencia`](docs/providers/tjpr_jurisprudencia/README.md) | implemented | `implementation_ready` | 4 | medio | - | 0 | 1 |
| [`tjrj_eproc_jurisprudencia`](docs/providers/tjrj_eproc_jurisprudencia/README.md) | implemented | `needs_deepening` | 4 | medio | - | 6 | 0 |
| [`tjrn_jurisprudencia`](docs/providers/tjrn_jurisprudencia/README.md) | candidate | `research_ready` | - | research | - | 0 | 0 |
| [`tjro_liame`](docs/providers/tjro_liame/README.md) | candidate | `research_ready` | - | research | - | 0 | 0 |
| [`tjrr_juris`](docs/providers/tjrr_juris/README.md) | candidate | `research_ready` | - | research | - | 8 | 0 |
| [`tjrs_solr`](docs/providers/tjrs_solr/README.md) | implemented | `needs_deepening` | 4 | medio | identity, mcp, next_steps | 0 | 0 |
| [`tjsc_eproc_jurisprudencia`](docs/providers/tjsc_eproc_jurisprudencia/README.md) | implemented | `implementation_ready` | 4 | medio | - | 0 | 0 |
| [`tjse_jurisprudencia`](docs/providers/tjse_jurisprudencia/README.md) | candidate | `research_ready` | - | research | - | 0 | 0 |
| [`tjsp_cjsg`](docs/providers/tjsp_cjsg/README.md) | implemented | `needs_deepening` | 3 | alto | data | 2 | 0 |
| [`tjsp_eproc_jurisprudencia`](docs/providers/tjsp_eproc_jurisprudencia/README.md) | implemented | `needs_deepening` | 4 | medio | - | 9 | 0 |
| [`tjsp_esaj_cpopg`](docs/providers/tjsp_esaj_cpopg/README.md) | implemented | `needs_deepening` | 4 | alto | - | 8 | 0 |
| [`tjsp_nugepnac`](docs/providers/tjsp_nugepnac/README.md) | implemented | `needs_deepening` | 4 | medio | - | 8 | 0 |
| [`tjto_jurisprudencia`](docs/providers/tjto_jurisprudencia/README.md) | candidate | `research_ready` | - | research | - | 0 | 0 |
| [`tnu_eproc_jurisprudencia`](docs/providers/tnu_eproc_jurisprudencia/README.md) | implemented | `needs_deepening` | 5 | baixo | - | 1 | 3 |
| [`tre_sp_temas`](docs/providers/tre_sp_temas/README.md) | implemented | `needs_deepening` | 4 | medio | - | 7 | 0 |
| [`trf2_eproc_jurisprudencia`](docs/providers/trf2_eproc_jurisprudencia/README.md) | implemented | `needs_deepening` | 5 | baixo | - | 1 | 3 |
| [`trf3_jurisprudencia`](docs/providers/trf3_jurisprudencia/README.md) | candidate | `research_ready` | - | research | - | 7 | 0 |
| [`trf4_eproc_jurisprudencia`](docs/providers/trf4_eproc_jurisprudencia/README.md) | implemented | `needs_deepening` | 5 | baixo | data, mcp, next_steps | 6 | 0 |
| [`trf5_jurisprudencia`](docs/providers/trf5_jurisprudencia/README.md) | implemented | `needs_deepening` | 4 | medio | next_steps | 5 | 0 |
| [`trf6_eproc_jurisprudencia`](docs/providers/trf6_eproc_jurisprudencia/README.md) | implemented | `needs_deepening` | 5 | baixo | - | 1 | 3 |
| [`trt2_pje_jurisprudencia`](docs/providers/trt2_pje_jurisprudencia/README.md) | candidate | `research_ready` | - | research | - | 4 | 0 |
| [`tst_jurisprudencia`](docs/providers/tst_jurisprudencia/README.md) | implemented | `needs_deepening` | 5 | medio | mcp, next_steps | 1 | 0 |

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
