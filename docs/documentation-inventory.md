# Inventario Documental

Gerado por `python tools/audit_documentation_inventory.py --write`. Este inventario orienta consolidacoes sem apagar contratos, evidencias ou caminhos de compatibilidade sem uma migracao explicita.

Documentos inventariados: **217** (`active_guide`=39, `canonical`=74, `compatibility_copy`=54, `generated`=10, `historical_evidence`=40).

## Regra De Limpeza

Um item somente pode ser removido quando nao tiver referencias, conteudo unico, funcao canonica, funcao de compatibilidade ou valor de evidencia. Nesta rodada, nenhuma exclusao automatica e recomendada.

| Arquivo | Papel | Referencias | Conteudo/justificativa | Acao |
| --- | --- | ---: | --- | --- |
| `AGENTS.md` | `canonical` | 0 | Entrada normativa, de produto ou de governanca. | `manter` |
| `CHANGELOG.md` | `canonical` | 0 | Entrada normativa, de produto ou de governanca. | `manter` |
| `CODE_OF_CONDUCT.md` | `canonical` | 1 | Entrada normativa, de produto ou de governanca. | `manter` |
| `CONTRIBUTING.md` | `canonical` | 3 | Entrada normativa, de produto ou de governanca. | `manter` |
| `GOVERNANCE.md` | `canonical` | 4 | Entrada normativa, de produto ou de governanca. | `manter` |
| `MAINTAINERS.md` | `canonical` | 4 | Entrada normativa, de produto ou de governanca. | `manter` |
| `README.md` | `canonical` | 27 | Entrada normativa, de produto ou de governanca. | `manter` |
| `SECURITY.md` | `canonical` | 3 | Entrada normativa, de produto ou de governanca. | `manter` |
| `SPECS.md` | `canonical` | 0 | Entrada normativa, de produto ou de governanca. | `manter` |
| `docs/README.md` | `canonical` | 1 | Entrada normativa, de produto ou de governanca. | `manter` |
| `docs/ai-agent-usage.md` | `active_guide` | 2 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/architecture.md` | `canonical` | 4 | Entrada normativa, de produto ou de governanca. | `manter` |
| `docs/audience-ux.md` | `active_guide` | 2 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/candidate-live-validation-2026-08-11.md` | `historical_evidence` | 56 | Registro de pesquisa, QA ou validacao. | `manter` |
| `docs/case-studies.md` | `active_guide` | 2 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/courtsbr-provider-analysis.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/coverage/README.md` | `generated` | 2 | Gerado por build_provider_coverage.py. | `manter` |
| `docs/coverage/field-coverage.md` | `generated` | 1 | Gerado por build_provider_coverage.py. | `manter` |
| `docs/coverage/improvement-queue.md` | `generated` | 2 | Gerado por build_provider_coverage.py. | `manter` |
| `docs/coverage/inputs.md` | `generated` | 1 | Gerado por build_provider_coverage.py. | `manter` |
| `docs/coverage/live-status.md` | `generated` | 1 | Gerado por build_provider_coverage.py. | `manter` |
| `docs/coverage/matrix.md` | `generated` | 8 | Gerado por build_provider_coverage.py. | `manter` |
| `docs/coverage/maturity-score.md` | `generated` | 2 | Gerado por build_provider_coverage.py. | `manter` |
| `docs/coverage/maturity-waves.md` | `active_guide` | 3 | Plano mantido manualmente; os indicadores de cobertura sao gerados separadamente. | `revisar_periodicamente` |
| `docs/coverage/maturity.md` | `generated` | 3 | Gerado por build_provider_coverage.py. | `manter` |
| `docs/coverage/outputs.md` | `generated` | 1 | Gerado por build_provider_coverage.py. | `manter` |
| `docs/coverage/source-of-truth.md` | `generated` | 1 | Gerado por build_provider_coverage.py. | `manter` |
| `docs/demo-studio-mcp.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/documents.md` | `active_guide` | 1 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/elite-extraction-blueprint.md` | `active_guide` | 1 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/external-court-scraper-survey-2026-08-02.md` | `historical_evidence` | 1 | Registro de pesquisa, QA ou validacao. | `manter` |
| `docs/extraction-pipeline.md` | `active_guide` | 4 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/github-scraper-research.md` | `active_guide` | 1 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/github-transfer-checklist.md` | `active_guide` | 1 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/gold-maturity.md` | `active_guide` | 2 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/implementation-live-validation-2026-08-11.md` | `historical_evidence` | 1 | Registro de pesquisa, QA ou validacao. | `manter` |
| `docs/jurimetry-idpj-demo.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/live-provider-validation.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/live-validation-2026-08-11.md` | `historical_evidence` | 66 | Registro de pesquisa, QA ou validacao. | `manter` |
| `docs/live-validation-2026-08-15.md` | `historical_evidence` | 1 | Registro de pesquisa, QA ou validacao. | `manter` |
| `docs/live-validation-latest.md` | `active_guide` | 2 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/mcp.md` | `canonical` | 4 | Entrada normativa, de produto ou de governanca. | `manter` |
| `docs/migration-to-nanojud.md` | `active_guide` | 3 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/national-coverage-matrix.md` | `active_guide` | 1 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-contract-validation-2026-08-12.md` | `historical_evidence` | 0 | Registro de pesquisa, QA ou validacao. | `manter` |
| `docs/provider-coverage-map.md` | `active_guide` | 5 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-development-queue.md` | `active_guide` | 4 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-development.md` | `canonical` | 8 | Entrada normativa, de produto ou de governanca. | `manter` |
| `docs/provider-discovery-2026-08-12.md` | `active_guide` | 1 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-documentation-audit.md` | `active_guide` | 4 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-dossier-template.md` | `canonical` | 7 | Entrada normativa, de produto ou de governanca. | `manter` |
| `docs/provider-expansion-analysis-2026-08-02.md` | `active_guide` | 1 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-status.md` | `active_guide` | 2 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/providers.md` | `active_guide` | 3 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/providers/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/bnp_pangea/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/cjf_jurisprudencia/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/cnj_jurisprudencia/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/eproc_jurisprudencia_federal/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/falcao_jt/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/justica_eleitoral_sjur/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/stf_informativo/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/stf_juris/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/stj_dados_abertos_jurisprudencia/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/stj_informativo/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/stj_scon/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/stm_jurisprudencia/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/tce_sp_jurisprudencia/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/tcu_jurisprudencia/README.md` | `canonical` | 2 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/tjac_cjsg/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/tjal_cjsg/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/tjam_cjsg/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/tjap_tucujuris/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/tjba_graphql/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/tjce_cjsg/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/tjce_informativos/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/tjce_sjuris/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/tjdf_juris/README.md` | `canonical` | 2 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/tjdf_juris/api-v1.md` | `active_guide` | 2 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/providers/tjes_jurisprudencia/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/tjgo_projudi_jurisprudencia/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/tjma_jurisconsult/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/tjmg_jurisprudencia/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/tjms_cjsg/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/tjmt_jurisprudencia_api/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/tjpa_jurisprudencia_bff/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/tjpb_pje_jurisprudencia/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/tjpe_jurisprudencia/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/tjpi_juspi/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/tjpr_jurisprudencia/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/tjrj_eproc_jurisprudencia/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/tjrn_jurisprudencia/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/tjro_liame/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/tjrr_juris/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/tjrs_solr/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/tjsc_eproc_jurisprudencia/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/tjse_jurisprudencia/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/tjsp_cjsg/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/tjsp_eproc_jurisprudencia/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/tjsp_nugepnac/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/tjto_jurisprudencia/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/tnu_eproc_jurisprudencia/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/tre_sp_temas/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/trf2_eproc_jurisprudencia/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/trf3_jurisprudencia/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/trf4_eproc_jurisprudencia/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/trf5_jurisprudencia/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/trf6_eproc_jurisprudencia/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/trt2_pje_jurisprudencia/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/tst_jurisprudencia/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/public-provider-discovery-2026-08-10.md` | `active_guide` | 1 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/qa/professional-usage-audit-2026-08-16.md` | `historical_evidence` | 0 | Registro de pesquisa, QA ou validacao. | `manter` |
| `docs/qa/studio-live-journey-2026-08-16.md` | `historical_evidence` | 0 | Registro de pesquisa, QA ou validacao. | `manter` |
| `docs/qa/studio-playwright.md` | `historical_evidence` | 0 | Registro de pesquisa, QA ou validacao. | `manter` |
| `docs/qa/studio-provider-audit-2026-08-15.md` | `historical_evidence` | 2 | Registro de pesquisa, QA ou validacao. | `manter` |
| `docs/quickstart.md` | `canonical` | 3 | Entrada normativa, de produto ou de governanca. | `manter` |
| `docs/registry/README.md` | `canonical` | 0 | Catalogo, schema ou indice de integracao. | `manter` |
| `docs/release-checklist.md` | `active_guide` | 3 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/research/idpj-pilot-2026-08-16.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/responsible-use.md` | `canonical` | 3 | Entrada normativa, de produto ou de governanca. | `manter` |
| `docs/roadmap.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/route-mapping-playbook.md` | `canonical` | 6 | Entrada normativa, de produto ou de governanca. | `manter` |
| `docs/route-mapping-results-2026-08-07.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/source-capabilities.md` | `active_guide` | 5 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/source-contracts.md` | `active_guide` | 2 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/source-contracts/README.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/source-contracts/bnp_pangea.md` | `compatibility_copy` | 1 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/cjf_jurisprudencia.md` | `compatibility_copy` | 3 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/cnj_jurisprudencia.md` | `compatibility_copy` | 2 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/eproc_jurisprudencia_federal.md` | `compatibility_copy` | 1 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/falcao_jt.md` | `compatibility_copy` | 2 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/justica_eleitoral_sjur.md` | `compatibility_copy` | 2 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/stf_informativo.md` | `compatibility_copy` | 1 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/stf_juris.md` | `compatibility_copy` | 1 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/stj_dados_abertos_jurisprudencia.md` | `compatibility_copy` | 2 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/stj_informativo.md` | `compatibility_copy` | 1 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/stj_scon.md` | `compatibility_copy` | 1 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/stm_jurisprudencia.md` | `compatibility_copy` | 1 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tce_sp_jurisprudencia.md` | `compatibility_copy` | 1 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tcu_jurisprudencia.md` | `compatibility_copy` | 4 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjac_cjsg.md` | `compatibility_copy` | 1 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjal_cjsg.md` | `compatibility_copy` | 1 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjam_cjsg.md` | `compatibility_copy` | 1 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjap_tucujuris.md` | `compatibility_copy` | 2 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjba_graphql.md` | `compatibility_copy` | 2 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjce_cjsg.md` | `compatibility_copy` | 2 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjce_informativos.md` | `compatibility_copy` | 1 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjce_sjuris.md` | `compatibility_copy` | 2 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjdf_juris.md` | `compatibility_copy` | 1 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjes_jurisprudencia.md` | `compatibility_copy` | 2 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjgo_projudi_jurisprudencia.md` | `compatibility_copy` | 2 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjma_jurisconsult.md` | `compatibility_copy` | 1 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjmg_jurisprudencia.md` | `compatibility_copy` | 2 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjms_cjsg.md` | `compatibility_copy` | 1 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjmt_jurisprudencia_api.md` | `compatibility_copy` | 2 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjpa_jurisprudencia_bff.md` | `compatibility_copy` | 2 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjpb_pje_jurisprudencia.md` | `compatibility_copy` | 2 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjpe_jurisprudencia.md` | `compatibility_copy` | 2 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjpi_juspi.md` | `compatibility_copy` | 2 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjpr_jurisprudencia.md` | `compatibility_copy` | 2 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjrj_eproc_jurisprudencia.md` | `compatibility_copy` | 2 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjrn_jurisprudencia.md` | `compatibility_copy` | 2 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjro_liame.md` | `compatibility_copy` | 2 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjrr_juris.md` | `compatibility_copy` | 2 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjrs_solr.md` | `compatibility_copy` | 2 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjsc_eproc_jurisprudencia.md` | `compatibility_copy` | 3 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjse_jurisprudencia.md` | `compatibility_copy` | 2 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjsp_cjsg.md` | `compatibility_copy` | 1 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjsp_eproc_jurisprudencia.md` | `compatibility_copy` | 1 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjsp_nugepnac.md` | `compatibility_copy` | 1 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjto_jurisprudencia.md` | `compatibility_copy` | 2 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tnu_eproc_jurisprudencia.md` | `compatibility_copy` | 1 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tre_sp_temas.md` | `compatibility_copy` | 1 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/trf2_eproc_jurisprudencia.md` | `compatibility_copy` | 1 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/trf3_jurisprudencia.md` | `compatibility_copy` | 3 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/trf4_eproc_jurisprudencia.md` | `compatibility_copy` | 1 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/trf5_jurisprudencia.md` | `compatibility_copy` | 3 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/trf6_eproc_jurisprudencia.md` | `compatibility_copy` | 1 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/trt2_pje_jurisprudencia.md` | `compatibility_copy` | 1 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tst_jurisprudencia.md` | `compatibility_copy` | 2 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-discovery.md` | `active_guide` | 3 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/state-court-route-mapping-2026-08-07.md` | `historical_evidence` | 4 | Registro de pesquisa, QA ou validacao. | `manter` |
| `docs/stf-stj-provider-research-2026-08-03.md` | `historical_evidence` | 0 | Registro de pesquisa, QA ou validacao. | `manter` |
| `docs/stj-provider-research.md` | `active_guide` | 1 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/stj-source-profile.md` | `active_guide` | 2 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/storage.md` | `canonical` | 3 | Entrada normativa, de produto ou de governanca. | `manter` |
| `docs/studio-har-audit-2026-08-07.md` | `historical_evidence` | 0 | Registro de pesquisa, QA ou validacao. | `manter` |
| `docs/unified-search-live-validation-2026-08-11.md` | `historical_evidence` | 2 | Registro de pesquisa, QA ou validacao. | `manter` |
| `docs/unified-search-live-validation-2026-08-12.md` | `historical_evidence` | 0 | Registro de pesquisa, QA ou validacao. | `manter` |
| `docs/use-case-simulation-2026-08-02.md` | `active_guide` | 1 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/use-case-validation-matrix.md` | `active_guide` | 5 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/validation-report-2026-08-02.md` | `active_guide` | 2 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/validation/runs/20260816T020958Z-unified-reference-no-env-proxy.md` | `historical_evidence` | 1 | Evidencia live estruturada e auditavel. | `manter` |
| `docs/validation/runs/20260816T023226Z-tcu-open-data-contract.md` | `historical_evidence` | 0 | Evidencia live estruturada e auditavel. | `manter` |
| `docs/validation/runs/20260816T033359Z-qa-20260816-studio-federated.md` | `historical_evidence` | 0 | Evidencia live estruturada e auditavel. | `manter` |
| `docs/validation/runs/20260816T033500Z-qa-20260816-studio-federated-final.md` | `historical_evidence` | 0 | Evidencia live estruturada e auditavel. | `manter` |
| `docs/validation/runs/20260816T061604Z-tjsp-eproc-document-contract-20260816.md` | `historical_evidence` | 0 | Evidencia live estruturada e auditavel. | `manter` |
| `docs/validation/runs/20260816T061824Z-cjsg-family-baseline-20260816.md` | `historical_evidence` | 0 | Evidencia live estruturada e auditavel. | `manter` |
| `docs/validation/runs/20260816T062254Z-cjsg-family-trace-20260816.md` | `historical_evidence` | 0 | Evidencia live estruturada e auditavel. | `manter` |
| `docs/validation/runs/20260816T063212Z-stf-trace-20260816.md` | `historical_evidence` | 0 | Evidencia live estruturada e auditavel. | `manter` |
| `docs/validation/runs/20260816T063409Z-stj-cjf-trace-20260816.md` | `historical_evidence` | 0 | Evidencia live estruturada e auditavel. | `manter` |
| `docs/validation/runs/20260816T063634Z-eproc-family-trace-20260816.md` | `historical_evidence` | 0 | Evidencia live estruturada e auditavel. | `manter` |
| `docs/validation/runs/20260816T070048Z-gold-wave-1-20260816.md` | `historical_evidence` | 0 | Evidencia live estruturada e auditavel. | `manter` |
| `docs/validation/runs/20260816T071033Z-gold-wave-1-final-20260816.md` | `historical_evidence` | 0 | Evidencia live estruturada e auditavel. | `manter` |
| `docs/validation/runs/20260816T071045Z-gold-wave-1-empty-20260816.md` | `historical_evidence` | 0 | Evidencia live estruturada e auditavel. | `manter` |
| `docs/validation/runs/20260816T071104Z-gold-wave-2-20260816.md` | `historical_evidence` | 0 | Evidencia live estruturada e auditavel. | `manter` |
| `docs/validation/runs/20260816T071450Z-gold-wave-2-final-20260816.md` | `historical_evidence` | 0 | Evidencia live estruturada e auditavel. | `manter` |
| `docs/validation/runs/20260816T071721Z-gold-wave-3-20260816.md` | `historical_evidence` | 0 | Evidencia live estruturada e auditavel. | `manter` |
| `docs/validation/runs/20260816T072134Z-gold-wave-3-final-20260816.md` | `historical_evidence` | 0 | Evidencia live estruturada e auditavel. | `manter` |
| `docs/validation/runs/20260816T072220Z-gold-wave-3-tjsp-trace-20260816.md` | `historical_evidence` | 0 | Evidencia live estruturada e auditavel. | `manter` |
| `docs/validation/runs/20260816T072343Z-gold-wave-1-verified-20260816.md` | `historical_evidence` | 0 | Evidencia live estruturada e auditavel. | `manter` |
| `docs/validation/runs/20260816T082132Z-tjsp-eproc-capacity-20260816.md` | `historical_evidence` | 0 | Evidencia live estruturada e auditavel. | `manter` |
| `docs/validation/runs/20260816T082800Z-cjsg-capacity-20260816.md` | `historical_evidence` | 0 | Evidencia live estruturada e auditavel. | `manter` |
| `docs/validation/runs/20260816T084500Z-tjpr-tjrr-capacity-20260816.md` | `historical_evidence` | 0 | Evidencia live estruturada e auditavel. | `manter` |
| `docs/validation/runs/20260816T090523Z-eproc-capacity-recheck-20260816.md` | `historical_evidence` | 0 | Evidencia live estruturada e auditavel. | `manter` |
| `docs/validation/runs/20260816T094054Z-wave2-acceptance-20260816.md` | `historical_evidence` | 0 | Evidencia live estruturada e auditavel. | `manter` |
| `docs/validation/runs/20260816T161500Z-stj-scon-document.md` | `historical_evidence` | 0 | Evidencia live estruturada e auditavel. | `manter` |

## Caminhos Duplicados Intencionais

`docs/providers/<source_id>/README.md` e o dossie canonico. `docs/source-contracts/<source_id>.md` continua como copia de compatibilidade enquanto catalogo, links e testes de paridade apontarem para ele. A consolidacao futura deve trocar cada copia por um apontador curto somente depois de migrar referencias e remover a regra de paridade.
