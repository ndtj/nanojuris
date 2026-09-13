# 0034 — governança de release de providers

Status: verified
Owner: Release, Architecture e Domain Owner

## Intenção

Fechar compatibilidade, documentação, rollout, depreciação e rollback antes de
expor novos providers ou contratos.

## Requisitos

- REQ-001: toda mudança declara impacto em SDK, CLI, MCP, Studio, store e exports.
- REQ-002: catálogos gerados, dossiers, source contracts e changelog ficam
  sincronizados.
- REQ-003: providers novos começam opt-in ou shadow conforme risco.
- REQ-004: rollback e desativação são independentes por provider.
- REQ-005: breaking changes exigem versão semântica e guia de migração.
- REQ-006: release requer gates técnicos, pareceres e autorização humana.
- REQ-007: depreciação possui prazo, aviso e alternativa.
- REQ-008: claims públicos usam evidência e data.
- REQ-009: todo relatório de tipos declara o escopo do comando; `mypy src` é
  bloqueante e a dívida conhecida de tools/tests possui baseline decrescente.

## Critérios de aceite

- AC-001: matriz de compatibilidade está completa.
- AC-002: documentação gerada não diverge do runtime.
- AC-003: rollout e rollback foram ensaiados localmente.
- AC-004: pacote de release registra riscos residuais.
- AC-005: produção não muda sem autorização explícita.
- AC-006: nenhuma mudança aumenta o baseline de erros de tipos fora de `src`, e
  o relatório não chama um subconjunto de “tipagem total”.
