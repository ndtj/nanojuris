# Design da mudança

Referência: `specs/changes/0003-premium-team-operating-model/spec.md`

## Organização

```text
Product/Domain Owner humano
            |
   Architecture Lead ───── Security/Privacy Lead
            |
  ┌─────────┼──────────┬──────────────┐
  v         v          v              v
Discovery  Provider   Data Quality   Platform/SRE
  Lead     Engineering   Lead          Lead
  |        Lead           |              |
  └────────┴──────────────┴──────────────┘
            |
      QA/Verification Lead
            |
   Documentation/SDD Lead
            |
      Human release gate
```

## Papéis e entregáveis

| Papel | Missão | Entregas principais |
| --- | --- | --- |
| Product/Domain Owner | decidir valor, escopo e prioridade | intenção, aceite, decisão de maturidade |
| Architecture Lead | manter coerência técnica e evolução | design, ADR, limites, decisões |
| Legal Data/Jurimetry Lead | garantir significado jurídico e qualidade analítica | taxonomia, identidade, campos, critérios de cobertura |
| Provider Discovery Lead | investigar fontes e rotas | `evidence.json`, rotas, XHR, fixtures candidatas, drafts |
| Provider Engineering Lead | transformar contrato em provider | código, parser, adapter, traces |
| Data Quality Lead | provar canonicalidade e completude | golden fixtures, invariantes, avaliação e regressão |
| Security/Privacy Lead | revisar confiança, dados e supply chain | threat model, revisão de segredos e permissões |
| Platform/SRE Lead | tornar operável e recuperável | CI/CD, SLO, logs, alertas, backup e runbook |
| QA/Verification Lead | fechar a cadeia requisito-prova | testes, matriz, evidências e relatório |
| Documentation/SDD Lead | preservar intenção e handoff | specs, dossiês, source contracts, changelog |

## Agentes especializados

| Agente | Pode fazer | Não encerra sozinho |
| --- | --- | --- |
| Discovery Agent | inventário, coleta bounded e hipóteses | autoridade da fonte ou maturidade |
| Spec Agent | `research`, `clarify`, `spec` e ACs | aceite do domínio |
| Design Agent | design, ADR e contratos técnicos | aprovação arquitetural |
| Planning Agent | decomposição e dependências | prioridade de produto |
| Implementation Agent | código, testes e documentação | revisão da própria mudança |
| Data Evaluation Agent | fixtures, invariantes e análise | classificação final de cobertura |
| Security Agent | threat model e achados | aceite do risco pelo responsável |
| Verification Agent | testes, comandos e `verification.md` | aprovação de release |
| Release Agent | execução após todos os gates | autorização humana de produção |

## RACI mínimo por provider

Legenda: `R` responsável por executar, `A` autoridade final, `C` consultado,
`I` informado.

| Atividade | Domain | Arch | Discovery | Provider | Data | Security | SRE | QA | Docs |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| intenção e escopo | A/R | C | C | I | C | I | I | C | R |
| pesquisa de fonte | A | C | R | C | C | C | I | C | R |
| contrato de provider | A | C | C | R | R | C | I | C | R |
| parser e adapter | C | A | C | R | R | C | I | C | R |
| fixtures e avaliação | C | C | C | R | A/R | C | I | R | C |
| threat model | I | C | C | C | C | A/R | C | C | R |
| operação e SLO | I | A | I | C | C | C | A/R | C | R |
| verificação | C | C | C | C | R | C | C | A/R | R |
| aceite e release | A/R | C | I | I | C | C | R | C | R |

## Fluxo operacional

```text
inspect → research → clarify → specify → design → plan → apply
        → verify → cross-review → human acceptance → release → observe
```

Cada etapa produz um artefato. Reprovação retorna à primeira etapa compatível;
não há aprovação implícita por ausência de comentários.

## Níveis de revisão

- `L1`: documentação ou refatoração sem mudança de comportamento;
- `L2`: provider, parser, fixture ou contrato de fonte;
- `L3`: dados canônicos, jurimetria, MCP/Studio, segurança ou produção;
- `L4`: migração irreversível, exposição pública ou alteração de governança.

L1 exige QA e documentação. L2 acrescenta domínio, provider/data e QA. L3
acrescenta arquitetura e segurança. L4 exige aprovação humana explícita e
plano de rollback/restore.
