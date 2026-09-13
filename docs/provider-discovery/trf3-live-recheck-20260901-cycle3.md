# Rechecagem live TRF3 - 2026-09-01

Foi feita uma rechecagem bounded das superficies publicas alternativas do
TRF3, sem credenciais e sem persistir corpos. As tres rotas expiraram por
timeout de leitura de 6 segundos nesta rede.

| Rota | Resultado | Classificacao |
| --- | --- | --- |
| `GET /acordaos/Acordao` | `ReadTimeout` | `blocked_transport` |
| `GET /jurisprudencia/Home/ResultadoTotais` | `ReadTimeout` | `blocked_transport` |
| `GET /jurisprudencia/Home/BuscarSugestao?term=dano` | `ReadTimeout` | `blocked_transport` |

O resultado nao autoriza criar adapter: action/payload, resposta, paginacao e
inteiro teor continuam sem contrato reproduzivel. O timeout nao e tratado como
zero resultados e nao prova indisponibilidade permanente.

Metadados completos: [`trf3-live-recheck-20260901-cycle3.json`](trf3-live-recheck-20260901-cycle3.json).
