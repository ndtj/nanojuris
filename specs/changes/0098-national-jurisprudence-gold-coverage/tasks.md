# Tarefas — execução da cobertura nacional ouro

Legenda: `[L]` local e verificável, `[E]` depende de fonte externa, `[H]`
decisão humana. Todas começam pendentes para o próximo modelo; marcar como
concluída somente com evidência em `verification.md` ou no dossiê do provider.

## Baseline e governança técnica

- [x] **T001 [L]** Ler AGENTS, constituição, SDD 0091/0092 e este pacote.
- [x] **T002 [L]** Regenerar catálogo, ledger, matriz, programa, manifest e
  auditoria de tarefas; salvar hashes do baseline.
- [x] **T003 [L]** Reconciliar runtime, catálogo, live, qualidade e federação.
- [x] **T004 [L]** Registrar toda superfície obrigatória sem provider, contrato ou
  evidence ID.
- [x] **T005 [L]** Validar que nenhum artefato gerado foi editado manualmente.

## Acesso público e descoberta

- [ ] **T006 [E]** Confirmar fonte oficial, coleção e grau por superfície.
- [ ] **T007 [E]** Testar uma rota pública bounded por lote de até três fontes.
- [ ] **T008 [E]** Procurar API, exportação, RSS/sitemap/dataset e portal oficial
  alternativo antes de scraping HTML.
- [ ] **T009 [E]** Classificar bloqueio, desafio passivo/obrigatório, timeout,
  rate limit, TLS e schema sem converter para vazio.
- [ ] **T010 [H]** Registrar autorização formal, allowlist, termos e retenção
  quando a fonte exigir decisão externa.
- [x] **T011 [L]** Comparar rota e semântica com Juscraper sem copiar código.

## Contratos e adapters

- [x] **T012 [L]** Fechar `ProviderCapabilities` e filtros remotos/traduzidos/
  locais/ignorados.
- [x] **T013 [L]** Fechar envelope `SearchPage`, total e `access_status`.
- [x] **T014 [L]** Implementar parser independente usando transporte compartilhado.
- [x] **T015 [L]** Preservar campos canônicos, `raw`, `SourceTrace` e ausência
  explícita.
- [x] **T016 [L]** Validar paginação, cursor/offset, ordenação e sobreposição.
- [x] **T017 [L]** Implementar detalhe/documento sob demanda com limites.

## Fixtures, documentos e qualidade

- [x] **T018 [L]** Criar fixture sanitizada de sucesso.
- [x] **T019 [L]** Criar fixture de vazio autoritativo e vazio não confirmado.
- [x] **T020 [L]** Criar fixtures de parâmetro inválido, bloqueio e schema drift.
- [ ] **T021 [E]** Obter segunda página quando a fonte suportar.
- [ ] **T022 [E]** Validar PDF/HTML, MIME, hash, tamanho, codificação e extração.
- [x] **T023 [L]** Validar autoridade, ramo, grau, instância, coleção, classe,
  órgão, relator, datas e identificador.
- [x] **T024 [L]** Executar deduplicação exata e aproximada conservadora.
- [x] **T025 [L]** Medir completude por campo e qualidade por registro.

## Federação e relevância

- [x] **T026 [L]** Executar smoke federado opt-in sem alterar rollout padrão.
- [x] **T027 [L]** Retornar estado, latência, páginas, total, filtros e trace por
  fonte.
- [x] **T028 [L]** Impedir candidatos, bloqueados e contextuais no rollout padrão.
- [x] **T029 [L]** Preservar modo explícito `all` e seleção manual de fontes.
- [x] **T030 [L]** Validar ranking determinístico, deduplicação e estabilidade à
  ordem de chegada.

## Operação e segurança

- [x] **T031 [L]** Configurar timeout, bytes, concorrência, retry e circuit breaker.
- [x] **T032 [L]** Implementar ETag/Last-Modified e cache efêmero invalidável.
- [x] **T033 [L]** Adicionar allowlist de hosts e proteção contra SSRF/documentos.
- [x] **T034 [L]** Redigir logs, remover PII e não persistir tokens/cookies.
- [x] **T035 [L]** Criar smoke periódico, fingerprint de schema e alerta de drift.
- [x] **T036 [L]** Testar rollback de parser e shadow mode.

## Cobertura por famílias

- [ ] **T037 [E]** Fechar CJPG/primeiro grau em lotes prioritários.
- [ ] **T038 [E]** Fechar CJSG/segundo grau nos 27 TJs ou registrar bloqueio.
- [ ] **T039 [E]** Fechar TRF/STJ/STF/STM/CJF/TNU por coleção.
- [ ] **T040 [E]** Fechar TRT/TST e TSE/TRE/SJUR por coleção.
- [ ] **T041 [E]** Avaliar TCEs e fontes especializadas textuais.
- [ ] **T042 [H]** Aprovar owners, termos, licença, retenção e frequência.

## Fechamento

- [x] **T043 [L]** Regenerar inventários e abrir workpacks restantes.
- [x] **T044 [L]** Rodar suíte completa, Ruff, format, mypy, compileall, SDD e
  `git diff --check`.
- [x] **T045 [L]** Auditar TODOs, estados falsamente vazios e divergências.
- [ ] **T046 [H]** Aprovar promoção padrão, release ou mudança externa.

## Inventário nacional operacional (matriz gerada)

As tarefas abaixo são o backlog de descoberta de **todas** as autoridades e
famílias restantes. A lista completa, com uma linha por superfície, provider,
evidência e próxima ação, é gerada em
`national-source-task-matrix.json` e resumida em
`national-source-task-matrix.md`. O gerador é a fonte editável; não altere a
matriz gerada manualmente.

Os diretórios CNJ foram verificados por GET bounded em
`docs/provider-discovery/national-directory-live-20260908.json` (HTTP 200 nas
cinco âncoras). Isso comprova apenas a descoberta institucional, não a
disponibilidade de qualquer endpoint de jurisprudência.

- [ ] **T047 [E]** Inventariar e fechar `CJPG` dos 27 TJs: TJAC, TJAL, TJAM,
  TJAP, TJBA, TJCE, TJDFT, TJES, TJGO, TJMA, TJMG, TJMS, TJMT, TJPA, TJPB,
  TJPE, TJPI, TJPR, TJRJ, TJRN, TJRO, TJRR, TJRS, TJSC, TJSE, TJSP e TJTO.
- [ ] **T048 [E]** Inventariar e fechar `CJSG` dos mesmos 27 TJs, com contrato
  explícito de segundo grau e rejeição de registros de primeiro grau.
- [ ] **T049 [E]** Avaliar as fontes alternativas já registradas (PJe, eproc,
  Projudi, SAJ, ementários, boletins, turmas recursais, SJUR e portais), além
  das 59 superfícies `CPOPG`/`CPOSG`/`detail` declaradas pelo Juscraper. Provar
  semântica, grau e texto antes de criar adapter; não promovê-las
  automaticamente como jurisprudência geral.
- [ ] **T050 [E]** Fechar TRF1–TRF6 e CJF, separando jurisprudência textual de
  consulta processual, DataJud e metadados.
- [ ] **T051 [E]** Fechar STF, STJ, STM, TNU, TST, TSE, CSJT e CNJ com coleção,
  autoridade, tipo documental e capacidade de inteiro teor comprovadas.
- [ ] **T052 [E]** Descobrir e validar fontes oficiais de segundo grau para
  TRT1–TRT24; manter `trt2_pje_jurisprudencia` candidato enquanto o desafio
  público impedir contrato reproduzível. O adapter opt-in de diagnóstico do
  TRT2 foi implementado em `src/nanojuris/providers/trt2_pje_jurisprudencia.py`;
  opções/filtros públicos são consultáveis, mas `POST /documentos` continua
  explicitamente bloqueado quando retorna `tokenDesafio`/imagem/áudio.
- [x] **T053 [E]** Inventariar TSE e os 27 TREs, validar SJUR ou portal local,
  e distinguir acórdão eleitoral de temas, eleições e dados administrativos.
  O inventário bounded `docs/provider-discovery/tre-sjur-route-inventory-live-20260909.json`
  confirmou a rota oficial por UF: 26 TREs retornaram jurisprudência textual e
  TRE-RR informou vazio autoritativo para o termo testado. A superfície TSE
  continua documentada separadamente; temas, eleições e catálogos não foram
  contados como resultados decisórios.
- [ ] **T054 [E]** Inventariar os três TJMs (TJMSP, TJMMG e TJMRS) e STM,
  confirmando segundo grau militar e inteiro teor público.
- [ ] **T055 [E/H]** Decidir o escopo condicional e, se aprovado, inventariar
  TCEAC, TCEAL, TCEAP, TCEAM, TCEBA, TCECE, TCDF, TCEES, TCEGO, TCEMA,
  TCEMT, TCEMS, TCEMG, TCEPA, TCEPB, TCEPR, TCEPE, TCEPI, TCERJ, TCERN,
  TCERO, TCERR, TCERS, TCESC, TCESE, TCESP e TCETO, além de TCMBA, TCMGO,
  TCMPA e TCMSP. Essas fontes não contam como cobertura da Justiça enquanto o
  escopo não for aprovado.
- [ ] **T056 [E]** Para cada linha `discovery_pending`, localizar primeiro o
  diretório oficial do CNJ e, em seguida, a rota publicada pelo tribunal (API,
  exportação, RSS/sitemap ou portal). Registrar `official_entry_point` sem
  adivinhar endpoints.
- [ ] **T057 [E]** Executar chamadas live bounded em lotes de até três fontes,
  com termo jurídico neutro, página pequena e classificação explícita de
  sucesso, vazio autoritativo, bloqueio, timeout, rate limit ou schema drift.
- [ ] **T058 [E]** Implementar contrato, adapter independente, fixtures de
  sucesso/vazio/erro/segunda página, inteiro teor e validação canônica para
  cada fonte cuja chamada seja reproduzível.
- [ ] **T059 [E/H]** Executar smoke federado opt-in e promover somente fontes que
  passem os oito gates; preservar candidatos, contextuais e bloqueados no
  diagnóstico.
- [x] **T060 [L]** Reconciliar matriz, catálogo, runtime, evidências live,
  federação e ledger. Um HTTP 403, CAPTCHA, WAF, Turnstile, timeout, TLS ou
  schema inválido deve permanecer como estado explícito, nunca como vazio.

## Decisões fixadas em 2026-09-09

O escopo é core + condicional; coleções curadas ficam opt-in; promoção técnica
entra somente no manifesto local; nenhuma ação de release/deploy é inferida.
O pacote de governança fixa cache de 10 minutos, telemetria de 30 dias,
frequência mínima de 2 segundos e três páginas por sonda. T010, T042, T046,
T055 e demais tarefas externas/humanas permanecem abertas quando exigirem
prova do tribunal ou decisão do mantenedor.

## Dependências

`T001–T005 → T006–T011 → T012–T017 → T018–T025 → T026–T036 → T037–T042 →
T043–T046 → T047–T055 → T056–T060`. T010, T042, T046 e T055 nunca podem
ser simuladas por um agente. T047–T055 são fontes paralelizáveis; T056 precede
T057, T057 precede T058 e T059; T060 fecha cada lote.
