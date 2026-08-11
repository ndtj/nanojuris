# Candidate Provider Live Validation

Snapshot: `2026-08-11`. Este relatorio registra a rodada inicial de chamadas
publicas controladas para 28 fontes candidatas. Oito delas foram promovidas
desde entao; o registro atual possui 20 candidatos sem provider runtime. A evidencia e
ambiental e temporal: um HTTP 200 de uma pagina de entrada nao equivale a uma
busca juridica reproduzivel.

As chamadas usaram sessoes HTTP novas, sem login, cookies exportados, proxy,
captcha resolvido, proxy reverso ou bypass de WAF. Para o TJPE, a verificacao
TLS padrao falhou neste ambiente; o JSON foi confirmado apenas com verificacao
desabilitada para diagnostico e nao esta aprovado para uso em producao.

## Classificacao

- `live_valid`: rota de busca, catalogo ou dataset publico retornou conteudo
  juridico/estruturado suficiente para a proxima etapa de fixture.
- `partial`: existe contrato publico util, mas busca, detalhe ou documento ainda
  tem uma lacuna verificavel.
- `blocked_or_inconclusive`: a janela respondeu com bloqueio, captcha, login,
  timeout, erro de transporte ou apenas shell sem contrato decisorio.

## Matriz

| Fonte | Chamada representativa | Resultado observado | Estado |
| --- | --- | --- | --- |
| `cjf_jurisprudencia` | GET TRF1 + POST JSF com `dano moral`/`ACORDAO` | HTTP 200; pagina de resultados, contagem de 7.483 documentos, ementas, processos e links | `live_valid` |
| `cnj_jurisprudencia` | GET `/jurisprudencia?argumento=cartorios` | HTTP 200; HTML paginado com informativos, ementas/resumos e links PDF | `live_valid` |
| `falcao_jt` | GET `https://jurisprudencia.jt.jus.br/` | HTTP 403 CloudFront; sem contrato de busca | `blocked_or_inconclusive` |
| `justica_eleitoral_sjur` | POST TSE `/rest/public/pesquisa/classes` com `["TSE"]` | HTTP 200 JSON; 136 classes. Busca decisoria continua retornando controle antirrobo | `partial` |
| `tjap_tucujuris` | GET pagina Tucujuris | HTTP 200 shell curto, sem sinais de resultado juridico ou contrato | `blocked_or_inconclusive` |
| `tjba_graphql` | POST GraphQL + introspection | HTTP 200; schema, 38 orgaos, 211 relatores e 263 classes. `filter` retornou erro interno nesta janela | `partial` |
| `tjce_cjsg` | GET e-SAJ `resultadoCompleta.do` | EOF TLS antes da resposta | `blocked_or_inconclusive` |
| `tjce_informativos` | GET `/informativo-jurisprudencia/` | HTTP 200; 489 KB de HTML com informativos, ementas, relatores e links documentais | `live_valid` |
| `tjes_jurisprudencia` | GET portal atual e GET rota ColdFusion legada | portal: timeout de 25 s; legado: HTTP 404 | `blocked_or_inconclusive` |
| `tjma_jurisconsult` | GET `lista_relatorios` e catalogos | HTTP 200; relatorios, tipos, classes, magistrados e camaras. Busca principal responde `captcha_not_provided` | `partial` |
| `tjmg_jurisprudencia` | GET formulario; GET busca textual com `dano moral` | formulario HTTP 200; busca HTTP 401 pedindo codigo/captcha | `partial` |
| `tjmt_jurisprudencia_api` | GET portal e API sem chave | portal HTTP 200 redireciona/login; API HTTP 401 | `blocked_or_inconclusive` |
| `tjpa_jurisprudencia_bff` | GET filtros + POST busca `dano moral` | HTTP 200 JSON; catalogos e resultados ricos; limite tecnico informado pelo backend | `live_valid` |
| `tjpb_pje_jurisprudencia` | GET shell, GET catalogos, POST busca, GET detalhe | HTTP 200; total 48.534, 10 hits, campos de ementa/processo e detalhe HTML | `live_valid` |
| `tjpe_jurisprudencia` | GET `/api/v1/jurisprudencias?page=0&size=2` | HTTP 200 JSON com 2 itens e campos ricos somente com `verify_ssl=False` | `partial` |
| `tjpr_jurisprudencia` | GET consulta refinada | HTTP 200 HTML com ementa, relator, orgao, processo e paginacao | `live_valid` |
| `tjrj_eproc_jurisprudencia` | GET formulario + POST `listar_resultados` | HTTP 200; 10 itens com ementa, processo e relator | `live_valid` |
| `tjrn_jurisprudencia` | GET portal | primeira janela HTTP 200; repeticao atual HTTP 403, sem rota de busca estavel | `blocked_or_inconclusive` |
| `tjro_liame` | GET portal LIAME | HTTP 200; catalogo de precedentes/processos, sem busca geral de acordaos confirmada | `partial` |
| `tjrr_juris` | GET + POST JSF com `dano moral` | HTTP 200; resultado com ementa, processo, relator, orgao e paginacao | `live_valid` |
| `tjrs_solr` | POST `ajax.php` com busca `dano moral` | HTTP 200 JSON apesar de content-type legado; `numFound=612.403`, 10 docs, facets e highlighting | `live_valid` |
| `tjsc_eproc_jurisprudencia` | GET formulario + POST `listar_resultados` | HTTP 200; 10 itens com ementa, processo, relator e paginacao | `live_valid` |
| `tjse_jurisprudencia` | GET formulario JSF | HTTP 200 com filtros e ViewState; bundle referencia Cloudflare Turnstile | `partial` |
| `tjto_jurisprudencia` | GET `consulta.php` | HTTP 403 | `blocked_or_inconclusive` |
| `trf3_jurisprudencia` | GET pesquisa | timeout de leitura de 25 s | `blocked_or_inconclusive` |
| `trf5_jurisprudencia` | GET formulario + POST resultado com `dano moral` | HTTP 200; resultado com processo, ementa e inteiro teor | `live_valid` |
| `trt2_pje_jurisprudencia` | GET shell + GET `/api/opcoes` | HTTP 200; opcoes publicas, mas documentos exigem `tokenDesafio`/imagem | `partial` |
| `tcu_jurisprudencia` | GET manifesto + Range no CSV de acordaos | HTTP 200/206; manifesto e schema `KEY|VISAOGERAL`; pesquisa interativa segue firewall | `live_valid` |

## Contratos Aprofundados

### CJF/TRF1

O fluxo atual e JSF/PrimeFaces:

```text
GET  https://jurisprudencia.cjf.jus.br/trf1/index.xhtml
POST https://jurisprudencia.cjf.jus.br/trf1/index.xhtml;jsessionid=<sessao>
```

O POST deve transportar o `javax.faces.ViewState`, o termo em
`formulario:textoLivre`, o tipo em `formulario:selectTiposDocumento` e o
comando `formulario:actPesquisar`. Os resultados exibem processo, classe,
relator, origem, orgao julgador, datas, ementa e links para inteiro teor. A
superficie `/unificada/index.xhtml` deve permanecer separada do parser TRF1.

### TJBA GraphQL

O schema publico confirmou estas operacoes: `filter`, `detalharProcesso`,
`findAllDecisoes`, `findAllOrgaosJulgadores`,
`findAllOrgaosJulgadoresGroupByInstancia`, `findAllRelatores`,
`findAllRelatoresGroupByInstancia` e `findAllClasses`.

`DecisaoFilter` confirmou os campos `assunto`, `numeroRecurso`, `orgaos`,
`relatores`, `classes`, `dataInicial`, `dataFinal`, `segundoGrau`,
`turmasRecursais`, `tipoAcordaos`, `tipoDecisoesMonocraticas` e
`ordenadoPor`. A resposta `Decisao` confirmou id, sourceId, numero/codigo do
processo, orgao, relator, classe, tipo, datas, conteudo, ementa, contentType,
hash e score. Catalogos sem busca retornaram HTTP 200; a busca `filter` deve
ser revalidada com uma combinacao de filtros e valores aceitos pelo backend.

### TJPB/PJe

O bundle publico confirmou:

```text
GET  /api/pje/origens/list
GET  /api/pje/classes/list/<id_origem>
GET  /api/pje/orgaosJulgadores/list/<id_origem>
GET  /api/pje/relatores/list/<id_orgao_julgador>
POST /api/jurisprudencia/pesquisar
GET  /jurisprudencia/view/<id>?words=<termos>
```

O POST usa JSON com `_token`, um objeto `jurisprudencia` e `page`. O objeto
possui `ementa`, `inteiro_teor`, `nr_processo`, `id_classe_judicial`,
`id_orgao_julgador`, `id_relator`, `dt_inicio`, `dt_fim` e `id_origem`.
Retornou `total` e `hits`; cada hit confirmou `_id`, `_score`,
`dt_ementa`, `ementa` e `numero_processo`. O detalhe HTML por `_id` respondeu
HTTP 200 com ementa e processo.

### TJPA

O BFF retornou envelope `{message, data}`. Na busca, `data` confirma
`content`, `totalElements`, `totalAcordaos`, `totalDecisoesMonocraticas`,
`totalPages`, `currentPage`, `size`, `facets`, `consultaUtilizada`,
`excedeuLimiteTecnico`, `limiteMaximo` e `mensagemLimiteTecnico`. Cada item
confirmou processo, tipo, datas, classe, assuntos, orgao, pessoas, ementa,
texto puro, indexacao e score. O provider deve preservar esse envelope e
tratar o limite tecnico como parte do contrato.

### TJRS

O POST legado retorna JSON mesmo declarando `text/html; charset=iso-8859-1`:

```text
action=consultas_solr_ajax
metodo=buscar_resultados
parametros=aba=jurisprudencia&realizando_pesquisa=1&pagina_atual=1
&q_palavra_chave=dano+moral&conteudo_busca=ementa_completa
```

O envelope confirmou `responseHeader`, `response`, `facet_counts`,
`highlighting`, `pages`, `query`, `facets` e `url`; `response.numFound` foi
612.403 e a primeira pagina trouxe 10 documentos. O parser deve decodificar
ISO-8859-1 e preservar facets/highlighting.

### TCU Dados Abertos

O manifesto respondeu 5.945 bytes. O arquivo de resumo de acordaos aceitou
`Range: bytes=0-4095`, retornou HTTP 206 e informou tamanho total de 55.293.296
bytes. O schema inicial confirma `KEY|VISAOGERAL`. Esse canal e implementavel
como sincronizacao incremental independente da pesquisa interativa protegida.

## Lacunas Que Permanecem Intencionais

As lacunas abaixo nao sao falhas de documentacao: sao contratos que a fonte
nao permitiu confirmar em sessao publica limpa nesta janela.

- Falcao, TJAP, TJCE e-SAJ, TJES, TJMT, TJRN, TJTO e TRF3 precisam de nova
  evidencia observavel (ou HAR publico obtido em consulta normal) antes de
  qualquer provider.
- TSE/SJUR, TJMA, TJMG, TJSE, TRT2 e TJBA possuem catalogos/formularios
  publicos, mas busca ou detalhe ainda tem antirrobo, captcha, Turnstile,
  desafio ou erro de contrato.
- TJPE precisa corrigir a cadeia TLS no ambiente de execucao; nunca se deve
  transportar `verify_ssl=False` para o provider.
- Para as fontes com busca valida ainda faltam fixtures sanitizadas, parser
  offline, resultado vazio, erro, paginacao completa e contrato de documento.

## Gate Para Desenvolvimento

Uma fonte so deve sair de candidata quando possuir: rota de busca reproduzida,
payload confirmado, filtros/catalogos, paginacao, estados vazio/erro/bloqueio,
campos canonicos, link de detalhe ou documento quando existir, fixture offline,
teste de contrato e decisao de rate limit. O proximo trabalho recomendado e
implementar primeiro os candidatos `live_valid` com JSON ou contratos HTML
estaveis: TJPB, TJPA, TJRS, TJSC, TJRJ, TRF5, TJRR, CJF/TRF1, TJPR e TCU.
