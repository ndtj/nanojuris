# Work pack — SJUR/TRE jurisprudencia de primeiro grau (família opt-in)

Source ID: tre_sjur_first_degree
Lifecycle: runtime
Coverage role: curated_context
Maturity: context
Target: context_verified
Priority: P3

## Contrato observado

- busca textual: True
- filtros: text, exact_phrase, number, all_words, any_words, without_words, authority, branch, degree, instance, collection, types, document_type, decision_type, case_class, rapporteur, party_name, judgment_date_from, judgment_date_to, published_from, published_to, election_year, observations, tags, municipality, publication_source, publication_number, publication_volume, uf
- paginação: none
- completude: unknown
- inteiro teor: unknown
- registros canônicos: JurisprudenceResult
- busca unificada: False

## Evidência local

- módulo: src/nanojuris/providers/tre_sjur_first_degree.py
- dossier: docs/providers/tre_sjur_first_degree/README.md
- source contract: docs/source-contracts/tre_sjur_first_degree.md
- readiness documental: needs_deepening
- itens documentais abertos: 3
- fixture evidence: versioned_fixture
- completion status: waiting_evidence
- completion phase: review
- disposition: deferred_with_review
- review after: 2026-10-12
- resume when: add sanitized versioned success, explicit-empty, and failure/schema fixtures

### Testes

- tests/test_tre_sjur_first_degree_probe.py
- tests/test_tre_sjur_jurisprudencia.py

### Fixtures

- tre_sjur_first_degree_success.json

## Evidência live versionada

- status: valid
- data: 2026-09-12
- esta fotografia não prova disponibilidade atual ou permanente

## Lacunas consolidadas

- documentation_open_items:3
- not_in_unified_search
- maturity:fora da busca unificada
- maturity:dossie com pendencias abertas
- full_text_contract_unknown
- known_defects_open

## Defeitos conhecidos

- documentacao_com_pendencias_abertas
- gap:Registrar como a fonte representa filtros, classes e tipos sem catalogo formal.
- gap:Mapear indisponibilidade, hash e tamanho de inteiro teor.

## Tarefas obrigatórias

Checklist WP marca que cada item foi avaliado nesta rodada; não
substitui evidência ausente nem converte limitação em sucesso.

- [x] WP-01 — reconciliar capability, dossier, source contract, módulo e interfaces — outcome: deferred_with_review; processed; resume condition: add sanitized versioned success, explicit-empty, and failure/schema fixtures
- [x] WP-02 — fechar todos os itens documentais objetivos — outcome: deferred_with_review; processed; resume condition: add sanitized versioned success, explicit-empty, and failure/schema fixtures
- [x] WP-03 — garantir fixtures versionadas de sucesso, vazio e falhas críticas — outcome: deferred_with_review; processed; resume condition: add sanitized versioned success, explicit-empty, and failure/schema fixtures
- [x] WP-04 — provar identidade, canonicalização, deduplicação, raw e traces — outcome: deferred_with_review; processed; resume condition: add sanitized versioned success, explicit-empty, and failure/schema fixtures
- [x] WP-05 — provar filtros, paginação, ordenação, limites e completude — outcome: deferred_with_review; processed; resume condition: add sanitized versioned success, explicit-empty, and failure/schema fixtures
- [x] WP-06 — provar estados de acesso, timeout, rate limit e schema drift — outcome: deferred_with_review; processed; resume condition: add sanitized versioned success, explicit-empty, and failure/schema fixtures
- [x] WP-07 — provar referência e inteiro teor quando declarados — outcome: deferred_with_review; processed; resume condition: add sanitized versioned success, explicit-empty, and failure/schema fixtures
- [x] WP-08 — executar testes locais, tipos, lint e auditorias geradas — outcome: deferred_with_review; processed; resume condition: add sanitized versioned success, explicit-empty, and failure/schema fixtures
- [x] WP-09 — executar canário live bounded somente quando autorizado — outcome: deferred_with_review; processed; resume condition: add sanitized versioned success, explicit-empty, and failure/schema fixtures
- [x] WP-10 — registrar scorecard, risco residual e decisão de tier — outcome: deferred_with_review; processed; resume condition: add sanitized versioned success, explicit-empty, and failure/schema fixtures

## Próximas ações sugeridas

- fechar checklist objetivo do dossie
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
