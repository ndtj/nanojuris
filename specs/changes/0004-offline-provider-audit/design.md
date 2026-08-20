# Design

## Fluxo

1. Carregar `docs/registry/provider-catalog.full.json`.
2. Para cada entrada, verificar módulo, registro runtime, dossier, contrato,
   referências de fixture e referências de testes.
3. Para entries `none` e `family`, carregar somente fixtures citadas localmente.
4. Aplicar `analyze_route_response`, `extract_route_candidates` e
   `suggest_selector_candidates` sobre os bytes locais.
5. Emitir relatório JSON determinístico quanto ao conteúdo e Markdown de leitura
   humana.

## Limites

O utilitário não importa cliente HTTP, Playwright, proxy, sessão, cookie ou
credencial. A ausência de fixture não dispara fallback para rede.

## Artefatos

- `tools/audit_provider_discovery_offline.py`
- `docs/provider-discovery/offline-audit.json`
- `docs/provider-discovery/offline-audit.md`

O catálogo permanece somente leitura. Alterações futuras de capabilities,
dossiers ou fixtures devem passar pelos geradores e testes existentes.
