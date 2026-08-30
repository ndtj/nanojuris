# Verificação

Status: `verified_local`

## Comandos e resultados

| Execução | Comando | Resultado |
|---|---|---|
| local | `pytest -q tests/test_collection.py tests/test_identity.py` | passed — 12 testes |
| local | `pytest -q tests/test_identity.py tests/test_collection.py tests/test_client_exporters.py tests/test_studio.py tests/test_mcp_tools.py tests/test_mcp_server.py tests/test_audit_regressions.py` | passed — 110 testes |
| local | `ruff check src tests tools` | passed |
| local | `git diff --check` | passed |
| local | `PYTHONPATH=. pytest -q` | passed — 785 testes, 8 skips, 1 aviso de depreciação existente |
| local | `python tools/validate_sdd.py` | passed — SDD validation passed |

## Evidência funcional

O runner preserva registros válidos em lotes mistos, conta cada item inválido,
registra posição/tipo/identidade limitada da falha e não marca páginas totalmente
inválidas como completas. A identidade compartilhada evita colisões de números
locais e mantém CNJ formatado determinístico quando não há ID de provider. O
envelope `source_outcomes` fornece exatamente um estado observável por fonte.

## Limitações e riscos residuais

- A validação acima é local e baseada em fixtures; não substitui uma execução
  live bounded dos providers.
- Providers com CAPTCHA, WAF, TLS, controle de acesso ou mudança de parser devem
  continuar classificados como falha explícita.
- A nova política pode aumentar contagens federadas ao preservar números locais
  iguais de fontes distintas; consumidores que dependiam da colisão incorreta
  devem revisar suas expectativas.
- Nenhum deploy ou publicação foi executado nesta mudança.

## Backlog identificado na revisão sênior

- aplicar o mesmo isolamento por registro ao `search_many` federado;
- centralizar sanitização e limite de mensagens de exceção de providers;
- definir formalmente se `ResearchRun.record_count` mede entradas recebidas ou
  registros persistidos após deduplicação;
- repetir cobertura live bounded dos providers em janela operacional autorizada.

## Rastreabilidade

| Requisito | Critério | Evidência |
|---|---|---|
| REQ-001 | AC-001 | `tests/test_collection.py` — lote misto, página inválida e limite |
| REQ-002 | AC-002/AC-003 | `tests/test_identity.py` |
| REQ-003 | AC-005 | `tests/test_client_exporters.py` — `source_outcomes` |
| REQ-004 | AC-005 | falhas limitadas e preservação no payload/Studio/MCP |
| REQ-005 | AC-004 | suíte completa, Ruff e diff check |
