# Matriz nacional de fontes e tarefas — SDD 0098

Gerada em `2026-09-10` por `tools/build_national_source_task_matrix.py`.
A matriz enumera fontes existentes e superfícies ainda não descobertas; não afirma que uma rota ou provider funciona.

## Escopo e regra de promoção

- Linhas: **249** (155 core; 94 condicionais).
- Core: jurisprudência textual oficial de TJs, TRFs/CJF, superiores, TRTs/TST, TSE/TREs e Justiça Militar.
- Condicional: tribunais de contas e outras fontes administrativas; exigem decisão de escopo antes de contar na cobertura judicial.
- `discovery_pending` nunca é vazio e nunca entra na federação.
- Superfícies Juscraper sem equivalente/semântica confirmada: **59**; exigem análise antes de qualquer adapter.
- Promoção exige contrato, fixture, chamada live bounded, qualidade canônica e federação; bloqueios permanecem explícitos.

## Diretórios oficiais de descoberta

- `cnj_state`: https://www.cnj.jus.br/tribunais-de-justica-estaduais/
- `cnj_labor`: https://www.cnj.jus.br/justica-do-trabalho/
- `cnj_electoral`: https://www.cnj.jus.br/justica-eleitoral-/
- `cnj_military`: https://www.cnj.jus.br/tribunais-de-justica-militar/
- `cnj_all`: https://www.cnj.jus.br/relatorio-por-tribunal/
- Evidência live bounded: `docs/provider-discovery/national-directory-live-20260908.json`

## Estado atual

| Estado | Linhas |
| --- | ---: |
| `blocked_or_unavailable` | 12 |
| `contract_pending` | 30 |
| `discovery_pending` | 137 |
| `federated_live` | 68 |
| `live_not_federated` | 2 |

## Lacunas prioritárias

- **CJPG não federado:** TJAC, TJAM, TJBA, TJCE, TJDFT, TJMA, TJMG, TJMT, TJPA, TJPB, TJPE, TJPI, TJPR, TJRJ, TJRN, TJRR, TJRS, TJSC, TJSE.
- **CJSG não federado:** TJAP, TJMA.
- **Federal sem descoberta:** CJF.
- **Trabalho sem descoberta:** TRT1, TRT10, TRT11, TRT12, TRT13, TRT14, TRT15, TRT16, TRT17, TRT18, TRT19, TRT20, TRT21, TRT22, TRT23, TRT24, TRT5, TRT7, TRT9.
- **Militar sem descoberta:** nenhuma.

## Tarefas rastreáveis

A execução deve usar os IDs abaixo em lotes de até três fontes. Cada linha no JSON contém `task_id`, provider atual, evidências, ação seguinte e diretório oficial.

| ID | Família | Escopo | Ação |
| --- | --- | --- | --- |
| T047 | CJPG | 27 TJs | inventariar e fechar primeiro grau |
| T048 | CJSG | 27 TJs | inventariar e fechar segundo grau |
| T049 | Alternativas | fontes registradas | validar ementários, eproc, PJe, portais e turmas |
| T050 | Federal | TRF1–TRF6/CJF | descobrir e validar jurisprudência federal |
| T051 | Superiores | STF/STJ/STM/TNU/TST/TSE/CSJT/CNJ | separar jurisprudência de contexto |
| T052 | Trabalho | TRT1–TRT24 | descobrir rota oficial e contrato |
| T053 | Eleitoral | TSE/TREs | validar SJUR e fontes locais |
| T054 | Militar | TJMs/STM | validar segundo grau militar |
| T055 | Condicional | TCEs/TCMs | decidir escopo antes da promoção |
| T056 | Descoberta | todas as lacunas | localizar rota oficial/API/exportação |
| T057 | Live | fontes descobertas | chamada bounded, filtros e paginação |
| T058 | Contrato | fontes com resposta | adapter, fixtures, inteiro teor e qualidade |
| T059 | Federação | fontes elegíveis | smoke opt-in e promoção técnica |
| T060 | Reconciliação | fontes bloqueadas/divergentes | manter estado explícito e atualizar ledger |

## Limites

A matriz não autoriza bypass de CAPTCHA, WAF, Turnstile, login, rate limit ou TLS. Quando o diretório oficial existe mas a consulta exige desafio ou autorização, a linha permanece `blocked_or_unavailable` e a evidência deve apontar a ação externa necessária.

Fonte institucional para a enumeração dos ramos: [CNJ — Tribunais de Justiça Estaduais](https://www.cnj.jus.br/tribunais-de-justica-estaduais/), [CNJ — Justiça do Trabalho](https://www.cnj.jus.br/justica-do-trabalho/), [CNJ — Justiça Eleitoral](https://www.cnj.jus.br/justica-eleitoral-/) e [CNJ — Tribunais de Justiça Militar](https://www.cnj.jus.br/tribunais-de-justica-militar/).
