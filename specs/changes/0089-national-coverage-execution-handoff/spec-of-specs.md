# Spec of specs — execução da cobertura nacional

ID: `0089-national-coverage-execution-handoff`  
Status: `proposed`  
Data: `2026-09-08`

## Resultado do programa

Entregar a um executor posterior um plano único, auditável e eficiente para
completar a cobertura nacional de jurisprudência do NanoJuris. O programa
abrange tribunais estaduais, trabalhistas, eleitorais, federais, superiores e
militares, além das camadas de inteiro teor, filtros, qualidade, federação e
busca web. Não cria um corpus próprio, não usa IA por consulta e não autoriza
publicação ou deploy.

## Subprogramas

| Trilha | Entrega | Gate independente |
| --- | --- | --- |
| A — fonte única | registro de superfície e provider reconciliado | nenhuma contagem manual ou conflito catálogo/runtime/live |
| B — descoberta | inventário oficial + comparação Juscraper | rota pública ou bloqueio terminal evidenciado |
| C — contrato | grau, coleção, filtros, paginação e campos | contrato verificável por provider |
| D — implementação | adapter, parser, transporte e documentos | testes locais e fixtures sanitizadas |
| E — qualidade | identidade, datas, duplicidade, texto e MIME | quality gate aprovado |
| F — federação | estados por fonte, ranking e traces | smoke federado opt-in e rollout explícito |
| G — operação | freshness, drift, métricas e rollback | certificação contínua sem mascarar falhas |
| H — revisão | licenças, retenção e decisões humanas | registro humano quando necessário |

## Dependências

```text
A -> B -> C -> D -> E -> F -> G
                    \-> H (em paralelo, sem promoção automática legal)
```

Cada provider pode terminar em `federation_enabled`, `opt_in`, `blocked`,
`source_unavailable` ou `human_review`. Bloqueio externo não bloqueia os demais
lotes.

## Fonte de verdade

Os documentos deste pacote orientam o executor; os valores atuais vêm dos
artefatos gerados listados em `execution-manifest.json`. Nunca editar catálogo
gerado manualmente.
