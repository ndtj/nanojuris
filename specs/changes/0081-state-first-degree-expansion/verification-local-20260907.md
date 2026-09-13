# Local verification - first-degree workpacks

- Bounded discovery queried one official homepage per state court with a
  five-second timeout and no scripts or candidate probes.
- Result: 27 authorities, 258 route candidates, 126 same-host jurisprudence
  candidates, 13 route-candidate workpacks, 10 research-ready, 3 blocked
  rechecks, and 1 transport discovery case.
- Generated artifacts:
  `docs/provider-discovery/first-degree-route-inventory-20260907.json`,
  `docs/provider-discovery/first-degree-route-inventory-20260907.md`,
  `docs/coverage/first-degree-workpacks-20260907.json`, and Markdown.
- `tests/test_first_degree_route_discovery.py` and
  `tests/test_first_degree_workpacks.py` pass.

No route was promoted. Process surfaces, external references, access control,
and transport errors remain explicitly excluded from CJPG coverage.
