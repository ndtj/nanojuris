# Benchmark offline — merge federado

Execução local em 2026-09-01, usando quatro fontes sintéticas, 25 páginas por
fonte e 100 registros por página:

| Métrica | Resultado |
|---|---:|
| páginas | 100 |
| registros de entrada | 10.000 |
| registros únicos | 10.000 |
| tempo do merge | 0,269 s |
| throughput observado | 37.169 registros/s |
| complete | `true` |

O benchmark mede somente materialização, ordenação e deduplicação local. Não é
uma promessa de latência, disponibilidade ou cobertura dos tribunais.
