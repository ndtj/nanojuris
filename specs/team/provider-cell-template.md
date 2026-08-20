# Template de célula de provider

Copiar este template para a mudança SDD do provider e preencher antes da
implementação.

## Identificação

- Source ID: `TBD`
- Fonte oficial: `TBD`
- Nível de revisão: `L2/L3/L4`
- Owner de domínio: `TBD`
- Data de início: `TBD`

## Alocação

| Função | Titular | Backup | Aceite |
| --- | --- | --- | --- |
| Domain Owner | TBD | TBD | pendente |
| Discovery | TBD | TBD | pendente |
| Provider Engineering | TBD | TBD | pendente |
| Data Quality | TBD | TBD | pendente |
| QA/Verification | TBD | TBD | pendente |
| Architecture | TBD | TBD | conforme risco |
| Security/Privacy | TBD | TBD | conforme risco |
| Platform/SRE | TBD | TBD | conforme risco |
| Documentation/SDD | TBD | TBD | obrigatório |

## Entradas obrigatórias

- dossier e source contract existentes, quando houver;
- resultado de `nanojuris.discovery` ou pesquisa equivalente;
- perguntas abertas e hipóteses;
- classificação de cobertura desejada;
- risco e nível de revisão.

## Saídas obrigatórias

- pacote SDD aceito;
- adapter/parser e testes offline;
- fixtures minimizadas;
- source trace e extraction trace;
- documentação sincronizada;
- decisão de maturidade e limitações;
- runbook quando houver operação live.

## Handoff

O handoff somente ocorre quando o próximo papel consegue executar sua etapa
usando os artefatos, sem depender do histórico de conversa.
