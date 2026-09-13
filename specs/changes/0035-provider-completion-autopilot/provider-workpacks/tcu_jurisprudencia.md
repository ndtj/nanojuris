# Work pack — TCU Jurisprudencia e Dados Abertos

Source ID: tcu_jurisprudencia
Lifecycle: runtime
Coverage role: administrative_context
Maturity: silver
Target: context_verified
Priority: P3

## Contrato observado

- busca textual: True
- filtros: text, number, collection, published_from, published_to
- paginação: local_window
- completude: unknown
- inteiro teor: unknown
- registros canônicos: CanonicalDecision, CanonicalPrecedent
- busca unificada: True

## Evidência local

- módulo: src/nanojuris/providers/tcu_jurisprudencia.py
- dossier: docs/providers/tcu_jurisprudencia/README.md
- source contract: docs/source-contracts/tcu_jurisprudencia.md
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
- tests/test_tcu_jurisprudencia.py

### Fixtures

- tcu_acordao_resumo.csv
- tcu_acordao_resumo_empty.csv
- tcu_jurisprudencia_selecionada.csv
- tcu_manifest.csv
- tcu_manifest_contract_changed.txt

## Evidência live versionada

- status: valid
- data: 2026-09-05T08:24:27+00:00
- esta fotografia não prova disponibilidade atual ou permanente

## Lacunas consolidadas

- known_defects_open

## Defeitos conhecidos

- gap:Completar dossie com casos reais publicos, fixtures e criterios de estabilidade.

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

- manter monitoramento e ampliar fixtures por variacao juridica
- manter o diagnostico historico e repetir o smoke bounded quando a fonte mudar
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
