# Mapa de portabilidade da biblioteca de discovery

Este mapa registra como as famílias Python do sistema local indicado foram
analisadas e convertidas em capacidades NanoJuris.

| Código analisado | Capacidade aproveitada | Destino NanoJuris |
| --- | --- | --- |
| `fetchers/requests.py` | sessão HTTP e métodos de coleta | `nanojuris.discovery.http` |
| `fetchers/chrome.py` | navegação dinâmica | `nanojuris.discovery.browser` |
| `fetchers/stealth_chrome.py` | opções avançadas de browser | não entra no runtime; browser público permanece explícito |
| `engines/toolbelt/custom.py` | resposta unificada, corpo, status, headers e hash | `discovery.models.DiscoveryResponse` |
| `engines/toolbelt/convertor.py` | conversão/captura de respostas XHR | `discovery.browser` |
| `parser.py` | seletores estruturais e candidatos adaptativos | `discovery.extract` + revisão humana |
| `core/storage.py` | persistência de observações estruturais | `discovery.replay` e artefatos JSON |
| `spiders/request.py` | request com método, URL e metadados | `DiscoveryRequest` |
| `spiders/engine.py` | pipeline de processamento | `DiscoveryCrawler` |
| `spiders/links.py` | extração e normalização de links | `extract_route_candidates` |
| `spiders/robotstxt.py` | respeito a robots.txt | `HttpDiscoveryClient` |
| `spiders/throttle.py` | atraso e limites | `DiscoveryPolicy` |
| `spiders/cache.py` | replay, fingerprint e cache de respostas | `discovery.replay` + `discovery.cache` |
| `spiders/checkpoint.py` | retomada de execução | `DiscoveryRun` + artefatos persistidos |
| `spiders/result.py` | estatísticas de execução | `DiscoveryRun.metrics()` |
| `core/ai.py` | superfície para agentes | CLI principal e MCP `discover_provider` |
| `core/shell.py` | conversão de conteúdo | drafts e relatórios SDD |

## Decisão

O NanoJuris absorve capacidades, contratos e testes de comportamento; não
mantém dois runtimes concorrentes nem importa a biblioteca inteira como
dependência obrigatória. O mapa é a referência para futuras melhorias e evita
perda de rastreabilidade.
