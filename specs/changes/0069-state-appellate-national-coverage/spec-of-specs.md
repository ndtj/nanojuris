# Spec of specs - programa TJ segundo grau 27/27

## Resultado final

Todos os 27 tribunais estaduais devem possuir ao menos uma superficie oficial
de jurisprudencia textual de segundo grau que complete os oito gates do SDD
0069. A meta e funcional e auditavel; nao exige que a fonte se chame
literalmente `CJSG`, mas exige prova de `degree=second` e impede que consulta
processual ou catalogo contextual conte como cobertura.

## Decomposicao

| Subprograma | Escopo | Saida |
| --- | --- | --- |
| A - manutencao | TJAC, TJAL, TJAM, TJES, TJMS | revalidacao sem regressao |
| B - contrato | 15 providers runtime com live valido | binding explicito de segundo grau, fixtures e federacao |
| C - alternativas | TJAP, TJCE, TJPE, TJSP | diagnostico/rechecagem ou rota oficial alternativa, sem bypass |
| D - adapters | TJMA, TJMG, TJSE | descoberta oficial, adapter independente e gates completos |
| E - encerramento | todos os 27 | matriz 27/27, suite, live e manifesto coerentes |

Cada tribunal deve receber pacote individual somente ao iniciar mudanca de
adapter/contrato. O workpack JSON e a fila completa e evita criar 108 arquivos
vazios antes da pesquisa. O pacote individual herda REQ-001 a REQ-008 e deve
conter `spec.md`, `design.md`, `tasks.md`, `verification.md`; inclua pesquisa,
rastreabilidade e threat model quando houver transporte ou acesso de risco.

## Ordem obrigatoria

1. fechar primeiro fontes runtime, publicas e live-validas;
2. corrigir bindings semanticamente errados antes de aumentar contagens;
3. pesquisar alternativas oficiais para bloqueios, sem contornar controles;
4. implementar os tres gaps de adapter;
5. regenerar a fonte unica de verdade apos cada tribunal;
6. declarar 27/27 somente quando o gerador informar 27 workpacks com 8/8.

## Dependencias

0069 depende dos contratos 0027, runtime 0028, intake 0029, identidade 0037,
semantica federada 0038, observabilidade 0033 e matriz 0048. Pacotes novos nao
podem duplicar esses componentes.
