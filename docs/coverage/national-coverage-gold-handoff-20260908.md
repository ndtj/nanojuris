# Handoff de cobertura nacional ouro — 2026-09-08

Este é o índice curto para outro modelo retomar a execução sem ler o histórico.
O pacote normativo completo está em
[`specs/changes/0091-national-coverage-gold-handoff/`](../../specs/changes/0091-national-coverage-gold-handoff/).

Para uma visão executável consolidada, incluindo o protocolo de filtros,
inteiro teor, ondas e acesso público legítimo, use também
[`national-coverage-model-handoff-20260908.md`](national-coverage-model-handoff-20260908.md)
e seu manifesto JSON correspondente.

## Começo rápido

1. Ler `AGENTS.md`, Constituição, README de SDD e este pacote.
2. Executar o baseline do `model-runbook.md` com `PYTHONPATH=src`.
3. Escolher 1–3 providers do `provider-batch-plan.json`.
4. Trabalhar somente com fontes públicas e bounded.
5. Fechar contrato, fixtures, live, qualidade e federação antes de promover.
6. Regenerar inventários e preencher `verification.md`.

## Artefatos

| Artefato | Uso |
| --- | --- |
| `GOAT_EXECUTOR_PROMPT.md` | prompt autônomo completo |
| `execution-manifest.json` | ondas, fontes de verdade e parada |
| `provider-batch-plan.json` | ordem de lotes estaduais |
| `surface-register.template.json` | registro canônico por superfície |
| `provider-workpack-template.md` | contrato e evidência por provider |
| `lawful-access-decision-matrix.md` | limites de acesso permitidos |
| `model-runbook.md` | comandos e ciclo operacional |
| `baseline-20260908.json` | referência histórica, não prova de conclusão |
| `docs/coverage/0091-local-gates-20260908.json` | auditoria offline dos gates locais |

## Limite legal/técnico

CAPTCHA, Turnstile, WAF, login, 403, 429, TLS e schema drift são estados
observáveis, nunca vazio. Não há solver, OCR de desafio, stealth, spoofing,
rotação de IP, replay de tokens, TLS downgrade, fuzzing privado ou “zona de
sombra”. Alternativas legítimas são export/API oficial, rota pública alternativa,
allowlist, documentação do tribunal ou intervenção humana autorizada.

O pacote não autoriza commit, push, publicação, deploy, Terraform, OCI ou
alteração de produção.
