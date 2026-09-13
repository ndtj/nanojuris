# Verificação

Status: verified_with_limitations — runtime compartilhado implementado e
validado; adapters que ainda usam a camada de compatibilidade permanecem em
migração incremental sem alterar o contrato público.

## Resultados

| Gate | Estado | Evidência |
| --- | --- | --- |
| segurança de transporte | passed (discovery) | `tests/test_discovery_http.py` (SSRF, redirect, limite de bytes e TLS) |
| resiliência | passed (retry) | `tests/test_http_retry.py` (Retry-After, idempotência, jitter e exceção) |
| isolamento federado | passed | suíte federada offline existente |
| regressão | passed local | `python -m pytest -q` — sem chamadas live |
| cliente compartilhado | passed | `tests/test_transport_runtime.py`; TJES/TJTO/TJRN usam `SharedHttpClient` |
| cache/circuito | passed | round-trip atômico, isolamento por operação e estados de circuito |
| gates locais | passed | Ruff, mypy e testes focados; suíte completa após sincronização |

## Rastreabilidade

REQ-001 a REQ-007 possuem evidência local no módulo `nanojuris.transport` e
nos adapters migrados. A compatibilidade de sessão mantém as mesmas políticas
para os providers restantes; a migração interna adicional é uma otimização,
não um bloqueio de funcionamento. Chamadas live e produção não fazem parte da
verificação padrão deste pacote.
