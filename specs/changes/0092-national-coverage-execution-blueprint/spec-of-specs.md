# Spec-of-specs — cobertura nacional ouro

## Propósito

Decompor a promessa de cobertura nacional em pacotes verificáveis por
superfície (`authority + branch + degree + instance + collection`), sem contar
um adapter genérico, uma consulta processual ou uma resposta HTTP 200 como
jurisprudência textual.

## Pacotes compostos

| Pacote | Entrega | Gate de saída |
| --- | --- | --- |
| C1 Registro | registro único e reconciliação catalog/runtime/live/federation | cada superfície tem estado e evidência |
| C2 Contrato | filtros, campos, paginação, datas, documentos e erros | contrato reproduzível ou bloqueio explícito |
| C3 Descoberta | fonte oficial, rotas públicas e comparação Juscraper | rota classificada sem copiar código |
| C4 Adapter | parser NanoJuris independente e transporte comum | runtime executável com fixture |
| C5 Qualidade | identidade, grau, texto, datas, deduplicação e fixtures | quality gate aprovado |
| C6 Federação | planner, filtros por provider, completude e diagnóstico | smoke opt-in sem falso vazio |
| C7 Documentos | detalhe, MIME, hash, extração, OCR permitido | `DocumentReference` rastreável |
| C8 Operação | smoke periódico, TTL, drift, métricas e rollback | alerta e rollback testados |
| C9 Governança | licença, retenção, owner e decisão humana | revisão humana registrada |

Cada pacote pode ser executado para um lote de 1–3 providers e deve fechar sua
própria evidência. C1–C6 são técnicos; C7 depende da disponibilidade dos
documentos; C8 exige configuração operacional; C9 não pode ser decidido por um
modelo.

## Fora de escopo

- consulta processual, DataJud, movimentações, partes e timelines;
- contorno de controles de acesso;
- ingestão de corpus para índice próprio;
- embeddings, LLM ou reranking pago por consulta;
- publicação, deploy e alteração de produção;
- afirmar 27/27 enquanto houver gate ausente.

## Invariantes

1. `access_blocked`, `timeout`, `rate_limited`, `schema_invalid` e
   `source_unavailable` nunca viram `authoritative_empty`.
2. Primeiro e segundo grau são superfícies distintas.
3. Fonte curada, precedente ou contextual não conta como acervo geral.
4. Todo registro aceito possui `source_trace` e preserva campos `raw` relevantes.
5. O catálogo gerado nunca é editado manualmente.
6. Um provider somente entra na federação com os oito gates do registro de
   promoção.
