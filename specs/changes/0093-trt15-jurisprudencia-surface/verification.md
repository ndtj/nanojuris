# Verificação — TRT15

## Resultados

- implementação local concluída para catálogo, payload, parser, detalhe e
  estados de erro;
- chamada live bounded em 2026-09-08: entrada/configuração/opções HTTP 200;
  busca HTTP 200 com `sucesso=3`, classificada como `access_blocked`;
- federação permanece desabilitada.

## Fluxo autorizado local

`search_authorized` foi adicionado para aceitar um `captcha_response` obtido
pela pessoa usuaria na UI oficial. O token e usado em uma unica chamada, nao e
gerado, resolvido, persistido ou reproduzido; os campos sao redigidos no trace
e o POST nao e cacheavel. As fixtures e testes cobrem resultado, token ausente
e redacao. Isso nao fecha T006 nem habilita a federacao sem evidencia live.

## Revalidacao bounded do catalogo

Em 2026-09-11, `GET /backend/listarOpcoes` respondeu HTTP 200 com 44 orgaos e
242 relatores. A evidencia sanitizada esta em
`docs/provider-discovery/trt15-jurisprudencia-options-live-20260911.json`.
Isso confirma somente o catalogo publico; a pesquisa continua protegida por
CAPTCHA e T006 permanece externo.

## Comandos

```powershell
$env:PYTHONPATH='src'
python -m pytest -q tests/test_trt15_jurisprudencia.py
python -m ruff check src/nanojuris/providers/trt15_jurisprudencia.py tests/test_trt15_jurisprudencia.py
python -m ruff format --check src/nanojuris/providers/trt15_jurisprudencia.py tests/test_trt15_jurisprudencia.py
python -m mypy src/nanojuris/providers/trt15_jurisprudencia.py
```

Evidência live redigida: `docs/provider-discovery/trt15-jurisprudencia-live-20260908.json`.

## Limitação

T006 continua externo: não existe resultado autorizado reproduzível enquanto a
fonte exigir desafio. Nenhum bypass foi tentado.
## Rastreabilidade

| Requisito | Tarefa | Evidência |
| --- | --- | --- |
| REQ-093-001 | T001-T002 | Rotas e contrato registrados no dossiê e no provider |
| REQ-093-002 | T003 | Catálogo público e resposta CAPTCHA preservados |
| REQ-093-003 | T004-T005 | Parser, estados externos e fixtures versionadas |
| REQ-093-004 | T006 | Pendente: resultado autorizado reproduzível pela fonte |
