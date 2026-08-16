# MCP Roadmap

NanoJuris deve oferecer um MCP local opcional para agentes de IA consumirem
jurisprudencia brasileira de forma auditavel. O MCP nao deve interpretar merito
juridico, recomendar tese ou redigir argumentos. Ele deve expor dados, fontes,
documentos e traces.

Para instalacao e prompts de uso por agentes, veja
[ai-agent-usage.md](ai-agent-usage.md).

## Principios

- Toda resposta deve ser JSON serializavel.
- Toda resposta de fonte deve incluir `SourceTrace` quando houver consulta.
- Toda resposta extraida deve incluir `ExtractionTrace` quando houver parsing.
- Ferramentas de store recebem `store_id`, nunca caminho arbitrario. O servidor
  resolve o identificador dentro de `NANOJURIS_STORE_ROOT` e rejeita
  separadores, `..` e caminhos absolutos.
- Respostas longas devem ser paginadas.
- Tools nao devem contornar captcha, login, segredo de justica ou acesso
  restrito.
- O servidor MCP deve ser dependencia opcional via `nanojuris[mcp]`.

## Camadas implementadas

NanoJuris separa MCP em duas camadas:

- `nanojuris.mcp_tools`: funcoes puras, testaveis sem servidor MCP e sem rede
  obrigatoria;
- `nanojuris.mcp_server`: wrapper opcional baseado em FastMCP, disponivel com
  `nanojuris[mcp]`.

Rodar servidor MCP:

```bash
nanojuris-mcp
```

Ou em Python:

```python
from nanojuris.mcp_server import create_server

server = create_server()
server.run()
```

## Tools implementadas

### `list_sources`

Retorna `ProviderCapabilities` de todas as fontes registradas.

Uso esperado:

- descobrir fontes nacionais disponiveis;
- verificar formatos e campos extraidos;
- permitir que agentes escolham a fonte correta antes da busca.

### `list_courts`

Retorna o catalogo brasileiro de tribunais conhecido pela NanoJuris,
independentemente de o provider ja estar implementado.

Parametros principais:

- `branch`: `state`, `federal`, `labor`, `superior`, `constitutional`,
  `electoral`, `military` ou `national_council`;
- `state`: UF, como `SP`;
- `source_system`: familia tecnica, como `esaj_cjsg`, `eproc`, `pje` ou
  `datajud`;
- `implemented`: `true` para listar apenas tribunais com provider no core.

Uso esperado: agentes podem descobrir o universo oficial brasileiro antes de
escolher provider, filtro de busca ou estrategia de coleta.

### `source_diagnostics`

Retorna `ProviderCapabilities` de uma fonte especifica, com limitacoes e status
de acesso possiveis.

### `source_health`

Executa uma consulta live pequena e opt-in para verificar o estado operacional
de uma ou mais fontes. A ferramenta preserva um relatorio por provider e nao
transforma resultado vazio em erro.

Estados possiveis:

- `healthy`: a fonte respondeu com resultados;
- `empty`: a fonte respondeu validamente sem resultados;
- `blocked`: login, CAPTCHA, WAF ou outro controle de acesso;
- `rate_limited`: a fonte sinalizou limite de requisicoes;
- `source_unavailable`: indisponibilidade ou problema de rede;
- `source_changed`: resposta incompatível com o parser conhecido;
- `timeout`: o prazo global foi excedido;
- `error`: falha nao classificada.

Parametros:

- `sources`: lista opcional; vazia usa as fontes aptas para busca unificada;
- `text`: termo curto para o probe, por padrao `responsabilidade civil`;
- `timeout`: prazo global opcional em segundos.

O health check faz chamadas reais aos portais publicos. Deve ser usado com
baixa frequencia e respeitando os limites declarados por cada provider.

### `source_validation`

Executa uma consulta live pequena e valida o contrato normalizado observado
pelo NanoJuris. Alem da disponibilidade, confirma identidade da fonte,
paginacao basica, IDs, conteudo juridico minimo e rastreabilidade
(`source_trace`) dos resultados.

Estados adicionais:

- `valid`: a resposta passou pelo contrato live minimo;
- `empty`: a fonte respondeu validamente sem resultados;
- `contract_invalid`: a fonte respondeu, mas o resultado nao cumpre o contrato;
- `blocked`, `source_changed`, `rate_limited`, `source_unavailable` e `timeout`:
  falhas operacionais classificadas sem mascaramento.

A validacao faz chamadas reais somente quando solicitada. Ela nao roda na
importacao, nos testes offline ou no CI padrao e nunca tenta contornar CAPTCHA,
WAF ou outro controle de acesso.

### `source_contracts`

Retorna maturidade, lacunas, proximos passos e recomendacao MCP de uma ou todas
as fontes.

Para contexto documental antes da chamada, agentes podem ler o catalogo
[`docs/registry/providers.json`](registry/providers.json) e o dossie canonico
`docs/providers/<source-id>/README.md`. O catalogo separa providers
implementados de fontes candidatas; `source_contracts` continua sendo a fonte
viva para maturidade e lacunas declaradas pelo codigo.

Parametros:

- `source`: opcional; quando vazio, retorna todos os providers.

Uso esperado:

- agente decide se uma fonte esta madura antes de consulta-la;
- mantenedor identifica `needs_deepening`;
- documentacao e roadmap usam o mesmo inventario declarado pelo codigo.

### Catalogo e sincronizacao de dados abertos

O provider `stj_dados_abertos_jurisprudencia` expoe quatro operacoes separadas
para agentes que precisam trabalhar com cargas publicadas pelo STJ:

- `list_source_datasets`: descobre datasets no catalogo CKAN;
- `describe_source_dataset`: retorna recursos, formatos, tamanhos e checksums;
- `plan_source_sync`: seleciona recursos por formato sem baixar arquivos;
- `sync_source_resource`: baixa explicitamente um recurso JSON ou CSV dentro de
  `max_bytes`, deduplica por `id` e persiste uma `ResearchRun` no store local;
  com o mesmo fingerprint da fonte, retorna `skipped=true`; `force=true` refaz
  a carga.
- `store_sync_manifests`: lista os manifestos de sincronizacao e seus hashes,
  contagens, `run_id` e data, sem expor caminhos arbitrarios ao agente.

O `sync_source_resource` recebe `store_id`, nao caminho de arquivo. O servidor
resolve esse identificador sob `NANOJURIS_STORE_ROOT`. ZIP permanece bloqueado
nesta primeira etapa, e a operacao valida que o recurso pertence ao dominio
oficial do STJ. O agente deve apresentar dataset, recurso, hash, bytes,
registros persistidos e `run_id` ao usuario; essa ingestao ainda nao promove a
fonte para a busca remota unificada.

### `search_jurisprudence`

Executa busca paginada em uma fonte e retorna resultados normalizados.

Parametros minimos:

- `source`
- `text`
- `courts`
- `types`
- `number`
- `source_origin`: filtro especifico de fontes que expoem origem/base; no
  TJSP/eproc aceita `colegio_recursal`, `primeiro_grau` e `segundo_grau`;
- `page`
- `page_size`
- `canonical`

O tamanho de pagina e limitado de forma conservadora para uso por agentes.
Use `source="all"`, `source="*"` ou `source="unified"` para agregar as fontes
de jurisprudencia implementadas em uma unica resposta, preservando erros por
fonte no campo `errors`.

### `search_unified`

Executa busca paginada em multiplas fontes de jurisprudencia e retorna uma lista
unificada de resultados.

Parametros principais:

- `text`
- `sources`: opcional; quando vazio, usa todas as fontes de categorias
  jurisprudenciais implementadas no core, incluindo precedentes qualificados,
  fontes administrativas e eleitorais;
- `courts`
- `types`
- `number`
- `source_origin`
- `page`
- `page_size`
- `canonical`

A resposta inclui `sources`, `total_returned`, `results` e `errors`. Isso permite
que agentes consultem varias fontes em uma chamada sem perder diagnosticos de
captcha, indisponibilidade ou mudanca de contrato de parser em uma fonte isolada.
Para demonstracoes e uso de producao, prefira grupos explicitos de fontes
tecnicamente relacionadas; deixar `sources` vazio consulta todas as fontes
aptas e pode ser mais lento ou produzir mais falhas parciais.

Para uso por agentes, a resposta tambem separa roteamento semantico:

- `searched_sources`: fontes efetivamente consultadas;
- `skipped_sources`: fontes nao chamadas porque nao se aplicam ao tipo de
  pergunta, com `reason` e `message` explicitos;
- `routing_summary`: explicacao curta, pronta para agentes, sobre fontes
  consultadas, puladas ou com falha;
- `errors`: fontes chamadas que falharam por indisponibilidade, captcha,
  controle de acesso ou mudanca de contrato.

Essa separacao evita falso diagnostico. Fontes de consulta processual,
DataJud/CNJ, DJEN e comunicacoes judiciais pertencem ao NanoJud. No NanoJuris,
o MCP deve tratar esses pedidos como fora do escopo da busca textual de
jurisprudencia.

Quando a consulta informa `number`, `party_name`, `oab` ou outro identificador,
o roteador compara o filtro com `supported_filters` da fonte. Uma fonte que
declara apenas texto livre e pulada com `reason=identifier_filter_not_supported`;
isso evita apresentar resultados textualmente parecidos como correspondencia
exata. Providers legados que ainda nao declaram `supported_filters` permanecem
consultaveis, mas o agente deve tratar a resposta como evidencia textual e
verificar o campo canonico retornado.

### `export_results`

Exporta resultados em formato textual:

- `json`
- `jsonl`
- `canonical-jsonl`
- `csv`
- `markdown`

### `get_document`

Recupera um inteiro teor publico como `CanonicalDocument` quando o provider
suporta a fonte e o documento esta acessivel sem bypass.

Parametros:

- `document_id`
- `source`

Use para agentes que precisam anexar texto bruto auditavel, hash, tamanho,
trace de fonte e status de acesso antes de qualquer etapa posterior.

No `tjsp_cjsg`, a tool retorna o texto limpo extraido do HTML publico quando a
rota `getArquivo.do` estiver acessivel. O HTML original nao e despejado no
campo `text`; seus sinais de auditoria ficam em `raw_metadata`, como hash,
tamanho, tipo de origem e warnings.

### `get_decisions`

Recupera textos publicos vinculados ao identificador de uma fonte quando o
provider expõe um `DecisionBundle`.

Parametros:

- `precedent_id`
- `source`

Use quando a fonte retorna um conjunto de textos/decisoes vinculadas antes de
haver um documento canonico unico.

### `store_stats`

Retorna contagens agregadas de um store SQLite local criado pela NanoJuris.

Parametro minimo:

- `store_id` (identificador, por exemplo `default`)

### `store_query`

Consulta registros canonicos salvos em um store SQLite local.

Parametros principais:

- `store_id`
- `kind`
- `source`
- `court`
- `case_number`
- `subject`
- `rapporteur`
- `decision_type`
- `precedent_type`
- `publication_date_from`
- `publication_date_to`

- `limit`

O limite e restringido de forma conservadora para uso por agentes.

### `store_get`

Recupera um registro canonico salvo por tipo e id.

Parametros minimos:

- `store_id`
- `kind`
- `record_id`

### `store_runs`

Lista buscas salvas em um store SQLite local.

Parametros principais:

- `store_id`
- `limit`

### `store_run`

Recupera metadados de uma busca salva.

Parametros minimos:

- `store_id`
- `run_id`

### `store_run_records`

Recupera registros canonicos vinculados a uma busca salva.

Parametros principais:

- `store_id`
- `run_id`
- `limit`
- `offset`

A resposta inclui `total`, `has_more` e `next_offset` para agentes percorrerem
runs grandes com controle de estado.

### `store_export_run`

Exporta registros vinculados a uma busca salva em formato textual.

Parametros principais:

- `store_id`
- `run_id`
- `output_format`: `json`, `jsonl`, `csv` ou `markdown`
- `limit`
- `offset`

Use `json` para agentes que precisam do envelope com metadados do run, `jsonl`
para processamento incremental, `csv` para analise tabular e `markdown` para
revisao humana.

A resposta tambem inclui `total`, `has_more` e `next_offset`.

## Busca unificada

`search_unified` retorna uma pagina federada: as fontes sao consultadas em
paralelo com limite de concorrencia e deadline global, os resultados sao
deduplicados e ordenados antes de aplicar `page`/`page_size`. O retorno inclui
`total_available`, `deduplicated_total`, `source_totals`,
`source_completeness`, `sources_complete`, `sources_partial`,
`sources_unknown`, `collection_complete`, `errors` e a trace de roteamento.
`total_available` representa a colecao agregada obtida nesta execucao; nao e uma
promessa de exaustividade quando `collection_complete` for falso. Isso e
diferente de pedir a mesma pagina individual em cada tribunal.

Para atender paginas federadas alem da primeira janela, o cliente busca cada
fonte em paginas incrementais, usando uma janela constante de ate 100 registros
por requisicao. A resposta informa `pages_fetched` dentro de
`source_completeness`, permitindo distinguir uma fonte consultada apenas uma
vez de uma fonte percorrida em varias paginas. O campo nao transforma o total
reportado pelo tribunal em um total nacional: ele descreve somente a coleta
observada nesta execucao.

## Tools planejadas

### `get_decision`

Recupera decisao ou precedente por identificador publico/canonico quando a fonte
suportar.

### Normalizacao de relevancia

Adicionar filtros opcionais de pos-processamento por ramo, classe, assunto e
tipo de decisao para reduzir falsos positivos em fontes de texto livre amplo.

## Ordem de implementacao MCP

1. Reusar `ProviderCapabilities` em `list_sources` e `source_diagnostics`.
  Implementado.
2. Reusar `NanoJurisClient.search` em `search_jurisprudence`. Implementado.
3. Reusar canonical mappers para respostas de dados objetivos. Implementado.
4. Adicionar limites de pagina, tamanho e timeout por tool. Implementado para
  pagina minima e tamanho de pagina.
5. Cobrir tools com testes sem rede. Implementado.
6. Expor store local para agentes. Implementado com `store_stats`,
  `store_query`, `store_get`, `store_runs`, `store_run`,
  `store_run_records` e `store_export_run`.
7. Implementar `get_decisions` e `get_document`. Implementado.
8. Adicionar exemplos de configuracao em clientes MCP.
