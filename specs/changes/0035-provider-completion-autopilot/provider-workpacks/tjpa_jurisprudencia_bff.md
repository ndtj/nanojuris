# Work pack — TJPA Jurisprudencia BFF

Source ID: tjpa_jurisprudencia_bff
Lifecycle: runtime
Coverage role: primary_textual_jurisprudence
Maturity: gold
Target: gold
Priority: P2

## Contrato observado

- busca textual: True
- filtros: text, types, source_origins, published_from, published_to, case_class, subject, rapporteur
- paginação: page
- completude: unknown
- inteiro teor: unknown
- registros canônicos: CanonicalDecision
- busca unificada: True

## Evidência local

- módulo: src/nanojuris/providers/tjpa_jurisprudencia_bff.py
- dossier: docs/providers/tjpa_jurisprudencia_bff/README.md
- source contract: docs/source-contracts/tjpa_jurisprudencia_bff.md
- readiness documental: implementation_ready
- itens documentais abertos: 0
- fixture evidence: versioned_fixture
- completion status: ready_for_review
- completion phase: review
- disposition: accepted_with_limitations
- review after: not scheduled
- resume when: rerun the promotion manifest after any contract, parser, or schema change

### Testes

- tests/test_initial_json_providers.py
- tests/test_tjpa_fixture_contract.py

### Fixtures

- tjpa_jurisprudencia_bff_empty.json
- tjpa_jurisprudencia_bff_filters.json
- tjpa_jurisprudencia_bff_invalid.json
- tjpa_jurisprudencia_bff_results.json

## Evidência live versionada

- status: valid
- data: 2026-09-08
- esta fotografia não prova disponibilidade atual ou permanente

## Lacunas consolidadas

- full_text_contract_unknown
- known_defects_open

## Defeitos conhecidos

- gap:Completar fixtures de filtros, vazio e erro do BFF.
- gap:Validar uma rota publica de detalhe antes de anuncia-la.

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
- manter o diagnostico historico e repetir o smoke bounded quando a fonte mudar
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
