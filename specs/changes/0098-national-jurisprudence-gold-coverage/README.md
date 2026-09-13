# SDD 0098 — Cobertura nacional ouro de jurisprudência

Status: `proposed`

Este pacote é um handoff executável para outro modelo concluir a cobertura
nacional de jurisprudência do NanoJuris. Ele consolida inventário de superfícies,
contratos, acesso público legítimo, qualidade de inteiro teor, federação,
operação e gates humanos em uma única mudança versionada.

## Como usar

1. Ler `spec-of-specs.md`, `spec.md`, `design.md`, `lawful-access-playbook.md`
   e `GOAT_EXECUTOR_PROMPT.md`.
2. Regerar o baseline com os comandos em `execution-manifest.json`.
3. Regenerar `national-source-task-matrix.json` e selecionar um lote de no
   máximo três superfícies conforme
   `provider-family-matrix.md`.
4. Executar somente as tarefas dependentes de evidência disponível; registrar
   bloqueios externos sem convertê-los em vazio.
5. Atualizar `verification.md` e os dossiês do provider trabalhado.
6. Rodar `python tools/validate_sdd.py` e os gates da seção de verificação.

Este pacote não autoriza commit, push, publicação, deploy, mudança de produção,
uso de credenciais pessoais ou contorno de CAPTCHA, WAF, Turnstile, login,
limites de frequência ou TLS. A expressão “contornar bloqueio” significa apenas
encontrar uma superfície oficial alternativa, uma exportação pública ou uma
autorização formal do mantenedor.

## Baseline observado em 2026-09-08

| Métrica | Valor |
| --- | ---: |
| Fontes documentadas | 73 |
| Providers em runtime | 68 |
| Fontes na busca unificada | 50 |
| Fontes primárias textuais | 45 |
| Fontes com algum documento/inteiro teor | 56 |
| Superfícies estaduais de segundo grau completas | 25/27 |
| CJPG comprovado | 8/27 |
| CJSG comprovado | 25/27 |
| Tarefas abertas | 60 (44 externas, 16 humanas) |
| Gates locais do SDD 0091 | 10 aprovados, 0 pendentes |

Os números são apenas o ponto de partida e devem ser regenerados antes de cada
lote. Eles não significam disponibilidade permanente nem aprovação jurídica.

## Artefatos

- `spec-of-specs.md`: decomposição dos pacotes e gates.
- `spec.md`: requisitos funcionais, não funcionais e critérios de aceite.
- `design.md`: arquitetura, contratos, estados e decisões de segurança.
- `research.md`: evidências locais, hipóteses e limites do Juscraper.
- `clarify.md`: decisões ainda necessárias e perguntas abertas.
- `implementation-plan.md`: ondas, ordem de execução e Definition of Done.
- `provider-family-matrix.md`: inventário orientador por ramo, grau e coleção.
- `national-source-task-matrix.json` e `national-source-task-matrix.md`:
  inventário gerado de autoridades core e condicionais, estado atual por
  superfície e tarefas T047–T060.
- `lawful-access-playbook.md`: técnicas permitidas e proibidas para fontes
  públicas, incluindo o caso de desafio passivo.
- `tasks.md`: backlog executável com dependências e responsáveis.
- `traceability.md`: ligação requisito → tarefa → evidência.
- `threat-model.md`: ameaças de coleta, segurança e conformidade.
- `execution-manifest.json`: manifesto de execução para agentes.
- `coverage-state.schema.json`, `evidence-record.schema.json` e
  `promotion-gate.schema.json`: contratos de dados.
- `quality-benchmark.json`: consultas e métricas de avaliação.
- `GOAT_EXECUTOR_PROMPT.md`: prompt operacional autocontido para o próximo
  modelo.
- `verification.md`: registro de execução deste pacote e do handoff.

## Fontes de verdade relacionadas

- `specs/changes/0091-national-coverage-gold-handoff/`
- `specs/changes/0092-national-coverage-execution-blueprint/`
- `docs/coverage/source-of-truth.md`
- `docs/coverage/public-access-boundary-playbook-20260908.md`
- `docs/registry/provider-catalog.full.json`
- `docs/coverage/state-appellate-program-20260905.json`
- `docs/coverage/surface-state-registry-20260902.json`
- `docs/provider-discovery/juscraper-parity-assessment-20260906.md`
