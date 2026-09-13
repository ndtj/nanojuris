# Work pack — TCE-SP Jurisprudencia

Source ID: tce_sp_jurisprudencia
Lifecycle: runtime
Coverage role: administrative_context
Maturity: context
Target: context_verified
Priority: P3

## Contrato observado

- busca textual: True
- filtros: text, types
- paginação: local_window
- completude: unknown
- inteiro teor: unknown
- registros canônicos: CanonicalPrecedent, CanonicalDocument
- busca unificada: False

## Evidência local

- módulo: src/nanojuris/providers/tce_sp_jurisprudencia.py
- dossier: docs/providers/tce_sp_jurisprudencia/README.md
- source contract: docs/source-contracts/tce_sp_jurisprudencia.md
- readiness documental: implementation_ready
- itens documentais abertos: 0
- fixture evidence: versioned_and_inline
- completion status: waiting_evidence
- completion phase: review
- disposition: deferred_with_review
- review after: 2026-10-12
- resume when: close the quality gate and rerun the promotion manifest

### Testes

- tests/test_tce_sp_jurisprudencia.py

### Fixtures

- tce_sp_boletins.html
- tce_sp_indice.html
- tce_sp_sumulas.html

## Evidência live versionada

- status: valid
- data: 2026-09-06
- esta fotografia não prova disponibilidade atual ou permanente

## Lacunas consolidadas

- not_in_unified_search
- maturity:fora da busca unificada
- maturity:risco operacional alto
- unified:excluded_from_unified_search
- full_text_contract_unknown
- known_defects_open

## Defeitos conhecidos

- gap:Mapear indisponibilidade, hash e tamanho de inteiro teor.

## Tarefas obrigatórias

Checklist WP marca que cada item foi avaliado nesta rodada; não
substitui evidência ausente nem converte limitação em sucesso.

- [x] WP-01 — reconciliar capability, dossier, source contract, módulo e interfaces — outcome: deferred_with_review; processed; resume condition: close the quality gate and rerun the promotion manifest
- [x] WP-02 — fechar todos os itens documentais objetivos — outcome: deferred_with_review; processed; resume condition: close the quality gate and rerun the promotion manifest
- [x] WP-03 — garantir fixtures versionadas de sucesso, vazio e falhas críticas — outcome: deferred_with_review; processed; resume condition: close the quality gate and rerun the promotion manifest
- [x] WP-04 — provar identidade, canonicalização, deduplicação, raw e traces — outcome: deferred_with_review; processed; resume condition: close the quality gate and rerun the promotion manifest
- [x] WP-05 — provar filtros, paginação, ordenação, limites e completude — outcome: deferred_with_review; processed; resume condition: close the quality gate and rerun the promotion manifest
- [x] WP-06 — provar estados de acesso, timeout, rate limit e schema drift — outcome: deferred_with_review; processed; resume condition: close the quality gate and rerun the promotion manifest
- [x] WP-07 — provar referência e inteiro teor quando declarados — outcome: deferred_with_review; processed; resume condition: close the quality gate and rerun the promotion manifest
- [x] WP-08 — executar testes locais, tipos, lint e auditorias geradas — outcome: deferred_with_review; processed; resume condition: close the quality gate and rerun the promotion manifest
- [x] WP-09 — executar canário live bounded somente quando autorizado — outcome: deferred_with_review; processed; resume condition: close the quality gate and rerun the promotion manifest
- [x] WP-10 — registrar scorecard, risco residual e decisão de tier — outcome: deferred_with_review; processed; resume condition: close the quality gate and rerun the promotion manifest

## Próximas ações sugeridas

- validar inteiro teor com hash, tamanho e access_status
- classificar WAF, captcha, timeout e mudanca de contrato separadamente

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
