# ADR — recuperação live sem índice próprio

ID: `ADR-0077-001`
Status: `accepted`
Data: `2026-09-07`

## Contexto

O produto precisa melhorar a relevância sem assumir banco de busca, pipeline de
ingestão, retenção de corpus ou custo permanente de indexação.

## Decisão

Recuperar candidatos exclusivamente das fontes oficiais durante a consulta.
Somente cache efêmero, não pesquisável, com TTL de 5–15 minutos é permitido.

## Alternativas consideradas

- OpenSearch/Elasticsearch gerenciado.
- PostgreSQL FTS/pgvector.
- SQLite FTS por usuário.
- corpus nacional pré-coletado.

Todas foram rejeitadas por decisão explícita do produto. Podem ser reavaliadas
em outro SDD, mas não como desvio deste programa.

## Consequências

### Positivas

- menor custo fixo e menor complexidade operacional;
- resultados permanecem ligados à fonte oficial;
- nenhuma migração ou retenção de corpus.

### Negativas

- recall limitado à janela e ao motor de cada tribunal;
- latência dependente de fontes externas;
- não há estatística global de corpus nem busca sem fontes disponíveis.

## Evidência e revisão

- Mudança: SDD 0077.
- Revisar somente se a qualidade do top 10 passar, mas recall continuar
  insuficiente para metas formais do produto.
