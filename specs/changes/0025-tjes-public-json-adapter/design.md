# Design

## Superfície observada

Base pública: `https://sistemas.tjes.jus.br/consulta-jurisprudencia`

| Rota | Uso no adapter |
| --- | --- |
| `GET /api/health` | diagnóstico opcional; confirma cores ativas e contagens. O campo `url` (rede `172.27.*`) é ignorado. |
| `GET /api/cores` | descoberta de catálogo: `pje1g`, `pje2g`, `pje2g_mono`, `legado`, `turma_recursal_legado`. |
| `GET /api/facets?core=<core>` | metadados de faceta (classe, jurisdição, magistrado, órgão, assunto); cacheável. |
| `GET /api/search?core=<core>&q=<termo>&page=<n>&per_page=<n>` | busca. Resposta de topo: `docs`, `facets`, `page`, `per_page`, `total`, `total_pages`. |

## Seleção de core (`REQ-002`)

O adapter expõe um parâmetro de core. Default proposto: `pje2g` (2º grau), por
ser o acervo de acórdãos mais comparável às outras fontes federadas. Uma busca
sem core explícito não consulta todos os cores; consulta apenas o default e
registra isso no `SourceTrace`. Consultas multi-core são uma extensão futura,
fora deste pacote.

## Mapeamento canônico (`REQ-004`)

| Canônico | PJe (`pje1g`/`pje2g`) | Legado |
| --- | --- | --- |
| `identifier` | `nr_processo` | `numero_processo_legado` |
| `court` | `"TJES"` | `"TJES"` |
| `rapporteur` | `magistrado` | `nome_desembargador` |
| `body` | `orgao_julgador` | órgão |
| `judgment_date` / `publication_date` | datas do documento | datas de julgamento/publicação |
| `summary` / `full_text` | `ementa`/`ementa_html`, `acordao`/`acordao_html`, `inteiro_teor`/`inteiro_teor_html` (1º grau) | conteúdo decisório HTML/RTF |
| `raw` | documento completo | documento completo |

Datas são normalizadas pelo utilitário existente; um formato não reconhecido é
preservado em `raw` e o campo canônico fica vazio, sem exceção.

## Paginação (`REQ-003`)

`SearchPage` é construída a partir de `page`, `per_page`, `total` e
`total_pages`. `is_complete` quando `page >= total_pages`. O `per_page` máximo
aceito é confirmado por teste live e fixado como constante do adapter; um
pedido acima do limite é reduzido antes da requisição.

## Classificação de erro (`REQ-005`)

| Condição | Resultado |
| --- | --- |
| HTTP != 200 | `SourceUnavailableError` / `RateLimitDetectedError` conforme o código |
| corpo sem `docs` ou sem `total` | `SourceContractError` (schema alterado) |
| documento sem identidade | `SourceContractError` |
| `docs` vazio com `total: 0` | página vazia completa, sem erro |
| core inválido / parâmetro rejeitado | erro de fonte, não ausência de resultados |

## Guardrails

- Somente requisições `GET` sem autenticação; nenhuma tentativa contra o Solr
  interno ou rotas não observadas.
- `SourceTrace` registra rota, core e parâmetros.
- Capability declara a fonte como opt-in até a revisão de condições de reuso.
- Fixtures são sanitizadas: nomes de partes e dados pessoais reduzidos ao
  necessário para exercitar o parser.
