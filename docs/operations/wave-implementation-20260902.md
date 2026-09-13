# Fechamento técnico das ondas — 2026-09-05

## Onda 1 — runtime e documentos

Concluída no ambiente local. `nanojuris.transport` centraliza HTTPS allowlist,
timeouts, retries idempotentes, `Retry-After`, orçamento por host, circuit
breaker, cache de envelopes e limites de resposta. `DocumentReference` e o
cache content-addressed só carregam inteiro teor sob demanda e registram hash,
tipo, tamanho e `SourceTrace`. O inventário documental cobre as 60 entradas do
catálogo (52 runtime e 7 candidates, com 1 família em especificação; 34 runtime declaram suporte a
  inteiro teor).

A federação também interrompe com segurança uma fonte que repete a mesma página
sem novos identificadores, mantendo `complete=None` quando o provider não
comprova completude e registrando o motivo no envelope de completude.
Há ainda um orçamento configurável de páginas por fonte (`unified_max_pages`,
padrão 25), que limita endpoints sem total confiável sem mascarar a coleta
parcial.

## Onda 2 — providers e Juscraper

TJES/CJSG, TJES/CJPG, TJRN, TJGO, TJMT, TJPI, TJPR, TJRO, TJRS, TJSP/CJPG e TJTO
foram exercitados com fixtures e chamadas públicas bounded. TJTO agora mantém a decisão base quando o detalhe falha,
marcando `partial` e o tipo do erro. Nenhuma rota foi inventada e nenhum
provider bloqueado foi transformado em lista vazia.

## Onda 3 — cobertura e identidade

A matriz CJPG/CJSG e a topologia nacional continuam geradas offline, com
denominadores e lacunas explícitos. O estado medido na janela atual é 2/27 CJPG
e 5/27 CJSG live-validado. As demais fotografias são 4/5 EPROC,
1/27 JURIS, 4/9 PORTAL e 0/30 SJUR; isso mede bindings, não acervo integral.
Identidade canônica, deduplicação e preservação de `raw`
seguem como gates transversais.

## Onda 4 — operação segura

Runner de probes allowlisted, SLIs pontuais, redaction, governança de rollout e
runbook foram implementados. O catálogo publica somente status observado,
latência quando disponível, hash e limitações; não há canário contínuo nem
alerta instalado neste workspace.

A matriz de impacto de interfaces foi gerada para as 60 entradas em
`docs/operations/interface-impact-matrix-20260902.json` e `.md`. Ela
explicita SDK, CLI, MCP, Studio, federação, store e exports, mas não altera
o modo de rollout.

O registro canônico por superfície foi gerado em
`docs/coverage/surface-state-registry-20260902.json` e `.md`. Ele separa
`lifecycle`, `contract_status`, `live_status`, `federation_status` e
`legal_status`; portanto, uma linha marcada como implementada na matriz não é
contada como live-validada quando a evidência atual está bloqueada ou ausente.

Compatibilidade 60/60, SBOM/proveniência e release rehearsal foram registrados
em `docs/operations/release-compatibility-20260902.*`,
`release-provenance-20260902.*` e `release-rehearsal-20260902-final6.*`.

O plano executável para fechar as lacunas de primeiro e segundo grau está em
`docs/coverage/degree-coverage-roadmap-20260902.md`, com fases, critérios de
promoção e metas CJPG/CJSG separadas.

## Ondas 5 e 6 — bloqueios deliberados

O operador autorizou o uso técnico local/federado de fontes públicas que
passaram os gates, sem uma etapa interna adicional de licença. Redistribuição,
retenção, credenciais OCI, IAM, terraform apply, merge, tag, publicação e
deploy exigem autoridade e ambiente externo; permanecem fora deste ciclo.

## Evidências e reprodução

- Sweep dos sete candidates catalogados:
  `docs/provider-discovery/all-provider-sweep-20260905-cycle40.json`.
  TJRN e TRF3 tiveram rotas públicas observadas; os demais exibiram robots ou
  controle de acesso. Nenhum candidate foi promovido sem contrato de busca,
  fixtures, qualidade e evidência live reproduzível.
- Rechecagem de paginação TJRN:
  `docs/provider-discovery/tjrn-jurisprudencia-pagination-live-20260902-cycle22.json`
  (page=1 e page=2, HTTP 200, 20 registros, total 53.366); a evidência foi
  incorporada ao contrato atual e o provider está habilitado no rollout técnico
  local.

- Sweep live bounded de todos os 52 providers runtime e 7 candidates nesta janela:
  `docs/provider-discovery/all-provider-sweep-20260905-cycle40.json` (148 rotas
  declaradas, 2.314 observações, dez sinais de controle de acesso; observação
  de rota não é prova de dados).
- Contratos públicos exercitados com dados reais: smoke live bounded atual,
  com bloqueios explícitos preservados e sem bypass.

- Smoke federado das fontes promovidas:
  `docs/provider-discovery/federated-promotion-live-20260905-cycle71.json`
  (38/38 fontes chamadas no ciclo 71, zero erros e zero registros inválidos;
  totais desconhecidos permanecem `None`). O ciclo 51 validou a busca pública
  dos quatro bindings CJSG e o detalhe TJMS, mantendo os três controles de
  acesso no detalhe explícitos (`cjsg-live-20260905-cycle51.json`). O ciclo 43
  validou inteiro teor público em TNU, TRF2 e TRF6
  (`eproc-detail-live-20260905-cycle43.json`) e habilitou 38 fontes no
  manifesto técnico.

- Rechecagem live de grau CJPG/CJSG:
  `docs/provider-discovery/degree-bindings-live-20260902-cycle26.json` (TJES
  CJPG/CJSG e TJSP CJPG com HTTP 200 e dados; TJSP CJSG bloqueado por controle
  de acesso). Nenhum corpo jurídico foi persistido.

- `docs/provider-discovery/tjes-jurisprudencia-live-20260902-cycle19.json`;
- `docs/provider-discovery/tjrn-jurisprudencia-live-20260902-cycle17.json`;
- `docs/provider-discovery/tjto-jurisprudencia-detail-live-20260902-cycle18.json`;
- `docs/coverage/document-capability-inventory.json`;
- `docs/operations/provider-incident-runbook.md`.

Comandos principais: `python -m pytest -q`, `python -m ruff check .`,
`python -m ruff format --check .`, `python -m mypy src`,
`python -m tools.validate_sdd --root .`, `python -m compileall -q src tools tests`.

## Atualizacao do ciclo 65

Os smokes dedicados posteriores foram incorporados ao inventario e ao
manifesto: BNP/Pangea (59), TJPA BFF (60), TRF4 eproc (61), TJSP eproc (63),
CNJ (64) e TJRO LIAME (66). O smoke federado ciclo 71 chamou **38/38** fontes
habilitadas, com zero erros e zero registros invalidos; 16 fontes continuam opt-in e 6
permanecem bloqueadas. Totais desconhecidos continuam explicitos e mantem a
coleta parcial. A suite local final registrou **1185 passed, 23 skipped**.
