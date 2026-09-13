# Rechecagem live TJRO/CJSG - 2026-09-01

O backend oficial respondeu HTTP 200 e JSON para tres consultas publicas
bounded, mas retornou total `0` e nenhum documento em todas elas. Isso e um
vazio observavel, nao erro HTTP; ainda assim nao fecha um contrato de resultados
para o NanoJuris.

| Consulta | Status | Total | Classificacao |
| --- | ---: | ---: | --- |
| `responsabilidade civil` | 200 | 0 | `reachable_empty_data` |
| `dano moral` | 200 | 0 | `reachable_empty_data` |
| `mandado` | 200 | 0 | `reachable_empty_data` |

Metadados, hashes e limites estao em
[`tjro-cjsg-live-recheck-20260901.json`](tjro-cjsg-live-recheck-20260901.json).
Nenhum corpo ou dado pessoal foi persistido. O provider permanece candidato;
uma futura promoção exige uma resposta de sucesso real e fixture sanitizada.
