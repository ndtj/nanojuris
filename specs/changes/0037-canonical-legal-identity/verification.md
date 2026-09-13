# Verificação

Status: verified — local identity migration and technical promotion gates are complete.

## Checkpoint da rodada autonoma (2026-09-01)

- `LegalIdentity`, `IdentityEvidence` e `IdentityMatch` implementados em
  `src/nanojuris/identity.py`;
- processos usam o numero CNJ como identidade de processo, nunca como
  identidade suficiente de uma decisao;
- decisoes no mesmo processo com data/tipo/texto diferentes permanecem
  distintas e a regra fica registrada no match;
- ausencia de identificador ou de evidencia semantica retorna `key=None` com
  motivo explicito;
- doze testes de identidade aprovados, incluindo corpus de colisões,
  roundtrip de hashes e compatibilidade com `identity_key` legado;
- `SQLiteStore` persiste `legal_identity_json` com migração idempotente e os
  exporters JSONL/CSV/markdown preservam a projeção sem remover campos legados;
- `tests/test_store.py` e `tests/test_client_exporters.py`: roundtrip aprovado.

T01–T08 estão concluídas. A migração de identidade foi exercitada para os
bindings TJES/CJPG e TJSP/CJPG; IDs nativos, republicação e roundtrip são
validados em `tests/test_identity_provider_migration.py`. Providers sem ID
nativo continuam com `key=None` e motivo explícito, sem promoção implícita.

## Gates previstos

- schema/serialization compatibility;
- collision corpus e golden relationships;
- property tests de determinismo, simetria e não colisão;
- mutation tests para regras de merge;
- roundtrip store/export;
- suíte completa e revisão de domínio jurídico.

## Resultados

Gates de identidade executados localmente: corpus/store/export, propriedades de
determinismo/simetria, guardas de mutação e migração de providers passam. A
ausência de contrato nativo em outras fontes permanece um estado explícito,
não uma falha mascarada.

Gates finais da rodada: `python -m pytest -q` passou com 884 testes e 9 skips
condicionais; Ruff, formatação e mypy também passaram. Nenhuma alteração de
produção ou publicação foi executada.

## Rastreabilidade

Os gates previstos correspondem aos requisitos e tarefas de `traceability.md`.
