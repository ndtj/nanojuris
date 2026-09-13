# Work pack — CJF Jurisprudencia TRF1

Source ID: cjf_jurisprudencia
Lifecycle: runtime
Coverage role: specialized_context
Maturity: blocked
Target: context_verified
Priority: P3

## Contrato observado

- busca textual: True
- filtros: text, number, types
- paginação: local_window
- completude: unknown
- inteiro teor: unknown
- registros canônicos: JurisprudenceResult, CanonicalDocument, DecisionBundle
- busca unificada: False

## Evidência local

- módulo: src/nanojuris/providers/cjf_jurisprudencia.py
- dossier: docs/providers/cjf_jurisprudencia/README.md
- source contract: docs/source-contracts/cjf_jurisprudencia.md
- readiness documental: needs_deepening
- itens documentais abertos: 2
- fixture evidence: versioned_fixture
- completion status: waiting_evidence
- completion phase: review
- disposition: deferred_with_review
- review after: 2026-10-12
- resume when: reexecute a bounded public request after the source removes access control

### Testes

- tests/test_cjf_jurisprudencia.py

### Fixtures

- cjf_trf1_access_control.html
- cjf_trf1_contract_changed.html
- cjf_trf1_document.html
- cjf_trf1_empty.html
- cjf_trf1_success.html

## Evidência live versionada

- status: access_control_required
- data: 2026-09-07
- esta fotografia não prova disponibilidade atual ou permanente

## Lacunas consolidadas

- documentation_open_items:2
- not_in_unified_search
- live_status:access_control_required
- maturity:fora da busca unificada
- maturity:dossie com pendencias abertas
- unified:excluded_from_unified_search
- unified:live_status_access_controlled
- full_text_contract_unknown
- known_defects_open

## Defeitos conhecidos

- documentacao_com_pendencias_abertas
- live:access_control_required
- gap:Registrar como a fonte representa filtros, classes e tipos sem catalogo formal.
- gap:Validar formatos de data aceitos e comportamento por intervalo vazio.
- gap:Mapear indisponibilidade, hash e tamanho de inteiro teor.

## Tarefas obrigatórias

Checklist WP marca que cada item foi avaliado nesta rodada; não
substitui evidência ausente nem converte limitação em sucesso.

- [x] WP-01 — reconciliar capability, dossier, source contract, módulo e interfaces — outcome: deferred_with_review; processed; resume condition: reexecute a bounded public request after the source removes access control
- [x] WP-02 — fechar todos os itens documentais objetivos — outcome: deferred_with_review; processed; resume condition: reexecute a bounded public request after the source removes access control
- [x] WP-03 — garantir fixtures versionadas de sucesso, vazio e falhas críticas — outcome: deferred_with_review; processed; resume condition: reexecute a bounded public request after the source removes access control
- [x] WP-04 — provar identidade, canonicalização, deduplicação, raw e traces — outcome: deferred_with_review; processed; resume condition: reexecute a bounded public request after the source removes access control
- [x] WP-05 — provar filtros, paginação, ordenação, limites e completude — outcome: deferred_with_review; processed; resume condition: reexecute a bounded public request after the source removes access control
- [x] WP-06 — provar estados de acesso, timeout, rate limit e schema drift — outcome: deferred_with_review; processed; resume condition: reexecute a bounded public request after the source removes access control
- [x] WP-07 — provar referência e inteiro teor quando declarados — outcome: deferred_with_review; processed; resume condition: reexecute a bounded public request after the source removes access control
- [x] WP-08 — executar testes locais, tipos, lint e auditorias geradas — outcome: deferred_with_review; processed; resume condition: reexecute a bounded public request after the source removes access control
- [x] WP-09 — executar canário live bounded somente quando autorizado — outcome: deferred_with_review; processed; resume condition: reexecute a bounded public request after the source removes access control
- [x] WP-10 — registrar scorecard, risco residual e decisão de tier — outcome: deferred_with_review; processed; resume condition: reexecute a bounded public request after the source removes access control

## Próximas ações sugeridas

- fechar checklist objetivo do dossie
- validar inteiro teor com hash, tamanho e access_status
- não submeter payload especulativo; revalidar por replay/contrato aprovado

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
