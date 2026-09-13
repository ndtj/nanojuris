# Verification — SDD 0095

Estado atual: `in_progress` (implementação técnica concluída; promoção padrão e
política de atualização continuam decisões humanas).

## Evidencia planejada

- URL do indice oficial e links dos quatro volumes;
- status, MIME, bytes e contagem de páginas em
  `docs/provider-discovery/tjal-turma-recursal-live-20260908.json`;
- volumes 1–3 classificados como textuais e volume 4 como image-only;
- parser bounded de `Ementas-3.pdf`, sem persistência do corpo;
- testes de sucesso, vazio, erro, filtros e escopo em
  `tests/test_tjal_turma_recursal_ementario.py`.

## Execução técnica

Comandos executados em 2026-09-08:

```text
python -m pytest -q tests/test_tjal_turma_recursal_ementario.py  # 6 passed
python tools/audit_provider_discovery_offline.py                 # 71 catalog / 66 runtime
python tools/build_fixture_completeness.py --write              # 66/66 complete
python tools/build_provider_coverage.py --write                 # 71 catalog / 50 unified
python tools/build_degree_coverage.py                           # CJPG 7/27, CJSG 25/27
python tools/build_surface_state_registry.py                    # 150 surfaces / 125 required
python tools/validate_sdd.py                                    # pass
```

O smoke é opt-in: a fonte não entra no rollout padrão. O estado recursal não
é promovido a CJPG/CJSG e não é tratado como texto integral.

## Resultados

- A chamada oficial retornou os quatro volumes com HTTP 200; três permitiram
  extração textual e um foi classificado como image-only.
- A busca live bounded de `responsabilidade civil` extraiu 29 registros na
  janela `Ementas-3.pdf`, com `total_known=false` e três resultados na página 1.
- O parser de fixture produziu registros recursais canônicos sem misturar
  primeiro ou segundo grau.
- Os seis testes focados passaram e os inventários foram regenerados.

## Rastreabilidade

| Critério | Evidência |
|---|---|
| AC-001 | índice e volumes oficiais no live evidence |
| AC-002 | identidade recursal validada no parser e no teste focado |
| AC-003 | limites, allowlist e estados de erro no adapter |
| AC-004 | fixtures de sucesso, vazio e PDF inválido |
| AC-005 | `SearchPage` com janela local e `total_unknown` |
| AC-006 | capacidade opt-in e exclusão de CJPG/CJSG |

## Limites

Esta mudanca nao afirma acervo integral, nao fecha CJPG/CJSG e nao executa
deploy. Tarefas T008/T009 continuam abertas para revisao humana.
