# Clarificacao - Implantacao inicial OCI

Mudanca: `0001-oci-initial-deployment`
Status: `pending`

## Perguntas criticas

| ID | Pergunta | Impacto | Resposta | Aprovador | Status |
| --- | --- | --- | --- | --- | --- |
| Q-001 | Qual regiao e compartment serao usados? | alto |  | humano | pending |
| Q-002 | Compute ou Container Instance para o primeiro runtime? | alto |  | Platform/SRE | pending |
| Q-003 | Qual dominio, DNS e certificado serao usados? | alto |  | humano | pending |
| Q-004 | Qual orcamento mensal e perfil de carga sao aceitaveis? | alto |  | Product/Finance | pending |
| Q-005 | Qual politica de retencao e restauracao do store? | alto |  | Security/SRE | pending |
| Q-006 | Quais endpoints serao publicos no primeiro release? | alto |  | Product/Security | pending |

## Hipoteses temporarias

| ID | Hipotese | Validacao |
| --- | --- | --- |
| H-001 | uma instancia atende o primeiro ambiente produtivo | teste de carga bounded |
| H-002 | SQLite permanece single-writer com volume persistente | smoke, concorrencia e restore |
| H-003 | MCP continua local e nao e exposto publicamente | revisao de superficie e smoke |

## Gate de saida

Este pacote nao deve avancar para `apply` ou `release` enquanto Q-001 a Q-006
nao tiverem resposta e aprovacao registradas.
