# Research

## Evidência usada

- inventário local `tjsp_jurisprudence_inventory.md` e JSON associado;
- cenários e evidências exportados do REA para SAJ/CJSG e eproc;
- scripts JavaScript exportados do entry point TJSP;
- providers e fixtures existentes em `src/` e `tests/`.

## Observações

- O entry point eproc atual usa `https://eproc1g.tjsp.jus.br/eproc`.
- A busca eproc usa POST em `listar_resultados`; paginação serializa
  `frmJurisprudenciaResultado` e usa `hdnUrlPaginar`.
- O resultado eproc declara `hdnLinkGerarPDF`, e cards de inteiro teor usam
  `download_inteiro_teor`.
- O CJSG usa `resultadoCompleta.do`, `trocaDePagina.do` e `getArquivo.do`.
- O fluxo documental observado passa por `verificarLoginArquivo.jsp` e depois
  repete `getArquivo.do` com `casChecked=true`.
- O formulário CJSG expõe datas de julgamento/publicação, origens e ordenação
  `relevancia`.

## Limitações

As observações são de uma janela de execução e podem mudar na fonte. Nenhuma
observação autoriza contornar controles de acesso ou afirmar cobertura de filtros
que não possuem tradução segura.
