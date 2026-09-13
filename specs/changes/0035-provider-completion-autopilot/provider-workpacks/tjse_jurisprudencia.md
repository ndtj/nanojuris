# Work pack — TJSE Jurisprudência Judicial

Source ID: tjse_jurisprudencia
Lifecycle: none
Coverage role: specialized_context
Maturity: context
Target: candidate_contract_confirmed
Priority: P4

## Contrato observado

- busca textual: True
- filtros: text, number, case_class, rapporteur, judging_body, degree, instance, document_type, judgment_date_from, judgment_date_to
- paginação: unknown_until_challenge_passed
- completude: unknown
- inteiro teor: unknown
- registros canônicos: CanonicalDecision
- busca unificada: False

## Evidência local

- módulo: src/nanojuris/providers/tjse_jurisprudencia.py
- dossier: docs/providers/tjse_jurisprudencia/README.md
- source contract: docs/source-contracts/tjse_jurisprudencia.md
- readiness documental: research_ready
- itens documentais abertos: 0
- fixture evidence: versioned_fixture
- completion status: waiting_evidence
- completion phase: research
- disposition: deferred_with_review
- review after: 2026-10-12
- resume when: approve an official contract, implement the adapter, and add success/empty/failure fixtures

### Testes

- tests/test_tjse_jurisprudencia.py
- tests/test_tjse_jurisprudencia_live.py

### Fixtures

- tjse_jurisprudencia_authorized.html
- tjse_jurisprudencia_catalog.html
- tjse_jurisprudencia_form.html

## Evidência live versionada

- status: blocked_access_control_no_reproducible_result
- data: 2026-09-06
- esta fotografia não prova disponibilidade atual ou permanente

## Lacunas consolidadas

- candidate_without_runtime
- candidate_without_local_fixture
- maturity:sem provider runtime
- maturity:fora da busca unificada
- known_defects_open
- external_block_recorded

## Defeitos conhecidos

- live:blocked_access_control_no_reproducible_result
- gap:Validar formatos de data aceitos e comportamento por intervalo vazio.

## Tarefas obrigatórias

Checklist WP marca que cada item foi avaliado nesta rodada; não
substitui evidência ausente nem converte limitação em sucesso.

- [x] WP-01 — confirmar fonte oficial, rota, método, payload e termos aplicáveis — outcome: deferred_with_review; processed; resume condition: approve an official contract, implement the adapter, and add success/empty/failure fixtures
- [x] WP-02 — fechar perguntas do dossier e source contract sem inferência — outcome: deferred_with_review; processed; resume condition: approve an official contract, implement the adapter, and add success/empty/failure fixtures
- [x] WP-03 — implementar adapter somente após fixtures e contrato aprovados — outcome: deferred_with_review; processed; resume condition: approve an official contract, implement the adapter, and add success/empty/failure fixtures
- [x] WP-04 — criar testes de sucesso, vazio, erro, timeout e schema drift — outcome: deferred_with_review; processed; resume condition: approve an official contract, implement the adapter, and add success/empty/failure fixtures
- [x] WP-05 — mapear identidade, campos canônicos, raw e traces — outcome: deferred_with_review; processed; resume condition: approve an official contract, implement the adapter, and add success/empty/failure fixtures
- [x] WP-06 — declarar filtros, paginação, ordenação e completude — outcome: deferred_with_review; processed; resume condition: approve an official contract, implement the adapter, and add success/empty/failure fixtures
- [x] WP-07 — executar scorecard e decidir promoção ou defer — outcome: deferred_with_review; processed; resume condition: approve an official contract, implement the adapter, and add success/empty/failure fixtures

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
