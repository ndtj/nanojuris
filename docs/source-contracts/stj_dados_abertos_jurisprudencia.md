# `stj_dados_abertos_jurisprudencia`

## Identidade

- Orgao: Superior Tribunal de Justica.
- Categoria: `court_jurisprudence_dataset`.
- Familia tecnica: `ckan_jurisprudencia_dataset`.
- Status: `implemented` para catalogo CKAN; nao e uma API de busca interativa.
- Fonte oficial: Portal de Dados Abertos do STJ.
- Portal: `https://dadosabertos.web.stj.jus.br/`.
- Licenca observada: Creative Commons Atribuicao (`cc-by`).

O portal oferece espelhos estruturados de acordaos selecionados pelo STJ e um
dataset separado com integras de decisoes terminativas e acordaos do Diario da
Justica. O corpus de espelhos nao deve ser descrito como todos os julgados do
STJ: a propria fonte informa que recebe tratamento tecnico-documentario quando
a ementa apresenta novidade de tese ou representatividade.

## Contrato de catalogo

O portal usa CKAN. A raiz observada foi:

```text
https://dadosabertos.web.stj.jus.br/api/3/action
```

Rotas:

```text
GET /package_search?q=jurisprudencia&rows=20
GET /package_show?id=<dataset-id-ou-name>
```

`package_search` retornou `success=true` e 11 datasets de jurisprudencia na
validacao live. Os datasets observados foram:

- `espelhos-de-acordaos-corte-especial`;
- `espelhos-de-acordaos-primeira-secao`;
- `espelhos-de-acordaos-segunda-secao`;
- `espelhos-de-acordaos-terceira-secao`;
- `espelhos-de-acordaos-primeira-turma`;
- `espelhos-de-acordaos-segunda-turma`;
- `espelhos-de-acordaos-terceira-turma`;
- `espelhos-de-acordaos-quarta-turma`;
- `espelhos-de-acordaos-quinta-turma`;
- `espelhos-de-acordaos-sexta-turma`;
- `integras-de-decisoes-terminativas-e-acordaos-do-diario-da-justica`.

O adapter deve sempre descobrir os recursos via `package_show`. Nao deve
montar URLs de arquivos por convencao, pois o CKAN publica identificadores,
nomes, tamanhos, datas e URLs de download como parte do contrato.

## Operacoes Runtime

O adapter oferece somente metadados e planejamento, sem baixar recursos:

```python
from nanojuris import NanoJurisClient

client = NanoJurisClient()

datasets = client.list_source_datasets(
    source="stj_dados_abertos_jurisprudencia",
    query="jurisprudencia",
    rows=20,
)
description = client.describe_source_dataset(
    source="stj_dados_abertos_jurisprudencia",
    dataset_id="espelhos-de-acordaos-primeira-turma",
)
plan = client.plan_source_sync(
    source="stj_dados_abertos_jurisprudencia",
    dataset_id="espelhos-de-acordaos-primeira-turma",
    format="JSON",
)
```

As mesmas operacoes estao disponiveis no MCP como
`list_source_datasets`, `describe_source_dataset` e `plan_source_sync`. O
plano contem URLs, formatos, tamanhos, checksums e limites, mas declara
`download=false`; a ingestao deve ser uma etapa local explicita.

## Recursos observados

Nos nove datasets de espelhos consultados havia 52 recursos; a Primeira e a
Quinta Turmas tinham 53. Os formatos publicados foram CSV, JSON e ZIP. O
dataset de integras possuia 2.560 recursos na mesma consulta de catalogo.
Essas contagens sao observacoes de uma versao do catalogo e devem ser lidas
novamente antes de cada sincronizacao.

No dataset `espelhos-de-acordaos-primeira-turma` foram observados:

- um ZIP historico `20220508.zip`;
- um CSV pequeno `dicionario-espelhodoacordao.csv`;
- arquivos JSON mensais, incluindo `20220531.json` e `20260630.json`.

O arquivo JSON de junho de 2026 respondeu HTTP 200 e iniciou com registros
estruturados. O dicionario respondeu HTTP 200 e tem delimitador `;`.

## Dados do espelho de acordao

O dicionario oficial lista estes campos:

```text
id
numeroProcesso
numeroRegistro
siglaClasse
descricaoClasse
nomeOrgaoJulgador
ministroRelator
ementa
tipoDeDecisao
dataDecisao
decisao
jurisprudenciaCitada
notas
informacoesComplementares
termosAuxiliares
teseJuridica
tema
referenciasLegislativas
acordaosSimilares
dataPublicacao
```

O campo `numeroDocumento` tambem apareceu no JSON live, embora nao estivesse
no dicionario consultado. Campos adicionais devem ser preservados em `raw` e
nao descartados por um parser baseado apenas na lista historica.

Mapeamento inicial para o modelo canonico:

- `id`: identificador estavel do registro no dataset;
- `numeroProcesso`: numero do processo no STJ;
- `numeroRegistro`: registro do processo autuado no STJ;
- `siglaClasse` e `descricaoClasse`: classe processual;
- `nomeOrgaoJulgador`: orgao julgador;
- `ministroRelator`: relator;
- `ementa`: resumo decisorio;
- `tipoDeDecisao`: tipo documental;
- `dataDecisao` e `dataPublicacao`: datas;
- `decisao`: resultado, votacao e eventualmente tese firmada;
- `teseJuridica` e `tema`: precedentes qualificados quando presentes;
- `jurisprudenciaCitada` e `referenciasLegislativas`: referencias;
- `informacoesComplementares`, `notas` e `termosAuxiliares`: enriquecimento;
- `raw`: registro inteiro, sem perda de campos.

Campos ausentes devem permanecer nulos. O adapter nao deve fabricar numero de
acordao, relator, tese ou inteiro teor quando a linha nao trouxer o campo.

## Sincronizacao e limites

Este canal e adequado para ingestao local e pesquisa posterior. Nao foi
observada uma rota oficial de busca textual online sobre esses arquivos. O
desenho recomendado e:

1. consultar `package_search` e `package_show`;
2. escolher recursos por formato, data e tamanho;
3. baixar em streaming, com limite configuravel;
4. guardar URL, nome, tamanho, data, checksum e dataset no manifesto local;
5. deduplicar por `id`, mantendo a ultima versao do registro;
6. indexar os campos textuais localmente para a busca unificada.

O ZIP historico pode ser grande. O provider nao deve baixa-lo por padrao em
uma consulta MCP. O MCP deve oferecer catalogo e plano de sincronizacao; a
busca de texto deve usar um indice local explicitamente informado ao usuario.

## Estados de resposta

- catalogo CKAN HTTP 200 com `success=true`: fonte disponivel;
- dataset sem recursos: erro de contrato ou dataset incompleto, nao busca vazia;
- recurso HTTP 200: arquivo disponivel para ingestao;
- timeout, 429, 5xx ou falha de download: `source_unavailable` com trace;
- JSON invalido, CSV com schema inesperado ou ZIP corrompido:
  `parser_contract_changed`;
- ausencia de um campo opcional: registro valido, campo nulo e `raw` preservado.

Nao interpretar a quantidade de recursos como quantidade de decisoes. Cada
JSON/CSV pode ser uma carga mensal, historica ou dicionario.

## Uso via MCP

Antes de implementar o provider, o MCP pode expor:

- `list_source_datasets(source="stj_dados_abertos_jurisprudencia")`;
- `describe_source_dataset(dataset_id=...)`;
- `plan_source_sync(dataset_id=..., format="JSON")`.

Uma pergunta por tese ou ementa so deve consultar esse candidato quando houver
indice local sincronizado. A resposta deve informar a data do manifesto, o
dataset, o recurso e a natureza de espelho ou integra. O agente nao deve
apresentar essa base como cobertura integral da jurisprudencia do STJ.

## Fixtures e promocao

- [x] fixture de `package_search` reduzida a metadados essenciais;
- [x] fixture de `package_show` com dois recursos sanitizados;
- [ ] parser de CSV com `;`, acentos e campos longos;
- [ ] parser de JSON que preserve campos desconhecidos;
- [ ] teste de deduplicacao por `id` entre carga historica e delta;
- [ ] teste de streaming e limite de bytes sem baixar o ZIP historico em CI;
- [ ] fixture de dataset vazio, recurso removido e schema alterado;
- [x] adapter de catalogo sem promover busca unificada;
- [ ] adapter de ingestao local antes de promover busca unificada.

## Proximos passos

1. criar ingestao incremental por recurso mensal, com deduplicacao por `id`;
2. indexar localmente e medir cobertura antes de integrar a busca unificada;
3. somente depois avaliar `CanonicalDecision` e operacoes MCP de pesquisa.

## Evidencia live

Validacao realizada em 2026-08-11:

- `package_search` retornou HTTP 200, `success=true` e 11 datasets;
- os datasets de jurisprudencia retornaram formatos CSV, JSON e ZIP;
- o dicionario da Primeira Turma retornou HTTP 200 com 20 campos;
- `20260630.json` retornou HTTP 200 e registros estruturados;
- a licenca retornada pelo catalogo foi `cc-by`.

## Fontes oficiais

- [Portal de Dados Abertos do STJ](https://dadosabertos.web.stj.jus.br/)
- [API CKAN de catalogo](https://dadosabertos.web.stj.jus.br/api/3/action/package_search?q=jurisprudencia&rows=20)
- [Espelhos de acordaos da Primeira Turma](https://dadosabertos.web.stj.jus.br/dataset/espelhos-de-acordaos-primeira-turma)
- [Dicionario de espelho de acordao](https://dadosabertos.web.stj.jus.br/dataset/espelhos-de-acordaos-primeira-turma)
- [Documentacao do CKAN API](https://docs.ckan.org/en/2.9/api/)

## Aprofundamento Do Contrato CKAN - 2026-08-12

O catalogo oficial de dados abertos do STJ confirma datasets de integras de
decisoes terminativas e acordaos do Diario da Justica, com recursos CSV, JSON
e ZIP e licenca Creative Commons Attribution. O contrato de catalogo deve ser
separado do contrato dos arquivos juridicos.

### Rotas E Filtros Do Catalogo

```text
GET https://dadosabertos.web.stj.jus.br/api/3/action/package_search?q=jurisprudencia&rows=20
GET https://dadosabertos.web.stj.jus.br/api/3/action/package_show?id=<dataset-id-ou-name>
```

Filtros de `package_search` pertencem ao catalogo CKAN: texto `q`, quantidade
`rows` e pagina/offset quando usados. `package_show` recebe o identificador do
dataset e devolve metadados, grupos, tags e a lista de `resources`. Licenca,
formato, URL, checksum, tamanho e data de modificacao devem ser preservados
por recurso.

## Revalidacao Live E Promocao Do Catalogo - 2026-08-14

- `package_search` respondeu HTTP 200 com `success=true`, 11 datasets e
  recursos JSON, CSV e ZIP.
- O adapter de catalogo foi validado com fixtures sanitizadas e nao baixa
  nenhum recurso durante `get_catalog`, `describe_dataset` ou
  `plan_source_sync`.
- O provider permanece fora da pesquisa unificada por contrato explicito:
  `supports_unified_search=false`. A pesquisa textual somente sera promovida
  depois de uma ingestao local, deduplicacao e indice versionado.

Os filtros juridicos dos espelhos nao sao parametros de `package_search`. Eles
existem nos campos dos arquivos publicados e somente ficam disponiveis depois
de baixar/ler o recurso, validar o schema e indexar localmente. O provider deve
deixar essa fronteira explicita para nao prometer uma busca remota que o CKAN
nao oferece.

### Estados De Sincronizacao

Registrar no catalogo local: dataset descoberto, recurso selecionado, checksum
validado, schema observado, quantidade de linhas, ultima sincronizacao e
falha. Os estados de erro devem distinguir recurso removido, checksum ausente
ou divergente, arquivo vazio, formato nao suportado e mudanca de schema.

Fixtures de promocao: `package_search`, `package_show`, recurso JSON pequeno,
recurso CSV, manifesto ZIP, dicionario de campos, checksum divergente e schema
alterado. A camada MCP deve expor descoberta e status de sincronizacao antes
de expor pesquisa juridica local.
