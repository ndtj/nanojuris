# Work pack — TRE-SP Temas Selecionados

Source ID: tre_sp_temas
Lifecycle: runtime
Coverage role: curated_context
Maturity: blocked
Target: context_verified
Priority: P3

## Contrato observado

- busca textual: True
- filtros: text, exact_phrase
- paginação: local_window
- completude: unknown
- inteiro teor: unknown
- registros canônicos: CanonicalPrecedent
- busca unificada: False

## Evidência local

- módulo: src/nanojuris/providers/tre_sp_temas.py
- dossier: docs/providers/tre_sp_temas/README.md
- source contract: docs/source-contracts/tre_sp_temas.md
- readiness documental: needs_deepening
- itens documentais abertos: 5
- fixture evidence: versioned_fixture
- completion status: waiting_evidence
- completion phase: review
- disposition: deferred_with_review
- review after: 2026-10-12
- resume when: recheck when the official source is available again

### Testes

- tests/test_tre_sp_temas.py

### Fixtures

- tre_sp_temas_detail.html
- tre_sp_temas_index.html

## Evidência live versionada

- status: source_unavailable
- data: 2026-09-05T08:24:37+00:00
- esta fotografia não prova disponibilidade atual ou permanente

## Lacunas consolidadas

- documentation_open_items:5
- not_in_unified_search
- live_status:source_unavailable
- maturity:fora da busca unificada
- maturity:live status: source_unavailable
- maturity:dossie com pendencias abertas
- unified:excluded_from_unified_search
- unified:live_status_source_unavailable
- full_text_contract_unknown
- known_defects_open
- external_block_recorded

## Defeitos conhecidos

- documentacao_com_pendencias_abertas
- live:source_unavailable
- gap:Mapear indisponibilidade, hash e tamanho de inteiro teor.

## Tarefas obrigatórias

Checklist WP marca que cada item foi avaliado nesta rodada; não
substitui evidência ausente nem converte limitação em sucesso.

- [x] WP-01 — reconciliar capability, dossier, source contract, módulo e interfaces — outcome: deferred_with_review; processed; resume condition: recheck when the official source is available again
- [x] WP-02 — fechar todos os itens documentais objetivos — outcome: deferred_with_review; processed; resume condition: recheck when the official source is available again
- [x] WP-03 — garantir fixtures versionadas de sucesso, vazio e falhas críticas — outcome: deferred_with_review; processed; resume condition: recheck when the official source is available again
- [x] WP-04 — provar identidade, canonicalização, deduplicação, raw e traces — outcome: deferred_with_review; processed; resume condition: recheck when the official source is available again
- [x] WP-05 — provar filtros, paginação, ordenação, limites e completude — outcome: deferred_with_review; processed; resume condition: recheck when the official source is available again
- [x] WP-06 — provar estados de acesso, timeout, rate limit e schema drift — outcome: deferred_with_review; processed; resume condition: recheck when the official source is available again
- [x] WP-07 — provar referência e inteiro teor quando declarados — outcome: deferred_with_review; processed; resume condition: recheck when the official source is available again
- [x] WP-08 — executar testes locais, tipos, lint e auditorias geradas — outcome: deferred_with_review; processed; resume condition: recheck when the official source is available again
- [x] WP-09 — executar canário live bounded somente quando autorizado — outcome: deferred_with_review; processed; resume condition: recheck when the official source is available again
- [x] WP-10 — registrar scorecard, risco residual e decisão de tier — outcome: deferred_with_review; processed; resume condition: recheck when the official source is available again

## Próximas ações sugeridas

- fechar checklist objetivo do dossie
- validar inteiro teor com hash, tamanho e access_status
- usar rota pública alternativa documentada ou aguardar acesso autorizado
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
