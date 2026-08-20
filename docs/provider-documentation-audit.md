# Provider Documentation Audit

Snapshot local: `2026-08-15`. Este relatorio e uma fotografia reproduzivel do estado documental;
nao afirma que uma rota nao observada exista nem que um provider esteja disponivel em qualquer rede.

## Como Ler

- `implemented`: existe no runtime; o nivel e risco vem de `source_contracts`.
- `candidate`: existe pesquisa documental, mas nao existe provider runtime.
- `family`: contrato compartilhado de implementacao, nao uma fonte executavel isolada.
- `needs_deepening`: provider implementado com lacunas documentais ou checklist aberto.
- `research_incomplete`: candidato ainda sem alguma secao obrigatoria.
- `research_ready`: candidato documentado para a proxima fase, ainda sem autorizacao para codigo.

## Resumo

- Dossies auditados: **55** (45 implemented, 9 candidates, 1 family).
- Dossies com secoes estruturais: **53/55**.
- Canonical/legacy em paridade: **55/55**.
- Prontidao: `family_spec`=1, `implementation_ready`=10, `needs_deepening`=35, `research_ready`=9.

A paridade confirma preservacao de informacao durante a migracao. Ela nao substitui a revisao
do contrato: itens `[ ]`, estados `pendente` e rotas apenas observadas continuam sendo bloqueios reais.

A evidencia live mais recente esta em [live-validation-latest.md](live-validation-latest.md).
A evidencia historica das 28 fontes candidatas esta em [candidate-live-validation-2026-08-11.md](candidate-live-validation-2026-08-11.md).

## Matriz Por Provider

| Provider | Ciclo | Prontidao | Nivel | Risco | Secoes faltantes | Pendencias | Fixtures referenciadas |
| --- | --- | --- | ---: | --- | --- | ---: | ---: |
| [`bnp_pangea`](providers/bnp_pangea/README.md) | implemented | `needs_deepening` | 4 | medio | data, next_steps | 0 | 0 |
| [`cjf_jurisprudencia`](providers/cjf_jurisprudencia/README.md) | implemented | `needs_deepening` | 4 | medio | - | 2 | 7 |
| [`cnj_jurisprudencia`](providers/cnj_jurisprudencia/README.md) | implemented | `needs_deepening` | 4 | medio | - | 6 | 1 |
| [`eproc_jurisprudencia_federal`](providers/eproc_jurisprudencia_federal/README.md) | family | `family_spec` | - | research | - | 1 | 3 |
| [`falcao_jt`](providers/falcao_jt/README.md) | candidate | `research_ready` | - | research | - | 0 | 0 |
| [`justica_eleitoral_sjur`](providers/justica_eleitoral_sjur/README.md) | implemented | `needs_deepening` | 4 | medio | - | 4 | 4 |
| [`stf_informativo`](providers/stf_informativo/README.md) | implemented | `needs_deepening` | 5 | baixo | - | 3 | 3 |
| [`stf_juris`](providers/stf_juris/README.md) | implemented | `needs_deepening` | 4 | alto | - | 3 | 6 |
| [`stj_dados_abertos_jurisprudencia`](providers/stj_dados_abertos_jurisprudencia/README.md) | implemented | `needs_deepening` | 4 | medio | - | 1 | 0 |
| [`stj_informativo`](providers/stj_informativo/README.md) | implemented | `needs_deepening` | 5 | medio | - | 3 | 4 |
| [`stj_scon`](providers/stj_scon/README.md) | implemented | `needs_deepening` | 4 | alto | - | 1 | 7 |
| [`stm_jurisprudencia`](providers/stm_jurisprudencia/README.md) | implemented | `needs_deepening` | 4 | medio | next_steps | 3 | 3 |
| [`tce_sp_jurisprudencia`](providers/tce_sp_jurisprudencia/README.md) | implemented | `needs_deepening` | 4 | alto | - | 7 | 3 |
| [`tcu_jurisprudencia`](providers/tcu_jurisprudencia/README.md) | implemented | `needs_deepening` | 4 | medio | - | 4 | 7 |
| [`tjac_cjsg`](providers/tjac_cjsg/README.md) | implemented | `needs_deepening` | 4 | alto | - | 4 | 3 |
| [`tjal_cjsg`](providers/tjal_cjsg/README.md) | implemented | `needs_deepening` | 4 | alto | - | 8 | 3 |
| [`tjam_cjsg`](providers/tjam_cjsg/README.md) | implemented | `needs_deepening` | 4 | alto | - | 8 | 3 |
| [`tjap_tucujuris`](providers/tjap_tucujuris/README.md) | candidate | `research_ready` | - | research | - | 0 | 0 |
| [`tjba_graphql`](providers/tjba_graphql/README.md) | implemented | `needs_deepening` | 5 | medio | - | 1 | 3 |
| [`tjce_cjsg`](providers/tjce_cjsg/README.md) | implemented | `needs_deepening` | 4 | alto | - | 7 | 0 |
| [`tjce_informativos`](providers/tjce_informativos/README.md) | implemented | `needs_deepening` | 4 | medio | - | 5 | 1 |
| [`tjce_sjuris`](providers/tjce_sjuris/README.md) | implemented | `implementation_ready` | 4 | medio | - | 0 | 1 |
| [`tjdf_juris`](providers/tjdf_juris/README.md) | implemented | `implementation_ready` | 5 | baixo | - | 0 | 3 |
| [`tjes_jurisprudencia`](providers/tjes_jurisprudencia/README.md) | candidate | `research_ready` | - | research | - | 0 | 0 |
| [`tjgo_projudi_jurisprudencia`](providers/tjgo_projudi_jurisprudencia/README.md) | implemented | `needs_deepening` | 4 | alto | - | 3 | 5 |
| [`tjma_jurisconsult`](providers/tjma_jurisconsult/README.md) | implemented | `implementation_ready` | 4 | alto | - | 0 | 1 |
| [`tjmg_jurisprudencia`](providers/tjmg_jurisprudencia/README.md) | candidate | `research_ready` | - | research | - | 0 | 0 |
| [`tjms_cjsg`](providers/tjms_cjsg/README.md) | implemented | `needs_deepening` | 4 | alto | - | 8 | 3 |
| [`tjmt_jurisprudencia_api`](providers/tjmt_jurisprudencia_api/README.md) | implemented | `implementation_ready` | 4 | medio | - | 0 | 1 |
| [`tjpa_jurisprudencia_bff`](providers/tjpa_jurisprudencia_bff/README.md) | implemented | `needs_deepening` | 5 | medio | - | 14 | 3 |
| [`tjpb_pje_jurisprudencia`](providers/tjpb_pje_jurisprudencia/README.md) | implemented | `needs_deepening` | 5 | medio | - | 6 | 3 |
| [`tjpe_jurisprudencia`](providers/tjpe_jurisprudencia/README.md) | implemented | `implementation_ready` | 4 | medio | - | 0 | 1 |
| [`tjpi_juspi`](providers/tjpi_juspi/README.md) | implemented | `needs_deepening` | 5 | medio | - | 4 | 6 |
| [`tjpr_jurisprudencia`](providers/tjpr_jurisprudencia/README.md) | implemented | `implementation_ready` | 5 | medio | - | 0 | 4 |
| [`tjrj_ejuris`](providers/tjrj_ejuris/README.md) | candidate | `research_ready` | - | research | - | 4 | 0 |
| [`tjrj_eproc_jurisprudencia`](providers/tjrj_eproc_jurisprudencia/README.md) | implemented | `needs_deepening` | 4 | medio | - | 6 | 3 |
| [`tjrn_jurisprudencia`](providers/tjrn_jurisprudencia/README.md) | candidate | `research_ready` | - | research | - | 0 | 0 |
| [`tjro_liame`](providers/tjro_liame/README.md) | implemented | `implementation_ready` | 4 | medio | - | 0 | 1 |
| [`tjrr_juris`](providers/tjrr_juris/README.md) | implemented | `needs_deepening` | 5 | medio | - | 2 | 3 |
| [`tjrs_solr`](providers/tjrs_solr/README.md) | implemented | `implementation_ready` | 5 | medio | - | 0 | 5 |
| [`tjsc_eproc_jurisprudencia`](providers/tjsc_eproc_jurisprudencia/README.md) | implemented | `implementation_ready` | 4 | medio | - | 0 | 3 |
| [`tjse_jurisprudencia`](providers/tjse_jurisprudencia/README.md) | candidate | `research_ready` | - | research | - | 0 | 0 |
| [`tjsp_cjsg`](providers/tjsp_cjsg/README.md) | implemented | `needs_deepening` | 4 | alto | - | 2 | 7 |
| [`tjsp_eproc_jurisprudencia`](providers/tjsp_eproc_jurisprudencia/README.md) | implemented | `needs_deepening` | 4 | medio | - | 6 | 3 |
| [`tjsp_nugepnac`](providers/tjsp_nugepnac/README.md) | implemented | `needs_deepening` | 4 | medio | - | 8 | 0 |
| [`tjto_jurisprudencia`](providers/tjto_jurisprudencia/README.md) | implemented | `implementation_ready` | 4 | medio | - | 0 | 1 |
| [`tnu_eproc_jurisprudencia`](providers/tnu_eproc_jurisprudencia/README.md) | implemented | `needs_deepening` | 5 | baixo | - | 1 | 6 |
| [`tre_sp_temas`](providers/tre_sp_temas/README.md) | implemented | `needs_deepening` | 4 | medio | - | 7 | 0 |
| [`trf2_eproc_jurisprudencia`](providers/trf2_eproc_jurisprudencia/README.md) | implemented | `needs_deepening` | 5 | baixo | - | 1 | 3 |
| [`trf3_jurisprudencia`](providers/trf3_jurisprudencia/README.md) | candidate | `research_ready` | - | research | - | 7 | 0 |
| [`trf4_eproc_jurisprudencia`](providers/trf4_eproc_jurisprudencia/README.md) | implemented | `needs_deepening` | 5 | baixo | - | 6 | 3 |
| [`trf5_jurisprudencia`](providers/trf5_jurisprudencia/README.md) | implemented | `needs_deepening` | 4 | medio | - | 2 | 7 |
| [`trf6_eproc_jurisprudencia`](providers/trf6_eproc_jurisprudencia/README.md) | implemented | `needs_deepening` | 5 | baixo | - | 1 | 3 |
| [`trt2_pje_jurisprudencia`](providers/trt2_pje_jurisprudencia/README.md) | candidate | `research_ready` | - | research | - | 4 | 0 |
| [`tst_jurisprudencia`](providers/tst_jurisprudencia/README.md) | implemented | `needs_deepening` | 5 | medio | - | 1 | 3 |

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
