# Design — inventário exaustivo e certificação ouro

Referência: `specs/changes/0070-provider-capability-gold-convergence/spec.md`

## Decisão arquitetural

Adicionar um ledger de capacidades baseado em evidências e gerado a partir dos
contratos existentes. O ledger será a junção auditável entre discovery e
runtime; não substituirá `ProviderCapabilities` de uma vez. A migração será
aditiva e provider por provider.

## Componentes

```text
fonte oficial
  -> discovery bounded/static capture
  -> EvidenceRecord (hash, data, rota, classificação)
  -> ProviderCapabilityLedger
       |-> FilterCapability
       |-> FieldCapability
       |-> PaginationCapability
       |-> DocumentCapability
       `-> FailureCapability
  -> workpack gerado por provider
  -> adapter/query translator/parser/document fetcher
  -> fixtures + testes diferenciais
  -> federação/SDK/CLI/MCP/Studio
  -> GoldAssessment por eixo
```

## Ledger canônico

Chave de uma superfície:

```text
source_id + authority + collection + degree + endpoint_role
```

Campos mínimos:

```text
schema_version
source_id
surface_id
official_entrypoint
technology_family
lifecycle
last_discovery_at
evidence_ttl
filters[]
fields[]
pagination
ordering[]
documents
failures
interfaces
gold_assessment
evidence_ids[]
```

### FilterCapability

```text
canonical_name
native_name
label
value_type
cardinality
allowed_values_source
search_scope
support_status
translation
normalization
remote_or_local
interaction_constraints
evidence_ids
last_verified_at
```

`search_scope` distingue ementa, inteiro teor, ambos, metadados e escopo
desconhecido.

### FieldCapability

```text
surface                 # result | detail | catalog | document
raw_path
canonical_target
value_type
nullable
enum_source
normalization
sensitivity
provenance
disposition             # canonical | raw_preserved | intentionally_ignored
reason
evidence_ids
```

### DocumentCapability

```text
availability
reference_field
endpoint
method
identifier_strategy
formats
mime_policy
max_bytes
redirect_policy
text_extractor
ocr_policy
page_count
linkage_strategy
evidence_ids
```

## Descoberta em passes

### Passo D1 — superfície e formulário

- localizar o ponto oficial público;
- registrar formulário, controles, valores ocultos e dependências entre
  selects;
- diferenciar filtros de busca, apenas apresentação e filtros locais da UI.

### Passo D2 — rede e contrato

- observar requests legítimos disparados pela UI;
- registrar rota, método, headers essenciais, payload e resposta;
- inspecionar OpenAPI/GraphQL apenas quando publicamente expostos;
- nunca reproduzir tokens pessoais ou mecanismos de desafio.

### Passo D3 — prova diferencial de filtros

Para cada filtro, executar no máximo um conjunto pequeno:

```text
Q0 = consulta controle
Q1 = Q0 + valor válido do filtro
Q2 = Q0 + valor válido distinto, quando necessário
Qe = valor inválido/ausente permitido pelo contrato de teste
```

Comparar request normalizado, IDs, totais, facets e fingerprint da página. Um
resultado idêntico não prova que o filtro foi ignorado, mas impede promoção
automática até que exista evidência melhor.

### Passo D4 — paginação e ordenação

- validar primeira e segunda janela;
- detectar página repetida, sobreposição e ordenação instável;
- separar total conhecido, desconhecido e zero real;
- registrar limite remoto e truncamento.

### Passo D5 — detalhe e documento

- seguir somente links oficiais e allowlisted;
- provar relação resultado/detalhe/documento;
- validar MIME real, magic bytes, tamanho e conteúdo textual;
- identificar PDFs escaneados e marcar OCR opcional com confiança.

### Passo D6 — dicionário de dados

- produzir união de campos das fixtures observadas;
- calcular frequência, tipo e nulabilidade;
- classificar cada campo e impedir descarte silencioso.

## Runtime e filtros

`JurisprudenceQuery` continua sendo o contrato comum. O plano por provider deve
ser construído a partir do ledger:

- `native`: nome e valor enviados sem transformação semântica;
- `translated`: alias/enum/formato convertido pelo adapter;
- `local_postfilter`: aplicado depois da coleta, com completude limitada;
- `validated_scope`: dimensão fixa validada pelo adapter antes da chamada,
  sem inventar um parâmetro remoto;
- `unsupported_by_source`: rejeitado/omitido com diagnóstico;
- `out_of_scope_nanojud`: capacidade processual inventariada, mas roteada para
  o produto correto;
- `access_blocked` ou `source_unavailable`: capacidade conhecida, mas não
  executável;
- `unverified`: permitido apenas durante desenvolvimento.

Identificadores têm semântica estrita: se não puderem ser aplicados, a fonte é
pulada. Refinamentos podem continuar com aviso somente quando o usuário aceitar
resultado potencialmente mais amplo.

## Dados e canonicalização

O parser usa dois estágios:

1. `SourceRecord`: representação fiel da resposta, tipada por provider;
2. `CanonicalDecision`/`CanonicalPrecedent`/`CanonicalDocument`: projeção
   nacional com provenance por campo.

Não será criado um campo canônico para cada peculiaridade local. Campos úteis
sem semântica nacional ficam em `raw` com dicionário e provenance. Campo
ignorado exige razão como duplicado, apresentação, segredo técnico ou sem valor
jurídico.

## Inteiro teor

O fluxo do SDD 0032 permanece obrigatório:

```text
SearchResult
  -> DocumentReference
  -> fetch explícito
  -> allowlist/redirect/size/MIME/magic-bytes
  -> bytes + SHA-256
  -> parser HTML/PDF/text/JSON
  -> OCR opcional e isolado
  -> CanonicalDocument
  -> DecisionDocumentLink
```

Quando houver várias versões, cada documento preserva identidade, data,
origem e relação (`original`, `republication`, `rectification`, `attachment`).

## Certificação ouro

O score atual continua disponível como indicador histórico. A nova avaliação é
um conjunto de gates booleanos:

| Eixo | Gate ouro |
| --- | --- |
| contrato | zero `unverified`; filtros/paginação/erros com evidência |
| dados | todos os campos classificados; identidade, datas e provenance válidos |
| documentos | estado terminal; pipeline completo quando a fonte oferece inteiro teor |
| operação | live bounded dentro do TTL ou bloqueio externo explicitamente separado |
| federação | filtros e resultados expostos honestamente, sem falso vazio |

Estados agregados:

```text
contract_gold
data_gold
document_gold | document_not_offered
operation_healthy | operation_blocked | operation_stale
federation_gold | not_applicable
engineering_gold
provider_gold
```

`engineering_gold` exige contrato e dados ouro e estado documental terminal.
`provider_gold` exige também operação saudável e federação ouro quando
aplicável. Saúde bloqueada não apaga qualidade de engenharia, mas impede
`provider_gold` e promoção operacional.

## Famílias técnicas

Implementações comuns podem compartilhar:

- eSAJ CJPG/CJSG;
- eproc;
- PJe;
- GraphQL/BFF/REST;
- Projudi;
- JSF/RichFaces;
- Solr/Elasticsearch;
- CSV/XLSX/datasets.

Cada provider mantém overlays de rota, enum, selector, filtro e parser. Um teste
de família nunca substitui fixture e evidência do tribunal.

## Interfaces

- **SDK:** contrato completo por `JurisprudenceQuery` e diagnóstico estruturado.
- **CLI:** flags derivadas do registro canônico; `--capabilities` por fonte.
- **MCP:** paridade com o SDK ou lista explícita de filtros não expostos.
- **Studio:** renderização dinâmica somente de filtros suportados pelas fontes
  selecionadas; mostrar interseção, união e suporte por fonte.
- **Store/export:** persistir campos canônicos, raw tipado, documento e
  provenance sem perder compatibilidade.

## Segurança e privacidade

- chamadas bounded e baixa frequência;
- redaction de cookies, tokens, partes e identificadores em evidências;
- fixtures mínimas e sanitizadas;
- allowlist HTTPS e validação de redirects;
- limites de bytes, compressão, páginas e tempo;
- nenhum conteúdo baixado é executado;
- OCR isolado e nunca usado contra CAPTCHA.

## Operação

- TTL separado para contrato, live e documento;
- fingerprints por formulário, bundle, schema e parser;
- revalidação incremental somente dos gates invalidados;
- shadow mode antes de habilitar novos filtros na federação padrão;
- rollback por provider/filter/document parser;
- métricas de uso, falha, latência, cobertura e drift por endpoint.
