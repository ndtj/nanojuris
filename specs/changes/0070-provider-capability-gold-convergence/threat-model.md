# Threat model — discovery e documentos de providers

Mudança: `specs/changes/0070-provider-capability-gold-convergence/spec.md`
Responsável: Security e Provider Engineering
Status: `verified_local; residual_review_pending`

## Ativos e limites de confiança

| Ativo | Origem | Classificação | Proteção |
| --- | --- | --- | --- |
| request/response de discovery | portal oficial | público com possíveis dados pessoais | redaction, hash e fixture mínima |
| catálogo de filtros | UI/API oficial | público | evidence ID e timestamp |
| documento jurídico | domínio oficial | público potencialmente hostil | allowlist, limites, quarentena |
| cache documental | runtime local | interno | content-addressed, TTL e limpeza |
| ledger de capacidades | repositório | público | schema, revisão e geração determinística |

## Ameaças e controles

| ID | Ameaça | Impacto | Controle | Evidência esperada |
| --- | --- | --- | --- | --- |
| TH-001 | pressão indevida no portal | alto | consultas bounded, delay, cache e rate limit | métricas por endpoint |
| TH-002 | bypass acidental de acesso | alto | proibir solver, credenciais e relaxamento TLS | testes/ revisão de transporte |
| TH-003 | falso suporte de filtro | alto | teste diferencial e estado `unverified` bloqueante | fixture e comparação |
| TH-004 | falso vazio | alto | contratos de acesso/extraction/total | testes de erro e vazio |
| TH-005 | documento malicioso/zip bomb | alto | MIME, magic bytes, tamanho, compressão e quarentena | testes adversariais |
| TH-006 | SSRF/redirect externo | alto | hosts allowlisted e redirect revalidado | testes de redirect |
| TH-007 | vazamento de dados pessoais | médio | sanitização e mínimo necessário | auditoria de fixtures/logs |
| TH-008 | OCR consumir recurso excessivo | médio | opt-in, timeout, páginas e sandbox | métricas e testes de limite |
| TH-009 | abstração de família corromper semântica | alto | overlays por provider e golden fixtures próprias | testes diferenciais |
| TH-010 | evidência obsoleta manter ouro | alto | TTL, fingerprint e invalidação incremental | teste de freshness |

## Decisão de segurança

- [x] Limites e ameaças estão identificados para planejamento.
- [x] Implementação dos controles verificada.
- [x] Fixtures, logs e cache auditados.
- [ ] Riscos residuais revisados antes de qualquer release.

## Evidência de verificação local - 2026-09-07

The controls are covered by the current test suite and release gates. Access
challenges, rate limits, TLS failures and schema errors remain explicit states;
no bypass mechanism is enabled. Release approval and residual-risk acceptance
remain human decisions and are intentionally not marked complete here.
