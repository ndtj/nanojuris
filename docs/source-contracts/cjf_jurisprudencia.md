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

Cada registro da rota `/trf1/index.xhtml` preserva a identidade canônica
comprovada pelo escopo oficial: `authority=TRF1`, `branch=federal`,
`degree=second`, `instance=second` e `collection=JURISPRUDENCIA`. Quando o
cartão HTML não repete o grau, essa origem é registrada em `field_provenance`
como escopo da rota, e não inferida por texto livre.

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

### Rechecagem bounded de acesso (2026-09-01, ciclo 8)

Uma abertura GET publica da rota TRF1 respondeu HTTP 200, mas o HTML continha
marcadores `captcha` e `recaptcha` e nao apresentou tabela de resultados. A
rodada foi classificada como `blocked_access`; nenhum POST com ViewState foi
enviado depois do desafio e nenhum resultado foi convertido em vazio. Hash,
tamanho e limites estao registrados em
`docs/provider-discovery/cjf-trf1-live-recheck-20260901-cycle8.json`.

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
link externo. URLs observadas podem ser buscadas sob demanda pelo pipeline
compartilhado; respostas sem contrato de documento continuam sendo rejeitadas.

## Fixtures e criterio de promocao

- `tests/fixtures/cjf_trf1_success.html` cobre formulario, resultado, ementa,
  link externo, identidade estavel e datas separadas;
- `tests/fixtures/cjf_trf1_empty.html` cobre zero resultado;
- `tests/fixtures/cjf_trf1_access_control.html` cobre controle de acesso;
- `tests/fixtures/cjf_trf1_contract_changed.html` cobre mudanca de contrato;
- `tests/fixtures/cjf_trf1_document.html` cobre documento HTML extraido;

- [x] fixture TRF1 de formulario com ViewState normalizado;
- [x] fixture de resultados com ementa e links PJe/arquivo;
- [x] fixture vazia, acesso controlado e contrato alterado;
- [ ] fixture separada da superficie unificada;
- [x] parser offline resiliente a IDs dinamicos;
- [x] teste de identidade estavel, datas separadas e preservacao da origem;
- [ ] teste live opt-in com pagina pequena.

- [x] rechecagem bounded 2026-09-01 registrada como `blocked_access`, sem corpo
  live ou bypass de controle de acesso;

O provider deve ser separado em `cjf_trf1_jurisprudencia` e, se o contrato
unificado for confirmado, `cjf_jurisprudencia_unificada`; nao juntar as duas
superficies em um parser sem discriminacao de origem.

## Proximos passos

1. Criar fixture offline do formulario TRF1 com `javax.faces.ViewState`
   substituido por marcador estavel.
2. Criar fixture reduzida de resultado com pelo menos um item com link PJe e
   um item com link de arquivo publico, preservando origem, orgao e datas.
3. Reproduzir a superficie unificada em sessao limpa e decidir se ela vira
   provider separado ou apenas fonte candidata.
4. Adicionar teste de paginacao com preservacao de `source_court`, impedindo
   mistura entre CJF, TRF1, JEF1 e superficie unificada.
5. Validar `get_document` separando contratos PJe, arquivo HTML e arquivo
   binario; respostas sem texto extraivel devem permanecer como erro explicito.
6. Rodar teste live opt-in com termo juridico pequeno e registrar no dossie a
   data, HTTP status, total declarado e estado de acesso.

7. Repetir a captura somente quando houver uma pagina publica sem desafio e
   contrato JSF reproduzivel; ate la, manter o status operacional bloqueado.

## Validacao live 2026-08-11

- GET TRF1 e POST JSF com `dano moral`/`ACORDAO` retornaram HTTP 200, 7.483 documentos, ementas, processos e links de inteiro teor.
- O POST usa `formulario:textoLivre`, `formulario:selectTiposDocumento`, `formulario:actPesquisar` e `javax.faces.ViewState` dinamico.
- A superficie unificada e a superficie TRF1 responderam HTTP 200, mas permanecem contratos separados.

Evidencia detalhada: [candidate-live-validation-2026-08-11.md](https://github.com/ndtj/nanojuris/blob/main/docs/candidate-live-validation-2026-08-11.md).

## Referencias oficiais

- [Entrada da Jurisprudencia do CJF](https://jurisprudencia.cjf.jus.br/index.xhtml)
- [Jurisprudencia do TRF1 no CJF](https://jurisprudencia.cjf.jus.br/trf1/index.xhtml)
- [Perguntas frequentes do TRF1 sobre pesquisa de jurisprudencia](https://www.trf1.jus.br/trf1/ouvidoria/perguntas-frequentes)

## Transporte compartilhado (2026-09-08)

As rotas JSF de pesquisa usam o `SharedHttpClient` com allowlist de
`jurisprudencia.cjf.jus.br` e `pje2g.trf1.jus.br`, limite de 4 MB, timeout,
rate limit e circuit breaker. GET e POST preservam o ViewState da sessão sem
replay automático de POST; 401/403/429, timeout, TLS, redirecionamento fora da
allowlist, HTML de controle e schema inválido permanecem estados explícitos,
nunca resultados vazios.
