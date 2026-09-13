# 0037 — identidade jurídica canônica e deduplicação

Status: verified
Owner: Legal Data, Architecture e QA

## Intenção

Definir identidade estável e conservadora para processo, decisão, precedente,
publicação, documento e versão, permitindo unificação sem fusões juridicamente
incorretas.

## Requisitos

- REQ-001: IDs de processo, decisão, precedente, documento e publicação são
  tipos distintos.
- REQ-002: número CNJ identifica processo, nunca decisão isoladamente.
- REQ-003: identidade de decisão considera autoridade, grau, órgão, tipo, data,
  identificador nativo e evidência textual conforme a collection.
- REQ-004: republicação, correção e nova versão preservam linhagem.
- REQ-005: deduplicação é source-aware, explicável e reversível.
- REQ-006: hash textual usa normalização versionada e não apaga raw.
- REQ-007: ausência ou conflito produz estado explícito, não ID inventado.
- REQ-008: aliases e relações entre records sobrevivem a export/store roundtrip.
- REQ-009: decisões diferentes no mesmo processo jamais se fundem apenas por
  similaridade textual.

## Critérios de aceite

- AC-001: modelos e regras possuem versionamento e compatibilidade v1.
- AC-002: corpus de colisão cobre múltiplas decisões, republicações e fontes.
- AC-003: merge registra regra, confiança, evidência e pode ser desfeito.
- AC-004: property tests provam determinismo e ausência de colisões conhecidas.
- AC-005: store, exports, SDK, CLI, MCP e Studio preservam IDs e relações.

## Fora de escopo

Resolver identidade civil de partes, inferir mérito ou criar identificador
oficial onde a fonte não o publica.
