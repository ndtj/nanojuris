# Design — intake Juscraper

## Pipeline

    snapshot fixado
      -> license ledger
      -> static inventory por classe e método
      -> surface inventory por coleção/grau
      -> semantic diff
      -> fixture minimization
      -> adapter spike
      -> equivalence tests
      -> provider-specific SDD
      -> review and promotion

## Ledger mínimo

- upstream commit e path;
- autor/licença;
- função ou fixture utilizada;
- autoridade, coleção, grau, método, rota e categoria de escopo;
- provider NanoJuris relacionado;
- mudança realizada;
- testes de equivalência;
- risco e responsável;
- decisão final.
- fingerprint da evidência e commit da última revisão.

## Fontes de inventário

O inventário usa a árvore `src`, AST, módulos, schemas, parsers e testes. O
`tribunal_manager.py`, os notebooks e a documentação são evidências auxiliares,
pois o snapshot observado apresenta divergência entre esses artefatos.

## Ordem de adaptação

1. implementar somente ganho novo e baixo risco: TJES, TJRN e TJRO;
2. adicionar detalhe lazy TJTO para ementa;
3. comparar overlaps e importar apenas correções comprovadas;
4. avaliar CJPG como collections próprias;
5. manter TJAP/TJMG bloqueados e TJRJ em revisão de acesso.

Testes diferenciais importam o snapshot apenas em ambiente de desenvolvimento e
nunca tornam o Juscraper dependência do pacote distribuído.

## Decisão de dependência

Adaptação seletiva é o default. Dependência opcional só poderá ser proposta em
novo ADR se reduzir risco e passar por supply-chain review.
