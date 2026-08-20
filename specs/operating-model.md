# Modelo operacional SDD — equipe humana e agentes

## Princípio

A equipe trabalha como um sistema de papéis especializados. Um agente pode
executar uma função, mas não deve ser a única autoridade sobre especificação,
implementação e aprovação da mesma mudança.

## Papéis humanos

| Papel | Responsabilidade principal |
| --- | --- |
| Product/Domain Owner | intenção do produto, prioridade e critérios jurídicos |
| Principal AI/Platform Architect | arquitetura, SDD, limites de agentes e decisões técnicas |
| Provider/Data Engineer | contratos, parsers, canonicalidade e provenance |
| Platform/SRE Engineer | OCI, Terraform, CI/CD, observabilidade e recuperação |
| Security/Privacy Reviewer | IAM, secrets, supply chain, LGPD e threat model |
| QA/Verification Engineer | testes, evidências, regressão e aceitação técnica |

## Papéis de agentes

| Agente | Entrada | Saída |
| --- | --- | --- |
| Discovery Agent | issue, contexto e repositório | perguntas, inventário e riscos |
| Spec Agent | intenção esclarecida | `spec.md` e critérios de aceite |
| Design Agent | spec aceita | `design.md`, contratos e ADRs |
| Planning Agent | design | `tasks.md` ordenado e estimável |
| Implementation Agent | tarefas | código, Terraform ou docs |
| Verification Agent | diff e spec | testes, falhas e `verification.md` |
| Security Agent | mudança e plano | threat model e achados |
| Release Agent | aprovação | deploy, smoke test e rollback |

## Gates

```text
discovery → spec review → design review → implementation → verification
→ security review → human acceptance → release
```

Uma mudança pode retornar a qualquer etapa anterior. “Código funciona” não é
critério suficiente para avançar para release.

## Matriz de autoridade

| Decisão | Agente propõe | Humano aprova |
| --- | --- | --- |
| comportamento do produto | sim | Product/Domain Owner |
| arquitetura | sim | Principal Architect |
| provider e dados | sim | Domain/Data Owner |
| IAM e exposição de rede | sim | Security/Platform Owner |
| código e testes | sim | reviewer técnico |
| produção e publicação | pode executar após gate | responsável operacional |
| destruição ou migração irreversível | não executa sozinho | aprovação explícita |

## Regra de revisão cruzada

Quem implementa não encerra sozinho a mudança. Toda alteração deve ser revisada
contra a especificação por pelo menos um papel diferente do implementador.
