# Verificação e handoff

## Resultados

### Ciclo local — TCU dados abertos SharedHttpClient (2026-09-08)

O provider de dados abertos do TCU foi migrado para o transporte compartilhado.
Manifesto e CSV usam allowlist oficial e limite de 80 MB; o parser continua
streaming sobre a janela limitada, e 401/403/429, timeout, TLS, redirecionamento
fora da allowlist e excesso de bytes permanecem estados explícitos. O retry é
desativado para não reiniciar downloads grandes automaticamente.

Validação: `python -m pytest -q tests/test_tcu_jurisprudencia.py
tests/test_initial_json_providers.py -k tcu` — 15 passed; Ruff e mypy do
provider — passed.

### Ciclo local — TJAL Turmas Recursais SharedHttpClient (2026-09-08)

O download do volume PDF foi migrado para o transporte compartilhado com
allowlist, limite de 8 MB, timeout, rate limit e circuito. A validação de
assinatura PDF continua no adapter e estados de acesso, transporte, MIME e
tamanho permanecem distintos de vazio. A coleção continua explicitamente
`degree=recursal`, fora de CJPG/CJSG.

Validação: `python -m pytest -q tests/test_tjal_turma_recursal_ementario.py`
— 6 passed; Ruff e mypy do provider — passed.

### Ciclo local — TJAP Banco de Sentenças SharedHttpClient (2026-09-08)

O fluxo Livewire público do TJAP (snapshot GET, dispatch POST, paginação e
leitor) passou a usar o transporte compartilhado, com allowlist, limite de 8 MB,
timeout, rate limit e circuito. Os estados de acesso, desafio, transporte e
schema continuam explícitos; o provider mantém escopo `degree=first`/CJPG e não
é confundido com o Tucujuris CJSG bloqueado.

Validação: `python -m pytest -q tests/test_tjap_banco_sentencas.py` — 7
passed; Ruff e mypy do provider — passed.

### Ciclo local — STF Informativo SharedHttpClient (2026-09-08)

O download XLSX do `stf_informativo` foi migrado para o `SharedHttpClient`,
com allowlist, limite de 20 MB, timeout, rate limit, circuito e classificação
explícita de falhas de TLS, acesso e transporte. O teste mantém a distinção
entre erro SSL e contrato XLSX inválido; nenhum erro é convertido em vazio.

Validação: `python -m pytest -q tests/test_stf_informativo.py` — 17 passed;
`python -m ruff check src/nanojuris/providers/stf_informativo.py
tests/test_stf_informativo.py` — passed.

### Ciclo local — TRF3 SharedHttpClient (2026-09-08)

O adapter `trf3_jurisprudencia` foi migrado das chamadas diretas de sessão para
o `SharedHttpClient`, mantendo o contrato estreito de consulta exata por número
CNJ. A política aplica allowlist, HTTP/1.1, timeout, limite de 8 MB, retry
idempotente, rate limit e circuit breaker; o teste de HTTP 403 confirma que
acesso controlado continua `AccessControlRequiredError`. O lookup documental
continua opt-in: a pesquisa textual geral do TRF3 permanece sem replay HTTP
reproduzível e não foi promovida.

Validação: `python -m pytest -q tests/test_trf3_jurisprudencia.py
tests/test_trf3_transport_recheck.py` — 9 passed; `python -m ruff check
src/nanojuris/providers/trf3_jurisprudencia.py tests/test_trf3_jurisprudencia.py`
— passed.

Estado deste pacote: `locally_verified_with_external_pending` (2026-09-08).
O ciclo atual executou os artefatos de reconciliação e os gates locais sem
alterar rollout, produção ou estados externos. As tarefas marcadas como
concluídas abaixo possuem evidência executável; as demais continuam pendentes.

### Ciclo local — SJUR/TSE catálogo SharedHttpClient (2026-09-08)

As rotas públicas de catálogo do TSE foram migradas para o transporte
compartilhado, com allowlist, limite de 4 MB, timeout, rate limit e circuito.
POST não é repetido automaticamente e falhas de acesso, transporte, TLS,
redirecionamento e schema permanecem distintas de catálogo vazio. O provider
continua somente catálogo; a busca decisória e a federação permanecem
desabilitadas sem contrato público reproduzível.

Validação: `python -m pytest -q tests/test_justica_eleitoral_sjur.py` — 4
passed; Ruff, format e mypy do provider — passed.

### Ciclo local — CJF/TRF1 SharedHttpClient (2026-09-08)

As rotas JSF GET/POST do TRF1 passaram a usar o transporte compartilhado com
allowlist do host CJF/PJe2G, limite de 4 MB, timeout, rate limit e circuito.
O ViewState continua restrito à sessão atual; POST não é repetido
automaticamente. 401/403/429, TLS, timeout, redirecionamento fora da allowlist,
HTML de controle e schema inválido continuam estados explícitos. A fonte segue
bloqueada/opt-in pela evidência live e não foi promovida.

Validação: `python -m pytest -q tests/test_cjf_jurisprudencia.py` — 11
passed; Ruff, format e mypy do provider — passed.

### Ciclo local — STJ SCON SharedHttpClient (2026-09-08)

Busca HTML e inteiro teor do SCON passaram a usar o transporte compartilhado,
com allowlist do host oficial, limite de 16 MB, timeout, rate limit e circuito.
O retry fica desativado para não repetir sessão diante de controles do STJ.
403, 429, timeout, TLS, desafio HTML e schema inválido continuam falhas
explícitas; a fonte permanece opt-in enquanto o controle de acesso impedir
validação live reprodutível.

Validação: `python -m pytest -q tests/test_stj_scon.py` — 13 passed; Ruff,
format e mypy do provider — passed.

### Fechamento técnico de reconciliação (T060)

T060 foi concluída pelo gerador e pelos testes do mapa nacional. A reconciliação
abrange matriz de superfícies, registro de estado, catálogo, runtime,
qualidade, evidências live, federação e ledger, mantendo bloqueios como estados
explícitos. Evidências:

- `docs/coverage/national-coverage-gap-map-20260908.json` — 251 superfícies,
  73 providers catalogados e 20 órfãos reconciliados;
- `tests/test_national_coverage_gap_map.py` — identidade catálogo/matriz,
  rollup dos 27 tribunais estaduais e preservação de bloqueios;
- `docs/coverage/open-task-audit-current.json` — 89 tarefas abertas após o
  fechamento, sendo 4 locais, 65 externas e 20 humanas;
- `docs/coverage/0091-local-gates-20260908.json` — 10 gates locais aprovados.

O marcador combinado `[E/H]` agora é classificado corretamente como revisão
humana em `tools/audit_open_tasks.py`, evitando que uma decisão externa seja
apresentada como pendência local.

### Smoke federado do manifesto atual

Foi executado o smoke bounded com o manifesto técnico atual:

```text
python tools/run_federated_promotion_smoke.py --output docs/provider-discovery/federated-promotion-live-20260908-cycle77.json --text "responsabilidade civil" --page-size 1
```

Resultado: 50/50 fontes habilitadas pesquisadas, 56 registros deduplicados,
zero erros e zero registros inválidos. Onze fontes declararam total
desconhecido, preservado como incompletude explícita.

Também foi executado um conjunto opt-in separado, sem alterar o manifesto
padrão. Quatro das quinze fontes opt-in ainda não estão registradas no runtime
(`eproc_jurisprudencia_federal`, `falcao_jt`, `tjse_jurisprudencia` e
`trt2_pje_jurisprudencia`), produzindo `UnsupportedProviderError`; as demais
não foram promovidas por esse smoke. A evidência está em
`docs/provider-discovery/federated-promotion-optin-live-20260908-cycle78.json`.
Isso mantém T059 pendente até que cada fonte candidata tenha adapter e contrato
reproduzível.

### Transporte compartilhado — família eproc federal

O ciclo também migrou a base `FederalEprocJurisprudenciaProvider` e o provider
`trf4_eproc_jurisprudencia` para `SharedHttpClient`, com allowlist por host,
timeout, retry transitório, limite de resposta, circuit breaker e classificação
de transporte preservados. A camada aceita respostas HTTP compatíveis usadas nos
testes sem transformar corpo textual em vazio. Os testes focados passaram:

```text
python -m pytest -q tests/test_eproc_jurisprudencia_federal.py \
  tests/test_trf4_eproc_jurisprudencia.py tests/test_transport_runtime.py \
  tests/test_state_eproc_jurisprudencia.py
56 passed
```

Isso fecha a migração da família eproc federal coberta por este lote, mas T014
continua pendente para os demais adapters que ainda usam a sessão compatível
legada; nenhum provider foi promovido apenas por essa alteração.

### Transporte compartilhado — helper TJSP/CJSG

O helper público e-SAJ do `tjsp_cjsg` também passou a usar `SharedHttpClient`.
A mudança preserva o fluxo oficial em duas etapas (`POST
/resultadoCompleta.do` seguido de `GET /trocaDePagina.do`), o diagnóstico de
CAPTCHA/controle de acesso, a decodificação declarada pela fonte e o download
bounded de inteiro teor. O cliente mantém allowlist de host, retry apenas para
GET idempotente, limite de bytes, circuit breaker e classificação explícita de
falhas; nenhum controle de acesso é contornado.

Os provedores e-SAJ cobertos pelos testes de regressão continuaram verdes; o
TJAC também passou a usar o mesmo limite de transporte compartilhado:

```text
python -m pytest -q tests/test_tjsp_cjsg.py tests/test_tjac_cjsg.py \
  tests/test_tjal_cjsg.py tests/test_tjam_cjsg.py tests/test_tjms_cjsg.py \
  tests/test_tjce_cjsg.py tests/test_state_eproc_jurisprudencia.py
87 passed
```

Esta é uma migração incremental do transporte; T014 permanece aberto para os
adapters que ainda fazem chamadas diretas e para a auditoria global de
configuração.

Smoke live bounded dos dois fluxos migrados:

```text
python tools/run_federated_promotion_smoke.py --output docs/provider-discovery/federated-promotion-live-20260908-cycle79.json --text "responsabilidade civil" --page-size 1 --sources tjsp_cjsg tjac_cjsg
2 fontes pesquisadas, 0 erros, 2 registros deduplicados, 0 inválidos
```

As duas fontes responderam com conteúdo textual válido. O resultado não altera
o status de cobertura nem promove novas superfícies por si só.

O lote seguinte concluiu a migração do helper e-SAJ nos seis providers CJSG:
`tjac_cjsg`, `tjal_cjsg`, `tjam_cjsg`, `tjce_cjsg`, `tjms_cjsg` e `tjsp_cjsg`.
O TJCE mantém seu adapter TLS específico, agora encapsulado no mesmo cliente
compartilhado. O smoke bounded conjunto confirmou as seis fontes:

```text
python tools/run_federated_promotion_smoke.py --output docs/provider-discovery/federated-promotion-live-20260908-cycle80.json --text "responsabilidade civil" --page-size 1 --sources tjac_cjsg tjal_cjsg tjam_cjsg tjce_cjsg tjms_cjsg tjsp_cjsg
6 fontes pesquisadas, 0 erros, 6 registros deduplicados, 0 inválidos
```

Isso reduz a superfície de chamadas diretas no grupo e-SAJ, mas não encerra a
migração global T014 nem altera os gates de qualidade de grau.

### Revalidação final do lote TJAL (2026-09-08)

O smoke federado dedicado foi executado sem persistir corpos de documentos:

```text
python tools/run_federated_promotion_smoke.py --output docs/provider-discovery/federated-promotion-live-20260908-tjal-esmal.json --text "responsabilidade civil" --page-size 1 --sources tjal_esmal_banco_sentencas
1 fonte pesquisada, 0 erros, 1 registro deduplicado, 0 inválidos
```

O resultado confirma `access_status=public`, `extraction_status=complete` e
`total_known=false`. A reconciliação regenerada agora mostra 51 fontes
declaradas na federação, 8 CJPG e 25 CJSG tecnicamente live/federados, sem
transformar a coleção curada ESMAL em cobertura integral.

O adapter HTML foi migrado para `SharedHttpClient`; o teste de acesso HTTP 403
permanece distinto de página vazia. A suíte focal do lote passou com 21 testes
e a suíte completa deve ser repetida após os gates estáticos.

### TJAL ESMAL — transporte compartilhado e promoção parcial

O provider `tjal_esmal_banco_sentencas` passou a usar `SharedHttpClient` na
busca HTML, mantendo a mesma allowlist, limite de bytes, rate limit, retry
transitório e classificação de 403/429/TLS/timeout. O detalhe PDF continua
restrito a URLs observadas e ao pipeline `DocumentReference`. Os testes focados
passaram (`8 passed`) e o smoke federado registra a fonte como habilitada
tecnicamente. A promoção é deliberadamente **parcial**: a coleção ESMAL é
curada, não publica total autoritativo e não deve ser apresentada como cobertura
integral do CJPG do TJAL.

O provider diagnóstico `tjse_jurisprudencia` também passou a usar o transporte
compartilhado para a descoberta GET. O Turnstile continua sendo classificado
como `access_control_required`, sem submissão de token e sem entrada na
federação. A verificação live bounded foi executada novamente:

```text
$env:NANOJURIS_RUN_TJSE_LIVE='1'
python -m pytest -q tests/test_tjse_jurisprudencia_live.py
1 passed
```

O teste confirma a fronteira de acesso; não é evidência de resultados
jurisprudenciais e não altera a classificação bloqueada.

## Inventário executado nesta rodada

- `python tools/build_national_source_task_matrix.py --write` gerou 251 linhas
  (155 core, 96 condicionais), 149 ainda em descoberta, 34 bloqueadas ou
  indisponíveis, 4 com contrato pendente, 62 live/federadas e 2 live fora da
  federação.
- O inventário Juscraper adicionou 59 superfícies `CPOPG`, `CPOSG` e `detail`
  como `juscraper_surface_semantics_pending`; elas não foram promovidas nem
  contadas como jurisprudência textual.
- Cinco diretórios CNJ responderam HTTP 200 em chamada GET bounded; a evidência
  está em `docs/provider-discovery/national-directory-live-20260908.json`.
- A matriz é idempotente (hash SHA-256 observado:
  `A31A17CFC80CFAA91F618275620A122DF2C55080900887AE8B60069F84866BEF`).

## Comandos e resultados esperados

Executar na raiz `repos/nanojuris`:

```text
python tools/build_national_source_task_matrix.py --write
python tools/validate_sdd.py
python tools/audit_provider_docs.py --write
python tools/build_provider_coverage.py --write
python tools/build_degree_coverage.py
python tools/build_surface_state_registry.py
python tools/build_state_appellate_program.py --write
python tools/build_promotion_manifest.py --write
python tools/build_fixture_completeness.py --write
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
python -m mypy src
python -m compileall -q src tools tests
git diff --check
```

O fechamento deve registrar versão do Python, duração, contagens, skips
opt-in/live e hashes dos inventários. Uma chamada HTTP 200 isolada não é
resultado suficiente.

### Reconciliação técnica TRF4 — 2026-09-08

O provider `trf4_eproc_jurisprudencia` foi revalidado para a superfície federal
de segundo grau. A origem oficial `selOrigem[]=1` foi mapeada explicitamente
para o próprio TRF4; a resposta live retornou dois registros públicos com
`degree=second`, `instance=second`, ementa e URL oficial de inteiro teor. O
envelope sem corpos persistidos está em
`docs/provider-discovery/trf4-second-degree-live-20260908.json`.

Como a matriz também enumera a categoria institucional genérica
`TRF4/federal/second/JURISPRUDENCIA`, ela agora registra essa linha como alias
explícito da superfície técnica EPROC, por meio de `coverage_alias_of`, em vez
de criar um falso providerless gap. O alias não duplica chamadas nem aumenta a
contagem de providers.

Após a reconciliação, a matriz permanece com 251 linhas (155 core e 96
condicionais), 150 em descoberta, 34 bloqueadas/indisponíveis, 2 com contrato
pendente, 63 federadas e 2 live fora da federação. A alteração é técnica e não
contorna qualquer controle de acesso.

### Fechamento federal EPROC — TRF2 e TRF6 (2026-09-08)

O contrato compartilhado agora traduz `degree=second`/`instance=second` para
`selOrigem[]=1` nos formulários oficiais de TRF2, TRF4 e TRF6. O smoke live
bounded de TRF2 e TRF6 retornou dois registros por fonte, todos com identidade
federal de segundo grau e URL oficial de documento. A evidência redigida está
em `docs/provider-discovery/federal-eproc-degree-live-20260908.json`.

O parser do TRF2 não expunha o grau no card; o hint só é aceito quando o filtro
oficial de origem `1` foi enviado, mantendo a rejeição de respostas sem contrato
em outras situações. Os totais foram marcados como não autoritativos após o
pós-filtro local. Testes focados: 17 aprovados.

### Fechamento do ciclo 2026-09-08

Após a migração e o smoke federado, os gates locais foram executados novamente:

```text
python -m pytest -q
1600 passed, 26 skipped
python -m ruff check .                 # All checks passed
python -m ruff format --check .        # 1842 files already formatted
python -m mypy src                      # Success: no issues found in 141 files
python -m compileall -q src tools tests
python tools/validate_sdd.py            # SDD validation passed
git diff --check                        # exit 0 (somente avisos CRLF/LF)
```

O estado nacional permanece **73 providers catalogados, 68 em runtime, 62
fontes federadas, 25/27 CJSG GOLD e 7/27 CJPG GOLD, com 6 tribunais nas duas
trilhas**. Ainda existem 89 tarefas abertas (65 externas, 20 humanas e 4
locais); portanto este pacote não declara cobertura nacional completa.

### Transporte compartilhado - TJSE Boletim Juridico

O provider publico `tjse_boletim_jurisprudencia` foi migrado para o
`SharedHttpClient`. A resposta de uma secao pode ultrapassar 8 MB de HTML
legitimo; o limite explicito foi ajustado para 16 MB, mantendo bound contra
respostas abusivas. O smoke live bounded retornou uma ementa de segundo grau,
com `access_status=public`, `extraction_status=complete` e total desconhecido
entre edicoes:

```text
python tools/run_federated_promotion_smoke.py --output docs/provider-discovery/federated-promotion-live-20260908-cycle81.json --text "responsabilidade civil" --page-size 1 --sources tjse_boletim_jurisprudencia
1 fonte pesquisada, 0 erros, 1 registro deduplicado, 0 invalidos
```

Esse resultado confirma disponibilidade publica e o contrato de secao, mas nao
declara completude nacional nem promove a superficie por si so.

### Transporte compartilhado - TJES/TJSP CJPG

Os adapters `tjes_cjpg` e `tjsp_cjpg` passaram a usar `SharedHttpClient` com
allowlist, limite de bytes, pacing compartilhado, sem retry de 429/5xx e estados
de acesso explícitos. Os testes focados ficaram verdes (17 TJES e 15 TJSP), e o
smoke live bounded confirmou ambas as superfícies públicas de primeiro grau:

```text
python tools/run_federated_promotion_smoke.py --output docs/provider-discovery/federated-promotion-live-20260908-cycle82.json --text "responsabilidade civil" --page-size 1 --sources tjes_cjpg tjsp_cjpg
2 fontes pesquisadas, 0 erros, 2 registros deduplicados, 0 inválidos
totais conhecidos: TJES=975879, TJSP=3838928 (janelas parciais)
```

Essas chamadas confirmam transporte e contrato CJPG, mas não completude de
primeiro grau nem promoção adicional.

### Transporte compartilhado - TJGO PROJUDI

O adapter `tjgo_projudi_jurisprudencia` passou a usar `SharedHttpClient` para
as buscas e o documento público bounded. O parser continua distinguindo
primeiro/segundo grau pelo `Id_Instancia`, preservando texto inline e
classificando páginas de desafio como controle de acesso. Os testes focados
passaram (28), e o smoke live retornou uma decisão textual pública, com total
conhecido e janela parcial:

```text
python tools/run_federated_promotion_smoke.py --output docs/provider-discovery/federated-promotion-live-20260908-cycle83.json --text "responsabilidade civil" --page-size 1 --sources tjgo_projudi_jurisprudencia
1 fonte pesquisada, 0 erros, 1 registro deduplicado, 0 inválidos
total conhecido: 14032 (janela parcial)
```

O resultado é evidência de transporte e contrato reproduzíveis, não uma
declaração de completude do acervo.

### Transporte compartilhado - TJPA BFF

O provider `tjpa_jurisprudencia_bff` passou a usar `SharedHttpClient` nos
endpoints de busca e catálogo, preservando payload JSON, allowlist, limite de
bytes, pacing e estados de acesso. O smoke live bounded retornou uma decisão
textual pública, com total conhecido de 10.000 e janela parcial:

```text
python tools/run_federated_promotion_smoke.py --output docs/provider-discovery/federated-promotion-live-20260908-cycle84.json --text "responsabilidade civil" --page-size 1 --sources tjpa_jurisprudencia_bff
1 fonte pesquisada, 0 erros, 1 registro deduplicado, 0 inválidos
total conhecido: 10000 (janela parcial)
```

O resultado confirma a rota pública e o contrato BFF, sem declarar completude
do acervo ou alterar a decisão de promoção.

### Transporte compartilhado - TJBA GraphQL

O provider `tjba_graphql` passou a usar `SharedHttpClient` para busca, catálogo
e inteiro teor. A migração preserva o payload GraphQL e os estados HTTP
explícitos, com allowlist, limite de bytes, pacing e trace uniforme. O smoke
live bounded retornou uma decisão pública de segundo grau:

```text
python tools/run_federated_promotion_smoke.py --output docs/provider-discovery/federated-promotion-live-20260908-cycle85.json --text "responsabilidade civil" --page-size 1 --sources tjba_graphql
1 fonte pesquisada, 0 erros, 1 registro deduplicado, 0 inválidos
total conhecido: 1970960 (janela parcial)
```

O resultado confirma a rota textual pública e o contrato CJSG, sem declarar
completude do acervo ou alterar a decisão de promoção.

### Transporte compartilhado - TJDFT SISTJ

O provider `tjdf_juris` passou a usar `SharedHttpClient` nas rotas HTML e API,
com allowlist para os hosts oficiais, limite de bytes, pacing e classificação
explícita de transporte. O smoke live bounded retornou uma decisão pública:

```text
python tools/run_federated_promotion_smoke.py --output docs/provider-discovery/federated-promotion-live-20260908-cycle87.json --text "responsabilidade civil" --page-size 1 --sources tjdf_juris
1 fonte pesquisada, 0 erros, 1 registro deduplicado, 0 inválidos
total conhecido: 132995 (janela parcial)
status: public / complete
```

### Transporte compartilhado - TJMT API

O provider `tjmt_jurisprudencia_api` passou a usar `SharedHttpClient` para o
`config.json` público e para a API de jurisprudência. O token de aplicação
continua sendo usado apenas no request e removido das URLs e traces. O smoke
live bounded retornou uma decisão pública de segundo grau:

```text
python tools/run_federated_promotion_smoke.py --output docs/provider-discovery/federated-promotion-live-20260908-cycle88.json --text "responsabilidade civil" --page-size 1 --sources tjmt_jurisprudencia_api
1 fonte pesquisada, 0 erros, 1 registro deduplicado, 0 inválidos
total conhecido: 74118 (janela parcial)
status: public / complete
```

Essas migrações confirmam transporte e contrato reproduzíveis, mas não declaram
completude dos acervos nem alteram a decisão de promoção.

### Transporte compartilhado - TJPB PJe

O provider `tjpb_pje_jurisprudencia` passou a usar `SharedHttpClient` para o
token CSRF público, busca JSON e detalhe HTML, com allowlist, limite de bytes,
pacing e classificação explícita de acesso. O smoke live bounded retornou uma
decisão pública de segundo grau:

```text
python tools/run_federated_promotion_smoke.py --output docs/provider-discovery/federated-promotion-live-20260908-cycle89.json --text "responsabilidade civil" --page-size 1 --sources tjpb_pje_jurisprudencia
1 fonte pesquisada, 0 erros, 1 registro deduplicado, 0 inválidos
total conhecido: 26092 (janela parcial)
status: public / complete
```

O resultado confirma a rota PJe oficial e o contrato CJSG reproduzível, sem
declarar completude do acervo ou alterar a decisão de promoção.

### Transporte compartilhado - TJPI/JusPI

O provider `tjpi_juspi` foi migrado para `SharedHttpClient`, com allowlist do
host oficial, limite de 8 MB, sem retries automáticos e classificação explícita
de transporte, acesso, rate limit, erro HTTP e conteúdo de controle de acesso.
O fallback para consulta por número CNJ permanece limitado às duas variações
oficiais (`tipo=Acordao` e sem `tipo`) e não contorna CAPTCHA, WAF ou
autenticação.

```text
python -m pytest -q tests/test_tjpi_juspi.py tests/test_tjpi_contract.py tests/test_tjpi_live.py
19 passed, 2 skipped (live opt-in)

python tools/run_federated_promotion_smoke.py --output docs/provider-discovery/federated-promotion-live-20260908-cycle90.json --text "responsabilidade civil" --page-size 1 --sources tjpi_juspi
1 fonte pesquisada, 0 erros, 1 registro deduplicado, 0 inválidos
total conhecido: 33404 (janela parcial)
status: public / complete
```

O smoke bounded confirma a rota pública do JusPI e o contrato de resultado,
sem declarar completude do acervo ou alterar a decisão de promoção.

### Transporte compartilhado - TJRR/JSF

O provider `tjrr_juris` foi migrado para `SharedHttpClient` mantendo o fluxo
oficial JSF/PrimeFaces, ViewState por sessão e paginação AJAX. A allowlist,
limite de 8 MB, pacing e classificação de transporte/HTTP permanecem no
cliente comum; CAPTCHA, WAF e acesso controlado continuam sendo erros
explícitos.

```text
python -m pytest -q tests/test_tjrr_juris.py
16 passed

python tools/run_federated_promotion_smoke.py --output docs/provider-discovery/federated-promotion-live-20260908-cycle91.json --text "responsabilidade civil" --page-size 1 --sources tjrr_juris
1 fonte pesquisada, 0 erros, 1 registro retornado, 0 inválidos
total conhecido: 14206 (janela parcial)
status: public / complete
```

O resultado confirma a rota pública de segundo grau e o parser reproduzível;
as dez entradas internas observadas foram consolidadas em uma decisão no
envelope federado. O smoke não declara completude do acervo nem altera a
decisão de promoção.

### Transporte compartilhado - TJRS/SOLR

O provider `tjrs_solr` foi migrado para `SharedHttpClient` mantendo o POST
AJAX/SOLR oficial, o envelope JSON e o inteiro teor TIFF em base64 com limite
de 24 MB. Respostas 401/403/407/451, 429, transporte incompleto e schema
inválido permanecem estados explícitos.

```text
python -m pytest -q tests/test_tjrs_solr.py
9 passed

python tools/run_federated_promotion_smoke.py --output docs/provider-discovery/federated-promotion-live-20260908-cycle92.json --text "responsabilidade civil" --page-size 1 --sources tjrs_solr
1 fonte pesquisada, 0 erros, 1 registro deduplicado, 0 inválidos
total conhecido: 706711 (janela parcial)
status: public / complete
```

O smoke confirma a rota pública e a extração JSON reproduzível; a janela
permanece limitada a uma página e não declara completude do acervo.

### Transporte compartilhado - TJPE REST/JSF

O provider `tjpe_jurisprudencia` foi migrado para `SharedHttpClient` nas duas
rotas oficiais (REST e fallback JSF), preservando allowlist, timeout, limite de
bytes, pacing e classificação explícita de acesso, rate limit, transporte e
schema. O fallback JSF continua sendo usado apenas para falha de transporte;
CAPTCHA, WAF e respostas 403/429 não são convertidos em vazio.

```text
python -m pytest -q tests/test_tjpe_jurisprudencia.py tests/test_tjpe_live_recheck.py
20 passed

python tools/run_federated_promotion_smoke.py --output docs/provider-discovery/federated-promotion-live-20260908-cycle93.json --text "responsabilidade civil" --page-size 1 --sources tjpe_jurisprudencia
1 fonte pesquisada, 1 erro, 0 registros deduplicados
status: SSL verification blocked (ambiente local)
```

O smoke encontrou falha de verificação da cadeia TLS local antes da obtenção
de qualquer conteúdo. O resultado é `SslVerificationError`, com
`collection_complete=false` e `reported_total=null`; não é um resultado vazio
e não autoriza promoção. O provider permanece pendente de uma verificação
live em ambiente com cadeia de certificados válida.

### Transporte compartilhado - TJCE/SJURIS

O provider `tjce_sjuris` foi migrado para `SharedHttpClient` na rota oficial
POST, preservando o payload observado, allowlist, timeout, limite de 24 MB para
o PDF inline, pacing e estados explícitos de acesso, rate limit, transporte e
schema. A resposta live reproduziu uma decisão textual pública de segundo grau
com ementa, inteiro teor e PDF inline:

```text
python -m pytest -q tests/test_tjce_sjuris.py
12 passed

python tools/run_federated_promotion_smoke.py --output docs/provider-discovery/federated-promotion-live-20260908-cycle94.json --text "responsabilidade civil" --page-size 1 --sources tjce_sjuris
1 fonte pesquisada, 0 erros, 1 registro deduplicado, 0 inválidos
total conhecido: 57518 (janela parcial)
status: public / complete
```

O ciclo confirma transporte e contrato reproduzíveis para a superfície SJURIS;
não altera a contagem de CJSG geral, pois a fonte já estava habilitada na
federação e sua cobertura é uma coleção SJURIS distinta.

### Transporte compartilhado - TJRO/JURIS

O provider `tjro_jurisprudencia` foi migrado para `SharedHttpClient` nas
rotas públicas de busca, documentos e documentos relacionados. A migração
preserva os payloads JSON, os cabeçalhos oficiais exigidos pela rota de
documento, allowlist, limite de 24 MB, pacing e os estados explícitos de
acesso, rate limit, transporte e schema.

```text
python -m pytest -q tests/test_tjro_jurisprudencia.py
37 passed

python tools/run_federated_promotion_smoke.py --output docs/provider-discovery/federated-promotion-live-20260908-cycle95.json --text "responsabilidade civil" --page-size 1 --sources tjro_jurisprudencia
1 fonte pesquisada, 0 erros, 1 registro deduplicado, 0 inválidos
total conhecido: 1908856 (janela parcial)
status: public / complete
```

O resultado confirma a rota oficial textual e o transporte reproduzível. A
janela bounded não é declaração de completude do acervo nem altera, sozinha,
os gates de grau, documentos e promoção.

### Transporte compartilhado - TJPR

O provider `tjpr_jurisprudencia` foi migrado para `SharedHttpClient` nas
rotas públicas de formulário, pesquisa e expansão XHR de inteiro teor. A
migração preserva a sessão pública, os IDs numéricos dos filtros, a allowlist,
limite de 8 MB, pacing e classificação explícita de acesso, rate limit,
transporte e schema. O detalhe HTML continua passando pelo pipeline de
documentos observado, sem reconstruir slugs.

```text
python -m pytest -q tests/test_tjpr_jurisprudencia.py
20 passed

python tools/run_federated_promotion_smoke.py --output docs/provider-discovery/federated-promotion-live-20260908-cycle96.json --text "responsabilidade civil" --page-size 1 --sources tjpr_jurisprudencia
1 fonte pesquisada, 0 erros, 1 registro deduplicado, 0 inválidos
total conhecido: 1004007 (janela parcial)
status: public / complete
```

O smoke confirma a rota textual oficial e a compatibilidade do transporte
compartilhado. A janela bounded não declara completude do acervo; a fonte já
estava habilitada na federação e não houve alteração de promoção.

### Correção do cálculo de gates GOLD

O gerador `build_national_coverage_gap_map.py` calculava `gold_gates` antes de
copiar `quality_tier` e `quality_critical_gaps` do ledger. Isso marcava como
falha de qualidade providers com qualidade GOLD comprovada. A ordem foi
corrigida e coberta por testes; a matriz regenerada passou de 21 para 62
superfícies com os nove gates técnicos satisfeitos. A correção não promove
nenhuma fonte nem altera a federação: apenas elimina um falso negativo do
relatório de cobertura.

### Fechamento técnico após os ciclos 81-96

```text
python -m pytest -q                  # 1600 passed, 26 skipped
python -m ruff check .               # All checks passed
python -m ruff format --check .      # 1842 files already formatted
python -m mypy src                   # Success: 141 source files
python -m compileall -q src tools tests
git diff --check                     # exit 0 (avisos CRLF/LF apenas)
```

Os inventários e o audit de gates foram regenerados; `passed=10`, `pending=0`,
com 89 tarefas abertas explicitamente classificadas como externas, humanas ou
locais. A conclusão GOLD nacional continua pendente.

### Transporte compartilhado - TJAC Ementario

O provider `tjac_ementario_jurisprudencia` foi migrado para `SharedHttpClient`
no download bounded do volume PDF oficial. A politica mantem allowlist do host,
TLS verificavel, limite de 8 MB, pacing e zero retry automatico para nao
ocultar bloqueios ou mudancas de contrato. O parser permanece em memoria e a
colecao continua sendo uma janela editorial de segundo grau com total
desconhecido.

```text
python -m pytest -q tests/test_tjac_ementario_jurisprudencia.py
5 passed

python tools/run_federated_promotion_smoke.py --output docs/provider-discovery/federated-promotion-live-20260908-cycle97.json --text "responsabilidade civil" --page-size 1 --sources tjac_ementario_jurisprudencia
1 fonte pesquisada, 0 erros, 0 registros, total desconhecido
status: public / complete; janela estatica sem correspondencia observada
```

O resultado nao foi convertido em vazio autoritativo: o volume nao publica
total pesquisavel entre edicoes. Nao houve alteracao de promocao ou federacao.

Uma segunda consulta bounded com `direito` foi registrada em
`federated-promotion-live-20260908-cycle98.json`: um registro valido retornado,
sem erros ou invÃ¡lidos, com total ainda desconhecido por contrato da colecao.

### Evidência live: rotas decisórias TJMA (2026-09-08)

Foi feita uma rodada pública bounded no JurisConsult/TJMA. Os endpoints de
catálogo responderam `200` com JSON, enquanto as rotas de acórdãos, decisões
monocráticas e sentenças responderam `400` com `captcha_not_provided`.
Isso confirma um desafio obrigatório para as superfícies CJSG e CJPG. Nenhum
token foi criado, reutilizado ou contornado; os estados permanecem
`access_blocked` e fora da federação. Evidência redigida:
`docs/provider-discovery/tjma-jurisprudence-route-live-20260908.json`.

### Evidência live: TJSC eproc e identidade de primeiro grau (2026-09-08)

O endpoint oficial eproc foi consultado com o mesmo termo e janela mínima para
graus primeiro e segundo. As duas requisições retornaram o mesmo registro
(`4870937`, total `886012`) sem campos explícitos de grau, instância, ramo ou
coleção. O rótulo observado foi “Acórdãos do Conselho da Magistratura”.
HTTP `200` não é suficiente para comprovar CJPG; a superfície foi classificada
como `degree_unproven`/`contract_invalid` e não foi promovida. Evidência:
`docs/provider-discovery/tjsc-eproc-cjpg-live-20260908.json`.

### Smoke federado opt-in: TJAL ESMAL (2026-09-08)

O smoke explícito habilitou temporariamente a fonte opt-in no roteador, sem
alterar o rollout padrão. A rota oficial retornou dois registros de primeiro
grau, sem erros ou inválidos; o contrato informa `total_known=false` porque a
coleção é curada. A fonte permanece opt-in e não é contada como cobertura
integral CJPG. Evidência redigida:
`docs/provider-discovery/federated-promotion-live-20260908-cycle100.json`.

### Descoberta bounded: TJPR Sentença Digital (2026-09-08)

A página oficial `https://www.tjpr.jus.br/sentenca-digital` respondeu HTTP
200 e expôs um iframe público para `/pesquisa_sentenca/publico/sentenca.do`.
O formulário documenta número do processo, comarca, vara/órgão, juiz, intervalo
de datas e paginação. Uma submissão bounded sem número obrigatório respondeu
HTTP 200 com erro de validação, sem decisão ou inteiro teor. A superfície fica
registrada como descoberta de consulta de sentenças/processos de primeiro grau,
sem promoção CJPG até que exista consulta válida reproduzível e parser de
decisão. Evidência redigida:
`docs/provider-discovery/tjpr-sentenca-digital-live-20260908.json`.

### Descoberta bounded: TJRS busca de sentencas (2026-09-08)

A rota oficial `https://www.tjrs.jus.br/novo/busca/` respondeu HTTP 200 para
um perfil publico com `site=sentencas`, mas a aba efetiva retornada foi
`site` (busca geral do portal). Nao foram observados registros de sentenca,
identificador de decisao ou texto juridico da colecao. A resposta nao e
classificada como vazio autoritativo nem como CJPG; permanece descoberta de
rota de primeiro grau ate que a submissao oficial do formulario produza um
registro reproduzivel. Evidencia redigida:
`docs/provider-discovery/tjrs-sentencas-live-20260908.json`.

### Descoberta bounded: TRT2 PJe Jurisprudencia (2026-09-08)

O portal oficial `https://pje.trt2.jus.br/jurisprudencia/` expôs os endpoints
`/juris-backend/api/opcoes`, `/filtros` e `/documentos`. `opcoes` respondeu
HTTP 200 com a versão `1.5.0-i1` e `captchaOption=2`. A chamada pública de
`filtros` respondeu HTTP 200 com 40.199.552 hits e agregações para assunto,
ano, tipo documental, instância, órgão, magistrado e classe. Já a chamada de
`documentos` respondeu HTTP 200 contendo apenas `tokenDesafio`, imagem e áudio,
sem documentos. Isso é controle de acesso, não vazio autoritativo. Nenhum
token ou imagem foi persistido e não houve tentativa de resolução ou bypass.
O candidato permanece fora do runtime/federação até existir acesso oficial
reprodutível sem esse desafio ou autorização formal. Evidência redigida:
`docs/provider-discovery/trt2-jurisprudencia-api-live-20260908.json`.

### Hardening de identidade canônica: CJF/TRF1 (2026-09-08)

O parser da rota TRF1 agora emite em cada resultado a identidade comprovada
pela superfície oficial: `authority=TRF1`, `branch=federal`, `degree=second`,
`instance=second`, `collection=JURISPRUDENCIA` e o tipo documental observado.
Quando o cartão HTML não repete o grau, a origem é registrada em
`field_provenance` como escopo da rota. A melhoria não promove a fonte: a
última evidência live continua classificando o host CJF como controlado, logo a
superfície permanece bloqueada e nunca é apresentada como busca vazia.

### Ciclo local — CNJ Informativos e STM SharedHttpClient (2026-09-08)

Os providers `cnj_jurisprudencia` e `stm_jurisprudencia` passaram a usar o
transporte compartilhado para consulta e documentos/inteiro teor, com
allowlists oficiais, limites de bytes, timeout, rate limit e circuito. CNJ
mantém sem retry automático para desafios e rate limit; STM permite somente os
hosts oficiais do portal eproc2g. Erros de acesso, transporte, TLS, schema e
conteúdo acima do limite permanecem distintos de vazio.

Validação: `python -m pytest -q tests/test_cnj_jurisprudencia.py
tests/test_stm_jurisprudencia.py tests/test_provider_documentation.py` — 27
passed; Ruff, format e mypy dos dois providers — passed.

### Ciclo local — CNJ, STM e STJ Informativo SharedHttpClient (2026-09-08)

CNJ Informativos, STM/JMU e STJ Informativo agora usam transporte compartilhado
nas consultas; documentos observados seguem o mesmo limite e allowlist por meio
do pipeline documental. Os providers mantêm limites conservadores e não repetem
automaticamente desafios, 403 ou rate limits. Vazio continua reservado a
resposta autoritativa ou recorte local explícito.

Validação: `python -m pytest -q tests/test_cnj_jurisprudencia.py
tests/test_stm_jurisprudencia.py tests/test_stj_informativo.py
tests/test_provider_documentation.py` — 44 passed; Ruff, format e mypy dos
providers — passed.

### Ciclo local — TJMA Informativos SharedHttpClient (2026-09-08)

A listagem oficial de boletins do TJMA passou a usar transporte compartilhado;
PDFs continuam obtidos somente sob demanda pelo pipeline documental. O provider
permanece curado e opt-in, e os estados de acesso, transporte e schema seguem
distintos de vazio.

Validação: `python -m pytest -q tests/test_tjma_informativos.py` — 10 passed;
Ruff, format e mypy do provider — passed.

### Ciclo local — TJMA JurisConsult SharedHttpClient (2026-09-08)

O catÃ¡logo pÃºblico do JurisConsult passou a usar transporte compartilhado,
com allowlist, limite de 4 MB, timeout, rate limit e circuito. A busca protegida
por CAPTCHA continua bloqueada de forma explÃ­cita; desafios, erros HTTP e JSON
invÃ¡lido nÃ£o sÃ£o interpretados como catÃ¡logo vazio.

ValidaÃ§Ã£o: `python -m pytest -q tests/test_tjma_jurisconsult.py` â€” 11 passed;
Ruff, format e mypy do provider â€” passed.

### Ciclo local — TJCE Informativos SharedHttpClient (2026-09-08)

O provider curado de informativos do TJCE passou a usar transporte compartilhado
com allowlist oficial, limite de 8 MB, timeout, rate limit e circuito. A fonte
continua fora da busca geral de acórdãos; bloqueios e schema não são vazios.

Validação: `python -m pytest -q tests/test_tjce_informativos.py` — 8 passed;
Ruff, format e mypy do provider — passed.

### Evidência live bounded — CNJ e STM (2026-09-08)

Os smokes oficiais foram executados após a migração de transporte. CNJ retornou
HTTP 200 em duas páginas, 2+2 itens e IDs disjuntos; STM retornou 2+2 itens em
duas páginas, total 2.597, e detalhe HTML extraído. Evidências redigidas:
`docs/provider-discovery/cnj-live-20260908-transport-recheck.json` e
`docs/provider-discovery/stm-live-20260908-transport-recheck.json`.

### Validação final deste lote (2026-09-08)

```text
python -m pytest -q
1610 passed, 26 skipped

python tools/validate_sdd.py
SDD validation passed

ruff check / ruff format --check / mypy src / compileall / git diff --check
pass
```

## Rastreabilidade

- Requisitos: `spec.md` REQ-001–REQ-015.
- Critérios: `spec.md` AC-001–AC-012.
- Tarefas: `tasks.md` T001–T046.
- Decisões de acesso: `lawful-access-playbook.md` e `threat-model.md`.
- Estado atual: `docs/coverage/source-of-truth.md` e baseline SDD 0091.

## Limitações explícitas

O pacote não afirma cobertura nacional completa, não aprova licenças, não
resolve bloqueios externos e não executa deploy. Providers bloqueados devem
continuar visíveis como bloqueados.
### Ciclo local — TJRJ EJURIS SharedHttpClient (2026-09-08)

As três etapas da sessão pública WebForms/XHR do `tjrj_ejuris` passaram a usar
o transporte compartilhado, com allowlist de `www3.tjrj.jus.br`, TLS verificado,
limite de 16 MB, intervalo por host e sem retry automático de POSTs que
carregam ViewState. Status de controle de acesso, rate limit, timeout, TLS,
redirecionamento fora da allowlist, resposta excedente e schema inválido
continuam explícitos; nenhum é convertido em vazio.

Validação: `python -m pytest -q tests/test_tjrj_ejuris.py
tests/test_provider_documentation.py` — 15 passed; Ruff e mypy do provider —
passed. A evidência live anterior de 2026-09-06 permanece válida; não foi
repetida uma chamada contra a mesma superfície sem necessidade.
### Ciclo local — TCE-SP catálogo público SharedHttpClient (2026-09-08)

As rotas públicas de súmulas, boletins e índice do `tce_sp_jurisprudencia`
passaram a usar transporte compartilhado com allowlist oficial, limite de
8 MB, TLS verificado, intervalo por host e sem retry automático. A busca
dinâmica com reCAPTCHA continua fora do fluxo; HTTP 403/429, timeout, TLS,
resposta excedente e schema inválido permanecem estados explícitos.

Validação: `python -m pytest -q tests/test_tce_sp_jurisprudencia.py` — 11
passed; Ruff e format do provider — passed. Não houve nova chamada live contra
a rota protegida.
### Ciclo local — TJSP/eproc SharedHttpClient (2026-09-08)

As requisições de listagem, paginação e inteiro teor do `tjsp_eproc_jurisprudencia`
passaram a usar transporte compartilhado com allowlist oficial, limite de 16 MB,
TLS verificado, intervalo por host e sem retry automático de POSTs. CAPTCHA,
401/403, 429, timeout, TLS, resposta excedente, redirecionamento fora da
allowlist e schema inválido continuam explícitos; nenhum é convertido em vazio.

Validação: `python -m pytest -q tests/test_tjsp_eproc_jurisprudencia.py
tests/test_provider_documentation.py` — 21 passed; Ruff, format e mypy do
provider — passed. A evidência live de 2026-09-05 continua classificando o
inteiro teor como controle de acesso, sem nova tentativa de bypass.
### Evidência live bounded — TJRJ EJURIS após transporte compartilhado (2026-09-08)

O smoke `NANOJURIS_RUN_TJRJ_EJURIS_LIVE=1 python -m pytest -q
tests/test_tjrj_ejuris_live.py` passou (1 teste). A busca de
`responsabilidade civil` respondeu HTTP 200, total conhecido 45.674 e um
resultado textual com `degree=second`. Evidência redigida:
`docs/provider-discovery/tjrj-ejuris-live-20260908-transport-recheck.json`.
### Ciclo local — TST jurisprudência REST SharedHttpClient (2026-09-08)

As consultas JSON, catálogos e downloads HTML do `tst_jurisprudencia` passaram
a usar transporte compartilhado com allowlist do backend oficial, limite de
16 MB, TLS verificado, intervalo por host e sem retry automático. 401/403,
429, timeout, TLS, resposta excedente, redirecionamento fora da allowlist e
schema inválido continuam explícitos; nenhum é convertido em vazio.

Validação: `python -m pytest -q tests/test_tst_jurisprudencia.py
tests/test_provider_documentation.py` — 18 passed; Ruff, format e mypy do
provider — passed.
### Ciclo local — TRT2 ementário SharedHttpClient (2026-09-08)

Os índices e tópicos públicos do `trt2_ementario_jurisprudencia` passaram a
usar transporte compartilhado com allowlist oficial, limite de 1,5 MB, TLS
verificado, intervalo por host e sem retry automático. Desafios, 401/403/407/451,
429, timeout, TLS, redirecionamento fora da allowlist e schema inválido seguem
explícitos; nenhum é convertido em vazio. O limite por tópico e o pipeline de
PDF observado continuam preservados.

Validação: `python -m pytest -q tests/test_trt2_ementario_jurisprudencia.py
tests/test_provider_documentation.py` — 11 passed; Ruff, format e mypy do
provider — passed.
### Ciclo local — TRF5 jurisprudência SharedHttpClient (2026-09-08)

As etapas WebForms do `trf5_jurisprudencia` passaram a usar transporte
compartilhado com allowlist oficial, limite de 16 MB, TLS verificado, intervalo
por host e sem retry automático de POSTs com token de sessão. O corpo legado
ISO-8859-1 continua preservado em bytes e decodificado no parser; desafios e
erros de acesso/transporte continuam distintos de vazio.

Validação: `python -m pytest -q tests/test_trf5_jurisprudencia.py` — 10
passed; Ruff, format e mypy do provider — passed.
### Evidência live bounded — TST e TRF5 após transporte compartilhado (2026-09-08)

`tools/run_tst_live_smoke.py` confirmou busca HTTP 200 e detalhe HTML público
com 91.008 bytes e texto extraível. `tools/run_trf5_live_smoke.py` confirmou
duas páginas HTTP 200 com IDs disjuntos, resumo e detalhe HTML público. Os
corpos não foram persistidos. Evidências redigidas:
`docs/provider-discovery/tst-live-20260908-transport-recheck.json` e
`docs/provider-discovery/trf5-jurisprudencia-live-20260908-transport-recheck.json`.

### Reconciliação local — TRF1/CJF (2026-09-09)

O provider existente `cjf_jurisprudencia` foi reconciliado à superfície
canônica `TRF1/federal/second/JURISPRUDENCIA`. Antes, o catálogo identificava
o adapter como `CJF/unknown` e a matriz mantinha TRF1 como providerless,
ocultando a diferença entre adapter executável e disponibilidade atual.

Alterações verificáveis:

- `src/nanojuris/coverage_matrix.py` vincula TRF1 ao provider existente e
  classifica `access_control_required` como `blocked_access`;
- `tools/build_provider_coverage.py` publica a identidade canônica TRF1,
  grau/instância second e coleção JURISPRUDENCIA sem renomear o provider;
- catálogos, matriz, registro, workpacks e mapa nacional foram regenerados;
- testes cobrem a identidade e garantem que `access_control_required` não vire
  vazio nem federação.

Resultado do inventário: superfícies nacionais continuam 251; providers
órfãos caem de 20 para 19; superfícies core providerless caem de 55 para 54;
TRF1 passa a `blocked_or_unavailable` com `cjf_jurisprudencia`, sem aumentar a

cobertura ouro (TRF1 continua sem live valido e fora da federacao). Os testes
focados passaram: 38 testes de catalogo/registro/mapa/workpacks.

Snapshot vigente apos todas as reconciliacoes deste ciclo: 249 superficies,
52 superfícies core sem provider e 183 itens na fila de descoberta. Os valores
anteriores de 251/54/185 acima pertencem ao subciclo TRF1 e foram substituidos
pela reconciliacao de ramo STJ/STM.

### ReconciliaÃ§Ã£o de ramo â€” STJ e STM (2026-09-09)

O gerador da matriz de tarefas criava linhas institucionais duplicadas para
STJ e STM usando `branch=federal`, apesar de os registros canÃ³nicos existentes
declararem respectivamente `branch=superior` e `branch=military`. A correÃ§Ã£o
mantÃ©m os providers existentes (`stj_scon` e `stm_jurisprudencia`), elimina as
duas linhas providerless incorretas e preserva os estados live reais: STJ
continua bloqueado e STM continua federado.

O mapa nacional agora registra 249 superfÃ­cies, 52 superfÃ­cies core sem
provider e 183 itens na fila de descoberta. CJPG/CJSG permanecem 8/27 e
25/27; nenhuma cobertura de grau foi inferida por essa reconciliaÃ§Ã£o.
cobertura ouro (TRF1 continua sem live válido e fora da federação). Os testes
focados passaram: 38 testes de catálogo/registro/mapa/workpacks.

### Nota de consistência do snapshot (2026-09-09)

O snapshot autoritativo após a reconciliação de ramo é o gerado em
`docs/coverage/national-coverage-gap-map-20260908.json`: 249 superfícies, 52
superfícies core sem provider e 183 itens na fila de descoberta. O texto deste
registro é histórico; não deve ser usado para substituir os artefatos gerados.

### Fechamento local de parser e detalhe eproc (2026-09-09)

As tarefas locais T014 e T017 deste pacote estão concluídas para a família
eproc federal implementada. O parser independente
`FederalEprocJurisprudenciaProvider`/`fetch_eproc_page` usa o transporte
compartilhado, preserva `SearchPage`, identidade canônica, `raw` e
`SourceTrace`, e rejeita explicitamente acesso controlado, rate limit,
transporte e schema inválido. O detalhe sob demanda
`FederalEprocJurisprudenciaProvider.get_document` limita bytes, valida a
allowlist da instância, preserva MIME/hash/bytes e alimenta
`CanonicalDocument`/`DecisionBundle` sem persistência automática.

Evidência executável:

```text
python -m pytest -q tests/test_eproc_jurisprudencia_federal.py \
  tests/test_trf4_eproc_jurisprudencia.py tests/test_state_eproc_jurisprudencia.py \
  tests/test_transport_runtime.py
56 passed
```

As chamadas bounded de TNU, TRF2 e TRF6 retornaram resultados públicos de
segundo grau e inteiro teor válido em
`docs/provider-discovery/eproc-detail-live-20260908-cycle75.json`.
O fechamento é restrito aos adapters eproc implementados; não promove
fontes candidatas nem encerra T058/T059, que continuam dependentes de rotas
reproduzíveis e gates de cada superfície nacional.

### Correção live — TNU/eproc módulo público (2026-09-09)

O host legado `eproctnu.cjf.jus.br/eproc` redireciona o acesso inicial para
SSO. O módulo público anunciado pelo CJF está em
`eproctnu-jur.cjf.jus.br/eproc`; a configuração foi corrigida para essa base.

Busca bounded executada com `txtPesquisa=aposentadoria`, página 1 e limite 10:
HTTP 200, cards `resultadoItem`, total informado e três registros normalizados
com `degree=second` e `instance=second`. O detalhe de um identificador real
retornou HTTP 200, HTML textual e inteiro teor extraível. Hashes e metadados
estão em `docs/provider-discovery/tnu-public-module-live-20260909.json`.

Validação executável:

```text
$env:PYTHONPATH='src'; python -c "... TnuEprocJurisprudenciaProvider ..."
```

Resultado: `tnu_eproc_jurisprudencia`, total informado, três resultados, página
`page`, status HTTP 200; detalhe público com `access_status=public`.

Smoke federado opt-in adicional:

```text
python tools/run_federated_promotion_smoke.py --output docs/provider-discovery/tnu-federated-live-20260909.json --text "aposentadoria" --page-size 1 --sources tnu_eproc_jurisprudencia
```

Resultado: `sources_searched=1`, `sources_with_errors=0`, `total_returned=1`,
`invalid_records=0`. O rollout padrão não foi ampliado nesta execução.

### Descoberta externa — TRT3 Ementário (2026-09-09)

O repositório oficial do TRT3 expôs a coleção `Ementário de Jurisprudência` e
um volume PDF público (n. 12, dezembro de 2016). A entrada respondeu HTTP 200
e o PDF respondeu `application/pdf`, com 35 páginas e texto extraível por
amostra. A evidência redigida está em
`docs/provider-discovery/trt3-ementario-live-20260909.json`.

Classificação: `curated_context`/`candidate_static_ementario_only`. O volume é
uma publicação estática de ementas, não uma busca geral com filtros, paginação
ou total autoritativo. Nenhum adapter de jurisprudência geral foi criado e a
fonte não foi habilitada na federação. O inteiro teor dos votos também não foi
demonstrado nesta prova.

### Descoberta externa — TRT6 (2026-09-09)

O portal oficial `apps.trt6.jus.br/acordaos/` respondeu HTTP 200 e documentou
formulário de pesquisa textual, filtros de processo, órgão, redator e datas,
além de paginação JavaScript. O POST de pesquisa exige `g-recaptcha-response`;
nenhum POST sem desafio foi emitido e nenhum CAPTCHA foi resolvido ou
reutilizado. A superfície está registrada como `access_blocked` em
`docs/provider-discovery/trt6-acordaos-route-live-20260909.json`; não há
resultado textual reproduzível para implementar ou promover.
