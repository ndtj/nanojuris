# Traceability

| Requisito | Implementação | Evidência | Teste |
| --- | --- | --- | --- |
| RF-001 | `discover_all_providers.py` | relatório `providers` | sweep smoke |
| RF-002 | `RouteCandidate` | `observed_routes` | discovery tests |
| RF-003 | `FilterCandidate` | `observed_filters` | extractor tests |
| RF-004/005 | `DiscoveryEvidence` | `observations` | provider discovery tests |
| RF-006 | GET-only materialization | `interpretation` | review/manual gate |
| RF-007/008 | relatório + cache | JSON evidence | replay/local tests |
