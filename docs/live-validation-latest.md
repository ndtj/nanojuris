# Validacao Live Mais Recente

As evidencias live machine-readable do NanoJuris ficam em
[`validation/runs/`](validation/runs/). O catalogo de cobertura le os arquivos
JSON desse diretorio e seleciona a observacao mais recente de cada provider;
ele nao deriva disponibilidade de edicao manual em Markdown.

A ultima rodada de referencia com rede limpa esta registrada em
[`validation/runs/20260816T020958Z-unified-reference-no-env-proxy.json`](validation/runs/20260816T020958Z-unified-reference-no-env-proxy.json)
e em sua [versao legivel](validation/runs/20260816T020958Z-unified-reference-no-env-proxy.md).

A auditoria ampla do Studio permanece em
[qa/studio-provider-audit-2026-08-15.md](qa/studio-provider-audit-2026-08-15.md),
e a rodada historica anterior em
[live-validation-2026-08-15.md](live-validation-2026-08-15.md).

Cada artefato registra a consulta, seu hash, fontes chamadas, estado
operacional, totais observados, paginação, latencia, estado de acesso quando
observado e limitações. Nenhuma rodada representa monitoramento continuo ou
garantia de disponibilidade futura.
