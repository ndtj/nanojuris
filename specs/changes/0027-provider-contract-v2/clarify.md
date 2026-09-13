# Clarificacao - contrato v2

Status: resolved

As decisoes abaixo encerram as questoes de adocao que poderiam bloquear o
ciclo. A compatibilidade continua aditiva e nao autoriza afirmar suporte sem
evidencia por fonte.

| ID | Pergunta | Decisao | Estado |
| --- | --- | --- | --- |
| Q-001 | v2 sera publico nesta release? | interno primeiro, com export aditivo e documentado | resolved |
| Q-002 | unknown sera enum ou ausencia? | estado explicito `unverified`/`unknown`, sem coercao para falso | resolved |
| Q-003 | aliases antigos serao mantidos por quanto tempo? | durante toda a serie 0.x e por ao menos um ciclo minor apos a adocao | resolved |
| Q-004 | qual campo minimo define identidade? | chave deterministica com categoria, fonte e identificador nativo; sem identificador suficiente, nao deduplicar | resolved |

Implementacao, fixtures, testes e gates registrados em `verification.md`
comprovam a adocao incremental para BNP/Pangea e STJ/SCON.
