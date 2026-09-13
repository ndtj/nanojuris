# SDD 0091 — handoff de cobertura nacional ouro

Este diretório é o pacote de execução para outro modelo. Ele não afirma que a
cobertura nacional está concluída: o snapshot atual e as lacunas estão em
`baseline-20260908.json` e nos inventários gerados em `docs/coverage/`.

## Entrada recomendada

1. Leia [`GOAT_EXECUTOR_PROMPT.md`](GOAT_EXECUTOR_PROMPT.md).
2. Consulte [`MODEL_HANDOFF.md`](MODEL_HANDOFF.md) para o roteiro compacto e
   o estado atual.
3. Consulte o índice operacional
   [`national-coverage-model-handoff-20260908.md`](../../../docs/coverage/national-coverage-model-handoff-20260908.md).
4. Regenere o baseline com os comandos de `model-runbook.md`.
5. Escolha um lote de 1–3 providers em `provider-batch-plan.json`.

## Arquivos do pacote

| Arquivo | Finalidade |
| --- | --- |
| `spec-of-specs.md` | escopo, invariantes e artefatos obrigatórios |
| `spec.md` | requisitos e critérios de aceite |
| `design.md` | arquitetura de superfícies, gates e estados |
| `implementation-plan.md` | ondas e comandos de fechamento |
| `tasks.md` | tarefas classificadas como locais, externas ou humanas |
| `provider-workpack-template.md` | checklist por provider |
| `surface-register.template.json` | registro canônico por superfície |
| `evidence-record.schema.json` | formato de evidência live redigida |
| `promotion-gate.schema.json` | gate técnico de promoção |
| `lawful-access-decision-matrix.md` | ações permitidas e estados de bloqueio |
| `model-runbook.md` | ciclo operacional do executor |
| `GOAT_EXECUTOR_PROMPT.md` | instrução autônoma completa |
| `MODEL_HANDOFF.md` | entrada operacional compacta para outro modelo |
| `model-handoff-status.json` | snapshot machine-readable do handoff |
| `handoff-artifact-manifest.json` | índice verificável de artefatos, gates, limites e comandos |
| `CONTINUATION_BRIEF.md` | resumo operacional para iniciar outro modelo sem o histórico da conversa |
| `surface-workpacks/manifest.json` | inventário gerado das 150 superfícies, seus gates e lacunas |
| `docs/benchmarks/live-ranking-evaluation-20260908.json` | resultado técnico do benchmark, com métricas pendentes de rótulos humanos |
| `verification.md` | resultados locais e limitações do handoff |
| `baseline-20260908.json` | snapshot; deve ser regenerado antes de confiar |

## Fronteira de acesso

O pacote permite apenas acesso público normal, APIs/exports oficiais,
paginação publicada, retry cooperativo, redirects allowlisted e suporte ou
allowlist concedidos pela autoridade. CAPTCHA, Turnstile, WAF, autenticação,
403, 429, TLS e schema inválido são estados explícitos. Não existe autorização
para solver/OCR, stealth, spoofing, rotação de IP/proxy, replay de token,
fuzzing privado, downgrade TLS ou exploração de “zona de sombra”.

## Condição de parada

Promova apenas quando os oito gates estiverem comprovados. Se restarem somente
bloqueios externos ou decisões humanas, registre a evidência uma vez e entregue
um relatório objetivo; não converta bloqueio em vazio e não declare 27/27.

Commit, push, publicação, OCI, Terraform e deploy estão fora do escopo.

## Lote verificado em 2026-09-08

O provider `tjma_informativos` foi adicionado como fonte oficial curada e
opt-in, com adapter, contrato, fixture, evidencia live e testes. Ele preserva
inteiro teor PDF sob demanda, mas nao e promovido como CJSG geral. O fechamento
local passou com 1578 testes e 26 skips; os numeros nacionais devem continuar
sendo regenerados pelos comandos do runbook.

O provider diagnostico `trt15_jurisprudencia` possui contrato, fixtures de
sucesso/vazio/bloqueio/schema drift e chamada bounded registrada. A fonte
respondeu a pagina publica, mas exigiu CAPTCHA antes de entregar resultados;
por isso permanece explicitamente bloqueada e nao e contada como jurisprudencia
vazia ou provider promovido.

O Studio também está ligado ao contrato de busca live inteligente: o modo
adaptativo e a versão do ranking são enviados explicitamente à API, e planos
com ondas respeitam a execução sequencial bounded. Consulte a seção de
atualização web em `verification.md`; a calibração humana do benchmark e o
rollout continuam pendentes.
