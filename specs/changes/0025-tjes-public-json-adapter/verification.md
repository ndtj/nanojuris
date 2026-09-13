# Verification

Status: `verified_with_limitations` — contrato comum e implementação foram
desdobrados nos bindings 0044 (CJPG), 0049 (CJSG) e 0067 (turma recursal), com
fixtures, testes e smoke live bounded; cada collection permanece independente.

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

Evidência adicional de 2026-09-01:
`docs/provider-discovery/juscraper-live-smoke-20260901.json` registra
`tjes` com HTTP 200, um documento e sinal de identidade/ementa. Isso é prova
de disponibilidade momentânea, não substitui fixtures nem equivalência.

Nenhuma credencial, CAPTCHA ou rota privada foi usada. O endpoint foi
descoberto no JavaScript da própria página oficial.

## Gates por binding

| Gate | Requisito | Bloqueio |
| --- | --- | --- |
| G-01 contrato público e limites | REQ-001..REQ-003 | passed nos bindings 0044/0049/0067 |
| G-02 fixtures sanitizadas e estados negativos | AC-001..AC-006, AC-008 | passed por binding |
| G-03 parser, trace e identidade | REQ-004..REQ-006 | passed por binding |
| G-04 registro, catálogo e matriz | REQ-007, REQ-009 | passed; artefatos regenerados |
| G-05 produção/coleta em escala | REQ-008 | fora do escopo; nenhum deploy ou publicação |

## Rastreabilidade

| Requisito | Evidência atual | Status |
| --- | --- | --- |
| REQ-001 | design fixa a URL pública; `url` privado de `/health` explicitamente ignorado | passed |
| REQ-002 | bindings separados por core/collection | passed |
| REQ-003 | contrato `page`/`per_page`/`total`/`total_pages` observado live | passed com limites |
| REQ-004 | mapeamento canônico por core nos bindings | passed |
| REQ-005 | matriz de classificação de erro nos testes | passed |
| REQ-006 | `SourceTrace` com rota/core/parâmetros | passed |
| REQ-007 | capability e catálogo por binding | passed |
| REQ-008 | escopo não promove produção nem coleta em escala | especificado |
| REQ-009 | design separa collection de core e T10 liga a topologia | passed |
