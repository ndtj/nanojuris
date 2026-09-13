# Verificacao

Status: verified

## Checkpoint da rodada autonoma (2026-09-01)

- o modelo `nanojuris.topology` implementa collections, bindings, epochs, claims,
  gaps e projecoes deterministicas;
- `docs/topology/national-topology.json` e seu schema sao gerados offline;
- o catalogo institucional individualiza 94 autoridades, com evidencia CNJ;
- a sondagem publica das 30 URLs novas esta separada em `reachable` e
  `access_controlled`, sem transformar HTTP 403 em ausencia;
- providers sem autoridade reconciliada permanecem em `authority:unknown`;
- `docs/topology/national-coverage-claims-20260901.json` e `.md` contem cinco
  dimensoes, 110 gaps por collection e a epoca `2026-09-01@2026-09-01`;
- o denominador de providers inclui os 35 bindings nao reconciliados, evitando
  que reconciliacao parcial seja apresentada como completude;
- a varredura live de providers continua registrada em
  `docs/provider-discovery/all-provider-sweep-20260901.json`.

T01/T02/T03/T04/T05/T06/T07/T08 estao concluidas para esta epoca. O aceite foi
registrado pelo operador/Domain Owner para o escopo tecnico local; isso nao
autoriza deploy, publicacao ou cobertura nacional inexistente.

## Resultados

| Gate | Estado | Evidencia |
| --- | --- | --- |
| claims deterministas | pass | `tools/build_national_coverage.py` e artefatos JSON/Markdown |
| gaps por ramo | pass | `summary.gaps_by_branch` e 110 entradas no JSON |
| duplicidade, epochs e denominadores | pass | `tests/test_topology.py` (10 testes) |
| revisao Domain Owner | accepted_with_limitations | T08; escopo tecnico local/federado, sem deploy |

## Rastreabilidade

Os gates acima correspondem aos requisitos e tarefas em `traceability.md`.
