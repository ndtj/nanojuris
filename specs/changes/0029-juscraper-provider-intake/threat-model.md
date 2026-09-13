# Threat model — intake de código externo

Status: pending

| ID | Ameaça | Impacto | Controle |
| --- | --- | --- | --- |
| TH-001 | licença/atribuição perdida | alto | ledger e review |
| TH-002 | dependência vulnerável importada | alto | adaptação seletiva e SBOM |
| TH-003 | cookie/token em fixture | alto | scan e sanitização |
| TH-004 | rota não oficial promovida | alto | fonte primária e dossier |
| TH-005 | comportamento externo tratado como contrato | alto | equivalence tests |
| TH-006 | atualização upstream silenciosa | médio | commit fixado |
| TH-007 | retry de 403 insiste contra controle de acesso | alto | política 0028 não retenta 401/403 de controle |
| TH-008 | exceção de detalhe engolida vira registro aparentemente completo | alto | outcome parcial e teste de falha por etapa |
| TH-009 | token publicado em configuração é tratado como segredo persistível | alto | revisão de finalidade, uso efêmero e redaction |
| TH-010 | superfície técnica agrupa collections distintas | alto | binding por collection/grau na topologia 0036 |

Nenhum update upstream é automático.
