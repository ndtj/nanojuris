# Pesquisa — inteiro teor

Status: in_progress

## Evidência atual

O catálogo declara 27 fontes com algum suporte documental, mas os formatos,
vínculos e limites são heterogêneos. Metadado de resultado não prova que o
documento esteja público, estável ou seguro para download automatizado.

## Decisão orientada

Separar referência, fetch, bytes imutáveis, parser e CanonicalDocument. Download
será explícito e provider-specific.

## Lacunas

- inventário de formatos e tamanhos;
- política de retenção/cache;
- sandbox para parsers;
- regra de licenciamento e redistribuição por fonte.
