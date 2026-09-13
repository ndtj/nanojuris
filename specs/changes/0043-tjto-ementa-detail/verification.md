# Verificacao

Status: verified_with_limitations — implementação e gates técnicos locais
concluídos; detalhe permanece opt-in e sujeito aos limites da fonte.

## Resultados

O contrato técnico da rota `GET /documento.php?uuid=<uuid>` foi reproduzido em
uma chamada pública bounded (ciclo 18), sem credenciais e sem persistir o corpo.
O adapter mantém a busca base e faz o detalhe somente com `fetch_details=True`.
Falhas controladas no detalhe deixam o item base disponível como `partial`, com
tipo e mensagem redigida no `raw`. Fixtures pareadas e testes negativos cobrem
sucesso, acesso, conteúdo inválido e transporte.

## Rastreabilidade

| Requisito | Evidencia | Estado |
| --- | --- | --- |
| REQ-001 | `docs/provider-discovery/tjto-jurisprudencia-detail-live-20260902-cycle18.json` | passed (technical) |
| REQ-002, REQ-003 | `TjtoJurisprudenciaProvider._enrich_with_detail`, trace e hashes separados | passed |
| REQ-004, REQ-005 | `tests/test_tjto_jurisprudencia.py`, erro de acesso preserva resultado | passed |
| REQ-006 | runtime sem Juscraper/cookies e testes de segurança | passed |
