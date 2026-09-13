# Juscraper — smoke público bounded (2026-09-01)

Esta evidência complementa o intake estático de
[`jtrecenti/juscraper`](./juscraper-intake-20260901.md). Foram feitas duas
requisições públicas, uma por endpoint, com User-Agent identificável, timeout
curto e sem autenticação. O corpo das respostas não foi persistido; somente
metadados e hashes foram registrados em
[`juscraper-live-smoke-20260901.json`](./juscraper-live-smoke-20260901.json).

## Resultado

| Fonte candidata | Rota | HTTP | Registros | Total declarado | Sinal jurídico | Classificação |
| --- | --- | ---: | ---: | ---: | --- | --- |
| `tjes_jurisprudencia` | `GET /consulta-jurisprudencia/api/search` (`core=pje2g`, `per_page=1`) | 200 | 1 | 200.397 | identidade + ementa/acórdão | `candidate_live_valid_data` |
| `tjrn_jurisprudencia` | `POST /api/pesquisar` (ementa, página 1) | 200 | 10 | 329.883 | identidade + ementa/inteiro teor | `candidate_live_valid_data` |

## Interpretação

As duas rotas devolveram JSON público reproduzível e registros com
identificador e conteúdo de jurisprudência. Isso confirma disponibilidade
live do contrato observado no upstream, mas ainda não equivale a provider
NanoJuris pronto: não há adapter runtime registrado, fixtures sanitizadas,
paridade independente de campos, nem revisão concluída das condições de
reutilização do acervo oficial.

O resultado não deve ser interpretado como cobertura integral. O total remoto
é apenas o contador informado pela fonte no momento da consulta, e não uma
garantia de coleta completa ou de estabilidade futura.

## Próxima decisão SDD

Manter `tjes_jurisprudencia` e `tjrn_jurisprudencia` como `candidate` nos
workpacks 0025/0039. Antes de promover qualquer adapter, concluir revisão de
reuso, capturar fixtures mínimas de sucesso/vazio/erro/paginação e mapear
identidade, datas, ementa, texto e `raw` para `CanonicalDecision` com
`SourceTrace`. Nenhuma cópia do código upstream foi feita e produção não foi
alterada.

Nota de atualizacao: este snapshot antecede o adapter TJES/CJSG do SDD
`0049`. O TJES foi posteriormente implementado de forma opt-in; o TJRN
permanece candidato ate novo contrato e evidencia live estaveis.
