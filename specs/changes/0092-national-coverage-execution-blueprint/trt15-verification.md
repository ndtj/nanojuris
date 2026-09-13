# Verificação TRT15

## Evidência live

`docs/provider-discovery/trt15-jurisprudencia-live-20260908.json` registra:

- entrada HTML HTTP 200;
- configuração pública HTTP 200;
- catálogo público com 44 órgãos e 242 relatores;
- pesquisa POST bounded HTTP 200 com `sucesso=3`;
- classificação `access_blocked`, sem corpo persistido e sem bypass.

## Testes locais

```powershell
$env:PYTHONPATH='src'
python -m pytest -q tests/test_trt15_jurisprudencia.py
python -m ruff check src/nanojuris/providers/trt15_jurisprudencia.py tests/test_trt15_jurisprudencia.py
python -m ruff format --check src/nanojuris/providers/trt15_jurisprudencia.py tests/test_trt15_jurisprudencia.py
python -m mypy src/nanojuris/providers/trt15_jurisprudencia.py
```

O gate live de resultados permanece pendente por bloqueio externo. O provider
não é elegível para federação padrão.
