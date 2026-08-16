# `trf4_eproc_jurisprudencia`

## Identidade e escopo

- Fonte oficial: busca publica de jurisprudencia eproc/TRF4.
- Categoria: `court_jurisprudence`.
- Familia tecnica: formulario HTML eproc + resposta HTML paginada + download HTML.
- URL de pesquisa: `https://eproc-jur.trf4.jus.br/eproc2trf4/externo_controlador.php?acao=jurisprudencia@jurisprudencia/pesquisar`.
- Status no NanoJuris: provider implementado, com busca e inteiro teor.
- Escopo: TRF4, TRU4, Turmas Recursais e Varas Federais conforme a origem
  selecionada no formulario.

O portal institucional do TRF4 descreve a pesquisa por origem, texto integral
ou ementa, processo, relator, data, orgao julgador, classe e tipo decisorio.
O provider deve manter a diferenca entre a superficie institucional e o
endpoint eproc reproduzido.

## Canais publicos observados

| Canal | Metodo | Finalidade | Estado |
| --- | --- | --- | --- |
| `...@jurisprudencia/pesquisar` | `GET` | formulario e listas de filtros | observado |
| `...@jurisprudencia/listar_resultados` | `POST` | primeira busca e HTML de resultados | implementado |
| `...@jurisprudencia/ajax_paginar_resultado` | `POST` | troca de pagina por AJAX | rota observada; replay estavel pendente |
| `...@jurisprudencia/download_inteiro_teor&id_jurisprudencia=<id>` | `GET` | inteiro teor | implementado |
| link `resultado_pesquisa.php` do TRF4 | `GET` | consulta processual relacionada | URL preservada, nao seguida automaticamente |
| `...@jurisprudencia/ajax_listar_tipo_documento` | `POST` | dependencias de origem/tipo documental | observado no JavaScript; nao necessario para busca minima |
| `...@jurisprudencia/ajax_carregar_listas_pesquisa` | `POST` | carregar listas de filtros | observado no formulario; nao promovido como provider catalog |

O NanoJuris nao utiliza cookies pessoais, login, captcha, WAF bypass, proxy de
contorno ou automacao de navegador para atravessar bloqueios.

## Formulario de pesquisa

Rota inicial:

```text
GET https://eproc-jur.trf4.jus.br/eproc2trf4/externo_controlador.php
    ?acao=jurisprudencia@jurisprudencia/pesquisar
```

Campos e controles observados no `frmJurisprudenciaPesquisa`:

| Campo | Tipo | Valores/uso |
| --- | --- | --- |
| `txtPesquisa` | texto | termo de busca |
| `rdoCampo` | radio | `I` = inteiro teor; `E` = ementa |
| `txtProcesso` | texto | numero do processo, enviado sem pontuacao pelo adapter |
| `selOrigem[]` | multi-select | `1` TRF4, `2` TRU4, `3` Turmas Recursais, `4` Varas Federais |
| `selTipoDocumento[]` | multi-select | `1` acordao, `2` decisao monocratica, `4` despacho/decisao da Vice-Presidencia |
| `chkPrecedenteRelevante` | checkbox | restringe a precedente relevante |
| `chkAgruparResultados` | checkbox | agrupa resultados relacionados |
| `chkCaput` | checkbox | controle adicional de campo textual observado no formulario |
| `selClasse[]` | multi-select | lista de classes processuais; 174 opcoes na pesquisa inicial e 196 no resultado observado |
| `dtDecisaoInicio/Fim` | data | intervalo de julgamento |
| `dtPublicacaoInicio/Fim` | data | intervalo de publicacao |
| `selRelator[]` | multi-select | relator; 255 opcoes na pesquisa inicial e 343 no resultado observado |
| `selOrgao[]` | multi-select | orgao julgador; 34 opcoes na pesquisa inicial e 72 no resultado observado |
| `ckbFiltroassunto_principal[]` | checkbox | assuntos sugeridos pelo resultado/filtro |

Os campos `hdnDecisaoInicio`, `hdnDecisaoFim`, `hdnPublicacaoInicio` e
`hdnPublicacaoFim` acompanham os campos de data no postback. Os campos
`hdnExibirPesquisaAvancada` e `hdnUrlCarregarListasCombobox` sao controles de
interface e nao devem ser confundidos com filtros canonicos.

## Contrato de busca e paginacao

Busca minima:

```text
POST https://eproc-jur.trf4.jus.br/eproc2trf4/externo_controlador.php
     ?acao=jurisprudencia@jurisprudencia/listar_resultados
Content-Type: application/x-www-form-urlencoded
```

O provider compartilha o builder eproc com TJSP e envia atualmente texto,
campo (`rdoCampo`), numero, datas, tipos, origens e agrupamento. Os filtros
`selClasse[]`, `selRelator[]`, `selOrgao[]`, assunto, precedente relevante e
caput estao documentados como contrato observado, mas ainda nao sao expostos
por `JurisprudenceQuery` neste provider.

O resultado HTML informa:

- `hdnTotalResultado`: total remoto; exemplo observado: `1734331`;
- `hdnTotalPaginas`: total de paginas;
- `hdnPaginaAtual`: pagina 1-based;
- `selTamanhoPagina`: valores `10`, `25`, `50` e `100`;
- `hdnUrlPaginar`: `externo_controlador.php?acao=jurisprudencia@jurisprudencia/ajax_paginar_resultado`.

O primeiro `POST` aceita `selTamanhoPagina` e devolve os cards da pagina
solicitada. O JavaScript oficial monta a troca de pagina serializando o
`frmJurisprudenciaResultado` e fazendo `POST` para `hdnUrlPaginar`. Um replay
isolado da rota AJAX retornou a moldura de resultados sem cards, portanto o
provider nao declara essa rota como paginacao implementada ate que um fixture
de sessao limpa com campos completos seja versionado.

Essa distinção evita reportar `total=len(cards)` como total nacional. No estado
atual, a busca do provider e uma pagina valida, e o `SearchPage.total` ainda e
uma contagem da resposta parseada, nao o total remoto do TRF4.

## Dados e mapeamento canonico

Cada resultado usa `.resultadoItem`. O parser reconhece:

| Origem HTML | Campo canonico/raw |
| --- | --- |
| `a.numero-processo` | `number` / `case_number` |
| `.resValueTipoJurisprudencia` | `type` / `decision_type_label` |
| label `PROCESSO` | `raw.case_class` e processo |
| label `UF` | `raw.state` |
| label `ORGAO JULGADOR` | `raw.judging_body` |
| label `DATA DO JULGAMENTO` | `raw.judgment_date` |
| label `DATA DA PUBLICACAO` | `publication_date` e `raw.publication_date` |
| label `RELATOR` | `rapporteur` |
| label `DECISAO` ou `EMENTA` | `summary` |
| `a.inteiroTeor[data-link]` | `raw.full_text_url` |
| `a.numero-processo[data-link]` | `raw.document_url`/URL processual |
| checkbox `.chkDocumento` | `id_jurisprudencia` |

O portal pode entregar mojibake quando a codificacao ISO-8859-1 nao e
interpretada corretamente. O provider define a codificacao da resposta e o
parser normaliza labels conhecidos, mas deve manter o valor bruto quando o
campo nao puder ser normalizado sem perda.

## Inteiro teor

```text
GET https://eproc-jur.trf4.jus.br/eproc2trf4/externo_controlador.php
    ?acao=jurisprudencia@jurisprudencia/download_inteiro_teor
    &id_jurisprudencia=<id>
```

O endpoint retornou HTML publico em validacao real. `get_document` produz
`CanonicalDocument` com `content_type=text/html`; `get_decisions` produz
`DecisionBundle`. O texto deve ser buscado sob demanda por MCP, preservando
`id_jurisprudencia`, URL e `SourceTrace`.

## Tipos e filtros no modelo atual

Filtros atualmente suportados pelo provider: `text`, `exact_phrase`,
`number`, `published_from`, `published_to`, `updated_from`, `updated_to`,
`types` e `source_origins`.

Mapeamentos de tipo: `acordao -> 1`, `monocratica -> 2`, `despacho -> 4`,
`sentenca -> 5` e `sumula -> 3` quando a fonte aceitar o valor. Mapeamentos de
origem: `colegio_recursal -> 3`, `primeiro_grau -> 4`, `segundo_grau -> 5`.
Os valores oficiais devem prevalecer sobre aliases textuais.

## Estados, limites e erros

| Estado | Comportamento |
| --- | --- |
| resultado | cards parseados e links preservados |
| zero resultado | formulario de resultados sem cards retorna lista vazia |
| HTTP 401/403, captcha ou login | `AccessControlRequiredError` |
| HTTP 429 | `RateLimitDetectedError` |
| HTTP 5xx/erro de rede | `SourceUnavailableError` |
| HTML sem `.resultadoItem` e sem estado vazio reconhecivel | `ParserContractChangedError` |
| inteiro teor nao localizado | erro de fonte, sem bypass |

O portal permite pagina tamanho 10/25/50/100. O NanoJuris deve limitar
consultas interativas, aplicar rate limit e evitar varreduras sem termo ou
filtro. O total remoto deve ser exposto somente quando for parseado do campo
oficial; caso contrario, a resposta deve dizer que a contagem e parcial.

## Evidencia live

Em 2026-08-11/12, uma busca publica por `aposentadoria` respondeu HTTP 200,
com cards HTML, `hdnTotalResultado=1734331`, quatro tamanhos oficiais de
pagina, 174/196 classes observadas, 255/343 relatores e 34/72 orgaos conforme
a etapa da pagina. O inteiro teor de um resultado respondeu HTML publico com
mais de 41 mil caracteres. A rota AJAX de paginacao foi identificada no
JavaScript e precisa de fixture de replay completo antes de ser ativada.

## Fixtures e testes

- [x] card com processo, classe, relator, orgao e datas;
- [x] busca com payload POST e numero CNJ;
- [x] inteiro teor por `id_jurisprudencia`;
- [x] detecao de bloqueio sem bypass;
- [ ] fixture real sanitizada com total remoto e `selTamanhoPagina`;
- [ ] fixture de pagina vazia;
- [ ] fixture de replay da rota `ajax_paginar_resultado`;
- [ ] fixture de filtros classe/relator/orgao/assunto;
- [ ] parser de total remoto no provider;
- [ ] catalogos oficiais de classes, relatores e orgaos.

## Uso pelo MCP

O MCP deve expor o TRF4 como fonte federal com `source=trf4_eproc_jurisprudencia`
e informar origem, tipo, campo textual, pagina, tamanho, amostra e limitacao
de contagem. Ao abrir inteiro teor, deve chamar o documento por ID e retornar
o link oficial. Se a pergunta exigir classe, relator, orgao, assunto ou
precedente relevante, o agente deve dizer que esses filtros foram observados
na fonte, mas ainda nao foram convertidos no contrato unificado do provider.

## Proximos passos

1. versionar fixture sanitizada com total remoto e tamanhos oficiais;
2. fechar fixture de pagina vazia e replay da rota AJAX de paginacao;
3. separar filtros observados de filtros efetivamente enviados pelo provider;
4. promover catalogos de classes, relatores e orgaos somente com contrato
   reproduzido e teste offline.

## Referencias oficiais

- [Pesquisa de Jurisprudencia TRF4](https://www.trf4.jus.br/trf4/controlador.php?acao=pagina_visualizar&id_pagina=3938)
- [Formulario publico eproc/TRF4](https://eproc-jur.trf4.jus.br/eproc2trf4/externo_controlador.php?acao=jurisprudencia@jurisprudencia/pesquisar)
