# Desenho tecnico

## Boundary

`TjesTurmaRecursalProvider` encapsula o endpoint oficial e fixa o core
`turma_recursal_legado`. O provider reutiliza somente a politica HTTP
compartilhada; parser, source id, fixtures e identidade sao proprios.

## Fluxo

1. validar texto, frase exata ou numero;
2. montar `core`, `q`, `page` e `per_page` limitado a 20;
3. chamar com `Accept: application/json` e transporte compartilhado;
4. classificar HTTP sem converter falha em vazio;
5. validar raiz, `docs`, core e janela de pagina;
6. mapear `id`, `num_processo`, `classe_processo`, `nome_juiz`,
   `orgao_julgador`, `data_julgamento` e `cont_ementa`;
7. devolver `SearchPage` com `collection=TURMA_RECURSAL` e trace.

## Seguranca e privacidade

O corpo live nao e persistido. Fixtures usam dados sinteticos. A evidencia
live registra apenas metadados e hash. Licenca, retencao, reuso e promocao
padrao permanecem gates humanos separados.
