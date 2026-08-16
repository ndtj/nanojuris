# Coverage

Gerado por `python tools/build_provider_coverage.py --write`. Nao edite manualmente os dados tabulares.

Esta area e o indice operacional do NanoJuris para humanos e agentes de IA.
Ela responde, em uma leitura curta, quais fontes existem, o que entram, o que saem,
quais estao maduras para busca unificada e quais ainda exigem aprofundamento.

## Resumo Atual

- Fontes documentadas: **54**.
- Providers implementados: **37**.
- Fontes na busca unificada: **36**.
- Fontes primarias de jurisprudencia textual: **29**.
- Fontes com algum suporte a inteiro teor/documento: **20**.

## Como Usar

| Pergunta | Arquivo |
| --- | --- |
| Quais fontes existem e em que estado estao? | [matrix.md](matrix.md) |
| Quais entradas e filtros cada provider aceita? | [inputs.md](inputs.md) |
| Quais campos e formatos cada provider entrega? | [outputs.md](outputs.md) |
| Quais campos canonicos estao cobertos? | [field-coverage.md](field-coverage.md) |
| O que significa ouro, prata, bronze e experimental? | [maturity.md](maturity.md) |
| Qual foi a ultima validacao live focada? | [live-status.md](live-status.md) |
| Qual catalogo uma IA deve ler? | [../registry/provider-catalog.full.json](../registry/provider-catalog.full.json) |

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
