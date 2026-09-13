# Inventario Documental

Gerado por `python tools/audit_documentation_inventory.py --write`. Este inventario orienta consolidacoes sem apagar contratos, evidencias ou caminhos de compatibilidade sem uma migracao explicita.

Documentos inventariados: **340** (`active_guide`=130, `canonical`=80, `compatibility_copy`=60, `generated`=14, `historical_evidence`=56).

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
| `README.md` | `canonical` | 30 | Entrada normativa, de produto ou de governanca. | `manter` |
| `SECURITY.md` | `canonical` | 3 | Entrada normativa, de produto ou de governanca. | `manter` |
| `SPECS.md` | `canonical` | 0 | Entrada normativa, de produto ou de governanca. | `manter` |
| `docs/README.md` | `canonical` | 1 | Entrada normativa, de produto ou de governanca. | `manter` |
| `docs/ai-agent-usage.md` | `active_guide` | 2 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/architecture.md` | `canonical` | 4 | Entrada normativa, de produto ou de governanca. | `manter` |
| `docs/audience-ux.md` | `active_guide` | 1 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/benchmarks/collection-runner-20260901.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/benchmarks/federated-merge-20260901.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/candidate-live-validation-2026-08-11.md` | `historical_evidence` | 46 | Registro de pesquisa, QA ou validacao. | `manter` |
| `docs/case-studies.md` | `active_guide` | 2 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/courtsbr-provider-analysis.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/coverage/README.md` | `generated` | 2 | Gerado por build_provider_coverage.py. | `manter` |
| `docs/coverage/degree-coverage-roadmap-20260902.md` | `generated` | 2 | Gerado por build_provider_coverage.py. | `manter` |
| `docs/coverage/document-capability-inventory.md` | `generated` | 0 | Gerado por build_provider_coverage.py. | `manter` |
| `docs/coverage/field-coverage.md` | `generated` | 1 | Gerado por build_provider_coverage.py. | `manter` |
| `docs/coverage/improvement-queue.md` | `generated` | 2 | Gerado por build_provider_coverage.py. | `manter` |
| `docs/coverage/inputs.md` | `generated` | 1 | Gerado por build_provider_coverage.py. | `manter` |
| `docs/coverage/live-status.md` | `generated` | 1 | Gerado por build_provider_coverage.py. | `manter` |
| `docs/coverage/matrix.md` | `generated` | 10 | Gerado por build_provider_coverage.py. | `manter` |
| `docs/coverage/maturity-score.md` | `generated` | 2 | Gerado por build_provider_coverage.py. | `manter` |
| `docs/coverage/maturity-waves.md` | `active_guide` | 3 | Plano mantido manualmente; os indicadores de cobertura sao gerados separadamente. | `revisar_periodicamente` |
| `docs/coverage/maturity.md` | `generated` | 3 | Gerado por build_provider_coverage.py. | `manter` |
| `docs/coverage/national-coverage-20260902.md` | `generated` | 0 | Gerado por build_provider_coverage.py. | `manter` |
| `docs/coverage/outputs.md` | `generated` | 1 | Gerado por build_provider_coverage.py. | `manter` |
| `docs/coverage/source-of-truth.md` | `generated` | 1 | Gerado por build_provider_coverage.py. | `manter` |
| `docs/coverage/surface-state-registry-20260902.md` | `generated` | 0 | Gerado por build_provider_coverage.py. | `manter` |
| `docs/data-quality-completion.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/demo-studio-mcp.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/documents.md` | `active_guide` | 1 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/elite-extraction-blueprint.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/engineering-team.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/external-court-scraper-survey-2026-08-02.md` | `historical_evidence` | 1 | Registro de pesquisa, QA ou validacao. | `manter` |
| `docs/extraction-pipeline.md` | `active_guide` | 4 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/federated-search-v2.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/github-scraper-research.md` | `active_guide` | 1 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/github-transfer-checklist.md` | `active_guide` | 1 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/gold-maturity.md` | `active_guide` | 2 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/identity.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/implementation-live-validation-2026-08-11.md` | `historical_evidence` | 1 | Registro de pesquisa, QA ou validacao. | `manter` |
| `docs/implementation-status-20260902.md` | `active_guide` | 1 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/jurimetry-idpj-demo.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/live-provider-validation.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/live-validation-2026-08-11.md` | `historical_evidence` | 56 | Registro de pesquisa, QA ou validacao. | `manter` |
| `docs/live-validation-2026-08-15.md` | `historical_evidence` | 1 | Registro de pesquisa, QA ou validacao. | `manter` |
| `docs/live-validation-latest.md` | `active_guide` | 2 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/mcp.md` | `canonical` | 4 | Entrada normativa, de produto ou de governanca. | `manter` |
| `docs/migration-to-nanojud.md` | `active_guide` | 3 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/national-coverage-matrix.md` | `active_guide` | 1 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/operations/interface-impact-matrix-20260902.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/operations/live-probes.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/operations/provider-incident-runbook.md` | `active_guide` | 2 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/operations/provider-promotion-policy-20260905.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/operations/release-compatibility-20260902.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/operations/release-provenance-20260902.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/operations/release-rehearsal-20260902-final.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/operations/release-rehearsal-20260902-final2.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/operations/release-rehearsal-20260902-final3.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/operations/release-rehearsal-20260902-final4.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/operations/release-rehearsal-20260902-final5.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/operations/release-rehearsal-20260902-final6.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/operations/release-rehearsal-20260902.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/operations/shared-runtime.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/operations/technical-promotion-manifest-20260905.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/operations/wave-implementation-20260902.md` | `active_guide` | 1 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-contract-v2-compatibility.md` | `active_guide` | 1 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-contract-v2.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-contract-validation-2026-08-12.md` | `historical_evidence` | 0 | Registro de pesquisa, QA ou validacao. | `manter` |
| `docs/provider-coverage-map.md` | `active_guide` | 5 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-development-queue.md` | `active_guide` | 4 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-development.md` | `canonical` | 8 | Entrada normativa, de produto ou de governanca. | `manter` |
| `docs/provider-discovery-2026-08-12.md` | `active_guide` | 1 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-discovery-source-map.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-discovery.md` | `active_guide` | 2 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-discovery/adapter-wave-board-20260901.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-discovery/all-provider-sweep-20260901-cycle2.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-discovery/all-provider-sweep-20260901.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-discovery/all-provider-sweep-20260902-cycle20.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-discovery/all-provider-sweep-20260902-cycle24.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-discovery/all-provider-sweep-20260905-cycle33.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-discovery/all-provider-sweep-20260905-cycle35.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-discovery/all-provider-sweep-20260905-cycle40.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-discovery/all-provider-sweep-20260905-cycle49.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-discovery/all-provider-sweep.md` | `active_guide` | 1 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-discovery/catalog-candidate-justica-eleitoral.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-discovery/catalog-candidates-sweep-20260902-cycle23.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-discovery/catalog-candidates-sweep-20260902-cycle25.md` | `active_guide` | 1 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-discovery/catalog-candidates-sweep.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-discovery/cjf-trf1-live-recheck-20260901-cycle8.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-discovery/degree-bindings-live-20260902-cycle26.md` | `active_guide` | 1 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-discovery/esaj-juscraper-flow-live-recheck-20260902-cycle12.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-discovery/federated-opt-in-live-20260905-cycle30.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-discovery/federated-promotion-live-20260905-cycle41.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-discovery/federated-promotion-live-20260905-cycle45.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-discovery/federated-promotion-live-20260905-cycle47.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-discovery/federated-promotion-live-20260905-cycle48.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-discovery/juscraper-court-inventory-20260901.md` | `active_guide` | 1 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-discovery/juscraper-intake-20260901.md` | `active_guide` | 1 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-discovery/juscraper-live-recheck-20260901.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-discovery/juscraper-live-smoke-20260901.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-discovery/juscraper-parity-live-recheck-20260901.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-discovery/juscraper-reuse-audit-20260901.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-discovery/juscraper-semantic-diff-20260901.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-discovery/juscraper-semantic-diff-20260905.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-discovery/official-alternatives-2026-08-27.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-discovery/offline-audit.md` | `active_guide` | 1 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-discovery/provider-closure-ledger.md` | `active_guide` | 3 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-discovery/public-contract-live-20260902-cycle21.md` | `active_guide` | 1 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-discovery/route-research-2026-08-27.md` | `historical_evidence` | 0 | Registro de pesquisa, QA ou validacao. | `manter` |
| `docs/provider-discovery/stf-informativo-live-recheck-20260901-cycle1.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-discovery/stf-juris-live-recheck-20260901-cycle9.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-discovery/tjes-jurisprudencia-live-20260902-cycle19.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-discovery/tjes-turma-recursal-live-20260905-cycle34.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-discovery/tjpe-live-recheck-20260901-cycle10.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-discovery/tjrn-jurisprudencia-live-20260902-cycle17.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-discovery/tjrn-jurisprudencia-live-20260905-cycle27.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-discovery/tjrn-jurisprudencia-live-20260905-cycle28.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-discovery/tjrn-jurisprudencia-pagination-live-20260902-cycle22.md` | `active_guide` | 1 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-discovery/tjrn-jurisprudencia-pagination-live-20260905-cycle31.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-discovery/tjro-cjsg-live-recheck-20260901.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-discovery/tjro-jurisprudencia-federated-live-20260902-cycle16.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-discovery/tjro-jurisprudencia-live-20260902-cycle15.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-discovery/tjro-jurisprudencia-live-recheck-20260902-cycle13.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-discovery/tjro-jurisprudencia-route-inventory-20260902-cycle14.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-discovery/tjro-tjgo-live-20260905-cycle32.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-discovery/tjsp-cjsg-live-recheck-20260901-cycle11.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-discovery/tjto-jurisprudencia-detail-live-20260902-cycle18.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-discovery/trf3-live-recheck-20260901-cycle3.md` | `active_guide` | 1 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-discovery/unified-contract-matrix.md` | `active_guide` | 2 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-discovery/zero-200-analysis-20260901.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-documentation-audit.md` | `active_guide` | 4 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-dossier-template.md` | `canonical` | 7 | Entrada normativa, de produto ou de governanca. | `manter` |
| `docs/provider-expansion-analysis-2026-08-02.md` | `active_guide` | 1 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/provider-status.md` | `active_guide` | 3 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/providers.md` | `active_guide` | 3 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/providers/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/bnp_pangea/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/cjf_jurisprudencia/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/cnj_jurisprudencia/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/eproc_jurisprudencia_federal/README.md` | `canonical` | 0 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/falcao_jt/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/justica_eleitoral_sjur/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/stf_informativo/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/stf_juris/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/stj_dados_abertos_jurisprudencia/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/stj_informativo/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/stj_scon/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/stm_jurisprudencia/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/tce_pr_viajuris/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
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
| `docs/providers/tjes_cjpg/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/tjes_jurisprudencia/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/tjes_turma_recursal/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
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
| `docs/providers/tjrj_ejuris/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/tjrj_eproc_jurisprudencia/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/tjrn_jurisprudencia/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/tjro_jurisprudencia/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/tjro_liame/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/tjrr_juris/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/tjrs_solr/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/tjsc_eproc_jurisprudencia/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/tjse_jurisprudencia/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
| `docs/providers/tjsp_cjpg/README.md` | `canonical` | 1 | Dossie tecnico canônico por provider. | `manter` |
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
| `docs/quality/README.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/quality/provider-quality.md` | `active_guide` | 1 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/quickstart.md` | `canonical` | 3 | Entrada normativa, de produto ou de governanca. | `manter` |
| `docs/registry/README.md` | `canonical` | 0 | Catalogo, schema ou indice de integracao. | `manter` |
| `docs/release-checklist.md` | `active_guide` | 3 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/research/idpj-pilot-2026-08-16.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/responsible-use.md` | `canonical` | 3 | Entrada normativa, de produto ou de governanca. | `manter` |
| `docs/roadmap.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/route-mapping-playbook.md` | `canonical` | 6 | Entrada normativa, de produto ou de governanca. | `manter` |
| `docs/route-mapping-results-2026-08-07.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/source-capabilities.md` | `active_guide` | 4 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/source-contracts.md` | `active_guide` | 2 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/source-contracts/README.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/source-contracts/bnp_pangea.md` | `compatibility_copy` | 2 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/cjf_jurisprudencia.md` | `compatibility_copy` | 4 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/cnj_jurisprudencia.md` | `compatibility_copy` | 3 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/eproc_jurisprudencia_federal.md` | `compatibility_copy` | 1 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/falcao_jt.md` | `compatibility_copy` | 3 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/justica_eleitoral_sjur.md` | `compatibility_copy` | 3 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/stf_informativo.md` | `compatibility_copy` | 2 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/stf_juris.md` | `compatibility_copy` | 2 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/stj_dados_abertos_jurisprudencia.md` | `compatibility_copy` | 3 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/stj_informativo.md` | `compatibility_copy` | 2 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/stj_scon.md` | `compatibility_copy` | 2 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/stm_jurisprudencia.md` | `compatibility_copy` | 2 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tce_pr_viajuris.md` | `compatibility_copy` | 1 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tce_sp_jurisprudencia.md` | `compatibility_copy` | 2 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tcu_jurisprudencia.md` | `compatibility_copy` | 5 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjac_cjsg.md` | `compatibility_copy` | 2 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjal_cjsg.md` | `compatibility_copy` | 2 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjam_cjsg.md` | `compatibility_copy` | 2 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjap_tucujuris.md` | `compatibility_copy` | 3 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjba_graphql.md` | `compatibility_copy` | 3 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjce_cjsg.md` | `compatibility_copy` | 3 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjce_informativos.md` | `compatibility_copy` | 2 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjce_sjuris.md` | `compatibility_copy` | 3 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjdf_juris.md` | `compatibility_copy` | 2 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjes_cjpg.md` | `compatibility_copy` | 1 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjes_jurisprudencia.md` | `compatibility_copy` | 3 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjes_turma_recursal.md` | `compatibility_copy` | 1 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjgo_projudi_jurisprudencia.md` | `compatibility_copy` | 3 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjma_jurisconsult.md` | `compatibility_copy` | 2 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjmg_jurisprudencia.md` | `compatibility_copy` | 3 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjms_cjsg.md` | `compatibility_copy` | 2 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjmt_jurisprudencia_api.md` | `compatibility_copy` | 3 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjpa_jurisprudencia_bff.md` | `compatibility_copy` | 3 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjpb_pje_jurisprudencia.md` | `compatibility_copy` | 3 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjpe_jurisprudencia.md` | `compatibility_copy` | 3 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjpi_juspi.md` | `compatibility_copy` | 3 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjpr_jurisprudencia.md` | `compatibility_copy` | 3 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjrj_ejuris.md` | `compatibility_copy` | 2 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjrj_eproc_jurisprudencia.md` | `compatibility_copy` | 3 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjrn_jurisprudencia.md` | `compatibility_copy` | 3 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjro_jurisprudencia.md` | `compatibility_copy` | 1 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjro_liame.md` | `compatibility_copy` | 3 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjrr_juris.md` | `compatibility_copy` | 3 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjrs_solr.md` | `compatibility_copy` | 3 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjsc_eproc_jurisprudencia.md` | `compatibility_copy` | 4 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjse_jurisprudencia.md` | `compatibility_copy` | 3 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjsp_cjpg.md` | `compatibility_copy` | 1 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjsp_cjsg.md` | `compatibility_copy` | 2 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjsp_eproc_jurisprudencia.md` | `compatibility_copy` | 2 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjsp_nugepnac.md` | `compatibility_copy` | 2 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tjto_jurisprudencia.md` | `compatibility_copy` | 3 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tnu_eproc_jurisprudencia.md` | `compatibility_copy` | 2 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tre_sp_temas.md` | `compatibility_copy` | 2 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/trf2_eproc_jurisprudencia.md` | `compatibility_copy` | 2 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/trf3_jurisprudencia.md` | `compatibility_copy` | 4 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/trf4_eproc_jurisprudencia.md` | `compatibility_copy` | 2 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/trf5_jurisprudencia.md` | `compatibility_copy` | 4 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/trf6_eproc_jurisprudencia.md` | `compatibility_copy` | 2 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/trt2_pje_jurisprudencia.md` | `compatibility_copy` | 2 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-contracts/tst_jurisprudencia.md` | `compatibility_copy` | 3 | Copia legada com links, catalogo e testes de paridade ativos. | `manter` |
| `docs/source-discovery.md` | `active_guide` | 3 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/state-court-route-mapping-2026-08-07.md` | `historical_evidence` | 4 | Registro de pesquisa, QA ou validacao. | `manter` |
| `docs/stf-stj-provider-research-2026-08-03.md` | `historical_evidence` | 0 | Registro de pesquisa, QA ou validacao. | `manter` |
| `docs/stj-provider-research.md` | `active_guide` | 1 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/stj-source-profile.md` | `active_guide` | 2 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/storage.md` | `canonical` | 3 | Entrada normativa, de produto ou de governanca. | `manter` |
| `docs/studio-har-audit-2026-08-07.md` | `historical_evidence` | 0 | Registro de pesquisa, QA ou validacao. | `manter` |
| `docs/template-comparison.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/topology/README.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/topology/cnj-tribunal-register-20260901.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/topology/court-catalog-url-probe-20260901.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/topology/degree-coverage-matrix-20260901.md` | `active_guide` | 1 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/topology/degree-coverage-matrix-20260902.md` | `active_guide` | 0 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
| `docs/topology/national-coverage-claims-20260901.md` | `active_guide` | 1 | Guia ativo; nao ha base automatica para remocao. | `revisar_periodicamente` |
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
| `docs/validation/runs/20260816T101402Z-tjpe-contract-diagnostic.md` | `historical_evidence` | 0 | Evidencia live estruturada e auditavel. | `manter` |
| `docs/validation/runs/20260816T103000Z-tjce-cjsg-contract-diagnostic.md` | `historical_evidence` | 0 | Evidencia live estruturada e auditavel. | `manter` |
| `docs/validation/runs/20260816T103927Z-remaining-tj-candidates.md` | `historical_evidence` | 0 | Evidencia live estruturada e auditavel. | `manter` |
| `docs/validation/runs/20260816T103927Z-state-candidate-surfaces.md` | `historical_evidence` | 0 | Evidencia live estruturada e auditavel. | `manter` |
| `docs/validation/runs/20260816T103927Z-tjce-sjuris-catalog.md` | `historical_evidence` | 0 | Evidencia live estruturada e auditavel. | `manter` |
| `docs/validation/runs/20260816T111431Z-tjce-sjuris-search.md` | `historical_evidence` | 0 | Evidencia live estruturada e auditavel. | `manter` |
| `docs/validation/runs/20260816T125603Z-tjto-tjma-tjro-live.md` | `historical_evidence` | 0 | Evidencia live estruturada e auditavel. | `manter` |
| `docs/validation/runs/20260816T161500Z-stj-scon-document.md` | `historical_evidence` | 0 | Evidencia live estruturada e auditavel. | `manter` |
| `docs/validation/runs/20260816T173000Z-tjmt-jurisprudencia-api-search.md` | `historical_evidence` | 0 | Evidencia live estruturada e auditavel. | `manter` |
| `docs/validation/runs/20260816T173500Z-tjto-anonymous-portal.md` | `historical_evidence` | 0 | Evidencia live estruturada e auditavel. | `manter` |
| `docs/validation/runs/20260828T010539Z-platform-live-summary.md` | `historical_evidence` | 1 | Evidencia live estruturada e auditavel. | `manter` |
| `docs/validation/runs/20260902T024407Z-local-quality-and-live-cycle.md` | `historical_evidence` | 0 | Evidencia live estruturada e auditavel. | `manter` |
| `docs/validation/runs/20260902T051332Z-local-quality-cycle.md` | `historical_evidence` | 0 | Evidencia live estruturada e auditavel. | `manter` |
| `docs/validation/runs/20260905T080812Z-federated-live-20260905-cycle37.md` | `historical_evidence` | 0 | Evidencia live estruturada e auditavel. | `manter` |
| `docs/validation/runs/20260905T082427Z-federated-live-20260905-cycle39.md` | `historical_evidence` | 0 | Evidencia live estruturada e auditavel. | `manter` |
| `docs/validation/runs/playwright-live-run-template.md` | `historical_evidence` | 2 | Evidencia live estruturada e auditavel. | `manter` |

## Caminhos Duplicados Intencionais

`docs/providers/<source_id>/README.md` e o dossie canonico. `docs/source-contracts/<source_id>.md` continua como copia de compatibilidade enquanto catalogo, links e testes de paridade apontarem para ele. A consolidacao futura deve trocar cada copia por um apontador curto somente depois de migrar referencias e remover a regra de paridade.
