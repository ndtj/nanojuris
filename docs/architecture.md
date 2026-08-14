# Architecture

NanoJuris e organizado em camadas, com separacao explicita entre aquisicao,
normalizacao por fonte e registro canonico. O objetivo e preservar a evidencia
original antes de criar uma visao comum entre tribunais.

Em termos de produto, o NanoJuris funciona como uma camada de dados entre
fontes judiciais heterogêneas e aplicações Python, pipelines de pesquisa e
agentes de IA:

```text
Fontes públicas
      │
      ▼
Provider + transporte HTTP
      │
      ▼
Parser específico da fonte
      │
      ▼
Registro normalizado
      │
      ▼
Modelo canônico + provenance
      ├──────────────┬──────────────┬──────────────┐
      │ Python SDK   │ CLI          │ MCP / Studio │
      └──────────────┴──────────────┴──────────────┘
      │
      ▼
SQLite · JSONL · CSV · Markdown · datasets
```

```text
providers
  Conectores para fontes publicas.

extraction
  Transporte HTTP compartilhado, bytes brutos, status de acesso e hash.

models
  Contratos tipados e estaveis.

client
  Fachada Python e federacao com concorrencia limitada, deadline, deduplicacao
  e pagina global.

canonical
  Mapeamento de JurisprudenceResult para CanonicalDecision e CanonicalPrecedent.

store
  Persistencia SQLite atomica e reprodutivel.

mcp_server / web
  Adaptadores opcionais para agentes e Studio local; nao participam do nucleo.

exporters
  JSONL, Markdown e outros formatos.

cli
  Interface de linha de comando.
```

## Provider contract

Todo provider deve implementar:

```python
search(query)
get_decisions(precedent_id)
get_parameters()
```

## Camadas de dados

```text
RawSourceRecord -> NormalizedProviderRecord -> CanonicalLegalRecord
```

`raw` preserva nomes e valores da fonte. O resultado intermediario conhece o
contrato daquele tribunal. O registro canonico normaliza somente significados
equivalentes. Datas canonicas usam ISO `YYYY-MM-DD`; o valor original fica em
`judgment_date_raw` ou `publication_date_raw`.

Essa separação é deliberada:

- **Raw source record:** resposta, bytes, status HTTP e evidência da fonte;
- **Normalized provider record:** interpretação dos campos segundo o contrato
  daquele tribunal;
- **Canonical legal record:** campos comuns entre fontes, sem apagar valores
  originais nem inventar equivalências.

## Modelo unificado

O modelo principal e `JurisprudenceResult`:

```text
id
source
court
type
number
question
thesis
summary
full_text
status
rapporteur
updated_at
judgment_date / publication_date
source_updated_at / retrieved_at
access_status / extraction_status
paradigm_cases
source_trace
```

## Rastreabilidade

`SourceTrace` preserva:

- provider;
- endpoint;
- query;
- data de coleta;
- URL publica;
- limitacoes;
- status HTTP, URL final, tipo de conteudo, hash e tamanho da resposta;
- parser, versao, latencia e transformacoes aplicadas quando disponiveis.

Ausencia de evidencia nao e convertida em `public`: um resultado intermediario
sem `access_status` chega ao registro canonico como `partial`.

## Ciclo de uma pesquisa

1. `NanoJurisClient` valida a consulta e seleciona o provider explicitamente ou
   por roteamento federado.
2. O provider executa apenas as rotas declaradas em seu dossiê e aplica os
   limites da fonte.
3. O transporte preserva resposta, hash, tamanho, URL final e estado de acesso
   quando essas informações estão disponíveis.
4. O parser converte a resposta em `JurisprudenceResult`, mantendo `raw`.
5. A canonicalização produz registros comuns sem confundir data de julgamento,
   publicação, atualização da fonte e coleta.
6. SDK, CLI, MCP e Studio expõem o mesmo resultado e os mesmos limites.

Falhas de rede, bloqueios, resultados vazios e bugs de parser não têm o mesmo
significado. O sistema deve conservar essa diferença em erros, traces e
`completeness_reason`, em vez de reportar uma busca parcial como completa.

## Interfaces e capacidades

`supports_unified_search`, `supports_mcp`, `supports_cli` e `supports_studio`
sao opt-ins independentes. O federador usa somente
`supports_unified_search`; suporte a MCP nao torna automaticamente uma fonte
apta para a busca Python.

Isso permite auditoria por advogados, pesquisadores e sistemas corporativos.

## Fronteiras de extensão

Um novo provider deve ficar restrito ao contrato da própria fonte. Ele não deve
alterar o modelo canônico para acomodar um campo exclusivo sem justificar a
semântica. A implementação deve incluir:

- capabilities declaradas explicitamente;
- parser offline com fixture mínima e representativa;
- cenários de sucesso, vazio, erro e controle de acesso;
- identificadores estáveis e paginação documentada;
- dossiê em `docs/providers/<source-id>/README.md`;
- teste live opt-in, nunca obrigatório para a suíte padrão.

O fluxo completo de promoção está em [Desenvolvimento de providers](provider-development.md)
e no [template de dossiê](provider-dossier-template.md).

Uma `SearchPage` tambem declara `pagination_mode`, `is_complete` e
`completeness_reason`. `None` significa que a fonte nao comprovou completude;
`False` significa que a janela e explicitamente parcial. O consumidor nao deve
interpretar `total` como total nacional quando a fonte nao declarar o contrato.
Providers com paginação verificável devem preencher esses campos a partir do
total autoritativo da fonte; o contrato de maturidade e os portões de promoção
estão em [Nivel Ouro](gold-maturity.md).
