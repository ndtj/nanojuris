# Verificacao

Status tecnico: `verified`; a fonte foi promovida tecnicamente como parcial e
continua sujeita à revisão humana de retenção.

## Resultados

- Chamada live bounded em 2026-09-08: `GET /indexS.php?pag=ler`, categoria
  `C`, termo `responsabilidade`, HTTP 200, 17 linhas com PDF.
- PDF observado no host oficial: HTTP 200, `application/pdf`, assinatura
  `%PDF-`, 143472 bytes recebidos no probe.
- Pagina 2 e termo inexistente responderam HTTP 200 sem linhas, mas sem
  marcador autoritativo; ambos permanecem `total_known=false`.
- Evidencia redigida: `docs/provider-discovery/tjal-esmal-banco-sentencas-live-20260908.json`.
- Teste focado: `python -m pytest -q tests/test_tjal_esmal_banco_sentencas.py` -> 8 passed.
- SDD, catalogo, inventarios e manifestos foram regenerados localmente.
- A busca HTML foi migrada para `SharedHttpClient`; o PDF continua usando o
  mesmo limite/allowlist via `DocumentReference`. O teste de transporte
  requests-compatível permanece reproduzível e não altera o escopo curado.

## Rastreabilidade

| Requisito | Evidencia | Resultado |
|---|---|---|
| RF-001/RF-002 | provider query builder + live evidence | OK |
| RF-003/RF-004 | parser HTML + fixture success | OK |
| RF-005 | `total_known=False` + fixture/test de pagina | OK |
| RF-006 | `DocumentReference` e transporte allowlisted | OK |
| RF-007 | erros HTTP/TLS/schema explicitamente classificados | OK |
| RF-008 | capabilities federated partial + `total_known=false` | OK técnico |

## Limites

O banco ESMAL é curado e não prova cobertura integral do CJPG. Nenhum corpo
judicial foi persistido neste artefato; somente metadados, hashes e limites
foram registrados. Nenhum commit, push, deploy ou alteracao de producao foi
feito.
