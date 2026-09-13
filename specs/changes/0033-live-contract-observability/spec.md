# 0033 — observabilidade live de contratos

Status: verified
Owner: SRE e QA

## Intenção

Detectar indisponibilidade e schema drift com canários seguros, distinguindo
saúde live de qualidade offline.

## Requisitos

- REQ-001: probes são opt-in, bounded, low-frequency e por allowlist.
- REQ-002: nenhuma probe submete POST sem contrato aprovado.
- REQ-003: SLI mede acesso, latência, schema, resultado e freshness.
- REQ-004: alertas são acionáveis e deduplicados por provider.
- REQ-005: artefatos removem segredo, PII e conteúdo jurídico desnecessário.
- REQ-006: falha live não reescreve fixtures automaticamente.
- REQ-007: health da biblioteca não depende de todos os tribunais simultâneos.
- REQ-008: cada estado inclui timestamp, região e versão do parser.

## Critérios de aceite

- AC-001: canário de referência executa dentro de orçamento.
- AC-002: WAF, timeout, 429, TLS e schema drift são distintos.
- AC-003: relatório live não afirma disponibilidade atemporal.
- AC-004: runbook define triagem, quarentena e recuperação.
- AC-005: CI padrão permanece offline.
