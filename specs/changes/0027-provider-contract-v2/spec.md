# 0027 — contrato de provider v2

Status: verified
Owner: Provider/Data Engineering

## Intenção

Evoluir o contrato comum sem quebrar a API pública, tornando capabilities,
filtros, paginação, completude, erros, identity e provenance verificáveis.

## Requisitos

- REQ-001: ProviderCapabilities deve declarar documento, busca, filtros,
  paginação, ordenação, detalhe, inteiro teor e interfaces.
- REQ-002: cada filtro deve ser native, translated, local_postfilter,
  unsupported ou unverified.
- REQ-003: SearchPage deve preservar total, janela, cursor/página, ordenação e
  completeness conhecidos ou unknown.
- REQ-004: erros devem usar taxonomia tipada e preservar provider, operação,
  retryability e trace seguro.
- REQ-005: CanonicalDecision, CanonicalPrecedent e CanonicalDocument devem
  preservar raw mínimo e SourceTrace/ExtractionTrace.
- REQ-006: a facade legada deve continuar funcional ou emitir depreciação
  documentada.

## Critérios de aceite

- AC-001: modelos v2 possuem testes de serialização e compatibilidade.
- AC-002: nenhum erro controlado é convertido em zero resultados.
- AC-003: filtros e completude aparecem na matriz gerada.
- AC-004: adapters existentes podem migrar incrementalmente.
- AC-005: SDK, CLI, MCP, Studio, exports e store têm impacto documentado.

## Fora de escopo

Implementar novos providers ou alterar produção.
