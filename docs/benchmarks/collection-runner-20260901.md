# Benchmark local do runner de coleta - 2026-09-01

## Escopo

Benchmark offline, com provider sintético, sem chamadas de rede e sem dados de
tribunais. Cada página retornou 100 decisões canônicas; a coleta foi limitada a
100 páginas/10.000 registros e usou checkpoint v2.

## Resultado observado

| Métrica | Resultado |
| --- | ---: |
| Tempo total | 1,08 s |
| Páginas | 100 |
| Registros salvos | 10.000 |
| Throughput | 9.259,26 registros/s |
| Completa | sim |
| Checkpoint final | 457.365 bytes |

O número é referência de processamento local, não promessa de latência de
providers externos. Rede, parser, limites da fonte, disco e rate limit devem
ser medidos separadamente em cada contrato. A coleta em massa continua sendo
opt-in e limitada por páginas/registros.
