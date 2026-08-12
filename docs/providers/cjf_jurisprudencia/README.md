# `cjf_jurisprudencia`

## Identidade

- Fonte oficial: Jurisprudencia do Conselho da Justica Federal.
- Superficies observadas: Jurisprudencia Unificada e Jurisprudencia do TRF1.
- Categoria: `court_jurisprudence`.
- Familia tecnica: `jsf_primefaces_jurisprudencia`.
- Entrada: `https://jurisprudencia.cjf.jus.br/index.xhtml`.
- Rotas especificas: `/unificada/index.xhtml` e `/trf1/index.xhtml`.
- Status observado: busca publica reproduzida em sessao limpa em 2026-08-11.
- Status no NanoJuris: implementado para a superficie TRF1; unificada ainda separada.

## Contrato observado

As paginas sao aplicacoes JSF/PrimeFaces. O cliente deve abrir a pagina,
preservar a sessao publica e enviar o `javax.faces.ViewState` atual junto com
o formulario. Nao ha necessidade de login no fluxo observado.

Para TRF1, o formulario principal declara:

```text
formulario:textoLivre
formulario:lista_resumida_input
formulario:ckbAvancada_input
formulario:selectTiposDocumento
formulario:j_idt62
formulario:actPesquisar
javax.faces.ViewState
```

Os tipos documentais observados incluem `ACORDAO`, `SUMULA`, `ARGUICAO` e
`DECISAOMONO`; as fontes incluem `TRF1` e `JEF1`. A superficie unificada
declara STF, STJ, TNU, TRF1, TRF2, TRF3, TRF4, TRF5, TR e TRU.

## Evidencia live

Em 2026-08-11, o fluxo TRF1 com `dano moral` e `ACORDAO` retornou:

- HTTP 200;
- 25.783 documentos encontrados, exibindo 30 na primeira pagina;
- numero de processo, classe, relator, origem, orgao julgador, datas,
  fonte de publicacao e ementa;
- links de inteiro teor para PJe2G ou para o arquivo publico do TRF1.

A busca observada retornou, por exemplo, o processo
`1001321-42.2024.4.01.3300`, com ementa e metadados decisorios. Esse numero
serve apenas como evidencia tecnica da sessao, nao como fixture obrigatoria.

## Campos canonicos

- `process_number`;
- `class_name`;
- `reporting_judge`;
- `origin`;
- `judging_body`;
- `judgment_date` e `publication_date`;
- `publication_source`;
- `summary`;
- `document_url`;
- `raw` com o HTML e a identificacao da instancia.

## Limites e riscos

- `javax.faces.ViewState` e dinamico e deve ser obtido a cada busca.
- IDs JSF como `j_idt75` e `j_idt253` podem mudar; o parser deve localizar
  labels e componentes por estrutura, nao por um unico ID.
- A busca unificada pode agrupar tribunais e tipos diferentes; o provider
  deve preservar `source_court` e nao misturar a origem com TRF1.
- Links PJe e arquivo podem ter contratos documentais distintos. `get_document`
  deve permanecer separado ate cada rota ser testada individualmente.
- A pagina retorna resultados volumosos; o provider deve limitar pagina,
  `page_size` e velocidade de coleta.

## MCP

Usar quando a pergunta pedir jurisprudencia federal do TRF1 ou pesquisa
unificada do CJF. O agente deve explicar a instancia, informar que a fonte
retorna ementas e metadados oficiais e preservar a URL do inteiro teor. Nao
deve salvar ViewState, cookies ou `jsessionid` como configuracao persistente.

## Implementacao 2026-08-11

`CjfJurisprudenciaProvider` abre `/trf1/index.xhtml`, extrai o ViewState da
sessao atual e envia a pesquisa JSF com termo e tipo documental. O parser usa
as tabelas semanticas `table.table_resultado` e os labels oficiais para
normalizar numero, classe, relator, origem, orgao, datas, ementa, decisao e
link externo. A rota individual de inteiro teor permanece fora do contrato
executavel.

## Fixtures e criterio de promocao

- [ ] fixture TRF1 de formulario com ViewState normalizado;
- [ ] fixture de resultados com ementa e links PJe/arquivo;
- [ ] fixture vazia e fixture de erro JSF;
- [ ] fixture separada da superficie unificada;
- [x] parser offline resiliente a IDs dinamicos;
- [ ] testes de paginacao e de preservacao da origem;
- [ ] teste live opt-in com pagina pequena.

O provider deve ser separado em `cjf_trf1_jurisprudencia` e, se o contrato
unificado for confirmado, `cjf_jurisprudencia_unificada`; nao juntar as duas
superficies em um parser sem discriminacao de origem.

## Validacao live 2026-08-11

- GET TRF1 e POST JSF com `dano moral`/`ACORDAO` retornaram HTTP 200, 7.483 documentos, ementas, processos e links de inteiro teor.
- O POST usa `formulario:textoLivre`, `formulario:selectTiposDocumento`, `formulario:actPesquisar` e `javax.faces.ViewState` dinamico.
- A superficie unificada e a superficie TRF1 responderam HTTP 200, mas permanecem contratos separados.

Evidencia detalhada: [candidate-live-validation-2026-08-11.md](https://github.com/ndtj/nanojuris/blob/main/docs/candidate-live-validation-2026-08-11.md).

## Referencias oficiais

- [Entrada da Jurisprudencia do CJF](https://jurisprudencia.cjf.jus.br/index.xhtml)
- [Jurisprudencia do TRF1 no CJF](https://jurisprudencia.cjf.jus.br/trf1/index.xhtml)
- [Perguntas frequentes do TRF1 sobre pesquisa de jurisprudencia](https://www.trf1.jus.br/trf1/ouvidoria/perguntas-frequentes)
