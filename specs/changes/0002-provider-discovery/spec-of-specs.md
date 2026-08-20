# Spec of specs - Descoberta de providers

Status: `accepted`

A capacidade de discovery é decomposta nos seguintes pacotes verificáveis:

| Pacote | Escopo | Saída |
| --- | --- | --- |
| Fundação de evidência | política, request, response, traces e redaction | envelope serializável |
| Descoberta de rotas | links, forms, scripts, JSON e candidatos | `RouteCandidate` |
| Navegação dinâmica | document, XHR e fetch com browser opcional | evidências de eventos |
| Exploração bounded | crawler, profundidade, páginas, bytes e replay | `DiscoveryRun` |
| SDD drafts | research, clarify, spec, design, tasks e verification | pacote revisável |

Todos os pacotes estão implementados em `src/nanojuris/discovery` e são
validados por `tests/test_provider_discovery.py`. Nenhum pacote promove provider
ou altera catálogo automaticamente.
