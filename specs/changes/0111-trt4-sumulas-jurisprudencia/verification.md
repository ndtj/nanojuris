# Verification — SDD 0111

- Live: `GET https://www.trt4.jus.br/portais/trt4/sumulas`, HTTP 200, HTML,
  489802 bytes, SHA-256 `47bf7acffa66402a1af5ddd3aad7c4cfbd18175f2da6d4cc5936bae978a9d7e9`.
- Replay: consulta bounded `responsabilidade`, 5 registros, `degree=second`,
  `branch=labor`, `authority=TRT4`.
- Documento: PDF oficial TRT4, HTTP 200, 69827 bytes, uma página,
  `application/pdf`, extração completa, SHA-256
  `92e006b79578e94e4e1f690ab408f5efb47b5636793c5ce7ee596e5a7da1df10`.
- Testes focados: `python -m pytest -q tests/test_trt4_sumulas_jurisprudencia.py` — 6 passed.
- Segurança: requisições públicas bounded; sem credenciais, CAPTCHA bypass,
  WAF bypass ou persistência do corpo bruto.
- Decisão: fonte contextual/opt-in; não entra na federação padrão.

## Resultados

Os resultados acima demonstram página pública reproduzível, cinco registros
filtrados e um documento oficial PDF validado. A coleção não representa o
corpus geral TRT4 e permanece fora do rollout padrão.

## Rastreabilidade

- Implementação: `src/nanojuris/providers/trt4_sumulas_jurisprudencia.py`.
- Fixture/teste: `tests/fixtures/trt4_sumulas_success.html` e
  `tests/test_trt4_sumulas_jurisprudencia.py`.
- Evidência: `docs/provider-discovery/trt4-sumulas-live-20260910.json`.
- Contrato/capability: catálogo gerado por `build_provider_coverage.py`.
