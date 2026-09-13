# Verification — TSE SJUR

## Evidência disponível

- `POST https://sjur-pesquisa-api.tse.jus.br/tse/sjur-pesquisa-backend/rest/public/pesquisa/simples`
- Consulta exata `codigoDecisao=504401`, TSE, HTTP 200, um registro, total 1.
- Corpo de 4560 bytes, SHA-256
  `cd416d0003842d35f525cfbad85cb71a6fe8d6a8be921c38439d66f541ab9c37`.
- Campos observados: código, processo, classe, tipo, relator, datas, ementa,
  decisão, publicações e `temInteiroTeorPDF`.
- `docs/provider-discovery/tse-sjur-empty-live-20260909.json`: consulta exata
  inexistente, HTTP 200, `totalRegistros=0`, vazio autoritativo.
- `docs/provider-discovery/tse-sjur-document-live-20260909.json`: rota oficial
  `download/pdf/<codigoDecisao>`, HTTP 200 e PDF válido de 57.680 bytes.
- `docs/provider-discovery/tse-sjur-pagination-live-20260909.json`: chamadas
  bounded nas páginas 1, 2 e 3; a fonte devolveu a mesma resposta de 132
  registros e o mesmo hash nas páginas 1 e 2. A capacidade foi registrada como
  `pagination_mode=none`, não como paginação suportada.

## Limitações

A consulta textual pública retornou todos os 132 registros independentemente de
`pagina`/`tamanho`; a paginação remota foi validada como não suportada e o
provider continua sem afirmar completude além da resposta única recebida. A
rota PDF pública foi localizada no bundle oficial e validada para o registro
observado 504401; o adapter só aceita identificadores observados na sessão.
O adapter foi promovido a runtime opt-in e permanece fora da federação padrão
por decisão técnica registrada em T009.

## Verificação local

Executar:

```text
python -m pytest -q tests/test_tse_sjur_jurisprudencia.py
python tools/validate_sdd.py
python -m ruff check src/nanojuris/providers/tse_sjur_jurisprudencia.py tests/test_tse_sjur_jurisprudencia.py
```

## Resultados

Os nove testes do provider passaram. O catálogo foi regenerado com a fonte em
estado `implemented`, `live_status=valid`, runtime opt-in e sem federação
padrão. A suíte nacional passou com 1.650 testes e 26 skips opt-in/ambiente; os gates locais também
passaram.

`T009` -> decisão técnica de promover `runtime`/`federation_status=disabled`;
isso não é aprovação jurídica nem autorização de deploy.

## Rastreabilidade

`REQ-001`/`REQ-002` -> adapter e `test_request_contains_serialized_dsl`;
`REQ-003`/`REQ-004` -> `test_exact_result_maps_fields_and_trace`;
`REQ-005` -> testes de vazio, bloqueio, sintaxe e schema, além da evidência live
de vazio autoritativo;
`REQ-006`/`REQ-007` -> política allowlist, limites e evidência live;
`REQ-008` -> rota PDF oficial, `DocumentReference`, MIME/magic bytes, hash e
limite de tamanho.

`AC-007` -> `test_document_route_is_limited_to_observed_result`.

`T007` -> `docs/provider-discovery/tse-sjur-pagination-live-20260909.json`;
as páginas solicitadas foram comparadas sem contornar controles.

Evidência adicional: `docs/provider-discovery/tse-sjur-empty-live-20260909.json`.
