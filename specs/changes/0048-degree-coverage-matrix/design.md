# Design — Matriz nacional por coleção e grau

## Modelo

`CoverageSurface` é uma linha atômica da matriz. Ela separa quatro conceitos
que não podem ser colapsados:

```text
authority  -> quem publica (TJSP, TRF3, TRESP, STM, ...)
branch     -> ramo constitucional, estadual, federal, eleitoral, militar,
              trabalhista ou superior
degree     -> first, second, recursal, superior, mixed ou unknown
collection -> CJPG, CJSG, EPROC, PJE, SJUR, PORTAL, PRECEDENT, ...
```

`CJPG` e `CJSG` são coleções semânticas do e-SAJ/TJs; não são sinônimos
universais de primeiro e segundo grau. A validação impede qualquer combinação
incompatível.

## Estados

As linhas usam os estados operacionais:

- `implemented`: provider runtime e contrato local reconciliados;
- `candidate`: fonte ou rota ainda não implementada;
- `pending_contract`: há provider/rota equivalente, mas falta prova específica
  de coleção ou grau;
- `blocked_access`: CAPTCHA, WAF, login ou controle de acesso;
- `blocked_transport`: falha de transporte comprovada;
- `source_unavailable`: fonte indisponível;
- `out_of_scope`: unidade ou superfície deliberadamente fora do produto.

Somente `implemented` e `queryable=true` entram como cobertura consultável. A
matriz continua mostrando todas as demais linhas para orientar o backlog.

## Reconciliação

O gerador parte de `nanojuris.brazil.COURTS`, adiciona as linhas esperadas de
TJ e aplica declarações explícitas de providers conhecidos. Uma declaração
`mixed` nunca satisfaz uma linha CJPG/CJSG; ela apenas cria uma superfície
equivalente pendente de contrato específico. Providers de catálogo (como
metadados eleitorais) ficam visíveis, mas não contam como busca de decisões.

Para ramos sem tribunal de primeiro grau representado no catálogo (varas
federais, varas do trabalho, zonas eleitorais e auditorias militares), a matriz
cria uma linha agregada `scope=judicial_unit_gap`, marcada como `candidate`.
Isso explicita a lacuna sem inventar uma autoridade ou URL.

Os 27 TREs são instanciados individualmente como autoridades de segundo grau
eleitoral. Eles usam `SJUR` como superfície nativa e ficam em
`pending_contract` enquanto o adapter só comprovar catálogos de metadados; a
linha agregada `TRES_AGGREGATE` não substitui essas 27 linhas.

## Saída

O gerador `tools/build_degree_coverage.py` grava:

- `docs/topology/degree-coverage-matrix-20260901.json` — fonte machine-readable;
- `docs/topology/degree-coverage-matrix-20260901.md` — leitura humana.

O JSON contém `summary.by_collection` (com numerador, denominador e razão),
`summary.by_degree`, `summary.by_branch`, `summary.by_status` e `gaps`. Os
percentuais são por linha esperada e nunca são apresentados como completude
temporal do acervo.

## Compatibilidade

O modelo é aditivo e não altera as assinaturas de `NanoJurisClient`,
`JurisprudenceQuery` ou providers existentes. A topologia histórica continua
válida; a matriz é a camada nova para planejamento de grau e coleção.
