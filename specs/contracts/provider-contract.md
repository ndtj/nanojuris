# Contrato de provider

Status: `accepted`

Este contrato complementa `docs/coverage/README.md`, o catálogo gerado, o
dossiê do provider, o source contract, o módulo runtime e seus testes.

## Obrigatório

- fonte oficial e entrada pública;
- rota, método, payload, resposta e filtros observados;
- paginação, ordenação e limites;
- sucesso, vazio, query inválida, timeout, rate limit e controle de acesso;
- campos canônicos, campos brutos e ausência de dados;
- identidade estável e datas quando disponíveis;
- fixture pública minimizada;
- teste offline do parser;
- decisão sobre texto integral, MCP, Studio e CLI;
- source trace e extraction trace.

## Estados operacionais

`valid`, `empty`, `invalid_query`, `access_controlled`, `rate_limited`,
`timeout`, `source_unavailable`, `tls_error`, `parser_changed` e `unknown` são
estados distintos. Nenhum deles deve ser convertido silenciosamente em
`zero_results`.

## Gate de maturidade

Um provider só pode ser recomendado para jurimetria ampla quando possui contrato
confirmado, identidade estável, conteúdo textual, data ou preservação da data
bruta, output canônico, provenance e validação suficiente para sua classificação.
