# Use Case Validation Matrix

Este documento detalha casos de uso praticos para testar NanoJuris como
biblioteca open source premium de extracao de jurisprudencia brasileira. A matriz
serve para descobrir o que ja esta bom, o que precisa melhorar e o que ainda nao
foi implementado.

A rodada de validacao executada em 2026-08-02 esta registrada em
[validation-report-2026-08-02.md](validation-report-2026-08-02.md).

Escopo: dados publicos, extracao objetiva, rastreabilidade, persistencia,
exportacao e MCP. Nao inclui interpretacao juridica, recomendacao de tese,
redacao de peca ou conclusao sobre merito.

## Legenda de status

- Implementado: existe no codigo e tem validacao offline ou automatizada.
- Parcial: existe parte do fluxo, mas ainda falta cobertura, UX ou fonte real.
- Planejado: nao existe ainda no core.
- Bloqueado por fonte: depende de acesso publico estavel, sem captcha, login ou
  restricao.

## Personas principais

### Advogado contencioso

Objetivo: localizar decisoes publicas relevantes, exportar dados objetivos e
revisar manualmente a fonte.

Sucesso pratico:

- busca retorna resultados com tribunal, numero, resumo e URL quando disponivel;
- exportacao gera CSV/Markdown para revisao;
- cada item tem fonte rastreavel;
- limitacoes de acesso aparecem claramente.

### Coordenador juridico ou legal operations

Objetivo: montar base local de decisoes por tema, tribunal ou carteira, sem
depender de planilhas manuais soltas.

Sucesso pratico:

- buscas podem ser salvas em SQLite;
- registros podem ser filtrados por tribunal, tipo, assunto, relator e numero;
- exportacoes podem ser repetidas;
- falhas por fonte sao diagnosticaveis.

### Pesquisador de jurimetria

Objetivo: construir dataset reproduzivel para contagem, filtros e analises
quantitativas.

Sucesso pratico:

- dados saem em CSV/JSONL canonico;
- store preserva schema completo;
- duplicidade pode ser identificada;
- completude por fonte pode ser medida.

### Desenvolvedor de legaltech

Objetivo: incorporar NanoJuris como biblioteca, backend de coleta ou componente
em pipeline de dados.

Sucesso pratico:

- API Python tem contratos estaveis;
- provider novo pode ser implementado sem alterar o core;
- erros sao tipados;
- dependencia pesada e opcional.

### Agente de IA via MCP

Objetivo: consultar fontes, buscar dados e exportar resultados por tools, sem
interpretar juridicamente o conteudo.

Sucesso pratico:

- agente lista fontes e capacidades;
- agente consulta dados com limite de pagina;
- resposta e JSON serializavel;
- traces e status acompanham os dados;
- tools recusam ou informam fontes bloqueadas.

### Mantenedor open source

Objetivo: receber contribuicoes de novas fontes com qualidade, testes e docs.

Sucesso pratico:

- novo provider tem ficha de fonte;
- fixtures offline acompanham a implementacao;
- live tests sao opt-in;
- docs e roadmap sao atualizados;
- riscos de acesso sao revisados.

## Mapa macro de capacidade

| Capacidade | Status | Onde testar | Evidencia esperada | Proxima melhoria |
| --- | --- | --- | --- | --- |
| Listar fontes e capacidades | Implementado | `client.list_sources`, `nanojuris fontes`, MCP `list_sources` | fontes com `ProviderCapabilities` | adicionar score de estabilidade por fonte |
| Listar tribunais brasileiros | Implementado | `list_courts`, `nanojuris tribunais`, MCP `list_courts` | catalogo por ramo, UF, familia tecnica e status de provider | adicionar URLs oficiais por tribunal |
| Diagnosticar fonte | Implementado | `nanojuris diagnostico`, MCP `source_diagnostics` | limites e status declarados | incluir ultimo teste live conhecido |
| Buscar BNP/Pangea | Parcial | provider e testes live opt-in | resultados ou erro HTTP claro | robustecer tratamento de HTTP 400 |
| Buscar TJSP/CJSG | Parcial | provider e fixture HTML | resultados offline e captcha detectado live | separar fetcher/parser/mapper |
| Buscar STJ | Parcial | `stj_scon` e fixture HTML | parser offline e acesso controlado live diagnosticado | ampliar rotas live estaveis sem bypass |
| Canonicalizar resultados | Implementado | `client.search_canonical` | `CanonicalDecision`/`CanonicalPrecedent` | ampliar campos por fonte |
| Salvar em SQLite | Implementado | `client.search_and_store`, `SQLiteStore` | registros persistidos e deduplicados por chave canonica | busca salva por id |
| Consultar store | Implementado | `SQLiteStore.query_records`, `nanojuris store query` | filtros estruturados, buscas salvas por `run_id` e paginacao por `offset` | cursor opaco para stores remotos |
| Exportar JSONL/CSV/Markdown | Implementado | exporters e CLI | arquivos/txt validos | Parquet/DuckDB opcional |
| Exportar CSV por tipo | Implementado | exporters typed CSV | colunas de decisao/precedente/documento | documentar dicionario de campos |
| MCP tools basicas | Implementado | `tests/test_mcp_tools.py` | busca, diagnostico e export | exemplos de clientes MCP |
| MCP tools de store | Implementado | `tests/test_mcp_tools.py` | stats, query, get, runs, records/export com `total`, `has_more` e `next_offset` | cursor opaco para stores remotos |
| Inteiro teor publico | Implementado parcial | `client.get_document`, `nanojuris documento`, MCP `get_document` | `CanonicalDocument` no TJSP/CJSG quando a URL publica responde sem controle de acesso | ampliar provider por fonte |
| Benchmark de cobertura | Planejado | docs/CI futuro | relatorio por fonte | medir completude por campo |
| Plugin externo de provider | Planejado | contrato futuro | provider fora do core | entrypoints Python |
| PostgresStore | Planejado | extra futuro | store compativel | migracoes e indices |

## UC-01: advogado busca jurisprudencia e exporta para revisao

Pergunta pratica: consigo sair de uma consulta textual para um arquivo revisavel
com fontes e campos objetivos?

Persona: advogado contencioso.

Fluxo:

1. listar fontes disponiveis;
2. escolher fonte com busca textual;
3. executar busca por termo;
4. canonicalizar resultados;
5. exportar CSV ou Markdown;
6. abrir URL publica quando disponivel;
7. registrar limitacoes de acesso.

Ferramentas envolvidas:

- `NanoJurisClient.list_sources()`;
- `NanoJurisClient.search()`;
- `NanoJurisClient.search_canonical()`;
- `to_csv`, `search_page_to_markdown`;
- CLI `nanojuris buscar`;
- MCP `search_jurisprudence` e `export_results`.

Status atual: Implementado para fluxo offline/controlado e parcial para fontes
live, porque fontes publicas podem rejeitar, bloquear ou exigir validacao.

Como testar agora:

- rodar testes de exporters e MCP;
- usar fixture TJSP/CJSG;
- executar CLI com provider disponivel;
- em live, habilitar env vars apenas quando aceitavel.

Evidencias de sucesso:

- CSV contem tribunal, tipo, numero, classe/assunto quando extraidos;
- Markdown nao omite fonte;
- `SourceTrace` aparece em resultado normalizado;
- erro de acesso nao vira traceback confuso.

Lacunas:

- `CanonicalDocument` para inteiro teor publico;
- agrupamento de resultados em projeto de pesquisa;
- cursor opaco para stores remotos;
- score de completude por resultado.

Backlog sugerido:

- `nanojuris documento --id ... --fonte ...`;
- `ResearchRun` para agrupar buscas;
- indicador `completeness_score` por registro;
- docs com exemplo advogado ponta a ponta.

## UC-02: advogado usa agente de IA via MCP sem interpretacao juridica

Pergunta pratica: um agente consegue usar NanoJuris como ferramenta de dados,
sem produzir conclusao juridica pelo core?

Persona: advogado com assistente de IA.

Fluxo:

1. agente chama `list_sources`;
2. agente chama `source_diagnostics` para conferir limites;
3. agente chama `search_jurisprudence` com `canonical=true`;
4. agente chama `export_results` em `canonical-jsonl` ou Markdown;
5. agente consulta store local com `store_stats`, `store_query` ou `store_get`;
6. humano revisa dados e fontes.

Ferramentas envolvidas:

- `nanojuris.mcp_tools`;
- `nanojuris.mcp_server`;
- entrypoint `nanojuris-mcp`;
- exporters canonicos.
- `SQLiteStore` para tools store-backed.

Status atual: Implementado como MCP minimo, com pure tools testadas offline e
wrapper opcional FastMCP.

Como testar agora:

- `python -m pytest tests/test_mcp_tools.py -q`;
- importar `nanojuris.mcp_tools` sem extra MCP;
- instalar `nanojuris[mcp]` e iniciar `nanojuris-mcp` em ambiente de teste.

Evidencias de sucesso:

- tools retornam dicionarios JSON serializaveis;
- `page_size` e limitado;
- exportacao aceita formatos documentados;
- import do core nao exige `mcp`.
- `store_stats`, `store_query` e `store_get` consultam base SQLite local.

Lacunas:

- exemplos de configuracao para clientes MCP reais;
- ultimo status live conhecido por fonte;
- telemetry/logging opcional de chamadas.

Backlog sugerido:

- exemplo de cliente MCP real;
- exportacao de busca salva por id;
- exemplo de configuracao em cliente desktop;
- testes com servidor MCP quando extra instalado.

## UC-03: legal operations monta base local de uma carteira

Pergunta pratica: consigo salvar resultados em base local e consultar depois?

Persona: coordenador juridico ou legal operations.

Fluxo:

1. executar busca por termo, tribunal ou numero;
2. salvar resultados canonicos em SQLite;
3. consultar por tipo, fonte, tribunal, assunto ou numero;
4. exportar subconjunto;
5. repetir busca em outro dia preservando rastreabilidade.

Ferramentas envolvidas:

- `client.search_and_store()`;
- `SQLiteStore.save_many()`;
- `SQLiteStore.query_records()`;
- `SQLiteStore.stats()`;
- CLI `buscar --store`.

Status atual: Implementado no core e na CLI para estatisticas, consulta e busca
por id.

Como testar agora:

- teste `tests/test_store.py`;
- teste `tests/test_client_exporters.py`;
- comando `nanojuris buscar ... --store nanojuris.db`;
- comandos `nanojuris store stats`, `nanojuris store query` e
  `nanojuris store get`.

Evidencias de sucesso:

- banco SQLite e criado;
- registros tem JSON canonico e traces;
- filtros retornam subconjuntos coerentes;
- registros equivalentes sao deduplicados por `canonical_key`;
- stats contam por tipo e fonte.

Lacunas:

- deduplicacao avancada por benchmark de fonte;
- migrations versionadas;
- exportar busca salva por id.

Backlog sugerido:

- streaming de arquivos para datasets muito grandes.

## UC-04: pesquisador constroi dataset de jurimetria

Pergunta pratica: consigo gerar dataset tabular reproduzivel sem perder origem?

Persona: pesquisador de jurimetria.

Fluxo:

1. consultar fonte com parametros controlados;
2. canonicalizar resultados;
3. exportar CSV por tipo de registro;
4. persistir JSON canonico;
5. medir completude e duplicidade;
6. carregar em pandas, DuckDB ou BI.

Ferramentas envolvidas:

- typed CSV exporters;
- canonical JSONL;
- `SQLiteStore`;
- `ProviderCapabilities`;
- futuros benchmarks.

Status atual: Parcial. Export e store existem; metricas de completude,
deduplicacao e guias analiticos ainda faltam.

Como testar agora:

- validar CSVs tipados com fixture fake;
- carregar JSONL canonico em script local;
- consultar store por tipo e fonte.

Evidencias de sucesso:

- linhas CSV batem com total de resultados;
- campos ausentes permanecem vazios, nao inventados;
- JSONL preserva modelo completo;
- query por tipo retorna decisoes e precedentes separadamente.

Lacunas:

- benchmark por fonte;
- completude por campo;
- deduplicacao;
- exemplos pandas/DuckDB.

Backlog sugerido:

- `nanojuris benchmark fixtures`;
- `StoreStats` expandido por campo/status;
- guia `docs/analytics.md`;
- export Parquet como extra opcional.

## UC-05: desenvolvedor cria provider novo

Pergunta pratica: um contribuidor consegue adicionar fonte nova sem quebrar o
core?

Persona: desenvolvedor de legaltech ou contribuidor open source.

Fluxo:

1. preencher ficha de fonte;
2. criar provider isolado;
3. adicionar fixtures offline;
4. implementar capabilities;
5. mapear resultados para modelos normalizados/canonicos;
6. criar testes unitarios e live opt-in;
7. atualizar docs.

Ferramentas envolvidas:

- `JurisprudenceProvider`;
- `ProviderCapabilities`;
- `SourceTrace`;
- `ExtractionTrace`;
- pytest fixtures;
- docs de fonte.

Status atual: Parcial. Existem providers e base; falta guia formal de provider
externo/plugin.

Como testar agora:

- estudar `bnp_pangea` e `tjsp_cjsg`;
- criar provider fake em teste;
- rodar suite offline;
- validar lint.

Evidencias de sucesso:

- novo provider nao altera cliente publico;
- `list_sources` inclui capabilities;
- erros de acesso sao tipados;
- fixtures cobrem pagina/resposta representativa.

Lacunas:

- template de provider;
- checklist de PR para fonte;
- entrypoints para plugin externo;
- documentacao de contrato por metodo.

Backlog sugerido:

- `docs/provider-development.md`;
- `examples/custom_provider.py`;
- interface de plugin via entrypoints;
- CI check para fixtures publicas representativas.

## UC-06: usuario diagnostica fonte instavel ou bloqueada

Pergunta pratica: quando uma fonte falha, o usuario entende se e bug, limite de
acesso ou mudanca externa?

Persona: advogado, dev ou mantenedor.

Fluxo:

1. usuario executa busca;
2. provider detecta status HTTP, captcha, validacao ou erro de contrato;
3. erro apresenta fonte, status e proximo passo;
4. diagnostico mostra capacidades e limitacoes;
5. issue pode ser aberta com dados reproduziveis.

Ferramentas envolvidas:

- `AccessStatus`;
- erros tipados;
- CLI `diagnostico`;
- `source_diagnostics` MCP;
- docs de responsible use.

Status atual: Parcial. Status e diagnostico existem; observabilidade e playbooks
ainda podem melhorar.

Como testar agora:

- rodar testes de provider offline;
- simular HTML de captcha;
- testar CLI diagnostico;
- consultar docs de capabilities.

Evidencias de sucesso:

- captcha/controle de acesso e reconhecido;
- usuario recebe mensagem acionavel;
- live tests continuam opt-in;
- docs declaram limitacoes.

Lacunas:

- playbook por fonte;
- ultimo status live conhecido;
- logging estruturado opcional;
- taxonomia completa de erros.

Backlog sugerido:

- `docs/source-playbooks.md`;
- campo `last_verified_at` em capabilities ou benchmark;
- logger estruturado opcional;
- comando `nanojuris diagnostico --json`.

## UC-07: mantenedor avalia release

Pergunta pratica: antes de publicar, conseguimos provar que a release esta
coerente?

Persona: maintainer/release engineer.

Fluxo:

1. rodar testes offline;
2. rodar lint/typecheck;
3. validar imports sem extras opcionais;
4. validar docs atualizadas;
5. conferir changelog e roadmap;
6. rodar live tests opt-in quando apropriado.

Ferramentas envolvidas:

- pytest;
- ruff;
- mypy/Pylance;
- `git diff --check`;
- smoke import;
- CI.

Status atual: Implementado com ressalva ambiental local. Testes, lint, mypy,
build, smoke de extras e checklist de release estao documentados no repositorio;
o CI Ubuntu e o gate definitivo para build isolado.

Como testar agora:

- `python -m pytest -q`;
- `python -m ruff check src tests`;
- `python -c "import nanojuris"`;
- `git diff --check`.

Evidencias de sucesso:

- suite offline passa;
- live tests pulam por padrao;
- imports opcionais nao quebram core;
- docs indicam status real.

Lacunas:

- validar os jobs no GitHub apos o proximo push;
- configurar branch protection e o environment `pypi`;
- publicar artefatos de cobertura se isso for adotado pelo mantenedor.

Backlog sugerido:

- exigir os checks obrigatorios na branch `main`;
- configurar Trusted Publishing no PyPI;
- adicionar um relatorio de cobertura publicado, se houver necessidade de
  acompanhamento historico.

## UC-08: sistema externo consome NanoJuris como SDK

Pergunta pratica: um produto consegue usar NanoJuris como dependencia sem
assumir detalhes internos?

Persona: desenvolvedor backend.

Fluxo:

1. instalar pacote;
2. instanciar cliente;
3. listar fontes;
4. buscar e salvar;
5. consultar store;
6. exportar dados;
7. tratar erros tipados.

Ferramentas envolvidas:

- `NanoJurisClient`;
- `CanonicalStore`;
- `SQLiteStore`;
- exporters;
- models dataclass;
- errors.

Status atual: Parcial/Implementado. SDK basico existe; padrao de plugins,
async e Postgres ainda nao.

Como testar agora:

- criar script pequeno com provider fake;
- usar store temporario;
- validar exportacoes;
- capturar excecoes de fonte.

Evidencias de sucesso:

- codigo de integracao e curto;
- tipos sao previsiveis;
- dependencias opcionais nao entram no core;
- store pode ser trocado por contrato.

Lacunas:

- async client;
- PostgresStore;
- plugin registry;
- exemplos de app real.

Backlog sugerido:

- `examples/sdk_workflow.py`;
- `PostgresStore` como extra;
- plugin entrypoints;
- docs de tratamento de erro.

## UC-09: extracao de inteiro teor publico

Pergunta pratica: conseguimos baixar e normalizar documento publico completo
quando a fonte permite?

Persona: advogado, pesquisador e agente MCP.

Fluxo desejado:

1. resultado de busca aponta URL ou id de documento;
2. `get_document` verifica acesso;
3. fetcher baixa HTML/PDF publico;
4. parser extrai texto e metadados;
5. modelo `CanonicalDocument` recebe conteudo e traces;
6. store salva documento associado ao resultado.

Ferramentas envolvidas:

- futuro `client.get_document()`;
- futuro MCP `get_document`;
- `HttpFetcher`;
- `ParsedContent`;
- `CanonicalDocument`;
- `SQLiteStore`.

Status atual: Planejado. Modelos e primitivas existem; fluxo completo por fonte
ainda nao.

Como testar quando implementado:

- fixture HTML/PDF publico;
- hash do conteudo bruto;
- status de acesso publico/parcial/bloqueado;
- parser versionado;
- armazenamento e exportacao.

Evidencias de sucesso:

- texto extraido corresponde a fixture;
- documento tem URL, hash e status;
- captcha ou login retorna acesso bloqueado;
- agente MCP nao recebe payload gigante sem paginacao.

Lacunas:

- metodo publico;
- parser por fonte;
- persistencia associada;
- limites de tamanho.

Backlog sugerido:

- implementar primeiro em fonte com HTML publico estavel;
- adicionar `document_text_page` para MCP;
- salvar documento separado de decisao;
- medir qualidade de extracao textual.

## UC-10: benchmark publico de cobertura

Pergunta pratica: conseguimos dizer com honestidade quao boa esta cada fonte?

Persona: maintainer, pesquisador e usuario institucional.

Fluxo desejado:

1. selecionar fixtures gold por fonte;
2. definir campos esperados por tipo;
3. rodar extracao offline;
4. medir completude, validade e erros;
5. publicar tabela por release;
6. abrir backlog para lacunas.

Ferramentas envolvidas:

- fixtures publicas representativas;
- parsers versionados;
- `ExtractionStatus`;
- `ProviderCapabilities`;
- futuro comando de benchmark.

Status atual: Planejado.

Como testar quando implementado:

- comando local sem rede;
- relatorio Markdown/JSON;
- CI falha em regressao relevante;
- docs atualizadas por release.

Evidencias de sucesso:

- cada fonte tem percentual de campos preenchidos;
- mudanca de parser altera versao;
- benchmark distingue ausencia real de falha;
- usuario sabe quais fontes sao maduras.

Lacunas:

- fixtures gold suficientes;
- calculo de completude;
- relatorio publico;
- politica de regressao.

Backlog sugerido:

- `nanojuris benchmark`;
- `docs/coverage.md`;
- score por fonte em capabilities;
- fixture review checklist.

## Plano de aplicacao pratica

### Sprint A: consolidar o que ja esta bom

Objetivo: provar os fluxos implementados.

Casos foco:

- UC-01 busca e exportacao;
- UC-02 MCP minimo;
- UC-03 store local;
- UC-07 release checks.

Checks sugeridos:

- `pytest -q`;
- `ruff check src tests`;
- `git diff --check`;
- smoke import de `nanojuris`, `nanojuris.mcp_tools` e `nanojuris.mcp_server`;
- rodar `nanojuris fontes` e `nanojuris diagnostico`.

Criterio de pronto:

- docs refletem status real;
- testes offline passam;
- MCP minimo funciona sem rede;
- store salva e consulta registros canonicos.

### Sprint B: melhorar pontos parciais

Objetivo: transformar fluxos parciais em experiencia completa.

Casos foco:

- UC-04 jurimetria;
- UC-05 provider novo;
- UC-06 diagnostico de fonte;
- UC-08 SDK externo.

Checks sugeridos:

- criar guia de provider;
- ampliar CLI de store para exportar busca salva por id;
- expandir stats/completude;
- melhorar mensagens de erro por fonte.

Criterio de pronto:

- contribuidor consegue criar provider por checklist;
- pesquisador consegue carregar dataset em pandas/DuckDB;
- usuario entende falha de fonte sem ler codigo;
- SDK tem exemplo ponta a ponta.

### Sprint C: implementar o que ainda falta

Objetivo: abrir novas capacidades de alto valor.

Casos foco:

- UC-09 inteiro teor publico;
- UC-10 benchmark de cobertura;
- PostgresStore;
- plugin externo de providers.

Checks sugeridos:

- implementar `get_document` em uma fonte estavel;
- adicionar benchmark offline;
- desenhar migracao para Postgres;
- criar entrypoints para providers externos.

Criterio de pronto:

- documentos publicos viram `CanonicalDocument`;
- benchmark mostra maturidade por fonte;
- storage escala sem pesar o core;
- comunidade consegue contribuir fontes fora do pacote principal.

## Checklist de review por caso de uso

Para cada caso antes de marcar como implementado:

- existe teste offline?
- existe fixture publica representativa quando depende de fonte?
- existe erro claro para acesso bloqueado?
- existe trace de fonte?
- existe trace de extracao quando ha parsing?
- existe documentacao de uso?
- existe exemplo Python, CLI ou MCP?
- o fluxo evita interpretacao juridica?
- a feature funciona sem dependencia opcional desnecessaria?
- o status no roadmap foi atualizado?
