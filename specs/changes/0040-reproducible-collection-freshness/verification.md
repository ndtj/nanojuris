# Verificação

Status: verified

## Gates previstos

- crash/restart e idempotência;
- fingerprint e incompatibilidade de checkpoint;
- version/republication/tombstone;
- store/export roundtrip;
- limites de bytes, páginas, tempo e disco;
- suíte offline completa e benchmark local.

## Resultados

- T01–T04 concluídos localmente: o runner usa checkpoint v2, fingerprint da
  intenção da consulta, fingerprint do contrato do provider e hash estrutural
  por página, sem persistir conteúdo bruto.
- Escrita do checkpoint usa arquivo temporário com permissões restritas,
  `fsync` e replace atômico. Checkpoints v1 são reconhecidos, mas recusados
  para retomada porque não permitem verificar compatibilidade do contrato.
- Retomada preserva `run_id`, contadores, identidades 0037 e hashes; mudança de
  contrato ou intenção da consulta falha de forma explícita.
- Checkpoint e manifesto redigem campos de parte, advogado, OAB e polícia; a
  intenção integral permanece apenas no fingerprint para validação de resume.
- Freshness é exposta por relatório com `observed_at`; datas ausentes da fonte
  continuam `null` e `coverage_end_known` permanece falso.
- O cache de discovery ganhou limpeza opt-in por idade e orçamento de bytes,
  limitada ao diretório do cache e com resumo auditável. Raw bytes continuam
  efêmeros por padrão, o store canônico não sofre purge automático e toda
  limpeza destrutiva exige uma ação explícita do operador.
- Manifestos de coleta agora acompanham o relatório e podem ser persistidos no
  `ResearchRun`; o SQLite migra `manifest_json` sem quebrar bancos legados e o
  export Markdown/JSON preserva completude, janela e versão do manifesto.
- Benchmark offline de referência registrado em
  `docs/benchmarks/collection-runner-20260901.md` (10.000 registros, 100
  páginas, 1,08 s); não representa latência de fontes externas.
- A escrita atômica também foi exercitada com `ENOSPC` simulado no `fsync`:
  o erro é propagado e nenhum arquivo temporário é deixado para trás.
- Tombstones agora têm ledger separado e API opt-in com validação de URL HTTPS,
  SHA-256, tipo e motivo; a decisão canônica nunca é removida ou ocultada.
- Gates finais desta rodada: smoke live 8/8; suíte completa 932 passed, 1
  skipped (`lxml` opcional ausente).
- Testes: `tests/test_collection.py` (20 passed), store/export/discovery focados
  (99 passed no conjunto combinado).

Todos os gates técnicos de T05a, T05b, T06, T07 e T08 têm cobertura e evidência
concluídas. Resta somente a aprovação humana dos limites e da política antes
de aceitar o SDD para release.

## Rastreabilidade

Os gates previstos correspondem aos requisitos e tarefas de `traceability.md`.
