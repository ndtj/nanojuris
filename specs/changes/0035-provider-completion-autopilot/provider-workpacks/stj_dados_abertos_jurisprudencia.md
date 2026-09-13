# Work pack — STJ Dados Abertos de Jurisprudencia

Source ID: stj_dados_abertos_jurisprudencia
Lifecycle: runtime
Coverage role: dataset_pipeline
Maturity: context
Target: context_verified
Priority: P3

## Contrato observado

- busca textual: False
- filtros: catalog_query, rows, dataset_id, resource_id, metadata_resource_id, text_resource_id, format, max_bytes, force
- paginação: catalog_offset
- completude: unknown
- inteiro teor: unknown
- registros canônicos: ProviderCatalog, CanonicalDecision, ResearchRun
- busca unificada: False

## Evidência local

- módulo: src/nanojuris/providers/stj_dados_abertos_jurisprudencia.py
- dossier: docs/providers/stj_dados_abertos_jurisprudencia/README.md
- source contract: docs/source-contracts/stj_dados_abertos_jurisprudencia.md
- readiness documental: implementation_ready
- itens documentais abertos: 0
- fixture evidence: versioned_fixture
- completion status: waiting_evidence
- completion phase: review
- disposition: deferred_with_review
- review after: 2026-10-12
- resume when: rerun the provider completion command after new source evidence

### Testes

- tests/test_stj_dados_abertos_jurisprudencia.py

### Fixtures

- stj_ckan_package_empty.json
- stj_ckan_package_resource_removed.json
- stj_ckan_package_search.json
- stj_ckan_package_show.json
- stj_ckan_schema_changed.csv

## Evidência live versionada

- status: valid
- data: 2026-09-06
- esta fotografia não prova disponibilidade atual ou permanente

## Lacunas consolidadas

- not_in_unified_search
- maturity:fora da busca unificada
- unified:excluded_from_unified_search
- unified:live_status_query_contract_rejected
- full_text_contract_unknown
- known_defects_open
- external_block_recorded

## Defeitos conhecidos

- gap:Mapear indisponibilidade, hash e tamanho de inteiro teor.

## Tarefas obrigatórias

Checklist WP marca que cada item foi avaliado nesta rodada; não
substitui evidência ausente nem converte limitação em sucesso.

- [x] WP-01 — reconciliar capability, dossier, source contract, módulo e interfaces — outcome: deferred_with_review; processed; resume condition: rerun the provider completion command after new source evidence
- [x] WP-02 — fechar todos os itens documentais objetivos — outcome: deferred_with_review; processed; resume condition: rerun the provider completion command after new source evidence
- [x] WP-03 — garantir fixtures versionadas de sucesso, vazio e falhas críticas — outcome: deferred_with_review; processed; resume condition: rerun the provider completion command after new source evidence
- [x] WP-04 — provar identidade, canonicalização, deduplicação, raw e traces — outcome: deferred_with_review; processed; resume condition: rerun the provider completion command after new source evidence
- [x] WP-05 — provar filtros, paginação, ordenação, limites e completude — outcome: deferred_with_review; processed; resume condition: rerun the provider completion command after new source evidence
- [x] WP-06 — provar estados de acesso, timeout, rate limit e schema drift — outcome: deferred_with_review; processed; resume condition: rerun the provider completion command after new source evidence
- [x] WP-07 — provar referência e inteiro teor quando declarados — outcome: deferred_with_review; processed; resume condition: rerun the provider completion command after new source evidence
- [x] WP-08 — executar testes locais, tipos, lint e auditorias geradas — outcome: deferred_with_review; processed; resume condition: rerun the provider completion command after new source evidence
- [x] WP-09 — executar canário live bounded somente quando autorizado — outcome: deferred_with_review; processed; resume condition: rerun the provider completion command after new source evidence
- [x] WP-10 — registrar scorecard, risco residual e decisão de tier — outcome: deferred_with_review; processed; resume condition: rerun the provider completion command after new source evidence

## Próximas ações sugeridas

- validar inteiro teor com hash, tamanho e access_status
- revalidar somente após alteração autorizada da política pública/robots

## Definition of Done

- contrato e capability sincronizados;
- fixtures e testes negativos reproduzíveis;
- identidade, conteúdo, datas, paginação, completude e traces comprovados;
- bloqueios externos preservados sem false empty;
- documentação e catálogos gerados em paridade;
- scorecard revisado pelo papel de dados/QA;
- evidência em verification.md do pacote de implementação;
- fingerprint da evidência registrado e sem alteração pendente;
- decisão final aceita, aceita com limitações, rejeitada, adiada com revisão ou fora de escopo;
- produção e publicação somente com autorização humana.
