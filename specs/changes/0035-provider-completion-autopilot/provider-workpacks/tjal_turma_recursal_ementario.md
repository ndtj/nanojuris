# Work pack — TJAL Ementario das Turmas Recursais

Source ID: tjal_turma_recursal_ementario
Lifecycle: runtime
Coverage role: specialized_context
Maturity: context
Target: context_verified
Priority: P3

## Contrato observado

- busca textual: True
- filtros: text, exact_phrase, number, without_words, degree, instance, branch, authority, collection, page
- paginação: local_pdf_window
- completude: unknown
- inteiro teor: unknown
- registros canônicos: CanonicalDecision, CanonicalDocument
- busca unificada: False

## Evidência local

- módulo: src/nanojuris/providers/tjal_turma_recursal_ementario.py
- dossier: docs/providers/tjal_turma_recursal_ementario/README.md
- source contract: docs/source-contracts/tjal_turma_recursal_ementario.md
- readiness documental: implementation_ready
- itens documentais abertos: 0
- fixture evidence: versioned_fixture
- completion status: waiting_evidence
- completion phase: review
- disposition: deferred_with_review
- review after: 2026-10-12
- resume when: run one bounded live check against the documented public route

### Testes

- tests/test_tjal_turma_recursal_ementario.py

### Fixtures

- provider_contracts.json
- tjal_turma_recursal_empty.txt
- tjal_turma_recursal_invalid.pdf
- tjal_turma_recursal_success.txt

## Evidência live versionada

- status: public_textual_recursal
- data: 2026-09-08
- esta fotografia não prova disponibilidade atual ou permanente

## Lacunas consolidadas

- not_in_unified_search
- live_status:public_textual_recursal
- maturity:fora da busca unificada
- unified:excluded_from_unified_search
- known_defects_open

## Defeitos conhecidos

- live:public_textual_recursal
- gap:Registrar como a fonte representa filtros, classes e tipos sem catalogo formal.

## Tarefas obrigatórias

Checklist WP marca que cada item foi avaliado nesta rodada; não
substitui evidência ausente nem converte limitação em sucesso.

- [x] WP-01 — reconciliar capability, dossier, source contract, módulo e interfaces — outcome: deferred_with_review; processed; resume condition: run one bounded live check against the documented public route
- [x] WP-02 — fechar todos os itens documentais objetivos — outcome: deferred_with_review; processed; resume condition: run one bounded live check against the documented public route
- [x] WP-03 — garantir fixtures versionadas de sucesso, vazio e falhas críticas — outcome: deferred_with_review; processed; resume condition: run one bounded live check against the documented public route
- [x] WP-04 — provar identidade, canonicalização, deduplicação, raw e traces — outcome: deferred_with_review; processed; resume condition: run one bounded live check against the documented public route
- [x] WP-05 — provar filtros, paginação, ordenação, limites e completude — outcome: deferred_with_review; processed; resume condition: run one bounded live check against the documented public route
- [x] WP-06 — provar estados de acesso, timeout, rate limit e schema drift — outcome: deferred_with_review; processed; resume condition: run one bounded live check against the documented public route
- [x] WP-07 — provar referência e inteiro teor quando declarados — outcome: deferred_with_review; processed; resume condition: run one bounded live check against the documented public route
- [x] WP-08 — executar testes locais, tipos, lint e auditorias geradas — outcome: deferred_with_review; processed; resume condition: run one bounded live check against the documented public route
- [x] WP-09 — executar canário live bounded somente quando autorizado — outcome: deferred_with_review; processed; resume condition: run one bounded live check against the documented public route
- [x] WP-10 — registrar scorecard, risco residual e decisão de tier — outcome: deferred_with_review; processed; resume condition: run one bounded live check against the documented public route

## Próximas ações sugeridas

- manter monitoramento e ampliar fixtures por variacao juridica

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
