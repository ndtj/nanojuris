# Fechamento local das ondas — 2026-09-05

Este documento registra o que foi efetivamente implementado nesta rodada. A
promoção técnica local/federada autorizada pelo operador está refletida no
manifesto; não há autorização de redistribuição nem ações de produção.

| Onda | Estado local | Evidência |
|---|---|---|
| P0 — semântica e segurança de resultados | concluída | `SearchPage.total_known`, estados de acesso/extração, orçamento de páginas por fonte, guarda de páginas repetidas e coleta por checkpoint |
| P1 — camadas de dados | concluída | filtros canônicos, migração/indexes SQLite, FTS5 opcional, linhagem por campo, deduplicação CNJ conservadora, cache limitado |
| P2 — promoção de adapters | concluída com limites | trinta e oito providers passaram os gates técnicos e foram habilitados no rollout federado local; candidatos, fontes incompletas e bloqueios permanecem explícitos |
| P3 — cobertura nacional | em expansão | matriz e inventários regenerados; lacunas permanecem mensuradas, sem alegação de cobertura total |
| P4 — operação segura | parcialmente concluída localmente | diagnósticos e estados operacionais são rastreáveis; observabilidade distribuída e shadow mode dependem de infraestrutura |
| P5 — validação externa | fora do escopo técnico local | a decisão do operador dispensa uma etapa interna adicional para uso técnico local/federado; redistribuição, retenção e publicação continuam não autorizadas |
| P6 — publicação/OCI | não executada | deliberadamente fora desta rodada |

## Regras de promoção

Um provider só pode ser promovido após contrato reproduzível, chamada pública
ou autorização formal, fixture sanitizada de sucesso/vazio/erro/timeout/schema,
validação de conteúdo jurídico e rastreabilidade. Neste ciclo, o operador
aceitou o uso técnico local/federado de todas as fontes que passam os gates;
isso não autoriza redistribuição ou produção. HTTP 403,
CAPTCHA, WAF, login, TLS, timeout ou rate limit nunca são convertidos em lista
vazia. DataJud e consultas processuais não substituem jurisprudência textual.

## Artefatos regenerados

- Evidência live bounded nacional e bindings de grau: `docs/provider-discovery/all-provider-sweep-20260905-cycle40.json`, complementada pelos contratos e paginação registrados em `docs/provider-discovery/`.

- `docs/quality/provider-quality.json` e `.md`, com `operational_blocked_providers`
  separado de `critical_gap_providers`.
- catálogos, matriz de cobertura, inventário de documentos e auditoria
  documental gerados pelos scripts oficiais.
- registro canônico de estado por superfície CJPG/CJSG em
  `docs/coverage/surface-state-registry-20260902.json` e `.md`, separando
  contrato, live, federação e aprovação legal.
- matriz de impacto das interfaces para as 60 entradas em
  `docs/operations/interface-impact-matrix-20260902.json` e `.md`.
- auditoria de compatibilidade 60/60 em `docs/operations/release-compatibility-20260902.json` e `.md`,
  SBOM/proveniência em `docs/operations/release-provenance-20260902.json` e `.md`,
  e rehearsal final de wheel/sdist em
  `docs/operations/release-rehearsal-20260902-final6.json` e `.md`.
- SDDs `0065-data-quality-completion` e `0066-degree-surface-contracts` com
  tarefas marcadas e verificação local. O manifesto de distribuição exclui
  somente relatórios operacionais gerados, mantendo testes e código-fonte no
  sdist.

## Gate final

`python -m pytest -q` terminou com **1182 passed, 23 skipped** na rechecagem final.
Também passaram Ruff, formatação, mypy, compilação e `validate_sdd`.

No repositório de plataforma, `python -m pytest -q` terminou com **143 passed**,
Ruff e mypy passaram em 17 módulos. No repositório de infraestrutura,
`terraform fmt -check -recursive` e `terraform validate` passaram; nenhum
`terraform apply` foi executado.

Os números de cobertura são fotografias do catálogo e das evidências disponíveis
em 2026-09-05; não representam disponibilidade futura dos tribunais.

## Rodada live e fechamento local adicional

Em 2026-09-05 foi executado um sweep público bounded dos 52 providers runtime
e 7 candidates: todos tiveram alguma rota declarada observada (148 rotas
declaradas, 2.314 observações e dez sinais de controle de acesso). Observação de rota não é
prova de resultado de jurisprudência.

Também foram executados 26 cenários de smoke live: respostas válidas e
bloqueios explícitos foram preservados como estados distintos. Os corpos das
respostas não foram persistidos e nenhum controle de acesso foi contornado.
O sweep atual registrou 52 providers runtime e 7 candidates observados, sem
falhas de execução.

O smoke federado das fontes promovidas está em
`docs/provider-discovery/federated-promotion-live-20260905-cycle71.json`: 38/38
fontes chamadas sem erros no ciclo 71. O ciclo 51 validou a busca pública
dos quatro bindings CJSG (TJAC, TJAL, TJAM e TJMS), mantendo controle de acesso
no detalhe explícito; o TJMS foi promovido por cumprir os gates de busca e
contrato. O ciclo 43 adicionou a validação
live de inteiro teor EPROC em
`docs/provider-discovery/eproc-detail-live-20260905-cycle43.json` e elevou o
manifesto técnico para 38 fontes habilitadas; cada execução continua
deliberadamente parcial por limitar-se a uma página.

A consolidação offline regenerou workpacks, inventário documental, matriz de
cobertura, quadro de adapters, ledger de fechamento e auditorias. O manifesto

## Atualizacao do ciclo federado 65

Depois dos smokes dedicados de BNP/Pangea, TJPA BFF, TRF4 eproc, TJSP eproc,
CNJ e TJRO LIAME, o manifesto tecnico permaneceu com 38 fontes habilitadas localmente, 16
opt-in e 6 bloqueadas. O ciclo federado 71 executou **38/38** chamadas sem
erros ou registros invalidos; 18 fontes nao informam total confiavel e, por
isso, `collection_complete` permanece explicitamente falso. Nenhuma fonte
bloqueada foi convertida em vazio e nenhuma acao de producao foi executada.
de promoção habilita trinta e oito fontes tecnicamente prontas no rollout local; as
demais continuam em `opt_in` ou `blocked` conforme contrato e evidência.
