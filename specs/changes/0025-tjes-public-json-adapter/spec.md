# 0025 — TJES public JSON jurisprudence adapter

Status: `verified`

## Intento

Promover a consulta pública de jurisprudência do TJES a um adapter local,
usando o contrato JSON servido pela página oficial atual
`sistemas.tjes.jus.br/consulta-jurisprudencia/`. Substitui a classificação de
busca `blocked_transport` registrada em
[0023-trt2-tjes-contract-audit](../0023-trt2-tjes-contract-audit/spec.md), que
observou apenas o portal ColdFusion legado (HTTP 503) e a rota histórica de
resultados (HTTP 404). O ementário PDF permanece uma superfície documental
independente.

## Contexto e decisão

Em 28/08/2026 a página oficial atual distribuiu um frontend público que chama
uma API no mesmo domínio. Uma chamada de baixa frequência, sem autenticação,
CAPTCHA ou acesso ao Solr interno, confirmou um contrato observável
(`/api/health`, `/api/cores`, `/api/facets`, `/api/search`). A evidência está
em [`docs/provider-discovery/route-research-2026-08-27.md`](../../../docs/provider-discovery/route-research-2026-08-27.md)
e no dossiê canônico do provider. A disponibilidade pública **não** é licença de
redistribuição; a promoção depende de revisão das condições de reuso.

## Requisitos

- **REQ-001**: o adapter deve usar somente a URL HTTPS pública
  `https://sistemas.tjes.jus.br/consulta-jurisprudencia`; o campo `url` de rede
  privada devolvido por `/api/health` deve ser ignorado.
- **REQ-002**: este adapter cobre somente a collection de segundo grau por meio
  dos cores `pje2g`, `pje2g_mono` e `legado`, com default explícito e sem fan-out
  silencioso. `pje1g` e `turma_recursal_legado` são evidências para collections
  e source IDs próprios sob 0039; não podem ser misturados neste resultado.
- **REQ-003**: a conversão de paginação deve seguir a convenção pública do
  NanoJuris a partir de `page`, `per_page`, `total` e `total_pages`.
- **REQ-004**: identidade, datas, ementa/acórdão e inteiro teor devem mapear
  para `CanonicalDecision` sem perda silenciosa; campos desconhecidos vão para
  `raw`. O core legado usa `numero_processo_legado`, `nome_desembargador` e
  conteúdo HTML/RTF.
- **REQ-005**: respostas sem `docs`/`total` ou sem identidade de documento
  devem gerar erro de contrato determinístico, não uma página vazia.
- **REQ-006**: `SourceTrace` deve registrar rota, core e parâmetros de cada
  requisição.
- **REQ-007**: o catálogo/capability deve declarar rota, cores, formatos,
  limitação de `per_page` e a natureza opt-in até a confirmação de reuso.
- **REQ-008**: nenhuma promoção a produção, coleta em escala ou rota de detalhe
  não documentada faz parte desta mudança.
- **REQ-009**: toda resposta registra `authority_id`, `collection_id`, core e
  grau conforme 0036/0037; core não substitui identidade de collection.

## Critérios de aceite

- **AC-001**: fixture de resultados de `pje2g` mapeia campos canônicos e
  preserva `raw`.
- **AC-002**: fixture vazia resulta em página completa sem falso erro.
- **AC-003**: fixture com schema alterado é rejeitada deterministicamente.
- **AC-004**: fixture de erro de parâmetro (core inválido / `per_page` acima do
  limite) é classificada como erro de fonte, não como ausência de resultados.
- **AC-005**: fixture do core `legado` mapeia identidade e datas próprias.
- **AC-006**: paginação de `page=1` para `page=2` preserva contagem e não
  duplica identidades.
- **AC-007**: SDD, lint e suíte local passam sem rede.
- **AC-008**: fixtures de `pje1g` e `turma_recursal_legado` não são aceitas pelo
  binding de segundo grau e não contaminam suas métricas.

## Fora de escopo

Bypass de qualquer controle, uso do Solr interno, rota de detalhe/documento
único não observada, primeiro grau, turma recursal, coleta federada por padrão e
redistribuição antes da revisão das condições de reuso.
