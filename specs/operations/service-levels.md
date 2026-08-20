# Service levels iniciais

Status: `proposed`
Escopo: Studio público, API de busca e persistência da implantação inicial OCI.

Estes são alvos iniciais para orientar medição e arquitetura; não são promessa
comercial até que haja histórico de produção e aprovação do Product/Domain Owner
e do Platform/SRE Engineer.

## SLIs e SLOs candidatos

| ID | SLI | Alvo inicial | Janela | Exclusões e observações |
| --- | --- | --- | --- | --- |
| SLO-001 | disponibilidade de requisições HTTP válidas | >= 99,5% | mensal | manutenção planejada comunicada |
| SLO-002 | latência p95 do `/api/health` | <= 500 ms | mensal | medir no ponto de entrada público |
| SLO-003 | respostas de busca offline sem erro inesperado | >= 99,0% | mensal | separar erro de entrada de indisponibilidade |
| SLO-004 | falha de provider classificada sem virar `zero_results` | 100% dos casos observados | contínua | validar por testes e logs estruturados |
| SLO-005 | RPO do store | <= 24 h | por incidente | reduzir após rotina de backup comprovada |
| SLO-006 | RTO do serviço | <= 4 h | por incidente | depende de restauração ensaiada |

## Error budget e revisão

- O orçamento inicial de indisponibilidade de `SLO-001` é 0,5% da janela mensal.
- Releases de produção devem ser pausados ou explicitamente aceitos quando o
  orçamento estiver consumido.
- Os alvos devem ser revisados após 30 dias de métricas reais e após cada
  incidente relevante.

## Instrumentação mínima

- request ID e versão do artefato;
- latência, status HTTP e classe de falha;
- provider, estado de acesso, timeout e completeness sem registrar segredo;
- backup criado, restaurado e validado;
- dashboard e alerta com proprietário e runbook.
