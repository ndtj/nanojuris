# Work pack — STF Jurisprudencia

Source ID: stf_juris
Lifecycle: runtime
Coverage role: specialized_context
Maturity: blocked
Target: context_verified
Priority: P3

## Contrato observado

- busca textual: True
- filtros: text, number, all_words, any_words, without_words, published_from, published_to, updated_from, updated_to, order_by
- paginação: offset
- completude: unknown
- inteiro teor: unknown
- registros canônicos: CanonicalDecision
- busca unificada: False

## Evidência local

- módulo: src/nanojuris/providers/stf_juris.py
- dossier: docs/providers/stf_juris/README.md
- source contract: docs/source-contracts/stf_juris.md
- readiness documental: needs_deepening
- itens documentais abertos: 3
- fixture evidence: versioned_fixture
- completion status: waiting_evidence
- completion phase: review
- disposition: deferred_with_review
- review after: 2026-10-12
- resume when: reexecute a bounded request after the official transport/TLS path is healthy

### Testes

- tests/test_stf_juris.py
- tests/test_stf_juris_live_recheck.py

### Fixtures

- stf_juris_empty.json
- stf_juris_infanticidio.json
- stf_juris_waf.html

## Evidência live versionada

- status: blocked_transport
- data: 2026-09-01
- esta fotografia não prova disponibilidade atual ou permanente

## Lacunas consolidadas

- documentation_open_items:3
- not_in_unified_search
- live_status:blocked_transport
- maturity:fora da busca unificada
- maturity:risco operacional alto
- maturity:dossie com pendencias abertas
- unified:excluded_from_unified_search
- unified:live_status_source_unavailable
- known_defects_open
- external_block_recorded

## Defeitos conhecidos

- documentacao_com_pendencias_abertas
- live:blocked_transport
- gap:Separar AWS WAF challenge, falha SSL local e ausencia de resultados.
- gap:Validar bases adicionais do frontend: decisoes, sumulas, informativos e noticias.
- gap:Promover inteiro teor do portal STF somente quando responder sem 403 em sessao limpa.

## Tarefas obrigatórias

Checklist WP marca que cada item foi avaliado nesta rodada; não
substitui evidência ausente nem converte limitação em sucesso.

- [x] WP-01 — reconciliar capability, dossier, source contract, módulo e interfaces — outcome: deferred_with_review; processed; resume condition: reexecute a bounded request after the official transport/TLS path is healthy
- [x] WP-02 — fechar todos os itens documentais objetivos — outcome: deferred_with_review; processed; resume condition: reexecute a bounded request after the official transport/TLS path is healthy
- [x] WP-03 — garantir fixtures versionadas de sucesso, vazio e falhas críticas — outcome: deferred_with_review; processed; resume condition: reexecute a bounded request after the official transport/TLS path is healthy
- [x] WP-04 — provar identidade, canonicalização, deduplicação, raw e traces — outcome: deferred_with_review; processed; resume condition: reexecute a bounded request after the official transport/TLS path is healthy
- [x] WP-05 — provar filtros, paginação, ordenação, limites e completude — outcome: deferred_with_review; processed; resume condition: reexecute a bounded request after the official transport/TLS path is healthy
- [x] WP-06 — provar estados de acesso, timeout, rate limit e schema drift — outcome: deferred_with_review; processed; resume condition: reexecute a bounded request after the official transport/TLS path is healthy
- [x] WP-07 — provar referência e inteiro teor quando declarados — outcome: deferred_with_review; processed; resume condition: reexecute a bounded request after the official transport/TLS path is healthy
- [x] WP-08 — executar testes locais, tipos, lint e auditorias geradas — outcome: deferred_with_review; processed; resume condition: reexecute a bounded request after the official transport/TLS path is healthy
- [x] WP-09 — executar canário live bounded somente quando autorizado — outcome: deferred_with_review; processed; resume condition: reexecute a bounded request after the official transport/TLS path is healthy
- [x] WP-10 — registrar scorecard, risco residual e decisão de tier — outcome: deferred_with_review; processed; resume condition: reexecute a bounded request after the official transport/TLS path is healthy

## Próximas ações sugeridas

- fechar checklist objetivo do dossie
- classificar WAF, captcha, timeout e mudanca de contrato separadamente
- revalidar somente após alteração autorizada da política pública/robots
- não submeter payload especulativo; revalidar por replay/contrato aprovado
- expandir estados somente se o contrato da fonte mudar
- manter fixture live/replay quando a fonte mudar

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
