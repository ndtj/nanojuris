# Tarefas executáveis

Legenda: `[L]` local/reproduzível, `[E]` depende da fonte oficial, `[H]` exige
decisão humana. O executor não deve marcar `[E]` ou `[H]` como concluída sem a
evidência correspondente.

## Baseline e contratos

- [x] **T001 [L]** regenerar todos os inventários com `PYTHONPATH=src`.
- [x] **T002 [L]** validar chaves e contagens entre catálogo, superfície e programa.
- [x] **T003 [L]** reconciliar lifecycle, maturity, live e federation sem editar
  arquivos gerados manualmente.
- [x] **T004 [L]** finalizar estados `total_unknown`, `access_blocked` e
  `schema_invalid` na API e no Studio.
- [x] **T005 [L]** completar a matriz canônica de filtros e campos.
- [x] **T006 [L]** adicionar fixtures transversais de vazio externo versus vazio
  autoritativo.

## Primeiro grau estadual

- [ ] **T007 [E]** descobrir a rota pública oficial por tribunal.
- [ ] **T008 [E]** provar `degree=first`, coleção e escopo textual.
- [ ] **T009 [E]** validar filtros, paginação e ordenação.
- [ ] **T010 [E]** implementar parser e fixtures sanitizadas.
- [ ] **T011 [E]** validar detalhe, PDF/HTML, MIME, hash e extração.
- [x] **T012 [L]** habilitar federação somente após os oito gates. O gate
  reproduzível em `docs/coverage/first-degree-federation-gate-20260908.json`
  confirma 27 superfícies CJPG, 7 federadas com gates consistentes e 20
  lacunas preservadas fora do rollout.

## Segundo grau estadual

- [x] **T013 [E]** revalidar TJAC, TJAL, TJAM, TJES e TJMS. A rechecagem
  bounded de 2026-09-08 retornou HTTP 200 e registros CJSG para os cinco;
  detalhes controlados por acesso permanecem classificados separadamente em
  `docs/provider-discovery/cjsg-live-20260908-cycle67.json`.
- [x] **T014 [E]** fechar TJBA, TJDFT, TJMT, TJPA, TJPB e TJRN. A
  rechecagem bounded de 2026-09-08 retornou duas páginas válidas, sem
  sobreposição e com identidade explícita de segundo grau para os seis;
  evidência redigida em `docs/provider-discovery/state-b1-live-20260908-cycle69.json`.
- [x] **T015 [E]** fechar TJGO, TJPI, TJPR, TJRR, TJRS e TJTO. A rechecagem
  de 2026-09-08 retornou as duas páginas sem sobreposição para os seis
  providers, com identidade `degree=second`/`collection=CJSG`; ver
  `docs/provider-discovery/state-cjsg-live-20260908-cycle68.json`.
- [x] **T016 [E]** revisar TJRJ, TJSC e TJRO/eproc. TJRJ/TJSC retornaram
  registros de segundo grau no eproc com identidade e hash; TJRO mantém a
  separação entre CJSG e Liame. Evidências: `docs/provider-discovery/state-eproc-degree-live-20260908.json`
  e `docs/provider-discovery/tjro-cjsg-live-20260906.json`.
- [x] **T017 [E]** registrar alternativa oficial ou bloqueio terminal de TJAP,
  TJCE, TJPE e TJSP. TJAP foi confirmado como PJe de consulta processual, não
  jurisprudência textual; TJCE/TJPE/TJSP tiveram rechecagem CJSG oficial, com
  detalhe controlado preservado. Evidências: `docs/provider-discovery/tjap-pje-2g-alternative-live-20260907.json`,
  `docs/provider-discovery/cjsg-live-legitimate-recheck-20260906.json`,
  `docs/provider-discovery/tjpe-cjsg-jsf-live-20260907.json` e
  `docs/provider-discovery/tjsp-cjsg-detail-continuation-live-20260907.json`.
- [x] **T018 [E]** pesquisar TJMG, TJMA e TJSE sem presumir rota. Foram
  registradas a API pública CJSG do TJMG, a coleção curada de informativos do
  TJMA e o boletim textual de segundo grau do TJSE; nenhum deles foi ampliado
  para além do escopo comprovado. Evidências: `docs/provider-discovery/tjmg-modern-api-live-20260908.json`,
  `docs/provider-discovery/tjma-informativos-live-20260908.json` e
  `docs/provider-discovery/tjse-boletim-jurisprudencia-live-20260907.json`.

## Outras famílias

- [x] **T019 [E]** provar TRT/TST por autoridade e grau. TST foi validado
  com busca/detalhe publicos; TRT2 foi validado no ementario oficial com
  grau second e documento, mantendo a instabilidade CloudFront como partial.
  Evidencias: `docs/provider-discovery/tst-live-20260907-cycle60.json` e
  `docs/provider-discovery/trt2-ementario-live-20260907.json`.
- [x] **T020 [E]** provar TSE/TRE/SJUR como coleções distintas. O bundle oficial
  do frontend separa TSE/TRE, tipos de decisão e endpoints SJUR; o backend
  bounded respondeu 404/503 em 2026-09-08 e permaneceu fora da federação.
  Evidência: `docs/provider-discovery/tse-tre-sjur-live-20260908.json`.
- [ ] **T021 [E]** fechar TRF, STJ, STF, STM e CJF com detalhe documental.
- [x] **T022 [E]** materializar eproc federal somente por contrato específico.
  O adapter parametrizado comprova contrato comum por tribunal e a rechecagem
  de 2026-09-08 registrou `authority`, `branch=federal`, `degree=second`,
  `instance=second`, coleção e detalhe válido para TNU, TRF2 e TRF6 em
  `docs/provider-discovery/eproc-detail-live-20260908-cycle75.json`.

## Qualidade e documentos

- [x] **T023 [L]** concluir fixtures de sucesso, vazio, erro, bloqueio, drift e
  segunda página por provider aplicável. A matriz gerada em
  `docs/coverage/fixture-completeness-20260908.json` confirma fixture
  específica para 62/62 providers runtime e o envelope compartilhado dos cinco
  estados canônicos; segunda página é exigida somente nas 47 superfícies com
  paginação remota.
- [x] **T024 [L]** testar identidade CNJ, autoridade, grau, coleção e classe.
- [ ] **T025 [E]** validar datas de julgamento, publicação, atualização e
  disponibilização.
- [ ] **T026 [E]** validar links de detalhe e documentos bounded.
- [x] **T027 [L]** concluir deduplicação exata, aproximada e republicação.
- [x] **T028 [L]** medir completude por campo e confiança do total.

## Federação e plataforma

- [x] **T029 [L]** expor status por fonte e filtros aplicados/local/ignorados.
- [x] **T030 [L]** executar smoke opt-in sem alterar rollout padrão.
- [x] **T031 [L]** garantir ranking determinístico independente da ordem de ondas.
- [x] **T032 [L]** congelar a ordem após interação do usuário no Studio.
- [x] **T033 [L]** adicionar razões de relevância e diagnóstico de resultado parcial.

## Operação e governança

- [x] **T034 [L]** gerar certificação, TTL, freshness e alertas de drift.
- [x] **T035 [L]** criar shadow mode e rollback de parser.
- [ ] **T036 [H]** obter decisão de licença, retenção e responsável por fonte.
- [ ] **T037 [H]** aprovar rótulos humanos de relevância para o benchmark.
- [x] **T038 [L]** executar suíte completa e auditoria de tarefas.
- [x] **T039 [L]** gerar handoff final sem commit, push ou deploy.

## Decisões fixadas em 2026-09-09

O mantenedor fixou escopo core + condicional, promoção apenas técnica local,
retenção de telemetria de 30 dias, cache live de 10 minutos e intervalo mínimo
de 2 segundos por provider. T036 e T037 continuam humanos; a matriz de 80
pré-rótulos não é aprovação.
