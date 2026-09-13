# Blueprint de cobertura nacional

Este diretório é uma porta de entrada curta para o SDD
[`0092-national-coverage-execution-blueprint`](../../../specs/changes/0092-national-coverage-execution-blueprint/README.md).

O SDD contém o plano normativo, os templates, a matriz de acesso lícito e o
prompt para outro modelo. Os números operacionais devem ser lidos dos
inventários gerados, especialmente:

- `docs/registry/provider-catalog.full.json`;
- `docs/coverage/provider-capability-ledger.json`;
- `docs/coverage/surface-state-registry-20260902.json`;
- `docs/coverage/open-task-audit-20260907.json`;
- `specs/changes/0091-national-coverage-gold-handoff/baseline-20260908.json`.

Nenhum arquivo deste diretório declara que a cobertura nacional terminou. Ele
apenas organiza o trabalho restante e seus gates.

## Métricas de encerramento

Para cada superfície, exigir simultaneamente: fonte oficial, contrato de grau,
runtime, fixtures, filtros/paginação, chamada live, qualidade canônica e
federação. A ausência de qualquer item mantém a superfície incompleta.

## Fronteira operacional

Use somente acesso público normal, API/export oficial, sessão própria,
paginação publicada, retry cooperativo e apoio institucional. CAPTCHA, WAF,
Turnstile, login, 403, 429, TLS e timeout são estados observáveis; nunca são
convertidos em vazio.
