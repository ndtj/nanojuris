# Verification

Status: `verified`

## Resultados

- `PYTHONPATH=src python -m pytest -q tests/test_tjsp_cjsg.py tests/test_busca_saj_tjsp.py`: **29 passed**.
- `python -m pytest -q -ra`: **898 passed, 9 skipped**.
- `python -m ruff check src tests examples tools`: passou.
- `python -m ruff format --check src tests examples tools`: passou.
- `python -m mypy src`: passou, sem erros.
- A evidencia live bounded registra a sequencia publica observada: GET do
  formulario, POST de inicializacao, POST da busca e GET de
  `trocaDePagina.do` na mesma sessao.
- O provider segue para `trocaDePagina.do` quando o POST retorna a tela
  intermediaria de controle e levanta `AccessControlRequiredError` somente se
  a resposta final continuar bloqueada.
- `python tools/validate_sdd.py`: passou.
- O fluxo nao resolve CAPTCHA, nao fabrica token e nao persiste credenciais ou
  cookies fora da sessao efemera.

## Rastreabilidade

Os comandos e resultados acima fecham REQ-001 a REQ-005; a disponibilidade live
continua sendo uma observacao limitada no tempo, nao uma garantia permanente.
