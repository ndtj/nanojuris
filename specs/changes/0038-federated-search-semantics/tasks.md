# Tarefas

- [x] T01 - inventariar semantica declarada de texto, filtros, score e paginacao.
- [x] T02 - definir SearchIntent, ProviderQueryPlan e cursor versionado.
- [x] T03 - implementar planner e traces de transformacao.
- [x] T04 - implementar merge deterministico e integracao 0037.
- [x] T05 - criar fixtures de filtro omitido, postfilter, cursor invalido e intents.
- [x] T06 - testar cursor, ordering da intencao e compatibilidade.
- [x] T07 - documentar a camada opt-in sem alterar SDK/CLI/MCP/Studio legados.
- [x] T08 - benchmark local e revisao de claims.

Dependencia: T01 -> T02 -> T03 -> T04 -> T05 -> T06 -> T07 -> T08.

O merge foi entregue como camada opt-in, sem alterar a API pública existente;
a integração automática ao cliente permanece fora desta mudança.
