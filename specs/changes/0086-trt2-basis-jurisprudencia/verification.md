# Verification

## Resultados

## Local

- `python -m pytest -q tests/test_trt2_basis_jurisprudencia.py` — 3 passed.
- Ruff no adapter, configuração, cliente e testes — pass.

## Live

O contrato foi confirmado com chamadas HTTPS bounded ao host oficial
`basis.trt2.jus.br`, usando `/discover` no escopo `123456789/16181`. A evidência
sanitizada fica em `docs/provider-discovery/trt2-basis-live-20260907.json`.

## Limitação

O provider cobre boletins oficiais selecionados. O PJe geral permanece uma
superfície separada e não é promovido por esta implementação.

## Rastreabilidade

| Critério | Evidência |
| --- | --- |
| AC-001/AC-002 | `tests/test_trt2_basis_jurisprudencia.py`, fixture curada |
| AC-003/AC-004 | testes de exceções e contrato do adapter |
| AC-005 | allowlist HTTPS e transporte compartilhado em `trt2_basis_jurisprudencia.py` |
| AC-006 | `docs/provider-discovery/trt2-basis-live-20260907.json` e testes locais |
