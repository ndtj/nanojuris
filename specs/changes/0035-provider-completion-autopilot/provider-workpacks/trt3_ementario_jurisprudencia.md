# Work pack — TRT3 Ementario de Jurisprudencia (volume curado)

Source ID: trt3_ementario_jurisprudencia
Lifecycle: runtime
Coverage role: curated_context
Maturity: context
Target: context_verified
Priority: P3

## Contrato observado

- busca textual: True
- filtros: text, exact_phrase, number, page
- paginação: remote_volume_search_local_pdf_window
- completude: unknown
- inteiro teor: unknown
- registros canônicos: CanonicalDecision, CanonicalDocument
- busca unificada: False

## Evidência local

- módulo: src/nanojuris/providers/trt3_ementario_jurisprudencia.py
- dossier: docs/providers/trt3_ementario_jurisprudencia/README.md
- source contract: docs/source-contracts/trt3_ementario_jurisprudencia.md
- readiness documental: needs_deepening
- itens documentais abertos: 0
- fixture evidence: versioned_fixture
- completion status: waiting_evidence
- completion phase: review
- disposition: deferred_with_review
- review after: 2026-10-12
- resume when: add sanitized versioned success, explicit-empty, and failure/schema fixtures

### Testes

- tests/test_trt3_ementario_jurisprudencia.py

### Fixtures

- trt3_ementario_success.json

## Evidência live versionada

- status: valid
- data: 2026-09-10
- esta fotografia não prova disponibilidade atual ou permanente

## Lacunas consolidadas

- not_in_unified_search
- maturity:fora da busca unificada
- maturity:dossie com secoes faltantes
- unified:excluded_from_unified_search
- known_defects_open

## Defeitos conhecidos

- identity
- contract
- data
- states
- fixtures
- mcp
- next_steps
- gap:Registrar como a fonte representa filtros, classes e tipos sem catalogo formal.

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

- completar secoes faltantes do dossie

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
