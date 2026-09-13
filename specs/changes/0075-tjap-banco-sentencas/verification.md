# Verification

## Resultados

- `python -m pytest -q tests/test_tjap_banco_sentencas.py` — 7 passed.
- Ruff passou no adapter e nos testes.
- Chamada live bounded 2026-09-07: GET `/` e POST Livewire `update-filters`
  retornaram HTTP 200; páginas 1 e 2 tiveram 3 registros cada, todos com
  unidade de primeiro grau e IDs distintos. Evidência:
  `docs/provider-discovery/tjap-banco-sentencas-live-20260907.json`.
- Uma tentativa de transporte excedida foi classificada como timeout
  transitório, sem conversão para vazio.
- Nenhum CAPTCHA, token de desafio, credencial, bypass, commit, push ou deploy
  foi executado.

## Rastreabilidade

| Requisito | Evidência |
|---|---|
| REQ-001 | `_initial_component`/`_call` usam somente a rota Livewire pública |
| REQ-002 | `_is_first_degree_unit` e campos `degree/instance/collection` |
| REQ-003 | parser de cartões, reader URL, `raw` e `SourceTrace` |
| REQ-004 | estados explícitos de timeout, acesso e `total_known` |
| REQ-005 | paginação por `gotoPage` e allowlist HTTPS em `get_document` |

## Decisão de promoção

Os oito gates técnicos foram executados. O provider está habilitado na busca
federada como CJPG de primeiro grau, com a limitação explícita de que a fonte é
um banco oficial curado e não prova cobertura integral do acervo. O Tucujuris
CJSG continua `access_controlled` e não é resolvido por esta rota.
