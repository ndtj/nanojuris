# Work pack — TJMA JurisConsult

Source ID: tjma_jurisconsult
Lifecycle: runtime
Coverage role: specialized_context
Maturity: blocked
Target: context_verified
Priority: P3

## Contrato observado

- busca textual: False
- filtros: types, catalog, text, exact_phrase, case_class, judging_body, rapporteur, published_from, published_to, page
- paginação: offset
- completude: unknown
- inteiro teor: unknown
- registros canônicos: ProviderCatalog, JurisprudenceResult, SearchPage
- busca unificada: False

## Evidência local

- módulo: src/nanojuris/providers/tjma_jurisconsult.py
- dossier: docs/providers/tjma_jurisconsult/README.md
- source contract: docs/source-contracts/tjma_jurisconsult.md
- readiness documental: implementation_ready
- itens documentais abertos: 0
- fixture evidence: versioned_fixture
- completion status: waiting_evidence
- completion phase: review
- disposition: deferred_with_review
- review after: 2026-10-12
- resume when: reexecute a bounded public request after the source removes access control

### Testes

- tests/test_tjma_jurisconsult.py

### Fixtures

- tjma_jurisconsult_catalog.json

## Evidência live versionada

- status: access_controlled
- data: 2026-09-06
- esta fotografia não prova disponibilidade atual ou permanente

## Lacunas consolidadas

- not_in_unified_search
- live_status:access_controlled
- maturity:fora da busca unificada
- maturity:risco operacional alto
- unified:excluded_from_unified_search
- unified:live_status_access_controlled
- known_defects_open

## Defeitos conhecidos

- live:access_controlled
- gap:Completar dossie com casos reais publicos, fixtures e criterios de estabilidade.

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

- classificar WAF, captcha, timeout e mudanca de contrato separadamente
- replay local e promover observação live quando a fonte permitir
- expandir estados somente se o contrato da fonte mudar

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
