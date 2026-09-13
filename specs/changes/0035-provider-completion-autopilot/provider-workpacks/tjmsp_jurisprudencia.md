# Work pack — TJMSP Jurisprudência (diagnóstico opt-in)

Source ID: tjmsp_jurisprudencia
Lifecycle: none
Coverage role: specialized_context
Maturity: blocked
Target: candidate_contract_confirmed
Priority: P4

## Contrato observado

- busca textual: True
- filtros: nenhum declarado
- paginação: unknown_until_contract
- completude: unknown
- inteiro teor: unknown
- registros canônicos: CanonicalDecision
- busca unificada: False

## Evidência local

- módulo: src/nanojuris/providers/tjmsp_jurisprudencia.py
- dossier: docs/providers/tjmsp_jurisprudencia/README.md
- source contract: docs/source-contracts/tjmsp_jurisprudencia.md
- readiness documental: research_incomplete
- itens documentais abertos: 0
- fixture evidence: versioned_fixture
- completion status: waiting_evidence
- completion phase: research
- disposition: deferred_with_review
- review after: 2026-10-12
- resume when: reexecute a bounded public request after the source removes access control

### Testes

- tests/test_tjmsp_jurisprudencia.py

### Fixtures

- tjmsp_portal.html

## Evidência live versionada

- status: access_control_required
- data: 2026-09-10
- esta fotografia não prova disponibilidade atual ou permanente

## Lacunas consolidadas

- candidate_without_runtime
- candidate_without_local_fixture
- maturity:sem provider runtime
- maturity:fora da busca unificada
- maturity:dossie com secoes faltantes
- known_defects_open

## Defeitos conhecidos

- data
- states
- fixtures
- mcp
- next_steps
- live:access_control_required
- gap:Registrar como a fonte representa filtros, classes e tipos sem catalogo formal.

## Tarefas obrigatórias

Checklist WP marca que cada item foi avaliado nesta rodada; não
substitui evidência ausente nem converte limitação em sucesso.

- [x] WP-01 — confirmar fonte oficial, rota, método, payload e termos aplicáveis — outcome: deferred_with_review; processed; resume condition: reexecute a bounded public request after the source removes access control
- [x] WP-02 — fechar perguntas do dossier e source contract sem inferência — outcome: deferred_with_review; processed; resume condition: reexecute a bounded public request after the source removes access control
- [x] WP-03 — implementar adapter somente após fixtures e contrato aprovados — outcome: deferred_with_review; processed; resume condition: reexecute a bounded public request after the source removes access control
- [x] WP-04 — criar testes de sucesso, vazio, erro, timeout e schema drift — outcome: deferred_with_review; processed; resume condition: reexecute a bounded public request after the source removes access control
- [x] WP-05 — mapear identidade, campos canônicos, raw e traces — outcome: deferred_with_review; processed; resume condition: reexecute a bounded public request after the source removes access control
- [x] WP-06 — declarar filtros, paginação, ordenação e completude — outcome: deferred_with_review; processed; resume condition: reexecute a bounded public request after the source removes access control
- [x] WP-07 — executar scorecard e decidir promoção ou defer — outcome: deferred_with_review; processed; resume condition: reexecute a bounded public request after the source removes access control

## Próximas ações sugeridas

- aguardar rota publica/alternativa oficial ou autorizacao humana bounded; nao repetir nem contornar o bloqueio
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
