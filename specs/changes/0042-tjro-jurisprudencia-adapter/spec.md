# 0042 — adapter de jurisprudência textual do TJRO

Status: verified
Owner: Provider Engineering, Legal Data, Security e QA

## Intenção

Adicionar a busca geral de jurisprudência textual do Tribunal de Justiça de
Rondônia como fonte independente de `tjro_liame`, que representa somente
precedentes qualificados.

## Contrato mínimo confirmado

A superfície oficial `https://juris-back.tjro.jus.br/search/varios_parametros/`
responde JSON por `POST` sem credenciais. O corpo usa `from` (offset base zero),
`size`, `fields.query`, ordenação, `token` e `highlight`; a resposta usa
`hits.total.value` e `hits.hits`. Paginação e `size=1/100` foram reproduzidos;
o limite remoto máximo permanece desconhecido e o adapter aplica teto local de
100. Datas de atualização, número e relator têm chamadas live reproduzíveis.

O campo `fields.tipo` tem contrato divergente e não é enviado. O transporte
aceita `grau_jurisdicao`, mas classe, grau, órgão e tipo ainda não são filtros
canônicos até haver vocabulário e fixtures suficientes.

## Requisitos

- REQ-001: confirmar rota, método, payload, paginação e limites em fonte oficial;
- REQ-002: manter `tjro_jurisprudencia` e `tjro_liame` como coleções e
  identidades independentes;
- REQ-003: mapear campos canônicos, preservar `raw`, bytes e `SourceTrace`;
- REQ-004: diferenciar ausência de resultados de bloqueio, timeout e schema drift;
- REQ-005: não importar Juscraper em runtime nem contornar controles de acesso;
- REQ-006: incluir somente a busca textual confirmada na federação padrão;
- REQ-007: manter inteiro teor e documentos relacionados sob demanda bounded.

## Critérios de aceite

- AC-001: contrato público reproduzível e fixture própria de sucesso;
- AC-002: fixtures negativas cobrem vazio confirmado, erro, acesso e schema drift;
- AC-003: busca federada registra TJRO textual sem reclassificar LIAME;
- AC-004: identidade e completude são testadas;
- AC-005: gates locais de qualidade e segurança passam antes da integração;
- AC-006: download público de inteiro teor tem parser, hash, bytes, URL e erro;
- AC-007: chamada federada live bounded confirma HTTP 200 e registro canônico.

## Fora de escopo

Consulta processual, LIAME como substituto da busca geral, crawling em escala,
credenciais, facetas sem modelo de retenção e produção/deploy.
