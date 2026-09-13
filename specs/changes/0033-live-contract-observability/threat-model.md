# Threat model — observabilidade live

Status: pending

| ID | Ameaça | Impacto | Controle |
| --- | --- | --- | --- |
| TH-001 | probe vira carga indevida | alto | budget e baixa frequência |
| TH-002 | query contém PII | alto | queries sintéticas permitidas |
| TH-003 | resposta vaza conteúdo | médio | minimização e hash |
| TH-004 | alerta causa retry storm | alto | dedupe e circuit breaker |
| TH-005 | dashboard afirma saúde atemporal | alto | timestamp/freshness |
| TH-006 | credencial entra no runner | alto | fontes públicas allowlisted |

Fontes autenticadas não entram sem novo threat model e autorização.
