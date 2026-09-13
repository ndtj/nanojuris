# Verificacao

Status: verified_with_limitations — intake e equivalência técnica concluídos
para a onda elegível; candidatos restantes aguardam evidência reproduzível.

## Resultados

| Gate | Estado | Evidencia |
| --- | --- | --- |
| snapshot/licenca | pass | `juscraper-intake-20260901.json`, commit e SHA-256 de `LICENSE` |
| cobertura do inventario | pass | 25 TJ, 4 TRF e 4 agregadores enumerados pelo script |
| diff semantico | pass (static) | `juscraper-semantic-diff-20260901.json/.md`; 87 superficies com dimensoes de campos, filtros, paginacao, erros e identidade |
| equivalencia | pass with limits | adapters independentes da onda elegível possuem fixtures/testes; candidatos restantes permanecem adiados |
| smoke live bounded | pass (evidencia) | TJES/TJRN HTTP 200 no snapshot inicial; recheck posterior preserva bloqueio TJRN 403 explicito |
| teste do intake | pass | `tests/test_juriscraper_intake.py` e `tests/test_juscraper_semantic_diff.py` |
| separacao de escopo | pass | CJPG/detalhe separados; CPOPG/CPOSG e agregadores fora do runtime textual |
| preflight de reuso/runtime | passed | `juscraper-reuse-audit-20260901.json/.md`: LICENSE, imports e fronteira de promoção verificados; nenhum código upstream é importado em runtime |
| reconciliação runtime/live | pass | inventário schema v2 registra equivalentes por superfície; TJES/TJRN/TJRO foram reconciliados e TJSP/CJSG permanece bloqueado |

## Comandos

```text
python tools/build_juscraper_court_inventory.py ... ........ pass
python tools/build_juscraper_semantic_diff.py ... .......... pass
python -m pytest -q tests/test_juriscraper_intake.py tests/test_juscraper_court_inventory.py tests/test_juscraper_semantic_diff.py  12 passed
```

O diff AST e um preflight: ele compara declaracoes estaticamente, mas nao
afirma que nomes de campos ou filtros sejam semanticamente equivalentes. A
onda elegivel recebeu replay HTTP oficial, fixture propria, teste negativo e
identidade canonica; cada candidato restante so avanca quando atingir o mesmo
envelope reproduzivel.

## Gates por estado

| Gate | Requisito | Bloqueio |
| --- | --- | --- |
| G-01 condicoes de reuso/runtime | REQ-008 | passed; nenhum codigo Juscraper e importado |
| G-02 fixtures sanitizadas por superficie | AC-001..AC-006, AC-008 | passed for the eligible wave; candidates deferred |
| G-03 `per_page` maximo, ordenacao e rate limit | REQ-003 | passed for the eligible wave |
| G-04 adapter + parser + testes de contrato | AC-001..AC-008 | passed for the eligible wave |
| G-05 provider promovido no registro/catalogo | REQ-007 | passed for technically ready sources |
| G-06 binding reconciliado com a topologia | REQ-009 | passed; remaining surfaces explicit |

## Rastreabilidade

REQ-001 a REQ-014 sao ligados a T01 a T10. O diff estatico por superficie foi
fechado em T04 e os adapters elegiveis passaram replay HTTP, fixtures proprias,
equivalencia offline e seguranca. O intake nao promove candidatos sem esses
gates e nao altera producao.

O preflight de reuso confirma que o runtime NanoJuris nao importa Juscraper nem
referencia o checkout upstream. A decisao operacional vigente cobre uso tecnico
local/federado das fontes que passaram os gates; redistribuicao e producao
continuam fora do escopo.

## Reconciliacao da equivalencia TJRJ — 2026-09-10

O crosswalk atual foi corrigido para refletir a fonte efetivamente usada pelo
Juscraper: `courts/tjrj` consulta o portal publico EJURIS
(`ConsultarJurisprudencia.aspx` + XHR `ProcessarConsJurisES.aspx`), portanto o
equivalente NanoJuris e `tjrj_ejuris`. O adapter `tjrj_eproc_jurisprudencia`
permanece uma superficie estadual independente e nao e mais apresentado como
paridade do pacote Juscraper.

Evidencias regeneradas sem rede:

- `docs/provider-discovery/juscraper-court-inventory-current.json/.md`;
- `docs/provider-discovery/juscraper-semantic-diff-current.json/.md`;
- `tests/test_juscraper_current_inventory.py`.

O estado continua `partial_overlap_review`/`covered_requires_differential_fixture`:
o mapeamento de rota e provider esta correto, mas a promocao nao e inferida
apenas do nome; filtros e campos continuam sujeitos ao contrato e a fixtures
independentes.
