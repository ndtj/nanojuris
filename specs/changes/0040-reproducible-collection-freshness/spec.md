# 0040 — coleta reprodutível e freshness

Status: verified
Owner: Data Engineering, Store, SRE e Security

## Intenção

Permitir pesquisas e coletas locais resumíveis, auditáveis e atualizáveis sem
confundir uma janela coletada com o acervo integral da fonte.

## Requisitos

- REQ-001: toda run persistida possui manifest versionado de query, provider,
  capability, parser, policy e ambiente.
- REQ-002: checkpoints registram cursor/página, hashes, tentativas e outcome.
- REQ-003: retomada é idempotente e não duplica decisões.
- REQ-004: versão/republicação usa identidade 0037 e preserva histórico.
- REQ-005: freshness é calculada por collection e evidência, nunca globalmente.
- REQ-006: remoção na fonte gera tombstone somente quando comprovada.
- REQ-007: cache, raw bytes e documentos obedecem limite, retenção e limpeza.
- REQ-008: execução respeita budgets 0028/0033 e pode parar com estado parcial.
- REQ-009: export registra completude, período e manifest da run.
- REQ-010: coleta em massa não é comportamento default nem gate de CI.

O REQ-006 é atendido pelo ledger de evidência explícita. O REQ-007 adota raw
efêmero por padrão, store sem purge automático e limpeza de cache somente com
limites opt-in definidos pela operação.

## Critérios de aceite

- AC-001: interrupção e retomada produzem o mesmo conjunto de uma run contínua.
- AC-002: mudança de parser/capability invalida checkpoint incompatível.
- AC-003: versões e tombstones possuem provenance.
- AC-004: store/export roundtrip mantém manifest e completeness.
- AC-005: limites de disco, rede e retenção são testados sem chamadas live.
- AC-006: documentação não promete espelho nacional integral.

## Fora de escopo

Data lake central público, redistribuição integral, crawling ilimitado e backup
servidor multiusuário.
