# Design

`tools/build_state_appellate_program.py` consome a matriz canonica gerada por
`tools/build_degree_coverage.py`. A matriz continua responsavel por identidade e
estado; o novo artefato apenas converte cada lacuna em um workpack uniforme.

O workpack usa oito gates ordenados:

1. `official_source` - rota oficial e limites identificados;
2. `degree_contract` - prova de que a superficie publica segundo grau;
3. `adapter` - provider registrado com contrato de erros explicito;
4. `fixtures` - sucesso, vazio, parametro invalido e schema drift;
5. `pagination_filters` - pagina 2, ordenacao e filtros comprovados;
6. `live_validation` - chamada bounded com conteudo juridico valido;
7. `quality` - identidade, grau, colecao, trace e deduplicacao;
8. `federation` - roteamento habilitado somente apos os gates anteriores.

O estado atual conclui somente gates que a matriz prova diretamente. Um
provider `implemented` conclui contrato/adapter/live/qualidade; um provider
existente mas `pending_contract` conclui apenas descoberta de fonte; bloqueios
preservam a pesquisa feita e exigem rechecagem legitima; ausencia de provider
mantem descoberta e implementacao abertas.

Saidas:

- `docs/coverage/state-appellate-program-20260905.json` para automacao;
- `docs/coverage/state-appellate-program-20260905.md` para revisao humana.

O programa nao altera automaticamente o runtime nem a lista federada.
