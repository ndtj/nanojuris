# Verification

Status: `proposed` — nenhum adapter, fixture ou alteração de runtime foi
introduzida neste ciclo. Este pacote registra a decisão e o plano; a
implementação depende de T02 (revisão de reuso) e T03 (fixtures live).

## Comandos e resultados

```text
TJES /api/health  (28/08/2026) ............ HTTP 200 JSON; service: ok; 5 cores ativas
TJES /api/cores ........................... HTTP 200 JSON; pje1g, pje2g, pje2g_mono, legado, turma_recursal_legado
TJES /api/facets?core=pje2g ............... HTTP 200 JSON; facetas de classe/jurisdição/magistrado/órgão/assunto
TJES /api/search?core=pje2g&q=...&per_page=1  HTTP 200 JSON; 1 doc; total: 166448
  (também respondeu para pje1g e legado, sem autenticação)
portal ColdFusion legado ................. HTTP 503 (0023)
rota histórica de resultados ............. HTTP 404 (0023)
paridade de dossiê canônico/legado ....... passed
python tools/validate_sdd.py ............. passed
```

Nenhuma credencial, CAPTCHA ou rota privada foi usada. O endpoint foi
descoberto no JavaScript da própria página oficial.

## Gates pendentes

| Gate | Requisito | Bloqueio |
| --- | --- | --- |
| G-01 revisão de condições de reuso/redistribuição concluída | REQ-008 | T02 |
| G-02 fixtures sanitizadas de sucesso/vazio/erro/paginação/legado | AC-001..AC-006 | T03 |
| G-03 `per_page` máximo, ordenação e rate limit confirmados | REQ-003 | T04 |
| G-04 adapter + parser + testes de contrato passam sem rede | AC-001..AC-007 | T05..T08 |
| G-05 provider promovido no registro e catálogo regenerado | REQ-007 | T09 |

## Rastreabilidade

| Requisito | Evidência atual | Status |
| --- | --- | --- |
| REQ-001 | design fixa a URL pública; `url` privado de `/health` explicitamente ignorado | especificado |
| REQ-002 | design define default `pje2g` e proíbe fan-out | especificado |
| REQ-003 | contrato `page`/`per_page`/`total`/`total_pages` observado live | pendente (G-03) |
| REQ-004 | tabela de mapeamento canônico por core no design | pendente (G-02) |
| REQ-005 | matriz de classificação de erro no design | pendente (G-02) |
| REQ-006 | `SourceTrace` com rota/core/parâmetros | pendente (G-04) |
| REQ-007 | capability opt-in planejada | pendente (G-05) |
| REQ-008 | escopo não promove produção nem coleta em escala | especificado |
