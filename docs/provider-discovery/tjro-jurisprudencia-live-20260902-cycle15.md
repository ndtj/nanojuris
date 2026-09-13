# TJRO/JURIS — evidência live do ciclo 15 (2026-09-02)

Validação pública bounded, sem credenciais e sem persistência de corpos brutos.

| Verificação | Resultado | Estado |
| --- | --- | --- |
| Busca com `size=100` | HTTP 200, 100 registros, total 675.950 | `reachable_valid_data` |
| Probe `size=101` | HTTP 200, 101 registros | remoto aceita pelo menos 101; contrato local permanece limitado a 100 |
| Datas de julgamento 2026 | HTTP 200, total 49.328, data da amostra em 2026 | `filter_reproduced` |
| Relator (`ds_nome`) | HTTP 200, total 126.418 | reproduzido sem persistir o nome |
| Grau `[1]` + datas | HTTP 200, total 21.624, amostra grau 1 | transporte reproduzido; não exposto no modelo de consulta |

O teste confirmou que o adapter atual envia corretamente datas e relator. O
campo `grau_jurisdicao` foi validado diretamente no contrato HTTP, mas a API
canônica `JurisprudenceQuery` ainda não possui esse campo; ele não foi
inventado nem aplicado implicitamente. O vocabulário de `tipo` continua sem
contrato, e o provider segue opt-in, fora da busca federada padrão.

Hashes, limites e bloqueadores estão em
[`tjro-jurisprudencia-live-20260902-cycle15.json`](tjro-jurisprudencia-live-20260902-cycle15.json).
