# Verificação

## Resultados

- adapter, configuração, catálogo e cliente adicionados;
- fixtures sanitizadas e oito testes locais aprovados;
- índice oficial respondeu HTTP 200/2.490.134 bytes/259 páginas;
- primeiro documento histórico respondeu HTTP 503 e permaneceu
  `source_unavailable`;
- federação padrão não habilitada.

## Rechecagem bounded 2026-09-08

- O índice oficial respondeu HTTP 200, `application/pdf`, 2.490.134 bytes e
  259 páginas.
- O primeiro documento oficial observado continuou HTTP 503. O estado foi
  mantido como `source_unavailable`; não houve repetição automática,
  persistência de cookies nem tentativa de contornar o bloqueio.
- Evidência redigida: `docs/provider-discovery/tjrj-banco-sentencas-live-20260908.json`.

## Reconciliacao documental 2026-09-08

- `docs/provider-discovery/tjrj-banco-sentencas-live-20260908.json` agora
  declara `source_id`, superficie `cjpg`, `partial`, acesso publico e
  extracao parcial, permitindo que o gerador associe a evidencia ao provider.
- O catalogo registra `live_status=partial`: o indice PDF foi alcancavel, mas
  o documento observado respondeu HTTP 503. Esse estado nao e vazio e nao
  promove a colecao como CJPG integral.
- O README canonico e o contrato legacy contem as secoes de contrato, dados,
  estados, fixtures, MCP e proximos passos e permanecem em paridade byte a
  byte.
- O item T008 continua pendente por exigir decisao humana sobre promocao de
  uma colecao curada; nenhuma aprovacao foi presumida.

## Comandos

```powershell
$env:PYTHONPATH='src'
python -m pytest -q tests/test_tjrj_banco_sentencas.py
python -m ruff check src/nanojuris/providers/tjrj_banco_sentencas.py tests/test_tjrj_banco_sentencas.py
python -m mypy src/nanojuris/providers/tjrj_banco_sentencas.py
```

## Rastreabilidade

| Critério | Evidência |
|---|---|
| AC-001/AC-003 | parser e `tests/test_tjrj_banco_sentencas.py` |
| AC-002/AC-005 | allowlist, estados de acesso e live evidence |
| AC-004 | `fetch_document_reference` e capabilities |
| AC-006 | `supports_unified_search=false`, `opt_in_unified_search=true` |
