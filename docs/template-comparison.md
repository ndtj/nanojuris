# Comparação local: template de scraping × NanoJuris

Esta matriz foi construída somente a partir dos arquivos locais em
`C:\Users\luciano.finozzi\Downloads\sistema\segunda lib` e do código atual do
NanoJuris. O template contém 117 arquivos Python, com núcleo de parser,
fetchers, engines, spiders, storage, checkpoint, cache e exportadores.

## Decisão de adaptação

| Família do template | Ganho para NanoJuris | Decisão | Destino |
| --- | --- | --- | --- |
| `parser.py` + `core/mixins.py` | seletores CSS/XPath, texto, atributos, ancestralidade, similaridade e recuperação | adaptar nativamente | `nanojuris.parsing` |
| `core/translator.py` | tradução CSS/XPath e seletores estruturais | adaptar com dependência opcional e fallback | `nanojuris.parsing` |
| `core/storage.py` | memória persistente de elementos/seletores | adaptar para evidência e memória de seletores, sem pickle de requests | `nanojuris.adaptive` |
| `spiders/engine.py` + `scheduler.py` | fila priorizada, deduplicação, concorrência e callbacks | adaptar ao contrato de providers, com limites explícitos | `nanojuris.collection` |
| `spiders/checkpoint.py` | retomada após interrupção | adaptar para checkpoint JSON/SQLite serializável | `nanojuris.collection` |
| `spiders/cache.py` | cache por fingerprint de requisição | reutilizar princípios na discovery e estender à coleta | `nanojuris.discovery` / `nanojuris.collection` |
| `spiders/result.py` | estatísticas e exportação de itens | adaptar para métricas canônicas e manifests | `nanojuris.collection` / `store.py` |
| `fetchers/requests.py` e `engines/static.py` | sessões sync/async e limites de transporte | adaptar somente abstrações bounded | `extraction.py` / `discovery` |
| `fetchers/chrome.py` | observação de páginas dinâmicas | já adaptado como browser opcional Playwright | `discovery.browser` |
| `fetchers/stealth_chrome.py`, fingerprints e proxy rotation | automação de identidade/contorno de controles | fora do núcleo | não incorporar |
| `core/ai.py` e `core/shell.py` | operação por agentes e geração de artefatos | adaptar como CLI/MCP e SDD, sem execução arbitrária | `cli.py`, `mcp_tools.py`, `specs` |
| integrações Scrapy/templates | integração genérica de spiders | manter fora da API principal até existir caso jurídico concreto | futura integração |

## Lacunas que motivaram a adaptação

Essas lacunas foram fechadas nesta mudança por quatro componentes novos:

- `nanojuris.parsing`: API comum de documento/nó, com CSS, XPath, texto,
  atributos, links, regex, seletores estruturais e fallback de backend.
- `nanojuris.normalization`: normalizadores seguros para texto, datas, CNJ,
  tipo de decisão e URL.
- `nanojuris.adaptive`: memória SQLite de sugestões com evidência e gate de
  aprovação explícita.
- `nanojuris.collection`: runner limitado, deduplicado, persistente e
  retomável por checkpoint, integrado ao cliente, CLI e MCP.

Permanece como trabalho incremental a migração dos demais providers HTML. Os
providers TJGO/Projudi, TJPR, CJF/TRF1, STJ Informativo e STJ SCON já usam o
adapter compartilhado. Cada
migração deve preservar fixture, contrato, trace e comportamento de erro; não
é uma substituição mecânica de imports.

## Ordem de implementação

1. Parser compartilhado com lxml opcional, fallback BeautifulSoup, CSS/XPath,
   texto, atributos, links, regex e similaridade.
2. Normalização centralizada e compatível com o modelo canônico existente.
3. Runner de coleta com páginas, deduplicação, limites, checkpoint e manifestos.
4. Migração progressiva dos parsers HTML mais simples para o novo núcleo, sempre
   preservando fixtures e contratos dos providers.
5. Exposição CLI/MCP, documentação de cobertura e avaliação de regressões.

O template não será copiado integralmente: as capacidades são adaptadas ao
contrato de jurisprudência pública, à proveniência e aos limites de acesso do
NanoJuris.
