# Threat model — adapters externos

| Ameaça | Impacto | Controle |
| --- | --- | --- |
| importar bypass ou credencial | crítico | deny gate e revisão Security |
| copiar bug upstream | alto | differential/golden tests |
| violar atribuição | alto | ledger, NOTICE e review |
| trocar rota madura por alternativa pior | alto | baseline e rollback |
| misturar processo com jurisprudência | alto | collection/source ID separados |
| dependência pesada no runtime | médio | adaptação sem pandas/Juscraper |
