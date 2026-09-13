# Verificacao

## Resultados

- Chamada live bounded em 2026-09-01: HTTP 200, HTML valido, dez resultados
  e total declarado de 4.658.921; corpo nao persistido.
- Fixtures e parser: sucesso, vazio, acesso e schema drift cobertos.
- Testes focados do adapter: 14 casos aprovados; teste live gated aprovado.
- O provider está incluído na busca unificada (`supports_unified_search=True`)
  e no modo `enabled` do manifesto técnico, mantendo CJPG separado de CJSG.

## Rastreabilidade

| Requisito | Evidencia |
| --- | --- |
| REQ-001/004 | `src/nanojuris/providers/tjsp_cjpg.py` e `test_tjsp_cjpg.py` |
| REQ-002/003 | parser, `raw`, `SourceTrace` e teste de canonicalizacao |
| REQ-005 | fixtures vazias, acesso, drift e testes HTTP parametrizados |
| REQ-006 | capability e catalogo `tjsp_cjpg` opt-in |
| REQ-007 | revisao de codigo; sem browser/cookies/bypass |

## Evidencia live

Em 2026-09-01, `GET https://esaj.tjsp.jus.br/cjpg/pesquisar.do` com busca
bounded por `responsabilidade` respondeu HTTP 200, HTML valido, 10 linhas e
total declarado de 4.658.921. O corpo nao foi persistido.

## Gates locais

- parser e classificacao cobertos por fixtures sinteticas;
- Ruff, format, mypy e compileall devem passar;
- suite completa deve passar antes de qualquer release;
- nenhum gate autoriza deploy ou push automaticamente.

## Gates pendentes

O escopo desta rodada não exige licença ou autorização judicial adicional para
o uso técnico local/federado autorizado pelo operador. Não houve deploy, push
ou alteração de produção.
