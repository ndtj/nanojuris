# Verificação

Status: verified_with_limitations

## Fechamento bounded das unidades (2026-09-05)

- `python tools/complete_provider_workpacks.py --write` processou as 60
  entradas do catálogo em modo `offline_evidence_review`; nenhuma chamada de
  rede, mutação de federação ou deploy foi realizada.
- 25 fontes que passaram o manifesto técnico foram registradas como
  `accepted_with_limitations`; 35 fontes sem todos os gates foram registradas
  como `deferred_with_review`, com owner, evidência, `review_after=2026-10-05`
  e `resume_when` objetivo.
- O estado v2 contém 60/60 disposições terminais, 60/60 owners e fingerprints;
  não há provider em `not_started` e os 60 work packs não possuem WP checkbox
  aberta. Lacunas, bloqueios e saúde operacional permanecem explícitos.
- Testes adicionados: `tests/test_provider_workpack_completion.py` (3 casos)
  e suíte focada `7 passed`; os gates completos continuam registrados abaixo.
- Gates finais desta rodada: `python -m pytest -q` (**1162 passed, 23 skipped**),
  smoke live bounded (**25/25 fontes parseáveis no ciclo 53; 4/4 buscas CJSG
  válidas e 1/4 detalhes sem controle no ciclo 51; 3/3 detalhes EPROC válidos
  no ciclo 43; paginação e detalhe TRF5 válidos no ciclo 44; TST busca e
  detalhe válidos no ciclo 46**), Ruff,
  format, mypy, compileall,
  `git diff --check` e `python tools/validate_sdd.py` aprovados.
- A reauditoria do repositório encontrou somente seis checkboxes abertos: as
  pré-condições de deploy no SDD 0001. As decisões de proveniência/reuso ou
  aceite nos SDDs 0048, 0049 e 0051–0061 estão registradas como dispensadas
  pelo operador para o escopo técnico local/federado; não há tarefa de código
  WP aberta.

## Atualização de fechamento local (2026-09-02)

- Workpacks regenerados para 59 entradas (50 runtime, 8 candidates e 1
  família), com prioridades e destinos explícitos.
- O ledger regenerado em 2026-09-02 registra 109 itens: 68 com evidência local,
  27 bloqueios externos e 14 itens candidate pendentes; nenhum bloqueio foi
  convertido em resultado vazio.
- Oito candidates foram observados em sweep público bounded; somente TJRN e
  TRF3 apresentaram rotas públicas úteis, sem promoção automática.
- T07, T08, T09, T10 e T13 estão concluídas para o escopo técnico local.
  Providers sem contrato/live/fixture permanecem explicitamente fora da
  federação padrão; deploy e publicação não fazem parte desta verificação.

## Checkpoint da rodada autonoma (2026-09-01)

- `python tools/build_provider_sdd_workpacks.py` — pass; 58 fontes (49 runtime,
  8 candidatas e 1 familia), sem rede.
- `python tools/validate_sdd.py` — pass.
- `python -m pytest tests/test_provider_sdd_workpacks.py tests/test_sdd_validation.py -q`
  — pass; 4 testes.
- `python -m ruff check .` — pass.
- `python -m ruff format --check .` — pass; 854 arquivos.
- `python -m mypy src` — pass; 93 arquivos.
- `python -m pytest -q` — pass; 988 aprovados e 12 skips condicionais após as
  ondas de cobertura e qualidade.
- estado v2: 59 itens `not_started`, 0 disposicoes terminais e 59 saudes
  operacionais nao verificadas; nenhuma promocao foi inferida.
- produção/publicação: não realizadas.

## Checkpoint de validação live (2026-09-01)

- `python -m pytest tests/test_bnp_pangea_live.py tests/test_stj_dados_abertos_live.py tests/test_stj_html_parsers_live.py tests/test_tjba_graphql_live.py tests/test_tjsp_cjsg_live.py -q` com `NANOJURIS_RUN_LIVE=1` e `NANOJURIS_RUN_TJSP_LIVE=1`: **8 pass**.
- `python tools/discover_all_providers.py --live --max-pages 1 --max-depth 0 --timeout 6 --delay 0.5 --output docs/provider-discovery/all-provider-sweep-20260901.json`: 46/46 providers runtime observados em uma chamada bounded.
- A varredura registrou 17 respostas públicas `valid` com sinais de jurisprudência e 6 observações adicionais com sinais jurídicos sob controle de acesso; houve 7 observações `access_controlled`, 3 `empty`, 12 `robots_disallowed` e 1 `redirect_outside_allowlist` (8 providers apresentaram algum sinal de controle de acesso). “Observado” não significa contrato completo ou promoção.
- A inconsistência do teste TJBA (URL absoluta válida versus expectativa relativa) foi corrigida em `tests/test_tjba_graphql_live.py`; a confirmação live passou após a correção.
- Os POSTs declarados não foram submetidos automaticamente sem payload contratado; nenhum provider foi promovido por esta varredura.

## Checkpoint de cobertura e rechecagem (ciclo 2/3)

- A varredura `all-provider-sweep-20260901-cycle2` observou 49 providers
  runtime e 8 candidatos, com 1.918 rotas e 191 filtros observados; 9 sinais de
  acesso controlado foram preservados como diagnóstico.
- TJRO/CJSG respondeu JSON HTTP 200, mas vazio em três termos; permaneceu
  candidato sem fixture de sucesso.
- TRF3 teve três rotas oficiais alternativas rechecadas. Todas expiraram por
  `ReadTimeout` de 6 segundos e foram classificadas como
  `blocked_transport`; nenhum adapter foi criado.
- TJES/CJSG ganhou fallback local para `ementa_html`/`acordao_html`, sem novas
  requisições ou mudança de status de acesso.

O checkpoint encerra somente esta rodada offline. A topologia 0036 teve a
fundacao de modelo e artefato iniciada, mas T07/T13 continuam pendentes; uma
proxima rodada deve iniciar 0027/0028/0031 e completar as projecoes 0036 antes
de qualquer validacao live autorizada.

## Checkpoint de evidencia e replay (ciclos 4/5)

- TJPB/PJe passou a ter `tests/fixtures/tjpb_pje_jurisprudencia_success.json`,
  um replay sintetico que exercita o parser de busca sem versionar token ou
  corpo live.
- STF Informativo passou a ter `tests/fixtures/stf_informativo_rows.json`;
  o builder XLSX continua cobrindo o contrato estrutural e schema drift.
- A rechecagem live STF de 2026-09-01 registrou `blocked_transport` (SSL) e
  `blocked_access` (HTTP 403), sem transformar falha em lista vazia.
- A auditoria offline agora reconhece 48/49 providers runtime com fixture
  versionada, 0 somente inline e 1 sem evidencia de fixture (TJRJ eproc).
- A suite completa foi executada novamente: 992 aprovados e 12 skips
  condicionais; nenhum deploy, push ou alteracao de producao.

## Checkpoint de proveniencia por tribunal (ciclo 6)

- TJRJ/eproc deixou de reutilizar a fixture TJSP: o teste agora carrega
  `tests/fixtures/tjrj_eproc_jurisprudencia_result.html` com UF RJ, processo
  `.8.19`, links TJRJ e valores ficticios.
- A auditoria offline confirma 49/49 providers runtime com fixture versionada,
  sem evidencia inline-only e sem divida de fixture.
- A fila regenerada permanece finita: 58 fontes (49 runtime, 8 candidatas e 1
  familia); nenhum provider foi promovido por fixture sintetica.
- A suite completa deste ciclo terminou com 992 aprovados e 12 skips
  condicionais; producao continua inalterada.

## Checkpoint de estados operacionais (ciclo 7)

- TJRJ/eproc passou a ter fixtures dedicadas de busca publica vazia e de
  desafio de acesso, ambas sanitizadas e sem reaproveitar TJSP.
- O parser compartilhado retorna `[]` apenas quando a pagina contem o
  formulario publico; marcadores de CAPTCHA/Cloudflare geram
  `AccessControlRequiredError`.
- A auditoria offline continua em 49/49 providers runtime com fixture
  versionada e sem `inline_only` ou provider sem evidencia.
- Gates locais desta rodada: Ruff, format, mypy, compileall, diff-check e
  `validate_sdd.py` aprovados.

## Checkpoint de rechecagem CJF/TRF1 (ciclo 8)

- A rota oficial `GET /trf1/index.xhtml` respondeu HTTP 200 em chamada publica
  bounded, mas o HTML continha `captcha` e `recaptcha` e nao apresentou tabela
  de resultados; o estado foi classificado como `blocked_access`.
- Nenhum POST com ViewState foi enviado apos o desafio, nenhum corpo live foi
  persistido e o provider permaneceu `runtime_unchanged`.
- Evidencia: `docs/provider-discovery/cjf-trf1-live-recheck-20260901-cycle8.json`;
  teste offline: `tests/test_cjf_trf1_live_recheck.py`.
- A suite completa terminou com 994 aprovados e 12 skips condicionais; gates
  de Ruff, format, mypy, compileall, diff-check e `validate_sdd.py` passaram.
- Producao, deploy e publicacao nao foram alterados.

## Checkpoint de rechecagem STF Jurisprudencia (ciclo 9)

- O endpoint contratado `POST /api/search/search` foi chamado uma vez em modo
  publico bounded, com timeout de 8 s e `verify_ssl=true`.
- A conexao falhou antes de HTTP por `SSLError`; o estado foi registrado como
  `blocked_transport`, sem converter falha em vazio e sem alterar o provider.
- Evidencia: `docs/provider-discovery/stf-juris-live-recheck-20260901-cycle9.json`;
  teste offline: `tests/test_stf_juris_live_recheck.py`.
- O catalogo e o workpack agora refletem `blocked_transport`/`blocked` e fila
  P0; 58 fontes continuam reconciliadas (49 runtime, 8 candidates, 1 familia).
- Suite completa: 995 aprovados e 12 skips condicionais; nenhum deploy, push ou
  alteracao de producao.

## Checkpoint de rechecagem TJPE (ciclo 10)

- A rota oficial `GET /api/v1/jurisprudencias` foi chamada uma vez em modo
  publico bounded, com timeout de 8 s e `verify_ssl=true`.
- A conexao falhou antes de HTTP por `SSLCertVerificationError`; o estado foi
  registrado como `blocked_transport`, sem converter falha em vazio e sem
  alterar o adapter.
- Evidencia: `docs/provider-discovery/tjpe-live-recheck-20260901-cycle10.json`;
  teste offline: `tests/test_tjpe_live_recheck.py`.
- O catalogo e o workpack refletem a fotografia mais recente; TJPE permanece
  `blocked` e na fila P0.
- Suite completa: 996 aprovados e 12 skips condicionais; producao,
  deploy e publicacao permanecem inalterados.

## Checkpoint de alinhamento eSAJ/Juscraper (ciclo 12)

- O fluxo compartilhado dos seis adapters eSAJ foi corrigido para
  `POST resultadoCompleta.do` (ack), `GET trocaDePagina.do` da pagina 1 e GET
  da pagina solicitada na mesma sessao.
- O TJSP propaga `conversationId` da pagina 1 em memoria e envia `Referer`;
  os demais adapters tambem enviam `Referer` sem sobrescrever headers.
- O parser passou a reconhecer a resposta oficial de zero resultados
  `Acórdãos(0)`/`Não foi encontrado nenhum resultado` (TJAC).
- 61 testes focados passaram. Rechecagem live bounded: TJAC (zero legítimo),
  TJAL, TJAM e TJMS com HTTP 200 e registros; TJCE `blocked_transport`; TJSP
  `blocked_access`. Evidência: `docs/provider-discovery/esaj-juscraper-flow-live-recheck-20260902-cycle12.json`.
- Nenhum corpo, cookie, token ou desafio live foi salvo/contornado; produção,
  deploy e publicação permanecem inalterados.

## Resultados

| Gate | Estado | Evidência |
| --- | --- | --- |
| auditoria offline | pass | 58 fontes, 49 runtime |
| gerador | pass | cardinalidade derivada do catálogo; snapshot: 58 fontes, 49 runtime, 8 candidates e 1 família |
| work packs | pass | um por entrada do catálogo; snapshot: 58 |
| preservação, invalidação e migração v1→v2 | pass | test_provider_sdd_workpacks.py |
| lint/format/tipos do gerador | pass | Ruff, format e mypy nos arquivos novos |
| suíte completa | pass | 998 passed, 12 skipped |
| SDD | pass | validate_sdd |
| rede | pass | não utilizada pelo gerador |
| produção | pass | não alterada |
| integração com topologia/superfícies | pending | T13 |
| bindings de topologia no baseline/estado | pass | 58 providers reconciliados; collections unknown preservadas |

## Rastreabilidade

REQ-001 a REQ-010 estão ligados a T01 a T10 em traceability.md. O gerador e os
artefatos foram verificados; a execução dos work packs permanece pendente.
