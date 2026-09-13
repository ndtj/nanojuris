# SDD 0092 — blueprint de execução da cobertura nacional

Status: `proposed`  
Owner: `provider-engineering`, `data-quality`, `search`, `security`  
Escopo: planejamento e handoff; nenhum código de provider, publicação ou deploy.

Este pacote é o manual de execução para um modelo que continuará o trabalho da
NanoJuris sem depender do histórico da conversa. Ele consolida a cobertura
nacional de jurisprudência, o fechamento de filtros e documentos, a comparação
independente com o Juscraper e a fronteira de acesso público responsável.

Ele não substitui os contratos já aceitos. A precedência é:

1. `AGENTS.md` e `specs/constitution.md`;
2. SDDs específicos de provider;
3. SDD 0091 (handoff ouro);
4. este blueprint, somente para ordem e execução;
5. inventários gerados em `docs/coverage/`.

## Início rápido para outro modelo

1. Leia `AGENTS.md`, a constituição, `specs/README.md` e o SDD 0091.
2. Regenere os inventários e `specs/changes/0091-national-coverage-gold-handoff/baseline-20260908.json`
   com o runbook; não confie em números copiados deste arquivo.
3. Escolha um lote de no máximo três superfícies em
   `provider-batch-plan.json`.
4. Para cada superfície, siga `provider-workpack-template.md` e a ordem de
   descoberta do `AGENTS.md`.
5. Faça somente chamadas públicas bounded. Registre bloqueios como bloqueios.
6. Rode testes focados, gere inventários e atualize `verification.md` do SDD do
   provider.
7. Só habilite federação quando todos os gates estiverem comprovados.

## Artefatos deste pacote

| Arquivo | Finalidade |
| --- | --- |
| `spec-of-specs.md` | decomposição em pacotes e fronteiras |
| `spec.md` | requisitos normativos e critérios de aceite |
| `design.md` | arquitetura e estados de dados |
| `implementation-plan.md` | ondas técnicas ordenadas |
| `tasks.md` | backlog executável com dependências |
| `research.md` | fontes oficiais, literatura e Juscraper |
| `clarify.md` | decisões fechadas e perguntas pendentes |
| `traceability.md` | requisitos → tarefas → evidências |
| `threat-model.md` | ameaças, limites e acesso lícito |
| `lawful-access-playbook.md` | técnicas permitidas e classificações |
| `provider-workpack-template.md` | checklist repetível por provider |
| `surface-register.template.json` | registro canônico por superfície |
| `evidence-record.schema.json` | envelope de chamada live redigida |
| `promotion-gate.schema.json` | gate técnico de promoção |
| `provider-batch-plan.json` | ordem inicial de lotes |
| `execution-manifest.json` | comandos, limites e condição de parada |
| `GOAT_EXECUTOR_PROMPT.md` | prompt completo para o próximo modelo |
| `verification.md` | protocolo de verificação e fechamento local; dependências externas permanecem abertas |

## Estado atual observado

O estado vivo deve ser regenerado a partir dos inventários abaixo e do baseline
do SDD 0091 antes de qualquer decisão. O snapshot atual do repositório registra 69 fontes
catalogadas, 64 em runtime, 47 na busca unificada, 7/27 CJPG e 25/27 CJSG;
essas contagens são informativas, não uma declaração de cobertura nacional.

## Fronteira de acesso

Permitidos: HTTP público documentado, APIs/exports oficiais, fluxo normal de
navegador, redirects allowlisted, cookies e CSRF emitidos para a própria sessão,
paginação publicada, retry transitório cooperativo, ETag/Last-Modified,
sitemaps/RSS, contato com o tribunal e allowlist formal.

Proibidos: solver ou OCR de CAPTCHA/Turnstile, bypass de WAF, stealth,
spoofing, replay de token, rotação de IP/proxy para evasão, downgrade TLS,
fuzzing de endpoints privados, contorno de autenticação, exaustão de rate limit
e qualquer “zona de sombra”. Um desafio pode ser resolvido manualmente pelo
usuário em uma sessão autorizada, sem automatizar nem persistir o token.

Nenhum commit, push, tag, publicação, Terraform, OCI ou deploy é autorizado por
este pacote.
