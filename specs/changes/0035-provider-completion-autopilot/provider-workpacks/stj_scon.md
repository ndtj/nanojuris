# Work pack — STJ SCON Acordaos

Source ID: stj_scon
Lifecycle: runtime
Coverage role: specialized_context
Maturity: blocked
Target: context_verified
Priority: P3

## Contrato observado

- busca textual: True
- filtros: text, number
- paginação: page
- completude: unknown
- inteiro teor: unknown
- registros canônicos: CanonicalDecision, CanonicalDocument
- busca unificada: False

## Evidência local

- módulo: src/nanojuris/providers/stj_scon.py
- dossier: docs/providers/stj_scon/README.md
- source contract: docs/source-contracts/stj_scon.md
- readiness documental: implementation_ready
- itens documentais abertos: 0
- fixture evidence: versioned_and_inline
- completion status: waiting_evidence
- completion phase: review
- disposition: deferred_with_review
- review after: 2026-10-12
- resume when: reexecute a bounded public request after the source removes access control

### Testes

- tests/test_stf_juris.py
- tests/test_stj_scon.py

### Fixtures

- stj_scon_access_control.html
- stj_scon_acordaos_result.html
- stj_scon_empty.html
- stj_scon_real_documentos.html

## Evidência live versionada

- status: access_control_required
- data: 2026-09-07
- esta fotografia não prova disponibilidade atual ou permanente

## Lacunas consolidadas

- not_in_unified_search
- live_status:access_control_required
- maturity:fora da busca unificada
- maturity:risco operacional alto
- unified:excluded_from_unified_search
- full_text_contract_unknown
- known_defects_open
- external_block_recorded

## Defeitos conhecidos

- live:access_control_required
- gap:Separar acesso bloqueado por verificacao automatica de ausencia de resultados.
- gap:Validar URL publica de inteiro teor em sessao limpa sem cookies.
- gap:Promover fixtures de monocraticas, sumulas e informativos.

## Tarefas obrigatórias

Checklist WP marca que cada item foi avaliado nesta rodada; não
substitui evidência ausente nem converte limitação em sucesso.

- [x] WP-01 — reconciliar capability, dossier, source contract, módulo e interfaces — outcome: deferred_with_review; processed; resume condition: reexecute a bounded public request after the source removes access control
- [x] WP-02 — fechar todos os itens documentais objetivos — outcome: deferred_with_review; processed; resume condition: reexecute a bounded public request after the source removes access control
- [x] WP-03 — garantir fixtures versionadas de sucesso, vazio e falhas críticas — outcome: deferred_with_review; processed; resume condition: reexecute a bounded public request after the source removes access control
- [x] WP-04 — provar identidade, canonicalização, deduplicação, raw e traces — outcome: deferred_with_review; processed; resume condition: reexecute a bounded public request after the source removes access control
- [x] WP-05 — provar filtros, paginação, ordenação, limites e completude — outcome: deferred_with_review; processed; resume condition: reexecute a bounded public request after the source removes access control
- [x] WP-06 — provar estados de acesso, timeout, rate limit e schema drift — outcome: deferred_with_review; processed; resume condition: reexecute a bounded public request after the source removes access control
- [x] WP-07 — provar referência e inteiro teor quando declarados — outcome: deferred_with_review; processed; resume condition: reexecute a bounded public request after the source removes access control
- [x] WP-08 — executar testes locais, tipos, lint e auditorias geradas — outcome: deferred_with_review; processed; resume condition: reexecute a bounded public request after the source removes access control
- [x] WP-09 — executar canário live bounded somente quando autorizado — outcome: deferred_with_review; processed; resume condition: reexecute a bounded public request after the source removes access control
- [x] WP-10 — registrar scorecard, risco residual e decisão de tier — outcome: deferred_with_review; processed; resume condition: reexecute a bounded public request after the source removes access control

## Próximas ações sugeridas

- validar inteiro teor com hash, tamanho e access_status
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
