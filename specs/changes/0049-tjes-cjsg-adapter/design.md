# Design — Adapter TJES/CJSG

O provider reutiliza a URL configurável `tjes_jurisprudencia_url`, mas possui
identidade própria (`tjes_jurisprudencia`) e fixa o core `pje2g`. A resposta
JSON é convertida em `JurisprudenceResult`; `ementa` alimenta `summary` e
`acordao` alimenta `full_text` quando presentes.

Cada chamada grava em `SourceTrace` o endpoint, query, URL final, status,
content-type, hash, bytes, latência e estado de recuperação. Campos não
conhecidos permanecem no `raw` para tolerar evolução não destrutiva.

O limite remoto conservador é 20 itens. A paginação usa `page`/`per_page` e o
total remoto só é considerado autoritativo quando inteiro e não negativo.
Nenhum retorno HTTP de erro ou corpo incompatível vira lista vazia.

O provider é inicialmente opt-in para busca unificada até revisão de licença e
reuso do acervo. A matriz pode promovê-lo como CJSG somente porque o core
`pje2g` é uma superfície de segundo grau explicitamente identificada.
