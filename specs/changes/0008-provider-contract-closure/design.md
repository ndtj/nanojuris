# Design — ledger de fechamento de TODOs

## Ledger

O sweep continua sendo a fonte de observação. Um ledger complementar consolida cada TODO com:

- `source` e texto original;
- `status`: `closed`, `implemented_with_local_evidence`, `blocked_external`, `candidate_pending_adapter` ou `needs_new_evidence`;
- `evidence`: contrato, módulo, fixture, teste, trace live ou motivo externo;
- `next_action`: ação concreta para reabrir o item;
- `verified_at` e versão do discovery.

## Promoção

Providers runtime podem receber adapter/parser quando o contrato existente for suficiente e os testes preservarem sucesso, vazio, erro, acesso e completude. Candidates continuam fora do runtime até passarem pelo mesmo gate.

## Estados externos

Robots, CAPTCHA, WAF, login, rate limit, TLS, timeout e indisponibilidade serão registrados como `blocked_external` quando reproduzidos ou documentados. Esse estado não reduz a qualidade do dado para zero nem autoriza bypass.
