# Design - 0066

## Decisoes

1. A normalizacao ocorre no parser de cada fonte, depois da preservacao do
   payload nativo em `raw`. O modelo `JurisprudenceResult` continua aditivo e
   posicionalmente compativel.
2. `JURISPRUDENCIA` identifica uma superficie textual generica. Somente
   `collection=CJPG` ou `collection=CJSG` em contrato especifico satisfaz a
   matriz de graus.
3. `total_known` e calculado a partir do marcador/contagem realmente presente
   na resposta. Quando ausente, `SearchPage.total` pode conter o tamanho da
   janela para compatibilidade, mas `effective_total` permanece `None`.
4. Falhas de transporte, acesso e schema continuam excecoes explicitas; a
   pagina vazia so e marcada `EMPTY` quando a resposta valida comprova zero.

## Mapeamentos

| Provider | Fonte canonica | Colecao | Grau |
|---|---|---|---|
| TJRN | TJRN | JURISPRUDENCIA | por registro, desconhecido se ausente |
| TJRO | TJRO | JURISPRUDENCIA | PJEPG/1 = first; PJESG/2 = second |
| TJTO | TJTO | JURISPRUDENCIA | somente se informado explicitamente |
| TJGO | TJGO | JURISPRUDENCIA | somente se informado explicitamente |

## Compatibilidade e rollback

Os novos atributos possuem default `None`; consumers que ignoram dimensoes
continuam funcionando. Rollback local consiste em reverter o pacote de mudanca
sem migracao destrutiva de banco.
