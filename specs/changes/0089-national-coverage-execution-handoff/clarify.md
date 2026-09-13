# Decisões fechadas e perguntas humanas

## Padrões já fechados

1. Sem índice documental persistente.
2. Sem LLM, embeddings ou serviço pago por consulta.
3. Busca live adaptativa e modo explícito “todos os tribunais”.
4. Bloqueios são estados de diagnóstico, nunca vazio.
5. A implementação é independente do Juscraper e usa apenas os contratos
   observados/licenciados como referência.
6. Nenhuma publicação/deploy nesta execução.

## Perguntas que não devem ser inventadas pelo executor

- retenção legal de cópias e inteiro teor;
- responsável humano por cada fonte;
- autorização para uso operacional de coleções selecionadas;
- rótulos de relevância e conjunto holdout;
- abertura de chamado oficial quando a fonte bloqueia acesso público.

## Default técnico

Na ausência de decisão humana, manter provider em `human_review` ou `opt_in`;
continuar apenas testes locais e evidência pública bounded.
