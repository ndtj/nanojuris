# Work pack — TJRJ EJURIS Jurisprudência (CJSG)

Source ID: tjrj_ejuris
Lifecycle: runtime
Coverage role: primary_textual_jurisprudence
Maturity: silver
Target: gold
Priority: P1

## Contrato observado

- busca textual: True
- filtros: text, exact_phrase, number, types, document_type, decision_type, published_from, published_to, updated_from, updated_to, degree, instance, branch, authority, collection, source_origin
- paginação: page
- completude: unknown
- inteiro teor: unknown
- registros canônicos: CanonicalDecision
- busca unificada: True

## Evidência local

- módulo: src/nanojuris/providers/tjrj_ejuris.py
- dossier: docs/providers/tjrj_ejuris/README.md
- source contract: docs/source-contracts/tjrj_ejuris.md
- readiness documental: implementation_ready
- itens documentais abertos: 0
- fixture evidence: versioned_fixture
- completion status: ready_for_review
- completion phase: review
- disposition: accepted_with_limitations
- review after: not scheduled
- resume when: rerun the promotion manifest after any contract, parser, or schema change

### Testes

- tests/test_tjrj_ejuris.py
- tests/test_tjrj_ejuris_live.py

### Fixtures

- tjrj_ejuris_empty.json
- tjrj_ejuris_form.html
- tjrj_ejuris_invalid.json
- tjrj_ejuris_page.json
- tjrj_ejuris_page2.json

## Evidência live versionada

- status: valid
- data: 2026-09-10
- esta fotografia não prova disponibilidade atual ou permanente

## Lacunas consolidadas

- full_text_contract_unknown
- known_defects_open

## Defeitos conhecidos

- gap:Registrar como a fonte representa filtros, classes e tipos sem catalogo formal.
- gap:Mapear indisponibilidade, hash e tamanho de inteiro teor.

## Tarefas obrigatórias

Checklist WP marca que cada item foi avaliado nesta rodada; não
substitui evidência ausente nem converte limitação em sucesso.

- [x] WP-01 — reconciliar capability, dossier, source contract, módulo e interfaces — outcome: accepted_with_limitations; processed; residual limitations remain explicit above
- [x] WP-02 — fechar todos os itens documentais objetivos — outcome: accepted_with_limitations; processed; residual limitations remain explicit above
- [x] WP-03 — garantir fixtures versionadas de sucesso, vazio e falhas críticas — outcome: accepted_with_limitations; processed; residual limitations remain explicit above
- [x] WP-04 — provar identidade, canonicalização, deduplicação, raw e traces — outcome: accepted_with_limitations; processed; residual limitations remain explicit above
- [x] WP-05 — provar filtros, paginação, ordenação, limites e completude — outcome: accepted_with_limitations; processed; residual limitations remain explicit above
- [x] WP-06 — provar estados de acesso, timeout, rate limit e schema drift — outcome: accepted_with_limitations; processed; residual limitations remain explicit above
- [x] WP-07 — provar referência e inteiro teor quando declarados — outcome: accepted_with_limitations; processed; residual limitations remain explicit above
- [x] WP-08 — executar testes locais, tipos, lint e auditorias geradas — outcome: accepted_with_limitations; processed; residual limitations remain explicit above
- [x] WP-09 — executar canário live bounded somente quando autorizado — outcome: accepted_with_limitations; processed; residual limitations remain explicit above
- [x] WP-10 — registrar scorecard, risco residual e decisão de tier — outcome: accepted_with_limitations; processed; residual limitations remain explicit above

## Próximas ações sugeridas

- validar inteiro teor com hash, tamanho e access_status

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
