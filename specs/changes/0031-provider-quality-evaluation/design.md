# Design — avaliação de qualidade

## Dimensões

| Dimensão | Peso inicial | Gate crítico |
| --- | ---: | --- |
| autoridade e escopo | 10 | fonte oficial |
| contrato e erros | 15 | sem false empty |
| identidade | 15 | determinística |
| conteúdo textual | 15 | conforme categoria |
| datas e temporalidade | 10 | raw ou normalizada |
| provenance e traces | 15 | completos |
| paginação/completude | 10 | honestas |
| testes e fixtures | 5 | cenários críticos |
| docs/operação | 5 | sincronizadas |

Score não substitui gates críticos. Um provider com false empty conhecido não
pode ser gold mesmo com pontuação alta.

## Artefatos

- provider-quality.json;
- relatório markdown;
- golden canonical JSON;
- invariants report;
- maturity decision assinável.
