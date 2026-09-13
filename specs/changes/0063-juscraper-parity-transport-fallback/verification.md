# Verificação

Status: verified

## Resultados

- Testes focados TJCE/TJPE/TJTO/TJSP e retry: 77 aprovados.
- Suíte completa final: 1007 aprovados e 12 skips condicionais (somente testes
  live opt-in e uma dependência opcional ausente).
- Gates finais: Ruff, formatação, mypy, compileall, `validate_sdd.py` e
  `git diff --check` aprovados.
- Nenhum corpo, cookie, ViewState, token ou credencial foi persistido.

## Rechecagem live bounded (2026-09-01)

- TJCE/CJSG: `blocked_access`, HTTP 200 com sinais de CAPTCHA/controle.
- TJPE REST: `blocked_transport` por `SSLCertVerificationError` com
  `verify_ssl=True`; TJPE JSF `auto`: HTTP 200 com marcador explícito de zero.
- TJTO: HTTP 200, um registro real e total remoto 147796.
- TJSP/CJSG: `blocked_access`, HTTP 200 com sinais de CAPTCHA/controle.
- Evidência sanitizada: `docs/provider-discovery/juscraper-parity-live-recheck-20260901.json`.

## Rastreabilidade

- REQ-001: `TjceTlsAdapter` e teste de montagem da sessão.
- REQ-002/003: transporte JSF TJPE, ViewState, escolha e paginação AJAX.
- REQ-004: `request_with_retries` e testes dos status transitórios.
- REQ-005: hashes/status/URL em `SourceTrace` e campos brutos preservados.
- REQ-006 a REQ-008: testes de compatibilidade, fixtures sanitizadas e escopo
  sem publicação.

## Evidências executadas

- testes unitários isolados sem rede para cada sequência HTTP;
- Ruff, formatação, mypy, compileall, `validate_sdd.py` e diff-check;
- chamadas live públicas limitadas, com classificação de bloqueio e sem
  persistência de corpos.

## Restrições

O pacote não autoriza deploy, publicação no PyPI, push ou alteração de
produção. Bloqueios externos permanecem documentados como bloqueios.
