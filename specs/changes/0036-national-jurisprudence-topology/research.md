# Pesquisa — topologia nacional

## Linha de base

O catálogo atual possui 56 fontes, 46 runtime, 42 unificadas e foco forte nos
TJs. A rodada de reconciliação acrescentou os 27 TREs e os três tribunais de
justiça militar estaduais (TJMMG, TJMSP e TJMRS), elevando o inventário de
autoridades de tribunal para 94. Algumas instituições possuem múltiplas
superfícies; outras entradas são famílias técnicas ou contexto administrativo.

## Fonte institucional da rodada

O diretório oficial de Tribunais do Conselho Nacional de Justiça foi consultado
em 2026-09-01 (`https://www.cnj.jus.br/poder-judiciario/tribunais/`). A resposta
HTTP 200 foi verificada com User-Agent identificável; o conteúdo bruto não foi
persistido. A contagem textual reproduzível encontrou 27 Tribunais Regionais
Eleitorais, três Tribunais de Justiça Militar estaduais, seis Tribunais
Regionais Federais e 24 Tribunais Regionais do Trabalho. O hash e os metadados
da captura estão em `docs/topology/cnj-tribunal-register-20260901.json`.

Uma verificação pública adicional das URLs-raiz dos 27 TREs e três TJMs
retornou HTTP 200 para TJMMG e TJMRS e HTTP 403 para TJMSP e os 27 TREs no
ambiente da auditoria. O resultado foi classificado como `reachable` ou
`access_controlled` em `docs/topology/court-catalog-url-probe-20260901.json`;
403 não foi convertido em ausência, zero resultados ou provider bloqueado
permanente.

## Risco identificado

Contar source IDs como tribunais superestima cobertura institucional e
subestima collections ausentes. Contar um TJ como coberto por precedentes não
prova que sua jurisprudência textual esteja pesquisável.

## Evidência necessária

Atos e páginas oficiais de estrutura institucional, catálogos das collections e
source contracts já versionados. O diretório CNJ sustenta a existência das
autoridades, mas não prova disponibilidade de uma API de jurisprudência para
cada uma delas. Discovery live continua necessário antes de promover providers.
