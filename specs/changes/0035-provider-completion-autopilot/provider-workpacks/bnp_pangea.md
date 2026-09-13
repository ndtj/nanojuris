# Work pack — Banco Nacional de Precedentes/Pangea

Source ID: bnp_pangea
Lifecycle: runtime
Coverage role: precedent_context
Maturity: context
Target: context_verified
Priority: P3

## Contrato observado

- busca textual: True
- filtros: text, number, courts, types, all_words, any_words, without_words, exact_phrase, updated_from, updated_to
- paginação: page
- completude: unknown
- inteiro teor: unknown
- registros canônicos: CanonicalPrecedent
- busca unificada: True

## Evidência local

- módulo: src/nanojuris/providers/bnp_pangea.py
- dossier: docs/providers/bnp_pangea/README.md
- source contract: docs/source-contracts/bnp_pangea.md
- readiness documental: implementation_ready
- itens documentais abertos: 0
- fixture evidence: versioned_fixture
- completion status: ready_for_review
- completion phase: review
- disposition: accepted_with_limitations
- review after: not scheduled
- resume when: rerun the promotion manifest after any contract, parser, or schema change

### Testes

- tests/test_bnp_pangea.py
- tests/test_bnp_pangea_live.py
- tests/test_client_exporters.py

### Fixtures

- bnp_precedentes_empty.json
- bnp_precedentes_invalid.json
- bnp_precedentes_species.json

## Evidência live versionada

- status: valid
- data: 2026-09-09
- esta fotografia não prova disponibilidade atual ou permanente

## Lacunas consolidadas

- unified:live_status_query_contract_rejected
- known_defects_open

## Defeitos conhecidos

- gap:O endpoint /precedentes passou a exigir 'orgaos' e 'tipos' nao vazios; o provider preenche ambos com o catalogo completo quando ausentes.
- gap:Documentar payload completo de filtros e agregacoes.
- gap:Cobrir heuristica de sugestoes/catalogo para consultas curtas.

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
