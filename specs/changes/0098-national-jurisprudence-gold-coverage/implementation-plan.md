# Plano de implementação por ondas

## Onda 0 — baseline e reconciliação

Regenerar catálogo, ledger, matriz de grau, registro de superfícies, programa
estadual, manifest de promoção, auditoria de tarefas e fixtures. Corrigir apenas
divergências de geração; nunca editar artefatos derivados manualmente.

## Onda 1 — contratos transversais

Fechar `SearchPage`, `ProviderCapabilities`, estados de total/acesso, filtros
remotos/locais/ignorados, datas, `DocumentReference`, `SourceTrace` e envelope
federado. Esta onda não cria adapters novos.

## Onda 2 — primeiro grau

Trabalhar em lotes de três superfícies: bancos de sentenças, ementários e
coleções CJPG. Validar explicitamente `degree=first`, limites de cobertura e
diferença entre fonte curada e acervo geral.

## Onda 3 — segundo grau estadual

Revalidar os cinco workpacks completos; depois APIs públicas; depois portais e
eproc; por fim bloqueios e candidatos. A ordem detalhada está em
`provider-family-matrix.md`.

## Onda 4 — federal, superior, eleitoral e trabalhista

Fechar separadamente TRF/STJ/STF/STM/CJF/TNU, TST/TRTs e TSE/TRE/SJUR. Não
misturar coleções apenas porque compartilham tecnologia (PJe, eproc, Solr ou
GraphQL).

## Onda 5 — documentos e qualidade ouro

Adicionar detalhe sob demanda, PDF/HTML, MIME, hash, texto, OCR permitido,
proveniência por campo, validação de CNJ, deduplicação e benchmark jurídico.

## Onda 6 — federação adaptativa

Integrar somente providers elegíveis, expor estados por fonte, preservar cursor,
completude, latência e filtros, e manter `all` como opção explícita.

## Onda 7 — operação contínua

Smoke live periódico de baixa frequência, fingerprints de schema, ETag,
stale-if-error identificado, circuit breaker, alertas, shadow mode e rollback de
parser.

## Onda 8 — gates humanos e release

Revisar licença, termos, retenção, owner, frequência, segurança e promoção.
Publicação/deploy só depois de autorização explícita e pacote de release.

## Definition of Done por superfície

Fonte oficial, contrato de coleção/grau, adapter, fixtures de sucesso/vazio/
erro/bloqueio, paginação, filtros, chamada live bounded, qualidade canônica,
documento validado quando disponível, teste federado e decisão de promoção.

