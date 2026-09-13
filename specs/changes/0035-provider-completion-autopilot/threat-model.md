# Threat model — execução autônoma

Status: pending

| ID | Ameaça | Impacto | Controle |
| --- | --- | --- | --- |
| TH-001 | loop sem progresso | alto | estados, três ocorrências e checkpoint |
| TH-002 | alteração ampla sem revisão | alto | uma unidade por ciclo e cross-review |
| TH-003 | tráfego excessivo | alto | offline-first e budget bounded |
| TH-004 | bypass por insistência | alto | política deny inviolável |
| TH-005 | estado corrompido | alto | JSON versionado e escrita preservadora |
| TH-006 | aceite falso | alto | DoD, traceability e verification |
| TH-007 | produção sem autorização | alto | gate humano explícito |
| TH-008 | segredo em artefato | alto | secret scan e redaction |
| TH-009 | conflitos com mudanças do usuário | alto | status/diff antes de editar |
| TH-010 | bloqueio externo tratado como conclusão | alto | waiting_evidence e deferimento revisável |
| TH-011 | conclusão obsoleta após mudança de evidência | alto | fingerprint e estado stale |
| TH-012 | número atual usado como cobertura nacional | crítico | topologia 0036 por coleção |

Autonomia amplia persistência, não autoridade.
