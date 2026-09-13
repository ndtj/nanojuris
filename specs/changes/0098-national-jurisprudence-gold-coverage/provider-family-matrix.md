# Matriz de famílias e lotes de cobertura

Esta matriz é um plano de execução, não uma afirmação de que todas as rotas
estão disponíveis. O estado real deve ser lido no catálogo e no registro de
superfícies regenerados.

## TJs estaduais — segundo grau

| Lote | Tribunais | Estratégia |
| --- | --- | --- |
| A | AC, AL, AM, ES, MS | revalidar workpacks completos, grau, paginação e federação |
| B1 | BA, DF, MT, PA, PB, RN | APIs/BFF/GraphQL públicas; contrato explícito de segundo grau |
| B2 | GO, PI, PR, RR, RS, TO | portais, Solr, Projudi, JusPI; validar filtros e ordenação |
| B3 | RJ, SC, RO | eproc/portal; não usar fonte contextual como jurisprudência geral |
| C | AP, CE, PE, SP | alternativas oficiais; bloquear quando controle persistir |
| D | MG, MA, SE | descoberta de busca decisória e contratos independentes |

## TJs estaduais — primeiro grau

Priorizar bancos de sentenças e CJPG com prova de `degree=first`: BA, PA, RJ,
AL, AP e demais lacunas. Um boletim ou ementário curado deve permanecer marcado
como parcial, mesmo quando útil para enriquecimento.

## Federal e superior

| Família | Superfícies a separar |
| --- | --- |
| STF/STJ/STM | jurisprudência geral, informativos, súmulas e dados abertos |
| TRFs/CJF/TNU | TRF1–TRF6, CJF, eproc federal e coleções próprias |
| TST/TRTs | acórdãos, ementários, jurisprudência e PJe |
| TSE/TREs | SJUR, acórdãos e decisões eleitorais |
| TCEs | somente fontes textuais públicas com escopo documentado |

## Regras de priorização

1. Fonte primária textual, pública e de baixa latência.
2. Contrato que prove grau, tipo documental e filtros.
3. Fixture e documento oficial disponíveis.
4. Diversidade regional sem sacrificar qualidade.
5. Bloqueio externo terminal uma vez evidenciado; não repetir chamadas.

## Estado inicial conhecido

O programa estadual atual registra 27 autoridades, 25 completas e duas em
`blocked_recheck`; isso não cobre automaticamente CJPG, SJUR ou primeiro grau.
As lacunas devem ser lidas em `surface-state-registry-20260902.json`.

