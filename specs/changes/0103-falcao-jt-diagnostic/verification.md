# Verification - SDD 0103

## Evidência live

- `docs/provider-discovery/falcao-live-recheck-20260908.json` registra GET
  bounded com HTTP 403 CloudFront e shell intermitente, sem corpo persistido.
- A página oficial do TRT9 confirma o escopo nacional, mas não expõe contrato
  de resultados ou exportação reproduzível.
- Sonda pelo adapter em `2026-09-10` recebeu HTTP 403 e foi classificada como
  `AccessControlRequiredError`; evidência redigida em
  `docs/provider-discovery/falcao-adapter-live-20260910.json`.

## Resultados

- Provider implementado como diagnóstico opt-in; não é roteado pela federação.
- CloudFront, shell e erros de transporte permanecem estados explícitos.
- T006 depende de rota/allowlist oficial e permanece pendente sem bloquear o
  restante do ciclo.

## Rastreabilidade

| Requisito | Evidência |
|---|---|
| REQ-001/AC-004 | `src/nanojuris/providers/falcao_jt.py` e allowlist HTTPS |
| REQ-002/AC-001 | `tests/test_falcao_jt.py::test_cloudfront_is_access_control_not_empty` |
| REQ-003/AC-002 | `tests/test_falcao_jt.py::test_public_shell_without_api_is_contract_change` |
| REQ-004/AC-003 | `tests/test_falcao_jt.py::test_falcao_capabilities_are_opt_in_and_unverified` |

## Incremento autorizado OIDC - 2026-09-11

- `FalcaoJtProvider.search_authorized` envia somente o token Bearer fornecido
  pelo chamador, usando o transporte compartilhado e sem persistir credenciais.
- O parser comum preserva os estados de acesso, total e resultado da rota
  pública; `SourceTrace` e `raw` não contêm o token.
- Testes: `tests/test_falcao_jt.py::test_falcao_authorized_search_uses_ephemeral_oidc_token`
  e `::test_falcao_authorized_search_requires_a_caller_token`.
- O gate externo T006 continua pendente: ainda não há evidência live
  autorizada reproduzível para promoção federada.
