# Architecture

NanoJuris e organizado em camadas, com separacao explicita entre aquisicao,
normalizacao por fonte e registro canonico. O objetivo e preservar a evidencia
original antes de criar uma visao comum entre tribunais.

```text
providers
  Conectores para fontes publicas.

extraction
  Transporte HTTP, bytes brutos, status de acesso e hash.

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
- status HTTP, URL final, tipo de conteudo, hash e tamanho da resposta quando
  o transporte compartilhado foi usado;
- parser, versao, latencia e transformacoes aplicadas quando disponiveis.

Ausencia de evidencia nao e convertida em `public`: um resultado intermediario
sem `access_status` chega ao registro canonico como `partial`.

## Interfaces e capacidades

`supports_unified_search`, `supports_mcp`, `supports_cli` e `supports_studio`
sao opt-ins independentes. O federador usa somente
`supports_unified_search`; suporte a MCP nao torna automaticamente uma fonte
apta para a busca Python.

Isso permite auditoria por advogados, pesquisadores e sistemas corporativos.

Uma `SearchPage` tambem declara `pagination_mode`, `is_complete` e
`completeness_reason`. `None` significa que a fonte nao comprovou completude;
`False` significa que a janela e explicitamente parcial. O consumidor nao deve
interpretar `total` como total nacional quando a fonte nao declarar o contrato.
Providers com paginação verificável devem preencher esses campos a partir do
total autoritativo da fonte; o contrato de maturidade e os portões de promoção
estão em [Nivel Ouro](gold-maturity.md).
