# Spec-of-specs — cobertura nacional ouro

## Propósito

Decompor a promessa de “toda a jurisprudência brasileira” em superfícies
verificáveis: `authority + branch + degree + instance + collection`. Um adapter
ou uma resposta HTTP 200 isolada nunca representa uma superfície completa.

## Pacotes

| Pacote | Escopo | Gate de saída |
| --- | --- | --- |
| G0 | Baseline e fonte única de verdade | catálogo, runtime, live e federação reconciliados |
| G1 | Inventário nacional | todas as autoridades e coleções obrigatórias mapeadas |
| G2 | Descoberta de fonte oficial | rota ou exportação pública documentada, ou bloqueio terminal |
| G3 | Contrato do provider | filtros, paginação, datas, erros e campos reproduzíveis |
| G4 | Adapter e parser | implementação independente, transporte comum e fixtures |
| G5 | Documentos | resumo/ementa/inteiro teor com MIME, hash e proveniência |
| G6 | Qualidade canônica | grau, identidade, datas, deduplicação e validações |
| G7 | Federação | estado por fonte, filtros aplicados e completude auditável |
| G8 | Operação | smoke bounded, drift, métricas, cache efêmero e rollback |
| G9 | Governança | licença, retenção, frequência, owner e aprovação humana |

G0–G8 são trabalho técnico; G9 não pode ser simulado por um agente. Cada
superfície deve fechar seus gates individualmente.

## Decomposição por famílias

1. TJs estaduais: CJPG, CJSG, ementários, bancos de sentenças, eproc/PJe,
   informativos e turmas recursais.
2. TRTs/TST: jurisprudência trabalhista e coleções de acórdãos/ementários.
3. TRFs/STJ/STF/STM/CJF/TNU: jurisprudência superior, federal e militar.
4. TSE/TREs: SJUR, acórdãos e decisões eleitorais, sem misturar consultas
   processuais ou prestação de contas.
5. TCEs e órgãos especializados: somente quando houver texto jurídico público
   e contrato explícito de coleção.

## Fora de escopo

- consulta processual, DataJud, movimentações, partes ou timelines;
- conteúdo privado, segredo de justiça ou login não autorizado;
- resolução automatizada de CAPTCHA/Turnstile ou evasão de WAF;
- corpus documental pesquisável localmente como índice próprio;
- embeddings, LLM ou reranking pago por consulta;
- publicação, deploy ou alteração de produção.

## Invariantes

1. `access_blocked`, `timeout`, `rate_limited`, `schema_invalid` e
   `source_unavailable` nunca viram `authoritative_empty`.
2. Primeiro e segundo grau são superfícies distintas.
3. Fonte contextual ou curada não conta como acervo geral.
4. Todo registro aceito conserva `source_trace`, `raw` relevante e motivo de
   ausência dos campos.
5. O catálogo gerado não é editado manualmente.
6. Promoção exige os oito gates técnicos e uma decisão humana quando indicada.
7. A comparação com Juscraper é técnica e contratual; nenhum código é copiado
   sem análise de licença e implementação independente.

