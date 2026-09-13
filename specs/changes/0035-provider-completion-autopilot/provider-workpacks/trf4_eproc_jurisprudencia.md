# Work pack — TRF4 eproc Jurisprudencia

Source ID: trf4_eproc_jurisprudencia
Lifecycle: runtime
Coverage role: primary_textual_jurisprudence
Maturity: gold
Target: gold
Priority: P2

## Contrato observado

- busca textual: True
- filtros: text, number
- paginação: local_window
- completude: unknown
- inteiro teor: unknown
- registros canônicos: CanonicalDecision, CanonicalDocument
- busca unificada: True

## Evidência local

- módulo: src/nanojuris/providers/trf4_eproc_jurisprudencia.py
- dossier: docs/providers/trf4_eproc_jurisprudencia/README.md
- source contract: docs/source-contracts/trf4_eproc_jurisprudencia.md
- readiness documental: implementation_ready
- itens documentais abertos: 0
- fixture evidence: versioned_and_inline
- completion status: ready_for_review
- completion phase: review
- disposition: accepted_with_limitations
- review after: not scheduled
- resume when: rerun the promotion manifest after any contract, parser, or schema change

### Testes

- tests/test_client_exporters.py
- tests/test_eproc_jurisprudencia_federal.py
- tests/test_state_eproc_jurisprudencia.py
- tests/test_trf4_eproc_jurisprudencia.py
- tests/test_trf4_fixture_contract.py

### Fixtures

- trf4_eproc_empty.html
- trf4_eproc_pagination.html
- trf4_eproc_results.html
- trf4_eproc_schema_drift.html

## Evidência live versionada

- status: valid
- data: 2026-09-08
- esta fotografia não prova disponibilidade atual ou permanente

## Lacunas consolidadas

- full_text_contract_unknown
- known_defects_open

## Defeitos conhecidos

- gap:Expandir fixtures por tipo decisorio.
- gap:Documentar paginacao, ordenacao e limites de consulta.

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
