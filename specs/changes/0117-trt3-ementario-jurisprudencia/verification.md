# Verification - SDD 0117

Evidencias live:

- `docs/provider-discovery/trt3-ementario-live-20260909.json` - volume PDF
  originalmente observado;
- `docs/provider-discovery/trt3-ementario-dspace-live-20260910.json` - pesquisa
  avancada DSpace e replay bounded do adapter.

## Sonda DSpace 2026-09-10

```text
query=acidente page=1 page_size=2
POST advanced-search HTTP=200, volumes_reported=61, bytes=52277
GET/POST bounded: 3 volumes max; first volume PDF HTTP=200, bytes=161600
results=2, total_known=false, completeness=partial
degree=second, instance=second, branch=labor, authority=TRT3
credentials=false, captcha_bypass=false, access_control_bypass=false
```

## Gates locais

```text
python -m pytest -q tests/test_trt3_ementario_jurisprudencia.py
python -m ruff check src/nanojuris/providers/trt3_ementario_jurisprudencia.py tests/test_trt3_ementario_jurisprudencia.py
python -m mypy src/nanojuris/providers/trt3_ementario_jurisprudencia.py
python -m compileall -q src/nanojuris/providers/trt3_ementario_jurisprudencia.py
```

Resultado: testes e gates focados aprovados. A colecao continua contextual,
opt-in e fora da federacao padrao. O contrato geral do portal
`juris.trt3.jus.br` permanece bloqueado por HTTP 403 e nao foi contornado.

## Resultados

| Verificacao | Resultado |
| --- | --- |
| Parser e contrato DSpace | passed |
| Fixture e testes focados | passed |
| Sonda live bounded | HTTP 200, dois resultados, total de volumes desconhecido como decisao |
| Ruff, mypy e compileall focados | passed |
| Federacao padrao | disabled por escopo contextual |

## Estado

| Requisito | Estado |
| --- | --- |
| Rota oficial e parser | passed |
| Identidade canônica de segundo grau | passed |
| Filtros locais e schema drift | passed |
| Sonda live DSpace bounded | passed |
| Inteiro teor dos votos | pending_external |
| Busca geral TRT3 | pending_external |
| Retencao/promocao | pending_human |

## Rastreabilidade

| Requisito | Evidencia | Estado |
| --- | --- | --- |
| REQ-001/REQ-002 | adapter, parser e evidencia DSpace | passed |
| REQ-003/REQ-004 | testes de identidade, filtros e data de volume | passed |
| REQ-005 | testes de schema drift e status HTTP | passed |
| REQ-006 | capabilities e manifesto opt-in | passed |
| Busca geral TRT3 | rota oficial ainda bloqueada | pending_external |
| Retencao/promocao | decisao do mantenedor | pending_human |
