# Design

O Workbench continua com busca síncrona e resultados parciais observáveis. O
copy de carregamento comunica uma ação em andamento (“Consultando fontes
públicas...”), sem expor detalhes de infraestrutura ao usuário.

A exportação Excel usa SpreadsheetML 2003 (`.xls`), um XML seguro e legível por
Excel/LibreOffice, gerado no navegador. Isso não adiciona dependência nem
transmite dados a terceiros. Os valores são escapados como texto para impedir
que conteúdo de decisões seja interpretado como fórmula.

Para eliminar cold starts quando houver quota e orçamento, o módulo OCI
Functions recebe um bloco opcional `provisioned_concurrency_config`. O padrão é
`NONE`; `CONSTANT` exige contagem múltipla de 10 (para a memória de 2048 MiB) e
é uma decisão operacional explícita no tfvars.
