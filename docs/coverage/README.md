# Coverage

Gerado por `python tools/build_provider_coverage.py --write`. Nao edite manualmente os dados tabulares.

Esta area e o indice operacional do NanoJuris para humanos e agentes de IA.
Ela responde, em uma leitura curta, quais fontes existem, o que entram, o que saem,
quais estao maduras para busca unificada e quais ainda exigem aprofundamento.

## Resumo Atual

- Fontes documentadas: **85**.
- Providers implementados: **80**.
- Fontes na busca unificada: **53**.
- Fontes primarias de jurisprudencia textual: **47**.
- Fontes com algum suporte a inteiro teor/documento: **66**.

## Como Usar

| Pergunta | Arquivo |
| --- | --- |
| Quais fontes existem e em que estado estao? | [matrix.md](matrix.md) |
| Quais entradas e filtros cada provider aceita? | [inputs.md](inputs.md) |
| Quais campos e formatos cada provider entrega? | [outputs.md](outputs.md) |
| Quais campos canonicos estao cobertos? | [field-coverage.md](field-coverage.md) |
| O que significa ouro, prata, bronze e experimental? | [maturity.md](maturity.md) |
| Como o score de maturidade e calculado? | [maturity-score.md](maturity-score.md) |
| Quais providers devemos amadurecer primeiro? | [improvement-queue.md](improvement-queue.md) |
| Qual e o plano de ondas para maturidade dos providers? | [maturity-waves.md](maturity-waves.md) |
| Qual artefato e a fonte de verdade para cada pergunta? | [source-of-truth.md](source-of-truth.md) |
| Qual foi a ultima validacao live focada? | [live-status.md](live-status.md) |
| Qual e o estado de fechamento das ondas tecnicas? | [../operations/wave-implementation-20260902.md](../operations/wave-implementation-20260902.md) |
| Qual e o roadmap executavel para CJPG/CJSG? | [degree-coverage-roadmap-20260902.md](degree-coverage-roadmap-20260902.md) |
| Qual e o mapa completo de lacunas por superficie, incluindo fontes com pouca informacao? | [national-coverage-gap-map-20260908.md](national-coverage-gap-map-20260908.md) e [national-coverage-gap-map-20260908.json](national-coverage-gap-map-20260908.json) |
| Quais tecnicas de acesso publico sao permitidas e quais sao proibidas? | [public-access-boundary-playbook-20260908.md](public-access-boundary-playbook-20260908.md) e [public-access-boundary-playbook-20260908.json](public-access-boundary-playbook-20260908.json) |
| Qual catalogo uma IA deve ler? | [../registry/provider-catalog.full.json](../registry/provider-catalog.full.json) |
| Qual pacote autonomo deve ser seguido para fechar a cobertura nacional? | [national-coverage-gold-handoff-20260908.md](national-coverage-gold-handoff-20260908.md) e [SDD 0091](../../specs/changes/0091-national-coverage-gold-handoff/) |
| Qual é o inventário atual de tarefas e decisões de baixo risco? | [low-risk-decision-register-20260909.md](low-risk-decision-register-20260909.md) e [open-task-audit-current.json](open-task-audit-current.json) |
| Qual foi o último ciclo de reconciliação técnica? | [reconciliation-cycle-20260909.md](reconciliation-cycle-20260909.md) |

## Regra De Produto

NanoJuris deve priorizar jurisprudencia textual, precedentes, informativos e
decisoes publicas com rastreabilidade. Consulta processual, DJEN, DataJud,
andamentos e timeline processual pertencem ao NanoJud.

## Fluxo De Maturidade

```text
fonte oficial -> contrato observado -> fixture -> parser -> campos canonicos
              -> validacao live opcional -> busca unificada -> jurimetria
```

O objetivo nao e apenas chamar tribunais. O objetivo e saber, com precisao,
qual campo veio de onde, em qual formato, com qual limite e com qual grau de
confianca operacional.
