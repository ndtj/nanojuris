# Validation Report: 2026-08-02

Este e um snapshot historico. Para o estado atual de release, consulte
[`release-checklist.md`](release-checklist.md), o CI e o registry de providers.

Este relatorio aplica [use-case-validation-matrix.md](use-case-validation-matrix.md)
para verificar o estado atual da NanoJuris como biblioteca open source premium de
extracao de dados juridicos.

Escopo validado: testes offline, lint, higiene de diff, imports do core/store/MCP,
exemplo SDK offline, CLI de fontes, CLI de diagnostico, matriz de casos de uso e
smokes live conservadores contra fontes publicas.

## Resumo executivo

Estado geral: fundacao tecnica forte para extracao, canonicalizacao, exportacao,
store local e MCP minimo. O projeto ja tem boa base para uso por desenvolvedores,
agentes e fluxos offline controlados. A rodada operacional posterior adicionou
CLI de store, tools MCP de store, guia de provider, checklist de release e
exemplo SDK offline, deduplicacao por `canonical_key`, buscas salvas por
`ResearchRun`, exportacao de runs salvos, paginacao por `offset`, `get_document`
parcial para inteiro teor publico TJSP/CJSG e catalogo brasileiro de tribunais.
Tambem foi feita uma limpeza de publicacao: artefatos internos de analise HAR,
documentacao operacional de equipe, scripts temporarios e PDFs locais nao fazem
parte do pacote publico.
O catalogo passou a expor `source_system` para descoberta por familia tecnica em
Python, CLI e MCP, e os principios de UX por publico foram formalizados em
[audience-ux.md](audience-ux.md).
Na sequencia de cobertura nacional, o catalogo recebeu URLs oficiais estaveis
para orgaos centrais, TRFs e TJs, e o STJ passou a ter ficha tecnica publica em
[stj-source-profile.md](stj-source-profile.md).
O provider inicial `stj_scon` foi implementado com parser offline, fixture
publica representativa, `ProviderCapabilities`, registro no cliente padrao e canonicalizacao
para `CanonicalDecision`.
Rodada live: BNP/Pangea respondeu catalogo, busca e MCP search com dados reais;
TJSP/CJSG e STJ/SCON retornaram controle de acesso em chamadas diretas e foram
classificados como `AccessControlRequiredError`, sem bypass.
O diagnostico TJSP/CJSG foi refinado para separar retorno ao formulario, campos
`recaptcha_response_token`, `uuidCaptcha`, rota `captchaControleAcesso`, scripts
de login e presenca de containers reais de resultado.
Na consulta processual TJSP/e-SAJ CPOPg, a entrada feita no navegador foi
reproduzida por sessao HTTP limpa via `search.do`, com redirect oficial para
`show.do`; o provider `tjsp_esaj_cpopg` foi implementado para consulta por numero
CNJ e o fluxo economico de descoberta de rotas foi formalizado.
As principais lacunas agora estao em ampliar inteiro teor por provider, expandir
`stj_scon` com contrato live opt-in, completar familias tecnicas onde houver
evidencia estavel, criar benchmark de cobertura, melhorar deduplicacao por fonte,
suportar streaming de arquivos muito grandes e definir plugin externo de
providers.

Resultado dos checks:

| Check | Resultado | Evidencia |
| --- | --- | --- |
| Higiene de diff | Passou | `git diff --check` sem saida |
| Testes offline | Passou | `121 passed` |
| Simulacao por publico | Passou | [use-case-simulation-2026-08-02.md](use-case-simulation-2026-08-02.md) |
| Testes live opt-in | Passou | BNP/Pangea e TJSP/CJSG: `3 passed` |
| Live API BNP/Pangea | Passou | catalogo `93` orgaos, `21` especies; busca retornou `stf-rg-615` |
| Live API TJSP/CJSG | Passou com acesso controlado | `AccessControlRequiredError` explicito, sem bypass |
| Live API TJSP/e-SAJ CPOPg | Passou | consulta por numero CNJ retornou processo publico via `search.do` -> `show.do` |
| Live API STJ/SCON | Passou com acesso controlado | endpoint oficial retornou validacao de acesso, classificada sem bypass |
| MCP live BNP/Pangea | Passou | busca canonica retornou 1 resultado real |
| MCP diagnostics | Passou | `bnp_pangea`, `tjsp_cjsg`, `tjsp_esaj_cpopg` e `stj_scon` declarados |
| Lint | Passou | `ruff check src tests examples`: `All checks passed!` |
| Exemplo SDK offline | Passou | workflow gerou run, stats e record offline |
| Smoke import | Passou | `imports ok: NanoJurisClient SQLiteStore` |
| Smoke MCP import | Passou | `mcp imports ok` |
| CLI fontes | Passou | fontes padrao listadas com capabilities, incluindo `tjsp_esaj_cpopg` |
| CLI diagnostico BNP | Passou | capabilities, endpoints, limites e uso responsavel exibidos |
| CLI diagnostico TJSP | Passou | acesso parcial/controle de acesso declarados sem bypass |
| Smoke caso real TJSP | Passou | e-SAJ CPOPg retornou processo publico; CJSG retornou controle de acesso explicito, sem bypass |

## Leitura tecnica por area

### Arquitetura

Verificacao: a separacao entre core, store, exporters e MCP minimo esta correta.
O import smoke confirma que `nanojuris.mcp_server` pode ser importado sem iniciar
servidor e sem quebrar o core.

Status: bom.

Proximo criterio tecnico: formalizar plugin externo de providers e evitar que
novas fontes acoplem regras diretamente ao cliente.

### Produto e open source

Verificacao: README, roadmap, casos de uso e matriz de validacao ja comunicam o
que esta implementado, parcial e planejado.

Status: bom.

Proximo criterio tecnico: transformar esta validacao em checklist recorrente de
release e issue templates por tipo de fonte/problema.

### Pesquisa de fontes

Verificacao: `nanojuris fontes` e `diagnostico` expõem capacidades reais das
fontes atuais. BNP/Pangea aparece como API publica JSON; TJSP/CJSG aparece como
HTML publico sujeito a captcha/controle de acesso; TJSP/e-SAJ CPOPg aparece como
consulta processual por numero CNJ com rota live validada.

Status: bom para fontes atuais, parcial para expansao nacional.

Proximo criterio tecnico: criar fichas formais para STJ, STF e proximas fontes
antes de implementar provider.

### Extracao de dados juridicos

Verificacao: testes offline validam canonicalizacao de decisao/precedente e
exports objetivos. Os modelos evitam interpretacao juridica.

Status: bom.

Proximo criterio tecnico: completar `CanonicalDocument` com fluxo real de
inteiro teor publico e dicionario de campos por tipo documental.

### Engenharia de providers

Verificacao: providers atuais declaram capabilities e testes live permanecem
opt-in. A CLI de diagnostico deixa claro quando a fonte pode ter acesso parcial
ou indisponibilidade. O fluxo `source_route_probe.py` permite validar rotas com
sessao limpa antes de promover uma descoberta para provider.

Status: parcial.

Proximo criterio tecnico: refatorar `bnp_pangea` e `tjsp_cjsg` para reutilizar
mais explicitamente o pipeline de fetch/parse e melhorar tratamento de erros live.

### Pipeline de extracao

Verificacao: existem primitivas de fetch/parse e testes offline, mas os providers
atuais ainda nao estao totalmente reorganizados em torno delas.

Status: parcial.

Proximo criterio tecnico: migrar providers existentes para o pipeline comum sem
alterar API publica.

### Schema canonico

Verificacao: canonical search, canonical JSONL, CSV tipado e store preservam
modelos canonicos. Smoke import e testes confirmam serializacao basica.

Status: bom.

Proximo criterio tecnico: versionamento explicito de schema/parser e regras de
deduplicacao avancada por fonte.

### Qualidade e proveniencia

Verificacao: traces existem e aparecem no desenho validado por testes. Ainda nao
ha benchmark de completude nem relatorio por campo.

Status: parcial.

Proximo criterio tecnico: criar benchmark offline por fixture e score de
completude por fonte/campo.

### Storage and Indexing Engineer

Verificacao: testes confirmam `SQLiteStore`, `CanonicalStore`, query e stats. O
fluxo local esta funcional no core.

Status: bom no SDK e na CLI basica.

Proximo criterio tecnico: preparar migracoes e cursor opaco para stores remotos.

### Data Product Engineer

Verificacao: JSONL canonico, CSV generico e CSV por tipo ja existem e passam em
testes. Isso atende primeira camada de Excel/pandas/BI.

Status: bom.

Proximo criterio tecnico: criar guias pandas/DuckDB e avaliar Parquet como extra
opcional.

### MCP and Agent Integration Lead

Verificacao: tools MCP basicas e tools MCP de store passam em testes offline. O
import do modulo nao quebra sem servidor. CLI/documentacao expõem MCP minimo e
consulta a stores SQLite locais.

Status: bom para MVP MCP.

Proximo criterio tecnico: adicionar `get_document`, cursor opaco remoto e exemplo
de configuracao em cliente MCP real.

### CLI e experiencia de desenvolvimento

Verificacao: `fontes`, `diagnostico` e `store` funcionam e retornam JSON rico. O
primeiro uso tecnico esta bom para descoberta de fonte e consulta local.

Status: bom para MVP operacional.

Proximo criterio tecnico: criar exportacao de buscas salvas e exemplos guiados
por persona.

### Seguranca, etica e conformidade

Verificacao: diagnostico TJSP declara captcha/controle de acesso e nao ha bypass.
Live tests permanecem opt-in. A matriz preserva a fronteira extraction-first.

Status: bom.

Proximo criterio tecnico: checklist de fonte responsavel antes de novos providers
e politica documentada de fixtures publicas representativas.

### QA e benchmark

Verificacao: suite offline passa rapidamente; live tests estao pulados por padrao
com env vars explicitas.

Status: bom para regressao local, parcial para benchmark publico.

Proximo criterio tecnico: implementar benchmark de cobertura e completude por
fonte.

### Observabilidade e confiabilidade

Verificacao: diagnostico existe, mas ainda falta logging estruturado e playbooks
por fonte.

Status: parcial.

Proximo criterio tecnico: taxonomia de erros, `diagnostico --json` e ultimo
status live conhecido por fonte.

### Release and Packaging Engineer

Verificacao: lint, testes, diff hygiene e import smoke passaram. Extras opcionais
nao quebraram o import basico.

Status: bom.

Proximo criterio tecnico: checklist formal de release, build wheel/sdist e smoke
de instalacao limpa em CI.

### Documentation Lead

Verificacao: docs centrais apontam para equipe, matriz de uso, MCP, storage,
capabilities e blueprint.

Status: bom.

Proximo criterio tecnico: adicionar guias operacionais: provider novo, analytics,
release checklist e source playbooks.

### Community Maintainer

Verificacao: ainda nao ha templates especificos para novas fontes, bugs de
provider e fixtures.

Status: planejado.

Proximo criterio tecnico: criar templates de issue/PR e checklist de provider.

## Validacao por caso de uso

### UC-01: advogado busca jurisprudencia e exporta para revisao

Status: parcial.

O que esta bom:

- busca, canonicalizacao e exportadores estao cobertos por testes offline;
- CLI suporta formatos de exportacao;
- capabilities orientam escolha de fonte;
- traces fazem parte dos modelos.

O que precisa melhorar:

- fluxo live depende da estabilidade da fonte;
- ainda nao ha inteiro teor publico via `get_document`;
- falta agrupamento de pesquisa como `ResearchRun`.

Veredito: pronto para fluxo controlado/offline e SDK; ainda nao completo para
uso real amplo com documentos completos.

### UC-02: agente de IA via MCP sem interpretacao juridica

Status: implementado como MVP.

O que esta bom:

- `mcp_tools` passa em testes offline;
- `search_jurisprudence`, `list_sources`, `source_diagnostics` e
  `export_results` existem;
- `store_stats`, `store_query` e `store_get` existem;
- `page_size` e limitado;
- import nao exige MCP runtime.

O que precisa melhorar:

- falta `get_document`;
- falta exemplo de cliente MCP real.

Veredito: MVP MCP aprovado; proxima fase deve focar documento, cursor opaco e
exemplo de cliente MCP real.

### UC-03: legal operations monta base local

Status: implementado no core e na CLI basica.

O que esta bom:

- `SQLiteStore`, `CanonicalStore`, query e stats passam em testes;
- `client.search_and_store` existe;
- `client.search_and_store_run` cria `ResearchRun` rastreavel;
- store preserva JSON canonico e traces.
- `nanojuris store stats`, `nanojuris store query` e `nanojuris store get`
  existem e possuem testes automatizados.
- `nanojuris store runs`, `nanojuris store run` e `nanojuris store records`
  retomam buscas salvas por `run_id`.
- `nanojuris store export` exporta runs salvos em `json`, `jsonl`, `csv` e
  `markdown`.
- `records` e `export` aceitam `offset` para paginar runs grandes.
- registros equivalentes sao deduplicados por `canonical_key`.

O que precisa melhorar:

- deduplicacao avancada por benchmark de fonte;
- falta cursor opaco para stores remotos.

Veredito: SDK e CLI basica aprovados; proxima melhoria e cursor opaco remoto e
deduplicacao por fonte.

### UC-04: pesquisador constroi dataset de jurimetria

Status: parcial.

O que esta bom:

- CSV, CSV por tipo e JSONL canonico existem;
- SQLite oferece base local simples;
- dados objetivos nao adicionam interpretacao.

O que precisa melhorar:

- falta benchmark de completude;
- falta deduplicacao avancada por fonte;
- faltam guias pandas/DuckDB;
- falta export Parquet opcional.

Veredito: bom para prototipos; precisa camada analitica para virar referencia em
jurimetria.

### UC-05: desenvolvedor cria provider novo

Status: parcial.

O que esta bom:

- arquitetura de provider existe;
- providers atuais servem como exemplo;
- capabilities padronizam descoberta;
- testes fake demonstram extensibilidade.

O que precisa melhorar:

- falta guia formal de provider;
- falta template de provider;
- falta plugin registry via entrypoints;
- falta checklist de fixture publica representativa.

Veredito: possivel para equipe interna; ainda trabalhoso para comunidade.

### UC-06: usuario diagnostica fonte instavel ou bloqueada

Status: parcial bom.

O que esta bom:

- `nanojuris diagnostico --fonte bnp_pangea` passou;
- `nanojuris diagnostico --fonte tjsp_cjsg` passou;
- TJSP declara `access_control_required` e nao promete bypass;
- limitations e responsible_use aparecem no output.

O que precisa melhorar:

- falta ultimo status live conhecido;
- falta playbook por fonte;
- falta logging estruturado;
- falta `diagnostico --json` se o output futuro mudar de formato.

Veredito: diagnostico atual e util e responsavel; precisa observabilidade para
operacao continua.

### UC-07: mantenedor avalia release

Status: parcial bom.

O que esta bom:

- `pytest -q`: 94 passed, 3 skipped;
- `ruff check src tests examples`: passou;
- `git diff --check`: passou;
- imports core/store/MCP passaram.

O que precisa melhorar:

- falta CI de build wheel/sdist;
- falta smoke de instalacao limpa;
- falta mypy como gate documentado, se o projeto decidir adotar.

Veredito: release local esta saudavel; processo formal ainda precisa virar doc e
CI.

### UC-08: sistema externo consome NanoJuris como SDK

Status: parcial bom.

O que esta bom:

- `NanoJurisClient`, `SQLiteStore`, exporters e MCP tools importam;
- API usa modelos tipados;
- extras opcionais nao quebram core.
- exemplo SDK offline ponta a ponta executa sem rede.

O que precisa melhorar:

- falta async client;
- falta PostgresStore;
- falta plugin externo.

Veredito: SDK ja serve para prototipo serio; falta extensibilidade de producao.

### UC-09: extracao de inteiro teor publico

Status: planejado.

O que esta bom:

- `CanonicalDocument` e primitivas de extracao existem como base;
- TJSP capabilities ja declaram endpoint potencial de arquivo;
- politica de acesso bloqueado esta clara.

O que falta:

- metodo publico `get_document`;
- parser real por fonte;
- persistencia associada ao documento;
- paginacao/limite de texto para MCP.

Veredito: proxima grande feature de valor para usuarios juridicos.

### UC-10: benchmark publico de cobertura

Status: planejado.

O que esta bom:

- testes offline e fixtures ja apontam o caminho;
- `ExtractionStatus` e capabilities suportam a ideia.

O que falta:

- comando de benchmark;
- fixtures gold suficientes;
- metricas de completude;
- relatorio publico por fonte.

Veredito: essencial para sustentar a promessa premium em escala nacional.

## Pontos aprovados nesta rodada

- Arquitetura extraction-first esta coerente.
- Core nao tenta interpretar merito juridico.
- MCP minimo esta testado e importavel.
- CLI de fontes e diagnostico funciona.
- Store local e exports estao cobertos por testes.
- Deduplicacao por `canonical_key` esta implementada e coberta em SDK, CLI e MCP.
- Live tests ficam opt-in e nao poluem a validacao local.
- TJSP/CJSG informa controle de acesso sem bypass.
- Smoke controlado com o processo publico `0003938-14.2017.8.26.0323` retornou
  `TJSP/CJSG requires captcha or another access-control step`, comportamento
  esperado e responsavel para fonte com controle de acesso.

## Pontos que precisam melhorar

1. `get_document`: inteiro teor publico como `CanonicalDocument`.
2. Benchmark: completude por fonte, tipo e campo.
3. Cursor opaco para stores remotos.
4. Provider development: template e plugin registry.
5. Observabilidade: taxonomia de erros, playbooks e ultimo status live conhecido.
6. Release: build em CI e smoke de instalacao limpa.
7. Analytics: guias pandas/DuckDB e possivel Parquet opcional.

## Backlog recomendado por prioridade

### P0: fechar MVP operacional

- criar cursor opaco para stores remotos;
- adicionar template de provider.

### P1: abrir valor juridico alto

- implementar `get_document` em uma fonte publica estavel;
- expor `get_document` via MCP;
- salvar `CanonicalDocument` no store;
- limitar texto longo para agentes.

### P2: provar qualidade nacional

- criar benchmark offline;
- publicar cobertura por fonte;
- adicionar score de completude;
- evoluir deduplicacao avancada por fonte.

### P3: preparar escala e comunidade

- plugin registry para providers externos;
- `PostgresStore` opcional;
- guias pandas/DuckDB;
- templates de issue/PR por fonte.

## Comandos executados

```powershell
git diff --check
.\.venv\Scripts\python.exe -m pytest -q
.\.venv\Scripts\python.exe -m ruff check src tests examples
.\.venv\Scripts\python.exe -c "import nanojuris, nanojuris.mcp_tools, nanojuris.mcp_server; from nanojuris import NanoJurisClient; from nanojuris.store import SQLiteStore; print('imports ok:', NanoJurisClient.__name__, SQLiteStore.__name__)"
.\.venv\Scripts\python.exe examples\sdk_workflow.py
.\.venv\Scripts\python.exe -m nanojuris.cli fontes
.\.venv\Scripts\python.exe -m nanojuris.cli diagnostico --fonte bnp_pangea
.\.venv\Scripts\python.exe -m nanojuris.cli diagnostico --fonte tjsp_cjsg
.\.venv\Scripts\python.exe -m nanojuris.cli store --help
.\.venv\Scripts\python.exe -m nanojuris.cli buscar "0003938-14.2017.8.26.0323" --fonte tjsp_cjsg --limite 1 --formato json
```

## Decisao de engenharia

A proxima fase mais pragmatica e implementar cursor opaco remoto e `get_document`
em uma fonte publica estavel. A CLI de store, o checklist de provider, o
checklist de release, o exemplo SDK offline, as buscas salvas, o export de runs e
a paginacao por offset ja reduzem o risco para uma publicacao inicial
transparente.
