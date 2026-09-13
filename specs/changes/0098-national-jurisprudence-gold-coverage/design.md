# Design — malha nacional de jurisprudência

## 1. Arquitetura em camadas

```text
Fonte oficial / exportação pública
        ↓
AccessSession (allowlist, timeout, bytes, rate limit, trace)
        ↓
ProviderAdapter (contrato, paginação, filtros, classificação de erro)
        ↓
CanonicalMapper (identidade, grau, datas, documento, provenance)
        ↓
QualityGate (schema, completude, duplicidade, texto e documento)
        ↓
FederatedPlanner (seleção, ondas, orçamento e estados por fonte)
        ↓
SearchPage / diagnóstico / Studio / MCP / CLI
```

O transporte compartilhado é a única camada autorizada a executar HTTP. O
adapter não deve criar sessões ocultas, desabilitar TLS ou implementar retry
próprio que desrespeite o contrato da fonte.

## 2. Registro de superfície

Cada combinação `authority + branch + degree + instance + collection` possui o
contrato de `coverage-state.schema.json`. `provider` pode ser nulo durante a
descoberta. `lifecycle`, `live_status`, `contract_status` e
`federation_status` nunca são derivados de um único booleano.

Estados de disponibilidade:

```text
not_checked → live_validated → federation_enabled
           ↘ authoritative_empty
           ↘ access_blocked | transport_blocked | source_unavailable
           ↘ schema_invalid | rate_limited | timeout | partial
```

`authoritative_empty` somente pode ser usado quando a fonte informa de maneira
inequívoca que o conjunto consultado é vazio. `unconfirmed_empty` é usado para
respostas sem total ou sem contrato suficiente.

## 3. Contrato de provider

Cada adapter expõe:

```python
search(request: SearchRequest) -> SearchPage
fetch_detail(reference: DocumentReference) -> DocumentResult | AccessEvent
capabilities() -> ProviderCapabilities
```

`SearchPage` deve carregar candidatos, `total_state`, `access_status`,
`filters_applied`, `filters_local`, `filters_unsupported`, paginação, latência e
`SourceTrace`. `DocumentReference` é opcional, mas sua ausência deve ser
explícita (`not_available`, `requires_detail`, `unknown`).

## 4. Descoberta e acesso

O executor começa pela superfície pública de menor custo: API/documentação,
exportação oficial, HTML público, RSS/sitemap/dataset, e somente depois jornada
de navegador normal. Redirects são allowlistados. Cookies e CSRF só podem viver
na sessão corrente. Um desafio obrigatório encerra a tentativa como
`access_blocked`; não há “zona cinzenta” operacional.

## 5. Inteiro teor

1. Buscar metadados e ementa no endpoint de pesquisa.
2. Buscar detalhe ou bitstream apenas sob demanda e com limite de bytes.
3. Validar URL, host, MIME, tamanho, hash e PDF/HTML.
4. Extrair texto visível; OCR só quando permitido, necessário e rastreado.
5. Preservar `extraction_status`, contagem de páginas, confiança e falhas.
6. Nunca substituir o documento original por texto sem apontar a origem.

## 6. Federação e custo

O modo adaptativo seleciona poucas fontes por onda, respeita orçamento global
de candidatos e usa timeout por provider. O modo `all` é explícito. Não há
índice documental próprio: cache é efêmero, tem TTL, chave por contrato e não é
consultável como corpus.

Uma fonte contextual pode enriquecer uma decisão, mas não substitui uma fonte
primária de jurisprudência. Diversidade é um critério de desempate, nunca um
bônus que ultrapasse uma decisão claramente mais relevante.

## 7. Juscraper

O Juscraper é uma fonte de hipóteses técnicas: nomes de tribunais, seletores,
paginação e normalização. Para cada equivalência, registrar rota observada,
licença, campos, filtros, diferença de comportamento e teste diferencial. O
parser NanoJuris permanece independente.

## 8. Segurança

Aplicar allowlist de hosts, proteção contra SSRF em documentos, limites de
resposta comprimida e não comprimida, verificação TLS, redaction de logs,
minimização de PII e circuit breaker cooperativo. Não armazenar tokens de
desafio, cookies persistentes ou credenciais.

