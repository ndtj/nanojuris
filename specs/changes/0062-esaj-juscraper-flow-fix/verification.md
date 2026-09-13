# Verificação

Status: verified

## Resultados (2026-09-02, ciclo 12)

- 61 testes focados nos seis adapters eSAJ: aprovados.
- Suíte completa: 998 aprovados e 12 skips condicionais.
- Ruff, formatação, mypy, compileall, `validate_sdd.py` e `git diff --check`: aprovados.
- Rechecagem live bounded: TJAC (zero legítimo), TJAL, TJAM e TJMS com
  resposta HTTP 200; TJCE `blocked_transport`; TJSP `blocked_access`.
- Artefato: `docs/provider-discovery/esaj-juscraper-flow-live-recheck-20260902-cycle12.json`.
- Nenhum corpo, cookie, token ou desafio foi persistido/contornado.

## Rastreabilidade

- REQ-001 a REQ-004: fluxo eSAJ, paginação, sessão e `conversationId` cobertos
  pelos testes dos seis adapters.
- REQ-005: variante de zero resultados TJAC coberta por fixture e teste.
- REQ-006 a REQ-008: classificação live, documentação e limites de segurança
  registrados no artefato do ciclo 12.

## Evidências planejadas

- testes unitários dos providers eSAJ com fixture sintética de confirmação do
  POST e HTML de resultados;
- suíte completa, Ruff, format, mypy, compileall, validate_sdd e diff-check;
- rechecagem live bounded por provider, com classificação explícita.

## Restrições

Nenhuma produção, publicação ou configuração externa será alterada neste
pacote. Bloqueios externos permanecem bloqueios.
