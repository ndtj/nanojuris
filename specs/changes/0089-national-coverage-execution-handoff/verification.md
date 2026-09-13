# Verificação e handoff

Status: `in_progress`

Este pacote é documentação para outro executor. Nenhum provider é promovido,
nenhum bloqueio é resolvido por evasão e nenhuma alteração de produção é
autorizada por este arquivo.

## Resultados

- pacote de handoff criado com escopo, design, ondas, tarefas, playbook de
  acesso, threat model e prompt independente;
- baseline copiado dos artefatos gerados de 2026-09-08;
- a implementação local posterior adicionou `tjrj_banco_sentencas` como coleção
  curada opt-in, com fixture, contrato, live evidence e seis testes;
- nenhuma promoção padrão, commit, push ou deploy foi feita;
- a validação SDD é executada novamente após cada alteração.

## Fechamento do eproc federal

O contrato comum parametrizado do eproc foi comprovado para TNU, TRF2 e TRF6.
Em 2026-09-08, `tools/run_eproc_detail_smoke.py` registrou HTTP 200, identidade
`branch=federal`, `degree=second`, `instance=second`, coleção
`JURISPRUDENCIA` e detalhe HTML com texto para os três providers. O artefato
`docs/provider-discovery/eproc-detail-live-20260908-cycle75.json` contém apenas
metadados, hashes e tamanhos; nenhum corpo foi persistido. T022 foi fechado.

## Baseline registrado

- snapshot: `2026-09-08`;
- providers catalogados/runtime: `67 / 62`;
- fontes federadas declaradas: `47`;
- superfícies mapeadas/obrigatórias: `150 / 125`;
- programa estadual: `25/27` workpacks completos;
- CJPG/CJSG: `7/27` e `25/27`;
- testes de biblioteca: `1531 passed, 26 skipped opt-in`;
- tarefas abertas: `44` (`39 external_source`, `5 human_review`, `0 local_evidence`).
  T012 foi fechado pelo gate reproduzível de federação CJPG e T023 pela matriz
  de completude de fixtures.

## Evidência local de fechamento

T001–T006, T024, T027–T035 e T038–T039 foram concluídas com os geradores, contratos
e testes abaixo:

- `python tools/audit_provider_docs.py --write` e os geradores de cobertura;
- `tests/test_provider_contract_v2.py`, `test_federated_equivalence.py`,
  `test_data_quality_completion.py`, `test_search_many_ranking.py`,
  `test_studio.py`, `test_observability_governance.py` e
  `test_provider_certification.py`;
- suíte completa local, Ruff, format, mypy, compileall e `validate_sdd`.
- `tools/audit_first_degree_federation.py --write`: 27 superfícies CJPG, 7
  federadas com gates consistentes, 20 lacunas preservadas e zero erros.
- `tools/build_fixture_completeness.py --write`: 62/62 providers runtime com
  fixture específica e envelope compartilhado de sucesso, vazio, falha,
  schema drift e segunda página; 47 providers possuem paginação remota
  aplicável.

## Comandos de fechamento

```powershell
cd C:\Users\admin\Desktop\Nanojuris\repos\nanojuris
$env:PYTHONPATH = 'src'
python tools/audit_provider_docs.py --write
python tools/build_provider_coverage.py --write
python tools/build_provider_quality.py --write
python tools/build_provider_capability_ledger.py --write
python tools/build_document_capability_inventory.py --write
python tools/build_degree_coverage.py
python tools/build_surface_state_registry.py
python tools/build_state_appellate_program.py --write
python tools/build_promotion_manifest.py --write
python tools/validate_sdd.py
python tools/audit_open_tasks.py
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
python -m mypy src
python -m compileall -q src tools tests
git diff --check
```

## Critério de conclusão

Só fechar o programa se todos os TNN estiverem concluídos ou justificados e o
programa gerado confirmar `complete_8_of_8 == authorities`, além de zero tarefas
locais abertas. Se restarem apenas fontes externas bloqueadas e decisões
humanas, emitir relatório terminal por tribunal; isso é parada legítima, não
27/27.

## Rastreabilidade

| Critério | Artefato |
| --- | --- |
| AC-001/AC-002 | `execution-manifest.json`, `spec.md`, `tasks.md` |
| AC-003/AC-004 | `design.md`, `legitimate-access-playbook.md`, `threat-model.md` |
| AC-005/AC-006 | `provider-workpack-template.md`, `implementation-plan.md` |
| AC-007 | `GOAT_EXECUTOR_PROMPT.md`, `verification.md` |
