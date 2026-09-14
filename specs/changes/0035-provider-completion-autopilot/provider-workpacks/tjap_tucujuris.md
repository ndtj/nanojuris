# Work pack — TJAP Tucujuris

Source ID: tjap_tucujuris
Lifecycle: none
Coverage role: specialized_context
Maturity: blocked
Target: candidate_contract_confirmed
Priority: P4

## Contrato observado

- busca textual: True
- filtros: text, number, case_class, rapporteur, judging_body, degree, instance, branch, collection, judgment_date_from, judgment_date_to, source_origin, decision_type, types
- paginação: offset
- completude: unknown
- inteiro teor: unknown
- registros canônicos: CanonicalDecision
- busca unificada: False

## Evidência local

- módulo: src/nanojuris/providers/tjap_tucujuris.py
- dossier: docs/providers/tjap_tucujuris/README.md
- source contract: docs/source-contracts/tjap_tucujuris.md
- readiness documental: research_ready
- itens documentais abertos: 0
- fixture evidence: versioned_fixture
- completion status: waiting_evidence
- completion phase: research
- disposition: deferred_with_review
- review after: 2026-10-12
- resume when: reexecute a bounded public request after the source removes access control

### Testes

- tests/test_juscraper_runtime_parity.py
- tests/test_tjap_tucujuris.py

### Fixtures

- tjap_tucujuris_access_control.json
- tjap_tucujuris_empty.json

## Evidência live versionada

- status: access_controlled
- data: 2026-09-13
- esta fotografia não prova disponibilidade atual ou permanente

## Lacunas consolidadas

- candidate_without_runtime
- candidate_without_local_fixture
- maturity:sem provider runtime
- maturity:fora da busca unificada
- known_defects_open
- external_block_recorded

## Defeitos conhecidos

- live:access_controlled
- gap:Completar dossie com casos reais publicos, fixtures e criterios de estabilidade.

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
- aguardar rota pÃºblica oficial reproduzÃ­vel ou alteraÃ§Ã£o observÃ¡vel da polÃ­tica de acesso antes de promover

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
