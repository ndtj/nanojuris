# Verificacao

Status: `in_progress`

## Comandos

```text
python tools/build_state_appellate_program.py --write
python -m pytest -q tests/test_state_appellate_program.py
python tools/validate_sdd.py
```

## Evidencia atual

### Snapshot consolidado — 2026-09-07

Os artefatos gerados atualmente são a autoridade para as contagens deste
programa: `docs/coverage/state-appellate-program-20260905.json` registra
25/27 autoridades com os oito gates, duas em `blocked_recheck` e a
reivindicação `25/27`. A matriz de grau registra CJPG `7/27` e CJSG `25/27`.
Os registros históricos abaixo são preservados como trilha de evolução e não
substituem esse snapshot.

As rechecagens públicas bounded de CJPG não encontraram outra rota oficial
reproduzível; consulta processual, ementário sem grau comprovado e páginas
institucionais permanecem fora da contagem. Evidências consolidadas:
`docs/provider-discovery/state-cjpg-27-audit-20260907.md` e
`docs/provider-discovery/legitimate-blocked-techniques-20260907.json`.

## Resultados

| Gate | Resultado |
| --- | --- |
| geracao deterministica | passed; 27 autoridades unicas |
| testes focados | passed; 3 testes |
| cobertura estrita | 20/27 workpacks com 8/8 gates |
| lacunas executaveis | 7 `contract_hardening`, 3 `adapter_discovery` |
| bloqueios explicitos | 4 `blocked_recheck` |
| inventario Juscraper | pass; snapshot `604c1dd70d6f313011cc1079790febe6c71807e2`, 25 TJs |
| correcao semantica TJRO | pass; CJSG nao aponta mais para `tjro_liame` |
| suite completa local | pass; 1.194 testes, 23 skips |

Neste ciclo foram fechadas tecnicamente as superfícies `TJBA/CJSG`,
`TJMT/CJSG` e `TJPA/CJSG`. Os adapters rejeitam filtros de primeiro grau,
validam o escopo de segundo grau quando a fonte o informa e expõem `degree`,
`instance`, `branch`, `authority`, `collection` e `document_type`. Chamadas
públicas bounded de 2026-09-05 retornaram HTTP 200 com conteúdo textual; nenhuma
proteção de acesso foi contornada.

Cobertura 27/27 permanece nao comprovada enquanto qualquer workpack possuir
tarefa aberta ou estado nao consultavel.

### Revalidacao local 2026-09-06

- O programa regenerado contabiliza 27 autoridades, 17 superfÃ­cies CJSG com
  os oito gates e 10 workpacks ainda incompletos; a reivindicaÃ§Ã£o permanece
  `17/27`.
- A suite completa local passou com 1.264 testes e 23 skips. Ruff, format,
  mypy, compileall, SDD e `git diff --check` tambÃ©m passaram.
- O smoke CJSG bounded classificou 4 buscas como vÃ¡lidas e 3 detalhes como
  controle de acesso. O smoke federado consultou 38/38 fontes, sem erros
  operacionais nesta execuÃ§Ã£o; nove fontes mantiveram total desconhecido e a
  coleta global permaneceu incompleta.
- TJRR foi corrigido para reproduzir o postback PrimeFaces com contexto
  completo do formulÃ¡rio; smoke bounded de 2026-09-06 confirmou pÃ¡gina 2 sem
  repetiÃ§Ã£o (`page_2_status=valid`). O detalhe PDF continua explicitamente
  `source_unavailable` quando a fonte entrega apenas o aviso do visualizador.
- Nenhum commit, push, deploy ou alteraÃ§Ã£o de produÃ§Ã£o foi executado.

### Ajustes adicionais de contrato e teste — 2026-09-06

- TJRN recebeu pós-filtros canônicos locais para grau, instância, classe,
  órgão julgador, origem, tipo de decisão e intervalo de data de julgamento.
  Como o total remoto permanece misto, qualquer refinamento marca
  `total_known=false` e completude não afirmativa; incompatibilidades não são
  convertidas em erro de transporte nem em falso vazio.
- O pytest passou a forçar o `src` da worktree (`tests/conftest.py`), evitando
  que um wheel instalado em `site-packages` mascare regressões locais.

### Bindings CJSG adicionais — 2026-09-06

- TJRN: duas páginas públicas bounded com `degree=second` e `instance=second`
  foram registradas em `docs/provider-discovery/tjrn-cjsg-live-20260906.json`.
  O binding nativo é `JURISPRUDENCIA`, mas o filtro canônico foi comprovado e
  a matriz agora o representa como CJSG; a superfície CJPG segue pendente.
- TJRO: o adapter traduz `collection=CJSG`, `degree=second` e
  `instance=second` para `fields.grau_jurisdicao=[2]`. A chamada live retornou
  três registros PJESG, todos de segundo grau, em
  `docs/provider-discovery/tjro-cjsg-live-20260906.json`.
- TJRR: a busca PrimeFaces retornou duas páginas exclusivamente de segundo
  grau; o detalhe PDF permanece `source_unavailable` quando a fonte entrega o
  aviso do visualizador, sem conversão para vazio.
- A cobertura estrita CJSG passou de 17/27 para 20/27. Nenhum commit, push,
  deploy ou alteração de produção foi executado.

## Rastreabilidade

### Fronteira oficial TJMA/JurisConsult - 2026-09-06

- A API publica confirmou `GET /v1/sg/jurisprudencias/processos` como rota de
  acórdãos; a mesma aplicação também expõe rotas de decisões monocráticas e
  turma recursal. A tentativa bounded sem token retornou HTTP 400 com
  `captcha_not_provided`.
- O adapter agora declara as quatro rotas oficiais e classifica respostas
  estruturadas de CAPTCHA como `AccessControlRequiredError`; respostas 400
  genéricas continuam `SourceUnavailableError`.
- Evidência redigida: `docs/provider-discovery/tjma-jurisprudencia-captcha-live-20260906.json`.
- Nenhum desafio foi criado, reutilizado ou contornado; TJMA permanece fora da
  federação e a lacuna CJSG continua explícita.

### Fechamento local do ciclo — 2026-09-06

- O workflow `live-validation.yml` passou a executar uma revalidaÃ§Ã£o semanal
  e um smoke federado bounded das fontes habilitadas; o acionamento manual e
  os limites continuam disponÃ­veis.

- Smoke live TJRN: 1/1 teste passou; a rota pública retornou decisões de
  segundo grau.
- Smoke live TJRO/TJGO: 5/5 testes passaram, incluindo a consulta CJSG com
  `grau_jurisdicao=[2]`.
- Smoke live TJRR: busca e segunda página válidas; detalhe permanece
  `source_unavailable` quando o portal entrega apenas o visualizador PDF.
- Suíte completa: 1.277 testes passaram e 24 foram pulados por dependerem de
  opt-in live ou de dependência opcional.
- Gates estáticos: Ruff, formatação, mypy, compileall, validação SDD e diff
  sem erros passaram.
- Inventários regenerados: 60 providers (52 runtime, 7 candidatos, 1 família),
  20/27 CJSG com oito gates e 7 workpacks incompletos por descoberta ou
  bloqueio externo.

REQ-001 a REQ-008 estao ligados a AC-001 a AC-006 em `traceability.md`. A
evidencia executavel desta fase e o teste focado, a suite completa local, o
inventario Juscraper e os artefatos gerados. A suite foi executada com
`PYTHONPATH=src` para garantir que o codigo local, e nao uma instalacao antiga,
fosse testado.
### Fechamento TJPB/CJSG - 2026-09-05

- Adapter: `TjpbPjeJurisprudenciaProvider` agora expõe identidade canônica de
  segundo grau, rejeita escopos de sentença e preserva proveniência.
- Evidência live: `docs/provider-discovery/tjpb-pje-live-20260905-cycle55.json`,
  duas páginas bounded e detalhe HTML público.
- Testes: parser, identidade CJSG e rejeição de primeiro grau aprovados.
- A matriz foi regenerada com TJPB/CJSG consultável; cobertura estrita passou a
  13/27. Nenhum deploy ou publicação foi executado.

### Paridade Juscraper/TJPB/TJPE - 2026-09-06

- TJPB: payload alinhado ao backend (`id_origem=8,2`, `teor`, `nr_rocesso` e
  `X-Requested-With`); validação de grau deixou de tratar a palavra `sentenca`
  na ementa como prova de primeiro grau.
- TJPE: `transport="auto"` virou o padrão, preservando REST e acionando o
  fluxo JSF/RichFaces público quando a falha é de transporte.
- Testes focados: 51 passed (`test_initial_json_providers.py` e
  `test_tjpe_jurisprudencia.py`).
- Live bounded: TJPB retornou 3 registros `degree=second`, `collection=CJSG`;
  TJPE padrão `auto` retornou 3 registros via JSF. Nenhum controle foi
  contornado.
- Comparação corrigida: 17/17 superfícies com dados no Juscraper também
  retornaram dados no NanoJuris; a divergência ficou em zero.
### Rechecagem de alternativas oficiais sem bypass — 2026-09-07

- TJAP: shell Tucujuris, API pública, PJe 2G e página oficial de súmulas foram
  inspecionados. A API exige Turnstile; PJe é apenas consulta processual e a
  página legada é especializada. Nenhuma rota tokenless de jurisprudência
  geral foi encontrada.
- TJMA: catálogos públicos confirmaram superfícies CJSG/CJPG e filtros de
  inteiro teor, mas as rotas de resultados retornam `captcha_not_provided`.
  O bundle oficial e o portal institucional não expõem contrato tokenless.
- TJTO, TJCE, TJSE, STF, STJ, CJF, TJMG/CJPG, TJBA/CJPG e o banco de sentenças
  militar foram rechecados por HTTPS comum e, quando público, navegador
  Chromium limpo. WAF/CAPTCHA/Turnstile, bloqueio de transporte, login ou
  consulta processual permaneceram estados explícitos.
- Componentes do template local foram auditados: navegação comum, parsing,
  redaction e fingerprint de schema são utilizáveis; stealth, fingerprints,
  rotação de proxy, replay de cookies/tokens, desativação de TLS e resolução
  de desafios não foram usados por serem bypass.
- TJMG/CJSG foi a única alternativa nova legitimamente desbloqueada: a API
  moderna oficial de JSON e o endpoint de inteiro teor estão públicos e já
  integram o adapter. TJAP e TJMA permanecem `blocked_recheck`.

Evidências redigidas: `docs/provider-discovery/legitimate-blocked-techniques-20260907.json`,
`official-alternative-surface-recheck-20260907.json`,
`blocked-route-recheck-20260907.json` e `lib-template-technique-audit-20260907.json`.
Nenhum commit, push, deploy ou alteração de produção foi executado.
