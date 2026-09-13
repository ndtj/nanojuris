# Design — busca federada

## Pipeline

    SearchIntent
      -> CapabilityPlanner
      -> ProviderQueryPlan[]
      -> bounded execution
      -> per-source pages/outcomes
      -> identity matching
      -> deterministic merge
      -> FederatedSearchPage + completeness map

## Ranking

`source_native_score` fica namespaced. O default global ordena por campo
comparável solicitado (por exemplo data) e chave estável. Relevância global só
pode existir após modelo calibrado, benchmark explícito e opt-in.

## Paginação

O cursor global referencia versão do planner, query fingerprint e posições por
fonte. Mudança de capability invalida o cursor em vez de retornar sequência
silenciosamente diferente.

## Explicabilidade

Cada fonte registra query enviada, filtros omitidos/transformados,
post-filtering, ordering, páginas, deadline e motivo de incompletude.
