# Rastreabilidade - intake Juscraper

| Requisito | Criterio | Tarefa | Evidencia | Estado |
| --- | --- | --- | --- | --- |
| REQ-001 | AC-001 | T01, T02 | `juscraper-intake-20260901.json` | pass |
| REQ-002 | AC-001 | T03 | inventory de `court_packages` e superfices | pass |
| REQ-003 | AC-002, AC-003 | T03, T04, T05 | `juscraper-semantic-diff-20260901.*` com dimensoes estaticas por superficie | pass (static) |
| REQ-004 | AC-005 | T02, T07 | MIT `LICENSE` hash; no copy | pass |
| REQ-005 | AC-004 | T03, T06 | dependencia e agregadores continuam separados; adapters pendentes | partial |
| REQ-006 | AC-003 | T06, T07, T08 | equivalencia ainda nao iniciada | pending |
| REQ-007 | AC-001 | T01, T03 | artifacts gerados e cross-reference do catalogo | pass |
| REQ-008 | AC-002 | T01, T03, T04 | inventario cruza CJSG, CJPG e detalhe TJTO e separa graus | pass |
| REQ-009 | AC-004, AC-006 | T03, T05, T07 | decisoes de acesso no ledger; adapter review pendente | partial |
| REQ-010 | AC-003, AC-007 | T04, T06, T07 | diff estatico compara snapshot upstream com capabilities locais; equivalencia pendente | pass (static preflight) |
| REQ-011 | AC-003, AC-007 | T08 | SDDs por provider continuam gated | pending |
| REQ-012 | AC-001, AC-008 | T09 | commit fixado e auditoria rerunnable | pass |

O artefato `juscraper-reuse-audit-20260901.*` cobre o preflight tecnico de
REQ-004/REQ-008: LICENSE fixado, nenhum import upstream no runtime e guarda de
promocao. O parecer sobre redistribuicao de dados permanece pendente.

`pass (static)` significa que a dimensão foi inventariada sem inferir
equivalência de comportamento. Promoção exige os gates de fixtures, replay,
segurança, identidade e reuso.
