# Verificação — TJMSP diagnóstico

- Fonte: `https://jurisprudencia-client.tjmsp.jus.br/`.
- Chamada bounded: HTTP 403, classificada como controle de acesso.
- Fixture: `tests/fixtures/tjmsp_portal.html`.
- Testes: `tests/test_tjmsp_jurisprudencia.py`.
- Decisão: runtime opt-in, não federado; sem bypass.
- ## Resultados

- The probe was classified as `access_control_required`.
- The external error was not converted to an empty result.
- The provider is opt-in and remains outside the default federation.

- ## Rastreabilidade

| Requirement | Evidence |
|---|---|
| AC-001 | `tests/test_tjmsp_jurisprudencia.py` HTTP 403 test |
| AC-002 | `tests/fixtures/tjmsp_portal.html` and schema-drift test |
| AC-003 | candidate registry and non-federated capability |
## Recheck de API oficial — 2026-09-12

A rota oficial `GET /v1/tema/retornaRegistrosAtivos` também respondeu HTTP 403
em uma sonda sem credenciais, cookies, tokens, proxy ou bypass. A resposta foi
classificada como `access_control_required`, não como lista vazia. Evidência
sanitizada: `docs/provider-discovery/tjmsp-api-access-recheck-live-20260912.json`.
O provider permanece opt-in e não federado; a conclusão depende de allowlist,
exportação ou contrato público fornecido pelo TJMSP.
