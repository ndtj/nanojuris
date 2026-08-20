# Especificação da auditoria offline de providers

ID: `0004-offline-provider-audit`
Status: `accepted`
Owner: `NanoJuris engineering`
Data: `2026-08-20`

## Objetivo

Auditar providers mapeados, mas ainda não implementados, cruzando catálogo,
dossiers, contratos, módulos, testes e fixtures. Executar a descoberta somente
em evidências locais e produzir uma fila de promoção verificável.

## Requisitos

- RF-001: ler o catálogo gerado sem editá-lo.
- RF-002: conferir a existência de módulo, dossier canônico, contrato legado e
  referências de teste por `source_id`.
- RF-003: classificar candidates sem módulo como não implementados e não
  registrá-los no runtime.
- RF-004: executar extração de rotas, probe sem rede e sugestões de seletores em
  fixtures locais disponíveis.
- RF-005: diferenciar `no_local_fixture` de `empty` e de falha de acesso.
- RF-006: gerar JSON e Markdown com bloqueadores, evidências e próxima ação.

## Critérios de aceite

- AC-001: a auditoria processa as entradas do catálogo sem consulta externa.
- AC-002: os nove candidates mapeados aparecem como sem módulo runtime.
- AC-003: a família eproc é identificada com evidência de módulo, teste e
  fixtures locais.
- AC-004: candidates sem fixture recebem `no_local_fixture`, nunca `empty`.
- AC-005: fixtures locais produzem métricas de rotas e seletores.
- AC-006: nenhum provider é promovido ou catálogo gerado é editado pelo
  relatório.
- AC-007: os resultados são rastreáveis no JSON, no Markdown e nos testes.
