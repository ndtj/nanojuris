# Verificacao

## Rechecagem de paginação

O contrato de paginação foi rechecado em 2026-09-02 no artefato
`docs/provider-discovery/tjrn-jurisprudencia-pagination-live-20260902-cycle22.json`:
as páginas 1 e 2 responderam HTTP 200, com 20 registros observados e total
reportado de 53.366. A ordenação nativa foi preservada como `source_default`;
filtros além de texto, expressão exata, número e página continuam explicitamente
não comprovados. O provider permanece `candidate_only` até os gates de reuso e
revisão humana.

Status: verified — adapter, parser, paginação e promoção técnica local concluídos;
limitações de filtros por grau permanecem explícitas.

## Resultados

O contrato live possui evidência bounded de HTTP 200 e dados reais nas páginas
1 e 2 em 2026-09-02. O adapter local opt-in, fixtures e equivalência canônica
foram implementados; o source permanece federável para a superfície textual
geral, enquanto bindings CJPG/CJSG específicos continuam não comprovados.
Bloqueios de acesso, quando observados, não são tratados como vazio. Evidências: `tests/`,
`docs/provider-discovery/tjrn-jurisprudencia-pagination-live-20260902-cycle22.json`
e `docs/provider-discovery/tjrn-jurisprudencia-live-20260902-cycle17.json`.

## Rastreabilidade

| Requisito | Evidencia | Estado |
| --- | --- | --- |
| REQ-001 | smoke bounded TJRN e portal oficial | pass para descoberta |
| REQ-002, REQ-003 | contrato e mapper | pass local |
| REQ-004, REQ-005 | fixtures e testes negativos | pass local; live bloqueado |
| REQ-006 | decisao de federacao opt-in | pass |

## Atualização técnica — 2026-09-05

- Smoke direto bounded: HTTP 200, total remoto 73.895, inteiro teor observado e
  `SourceTrace` com hash.
- Smoke de paginação: páginas 1 e 2 com `page_size=2`, intervalos 1–2 e 3–4,
  sem sobreposição de IDs; a janela permanece parcial.
- Smoke federado: o provider está incluído na federação padrão após a decisão
  técnica do operador; bindings de grau continuam separados.
- Suíte local após a atualização: 1.155 aprovados e 22 ignorados; Ruff, mypy e
  validação SDD aprovados.

O escopo desta rodada não exige licença ou autorização judicial adicional para
o uso técnico local/federado autorizado pelo operador. O histórico de HTTP 403
continua preservado como bloqueio de uma janela anterior, não como resultado vazio.
