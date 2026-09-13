# Design — TJRO jurisprudência textual

## Estado atual

O runtime possui `tjro_liame` para IRDR/IAC e precedentes qualificados. Este
adapter cobre a superfície textual geral do TJRO, descoberta e validada de modo
independente, sem importar Juscraper em runtime.

## Estratégia

Capturar método, rota, campos, paginação, ordenação e erros em memória; manter
fixture pequena e sanitizada; e mapear cada hit para o contrato canônico. O
identificador original permanece em `raw` e toda chamada produz `SourceTrace`.
Falhas de transporte, bloqueio e schema nunca viram zero resultados.

## Contrato fechado

O endpoint geral é `POST https://juris-back.tjro.jus.br/search/varios_parametros/`.
A busca usa offset `from` base zero, tamanho `size`, texto em `fields.query`,
ordenação por relevância/data e resposta Elasticsearch com `hits.total.value`
e `hits.hits`. `size` é limitado localmente a 100 para manter chamadas
bounded. Datas de atualização, número e relator têm evidência live.

O campo `fields.tipo` apresentou vocabulário divergente e permanece omitido.
`grau_jurisdicao` foi observado no transporte, mas ainda não é filtro canônico.
Classe, órgão e demais refinamentos só entram após contrato e fixtures próprios.

## Inteiro teor e relacionados

O bundle público revelou `GET /pje/buscar_pdf_ou_docx/<sistema_origem>/<id_processo_documento>/<pdf|docx>/`.
O adapter implementa `get_document`, `get_decisions` e `fetch_details=True`,
preservando bytes, hash, URL e `SourceTrace`. A rota
`GET /search/documentos_relacionados/<id_documento_principal>` é exposta
somente sob demanda, sem fan-out automático. Facetas (`POST /search/agregacoes`)
foram confirmadas, mas aguardam modelo canônico e política de retenção.

## Federação

Após os gates locais e a rechecagem live bounded, `supports_unified_search=True`
e o provider foi registrado na lista padrão do `NanoJurisClient`. A federação
usa somente o contrato mínimo confirmado; o roteador emite avisos para filtros
sem evidência e mantém a separação de `tjro_liame`.

## Segurança

Somente superfícies públicas e chamadas bounded são usadas. Nenhum CAPTCHA,
WAF, login, rate limit ou controle de acesso é contornado. Os gates globais de
release/licença continuam revisão externa e não autorizam deploy.
