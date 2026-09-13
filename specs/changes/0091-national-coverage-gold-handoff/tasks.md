# Tarefas — handoff executável

Legenda: `[L]` local/reproduzível, `[E]` depende de fonte externa, `[H]`
exige decisão humana. Não marcar `[E]` ou `[H]` sem evidência correspondente.

## Baseline e verdade única

- [x] **T001 [L]** ler a ordem obrigatória do `AGENTS.md` para o provider alvo.
- [x] **T002 [L]** regenerar catálogo, matriz, ledger, programa, manifesto,
  inventário de fixtures e auditoria de tarefas com `PYTHONPATH=src`.
- [x] **T003 [L]** conferir que cada provider catalogado possui `surface_id`,
  owner, próxima ação, evidence IDs e TTL.
- [x] **T004 [L]** reconciliar runtime, live, quality e federation sem editar
  JSON gerado manualmente.
- [x] **T005 [L]** produzir o baseline assinado por hash em
  `baseline-20260908.json`.

## Contrato e capacidades

- [x] **T006 [L]** fechar estados `total_known`, `total_unknown` e zero
  autoritativo na API e no Studio.
- [x] **T007 [L]** mapear grau, instância, ramo, coleção, tipo, classe, órgão,
  autoridade, datas e origem em `CanonicalDecision`.
- [x] **T008 [L]** catalogar filtros nativos, traduzidos, locais, ignorados e
  não suportados com evidência por endpoint.
- [x] **T009 [L]** testar que filtros identificadores sem suporte falham
  explicitamente em vez de serem descartados.
- [x] **T010 [L]** implementar envelope federado com filtros por fonte,
  completude, trace, latência, páginas e estado do total.
- [x] **T011 [L]** validar determinismo, deduplicação, republicação e ordem
  independente da chegada das ondas.

## Primeiro grau e segundo grau

- [ ] **T012 [E]** descobrir e classificar uma rota CJPG oficial por tribunal;
  registrar geral, curada, contextual ou indisponível.
- [ ] **T013 [E]** provar `degree=first`, coleção e escopo textual da CJPG.
- [x] **T014 [E]** revalidar as cinco superfícies CJSG da Onda A. A chamada
  bounded de 2026-09-08 confirmou TJAC, TJAL, TJAM, TJES/PJe2G e TJMS; estados
  de detalhe/controlados por acesso foram preservados no envelope
  `docs/provider-discovery/cjsg-live-20260908-cycle67.json`.
- [x] **T015 [E]** fechar APIs B1 na ordem definida pelo pacote 0089. A
  rechecagem bounded de 2026-09-08 retornou duas páginas válidas, sem
  sobreposição e com identidade explícita de segundo grau para TJBA, TJDFT,
  TJMT, TJPA, TJPB e TJRN; evidência redigida em
  `docs/provider-discovery/state-b1-live-20260908-cycle69.json`.
- [x] **T016 [E]** fechar portais B2 na ordem definida pelo pacote 0089. TJGO,
  TJPI, TJPR, TJRR, TJRS e TJTO passaram rechecagem de duas páginas com
  identidade CJSG, sem sobreposição ou bloqueio; evidência redigida em
  `docs/provider-discovery/state-cjsg-live-20260908-cycle68.json`.
- [x] **T017 [E]** revisar TJRJ, TJSC e TJRO/eproc sem contar contexto como
  jurisprudência geral. O eproc retornou `degree=second` nos dois primeiros e
  TJRO foi mantido na rota CJSG independente de Liame; ver
  `docs/provider-discovery/state-eproc-degree-live-20260908.json`.
- [x] **T018 [E]** avaliar alternativas oficiais para TJAP, TJCE, TJPE e TJSP;
  registrar bloqueio terminal quando necessário. TJAP foi confirmado como PJe
  de consulta processual, TJPE tem fluxo JSF público válido e TJCE/TJSP mantêm
  estados de detalhe/controlados separados; ver as evidências listadas no
  pacote 0089.
- [x] **T019 [E]** pesquisar TJMG, TJMA e TJSE sem inventar rotas. A API CJSG
  do TJMG, os informativos curados do TJMA e o boletim textual do TJSE foram
  documentados com seus limites, sem contar coleção curada como acervo geral;
  ver os três artefatos live de 2026-09-07/08.

## Famílias adicionais

- [x] **T020 [E]** inventariar TRT/TST por autoridade, grau e coleção. O
  inventario diferencia TST/JURISPRUDENCIA e TRT2_EMENTARIO, com identidade
  labor/second e limites de estabilidade preservados; ver os dois artefatos
  live citados no pacote 0082.
- [x] **T021 [E]** inventariar TSE/TRE/SJUR separando jurisprudência de boletim.
  A rota oficial foi identificada no bundle do frontend; as tentativas bounded
  de 2026-09-08 receberam 404/503 no backend e foram classificadas como
  `source_unavailable`, sem tratar como vazio. Evidência:
  `docs/provider-discovery/tse-tre-sjur-live-20260908.json`.
- [ ] **T022 [E]** fechar TRF, STJ, STF, STM e CJF com contratos documentais.
- [x] **T023 [E]** materializar eproc federal após contrato comum provado. O
  adapter parametrizado e a evidência live bounded de TNU, TRF2 e TRF6
  registram identidade explícita de segundo grau e detalhe HTML válido em
  `docs/provider-discovery/eproc-detail-live-20260908-cycle75.json`.

## Parser, documentos e fixtures

- [x] **T024 [L]** executar o template de workpack para cada superfície. O
  manifesto `surface-workpacks/manifest.json` materializa 150 superfícies, 125
  obrigatórias e conserva gates incompletos sem promover fontes.
- [ ] **T025 [E]** criar fixture real sanitizada de sucesso e segunda página.
- [ ] **T026 [E]** criar fixture de vazio autoritativo sem confundir com bloqueio.
- [x] **T027 [L]** criar fixtures de parâmetro inválido, schema drift e erro
  externo para cada parser aplicável.
- [ ] **T028 [E]** validar datas de julgamento, publicação, atualização e
  disponibilização, preservando granularidade e timezone.
- [ ] **T029 [E]** validar detalhe e documento por host allowlist, redirect,
  MIME, magic bytes, tamanho, hash e extração.
- [x] **T030 [L]** implementar `DocumentReference`, vínculo e provenance por
  página/trecho quando aplicável.
- [x] **T031 [L]** isolar OCR permitido com limites; nunca OCRizar desafio.

## Juscraper e acesso público

- [x] **T032 [L]** fixar commit e licença do Juscraper observado.
- [ ] **T033 [E]** comparar rota, payload, seletores, paginação e filtros com a
  fonte oficial atual.
- [x] **T034 [L]** implementar parser independente e teste diferencial.
- [ ] **T035 [E]** usar apenas HTTP público documentado, fluxo normal de browser,
  redirects oficiais e rate limit cooperativo.
- [x] **T036 [E]** registrar uma única evidência de CAPTCHA/WAF/403/429/login,
  sem repetir chamadas contra a proteção. O playbook de fronteira pública e
  seus artefatos redigidos consolidam os bloqueios observados, sem classificar
  qualquer um como vazio e sem repetir desafios. Evidências:
  `docs/coverage/public-access-boundary-playbook-20260908.md` e
  `docs/coverage/public-access-boundary-playbook-20260908.json`.
- [ ] **T037 [H]** solicitar allowlist, API, export ou esclarecimento ao tribunal
  quando necessário.

## Federação e busca web

- [x] **T038 [L]** executar smoke opt-in dos providers com oito gates.
- [x] **T039 [L]** promover tecnicamente apenas `runtime`, contrato, fixtures,
  live, quality e acesso público válidos.
- [x] **T040 [L]** integrar fontes federadas no planner 0077 respeitando papéis
  primário, precedente e contextual.
- [x] **T041 [L]** exibir chips de filtros inferidos e razões de relevância.
- [x] **T042 [L]** congelar ordem após foco, clique, seleção, abertura ou scroll.
- [x] **T043 [L]** manter modo “todos os tribunais” explícito e auditável.

## Qualidade e operação

- [x] **T044 [L]** executar o harness reproduzível de benchmark e persistir a
  avaliação pendente de rótulos. A parte CPU foi medida em 2026-09-08 para 240
  candidatos: p95 de 62,5 ms e zero chamadas de rede, em
  `docs/benchmarks/live-ranking-performance-20260908.json`. O avaliador
  executou sem inventar nDCG/P@5/MRR ou taxa de irrelevantes e registrou
  `pending_human_labels` em `docs/benchmarks/live-ranking-evaluation-20260908.json`;
  a aprovação dos rótulos continua exclusivamente em T045.
- [ ] **T045 [H]** aprovar rótulos de relevância e holdout do benchmark.
- [x] **T046 [L]** configurar smoke periódico, TTL, schema drift, completude,
  shadow mode e rollback do parser.
- [ ] **T047 [H]** aprovar licença, retenção, responsável e promoção padrão.
- [x] **T048 [L]** regenerar todos os inventários e rodar suíte completa.
- [x] **T049 [L]** auditar TODOs, tarefas pendentes, artefatos desatualizados e
  divergências entre catálogo e evidência. O resultado está em
  `docs/coverage/0091-artifact-audit-20260908.json` e `.md`.
- [x] **T050 [L]** preencher `verification.md` com resultados objetivos.
- [x] **T051 [L]** produzir relatório final sem commit, push, deploy ou produção.
  O relatório é `verification.md`; ele declara pendências externas e humanas
  explicitamente e não afirma cobertura nacional concluída.

## Decisões fixadas em 2026-09-09

Consultar `docs/coverage/decision-record-20260909.json`. Promoção técnica não
autoriza rollout padrão; fontes curadas permanecem opt-in; a revisão do
benchmark permanece pendente até o mantenedor validar as 80 linhas.
