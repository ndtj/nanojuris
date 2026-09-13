# TJRN — paginação pública live (2026-09-02, ciclo 22)

Foram feitas duas requisições sequenciais à rota pública conhecida do TJRN,
com `page_size=10` e sem credenciais. Os corpos não foram persistidos; somente
hashes e metadados operacionais foram registrados.

| Página | HTTP | Registros | Total informado | Janela | Classificação |
|---:|---:|---:|---:|---|---|
| 1 | 200 | 10 | 53.366 | 1–10 | `reachable_valid_data` |
| 2 | 200 | 10 | 53.366 | 11–20 | `reachable_valid_data` |

A continuidade 1–10 → 11–20 confirma a janela básica de paginação nesta
fotografia. O provider continua `candidate_only`: isso não comprova ordenação
global, filtros completos, estabilidade futura ou autorização de coleta em
escala.
