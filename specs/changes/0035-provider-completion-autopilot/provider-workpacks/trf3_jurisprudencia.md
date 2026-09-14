# Work pack — TRF3 Jurisprudência (processo exato)

Source ID: trf3_jurisprudencia
Lifecycle: runtime
Coverage role: specialized_context
Maturity: context
Target: context_verified
Priority: P3

## Contrato observado

- busca textual: False
- filtros: number, fetch_details, degree, instance, branch, collection, document_type, decision_type
- paginação: detail_links
- completude: unknown
- inteiro teor: unknown
- registros canônicos: JurisprudenceResult, CanonicalDocument
- busca unificada: False

## Evidência local

- módulo: src/nanojuris/providers/trf3_jurisprudencia.py
- dossier: docs/providers/trf3_jurisprudencia/README.md
- source contract: docs/source-contracts/trf3_jurisprudencia.md
- readiness documental: needs_deepening
- itens documentais abertos: 2
- fixture evidence: versioned_and_inline
- completion status: waiting_evidence
- completion phase: review
- disposition: deferred_with_review
- review after: 2026-10-12
- resume when: add sanitized versioned success, explicit-empty, and failure/schema fixtures

### Testes

- tests/test_trf3_jurisprudencia.py

### Fixtures

- trf3_jurisprudencia_detail.html
- trf3_jurisprudencia_process_empty.html
- trf3_jurisprudencia_process_results.html

## Evidência live versionada

- status: transport_error
- data: 2026-09-09
- esta fotografia não prova disponibilidade atual ou permanente

## Lacunas consolidadas

- documentation_open_items:2
- not_in_unified_search
- live_status:transport_error
- maturity:fora da busca unificada
- maturity:dossie com pendencias abertas
- unified:excluded_from_unified_search
- full_text_contract_unknown
- known_defects_open

## Defeitos conhecidos

- documentacao_com_pendencias_abertas
- live:transport_error
- gap:Registrar como a fonte representa filtros, classes e tipos sem catalogo formal.
- gap:Mapear indisponibilidade, hash e tamanho de inteiro teor.

## Tarefas obrigatórias

Checklist WP marca que cada item foi avaliado nesta rodada; não
substitui evidência ausente nem converte limitação em sucesso.

- [x] WP-01 — reconciliar capability, dossier, source contract, módulo e interfaces — outcome: deferred_with_review; processed; resume condition: add sanitized versioned success, explicit-empty, and failure/schema fixtures
- [x] WP-02 — fechar todos os itens documentais objetivos — outcome: deferred_with_review; processed; resume condition: add sanitized versioned success, explicit-empty, and failure/schema fixtures
- [x] WP-03 — garantir fixtures versionadas de sucesso, vazio e falhas críticas — outcome: deferred_with_review; processed; resume condition: add sanitized versioned success, explicit-empty, and failure/schema fixtures
- [x] WP-04 — provar identidade, canonicalização, deduplicação, raw e traces — outcome: deferred_with_review; processed; resume condition: add sanitized versioned success, explicit-empty, and failure/schema fixtures
- [x] WP-05 — provar filtros, paginação, ordenação, limites e completude — outcome: deferred_with_review; processed; resume condition: add sanitized versioned success, explicit-empty, and failure/schema fixtures
- [x] WP-06 — provar estados de acesso, timeout, rate limit e schema drift — outcome: deferred_with_review; processed; resume condition: add sanitized versioned success, explicit-empty, and failure/schema fixtures
- [x] WP-07 — provar referência e inteiro teor quando declarados — outcome: deferred_with_review; processed; resume condition: add sanitized versioned success, explicit-empty, and failure/schema fixtures
- [x] WP-08 — executar testes locais, tipos, lint e auditorias geradas — outcome: deferred_with_review; processed; resume condition: add sanitized versioned success, explicit-empty, and failure/schema fixtures
- [x] WP-09 — executar canário live bounded somente quando autorizado — outcome: deferred_with_review; processed; resume condition: add sanitized versioned success, explicit-empty, and failure/schema fixtures
- [x] WP-10 — registrar scorecard, risco residual e decisão de tier — outcome: deferred_with_review; processed; resume condition: add sanitized versioned success, explicit-empty, and failure/schema fixtures

## Próximas ações sugeridas

- fechar checklist objetivo do dossie
- validar inteiro teor com hash, tamanho e access_status
- manter o escopo promovido e ampliar somente com novo contrato reproduzivel
- preservar limites declarados; promover busca decisoria somente com contrato de resultados

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
