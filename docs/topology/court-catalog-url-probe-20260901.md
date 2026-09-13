# Probe público das URLs-raiz do catálogo — 2026-09-01

Foi feita uma requisição `GET` pública, sem credenciais, para cada URL-raiz dos
27 TREs e dos três TJMs adicionados ao catálogo. O probe não acessa rotas de
busca e não persiste conteúdo de resposta; o relatório machine-readable contém
somente status, URL final, tamanho e hash.

## Resultado

| Classificação | Quantidade | Interpretação |
| --- | ---: | --- |
| `reachable` | 2 | TJMMG e TJMRS responderam HTTP 200 |
| `access_controlled` | 28 | TJMSP e os 27 TREs responderam HTTP 403 neste ambiente |

O HTTP 403 é controle de acesso observado, não prova de que o tribunal esteja
fora do ar ou de que sua jurisprudência não exista. Nenhum controle foi
contornado e nenhuma URL foi promovida a provider por causa desse probe.

Detalhes e hashes: [`court-catalog-url-probe-20260901.json`](court-catalog-url-probe-20260901.json).
