# Work pack — TJSP NugepNac Precedentes

Source ID: tjsp_nugepnac
Lifecycle: runtime
Coverage role: precedent_context
Maturity: context
Target: context_verified
Priority: P3

## Contrato observado

- busca textual: True
- filtros: text, number, types
- paginação: local_window
- completude: unknown
- inteiro teor: unknown
- registros canônicos: CanonicalPrecedent
- busca unificada: False

## Evidência local

- módulo: src/nanojuris/providers/tjsp_nugepnac.py
- dossier: docs/providers/tjsp_nugepnac/README.md
- source contract: docs/source-contracts/tjsp_nugepnac.md
- readiness documental: implementation_ready
- itens documentais abertos: 0
- fixture evidence: versioned_fixture
- completion status: waiting_evidence
- completion phase: review
- disposition: deferred_with_review
- review after: 2026-10-12
- resume when: rerun the provider completion command after new source evidence

### Testes

- tests/test_tjsp_nugepnac.py

### Fixtures

- tjsp_nugepnac_detail.html
- tjsp_nugepnac_document.html
- tjsp_nugepnac_iac_detail_no_thesis.html
- tjsp_nugepnac_iac_list.html
- tjsp_nugepnac_list.html

## Evidência live versionada

- status: reachable_empty_data
- data: 2026-09-07
- esta fotografia não prova disponibilidade atual ou permanente

## Lacunas consolidadas

- not_in_unified_search
- live_status:reachable_empty_data
- maturity:fora da busca unificada
- unified:excluded_from_unified_search
- known_defects_open

## Defeitos conhecidos

- live:reachable_empty_data
- gap:Completar dossie com casos reais publicos, fixtures e criterios de estabilidade.

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

- manter monitoramento e ampliar fixtures por variacao juridica
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
