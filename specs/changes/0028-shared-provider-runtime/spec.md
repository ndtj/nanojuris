# 0028 — runtime compartilhado e resiliente

Status: verified
Owner: Provider Engineering e SRE

## Intenção

Centralizar transporte e política operacional repetitiva sem centralizar o
parser ou apagar particularidades dos tribunais.

## Requisitos

- REQ-001: HTTP deve ter timeout, tamanho máximo, redirects e hosts allowlisted.
- REQ-002: retry ocorre apenas em operações idempotentes e falhas transitórias.
- REQ-003: rate budget, concurrency e backoff são definidos por provider/host.
- REQ-004: resposta de transporte é imutável, hashável e independente do parser.
- REQ-005: circuit breaker e cache são isolados por provider e operação.
- REQ-006: logs removem auth, cookies, tokens, query sensível e conteúdo.
- REQ-007: famílias eSAJ/eproc compartilham infraestrutura, mas mantêm fixtures
  e contratos específicos.

## Critérios de aceite

- AC-001: testes simulam timeout, 403, 429, 5xx, redirect e resposta excessiva.
- AC-002: Retry-After e backoff com jitter são respeitados.
- AC-003: uma fonte falha sem derrubar outras fontes federadas.
- AC-004: adapters existentes migram incrementalmente.
- AC-005: nenhuma chamada live é necessária para a suíte padrão.
