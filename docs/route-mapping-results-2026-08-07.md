# Route Mapping Results - 2026-08-07

Rodada inicial de mapeamento de rotas publicas de jurisprudencia, usando sessao
HTTP limpa e sem cookies exportados do navegador. `idpj` foi usado apenas como
um dos termos de smoke test; a bateria recomendada por ramo esta em
[route-mapping-playbook.md](route-mapping-playbook.md).

## Resumo executivo

| Fonte | Rota | Resultado | Decisao |
| --- | --- | --- | --- |
| TST frontend | `GET https://jurisprudencia.tst.jus.br/` | HTTP 200, SPA publica, sem captcha/login | contrato oficial confirmado |
| TST config | `GET /config.json` | HTTP 200 JSON com `base_url`, URLs de acordao, despacho e processo | contrato oficial confirmado |
| TST backend | `POST /rest/pesquisa-textual/1/2` com payload textual publico | HTTP 200 JSON com `totalRegistros`, `registros`, `agregacoes`, ementa, dispositivo e metadados | `implemented`; monitorar contrato live |
| TST documento | `GET /rest/documentos/{id}` usando `registro.id` | HTTP 200 HTML com ementa, relatorio, fundamentacao e dispositivo | `implemented`; detalhe sob demanda |
| CJF/TRF1 hub | `GET https://www2.cjf.jus.br/jurisprudencia/trf1` | entrada antiga redireciona para CJF; a rota especifica atual `/trf1/index.xhtml` respondeu com busca JSF real na rodada de 2026-08-11 | consultar a secao federal complementar e o dossie CJF |
| TRF3 | `GET https://web.trf3.jus.br/jurisprudencia/home/index/1` | timeout ja registrado em tentativas HTTP limpas | nao repetir a mesma chave; usar captura automatica ou rota oficial alternativa |
| TRF5 | `GET https://jurisprudencia.trf5.jus.br/jurisprudencia/pesquisa.wsp` | timeout na rodada inicial; GET e POST do formulario responderam com resultados na rodada de 2026-08-11 | consultar a secao federal complementar e o dossie TRF5 |
| TJMG formulario | `GET /jurisprudencia/formEspelhoAcordao.do` | HTTP 200, formulario rico, campos e actions publicas | candidato forte para contrato, mas sem busca direta |
| TJMG palavras | `GET /jurisprudencia/pesquisaPalavrasEspelhoAcordao.do?palavras=idpj` | HTTP 401 com captcha | bloqueado para automacao; nao implementar bypass |
| TJRJ portal | `GET /web/portal-conhecimento/consulta-a-jurisprudencia` | HTTP 200, pagina institucional com links e menu de login | candidato documental, nao provider de resultados |
| TJRJ eJURIS | `GET /EJURIS/ConsultarJurisprudencia.aspx` | HTTP 200 formulario rico com reCAPTCHA | bloquear provider de busca enquanto depender de reCAPTCHA |
| TJPR jurisprudencia | `GET /jurisprudencia/publico/pesquisa.do?actionType=pesquisarRefinado&filtro=true` | HTTP 200, HTML com resultados, ementa, relator, orgao julgador e paginacao | promover para contrato e fixture |
| TJBA frontend | `GET https://jurisprudencia.tjba.jus.br/` | HTTP 200, SPA publica | usar para descobrir contrato |
| TJBA GraphQL | `POST https://jurisprudenciaws.tjba.jus.br/graphql` | HTTP 200 JSON estruturado com `decisoes`, `ementa`, `numeroProcesso`, `relator`, `orgaoJulgador` | promover para provider P0 |
| TJSC/eproc | `GET https://eprocwebcon.tjsc.jus.br/consulta1g/externo_controlador.php?acao=jurisprudencia@jurisprudencia/pesquisar` | HTTP 200, formulario eproc publico, sem captcha/login na pagina inicial | promover para contrato de familia eproc |
| TJSC portal historico | `GET https://busca.tjsc.jus.br/jurisprudencia/#formulario_ancora` | HTTP 200, pagina antiga com aviso de transicao | manter como fonte historica/documental |
| TJSC teses | `GET https://busca.tjsc.jus.br/juris-teses/#/listar` | HTTP 200 SPA curta | investigar API/bundle antes de provider |
| TJRS portal | `GET https://www.tjrs.jus.br/novo/buscas-solr/?aba=jurisprudencia` | HTTP 200, portal publico com iframe de jurisprudencia | usar como entrada documental |
| TJRS iframe | `GET https://www.tjrs.jus.br/buscas/jurisprudencia/` | HTTP 200, app publica com contrato Angular/SOLR | usar para descobrir payload |
| TJRS AJAX/SOLR | `POST https://www.tjrs.jus.br/buscas/jurisprudencia/ajax.php` | HTTP 200, JSON/SOLR com `response.numFound`, `response.docs`, facets e highlighting | promover para provider P0 |
| TNU/eproc | `POST https://eproctnu.cjf.jus.br/eproc/externo_controlador.php?acao=jurisprudencia@jurisprudencia/listar_resultados` | HTTP 200, HTML eproc com `resultadoItem`, processo, ementa, relator e inteiro teor | promover como extensao da familia eproc |
| TRF6/eproc | `POST https://eproc-jur.trf6.jus.br/eproc/externo_controlador.php?acao=jurisprudencia@jurisprudencia/listar_resultados` | HTTP 200, HTML eproc com resultados reais e bases TRF6/TRU6/Turmas/Varas | promover como extensao da familia eproc |
| TRF2/eproc | `POST https://eproc.trf2.jus.br/eproc/externo_controlador.php?acao=jurisprudencia@jurisprudencia/listar_resultados` | HTTP 200, HTML eproc com `resultadoItem`, numero CNJ, ementa/decisao, relator, orgao e inteiro teor | promover como P0 na familia eproc |
| TRF2 legado | `GET https://juris.trf2.jus.br/consulta.php?...` | falha DNS no ambiente atual, apesar de paginas publicas indexadas | nao promover; preferir eproc/TRF2 |
| CJF/TRF1 hub | `GET https://www2.cjf.jus.br/jurisprudencia/trf1/index.xhtml` | redireciona para `jurisprudencia.cjf.jus.br`, hub publico de jurisprudencia unificada/TNU/TRF1/CJF | documentar como entrada, nao provider de resultados |
| TRF1 ementario | `GET https://www.trf1.jus.br/trf1/pesquisa/ementario-de-jurisprudencia` | HTTP 200, catalogo documental paginado com ementarios | manter como rota documental/catalogo |
| TJGO/Projudi | `POST https://projudi.tjgo.jus.br/ConsultaJurisprudencia` | HTTP 200, HTML com mais de 1M resultados, processo, magistrado, orgao, decisao e inteiro teor no proprio card | promover para contrato HTML P0; download separado ainda pendente |
| TJMA/Jurisconsult metadados | `GET https://apijuris.tjma.jus.br/v1/jurisprudencia/lista_relatorios` | HTTP 200 JSON com relatorios e URLs tecnicas de acordaos, monocraticas, sumulas e sentencas | promover contrato parcial/metadados |
| TJMA/Jurisconsult busca | `GET https://apijuris.tjma.jus.br/v1/sg/jurisprudencias/processos?...` sem token | HTTP 400 JSON `captcha_not_provided` | nao automatizar busca principal sem fluxo publico limpo |
| TJAP/Tucujuris | `GET https://tucujuris.tjap.jus.br/tucujuris/pages/consultar-jurisprudencia/consultar-jurisprudencia.html` | Cloudflare/challenge no HTML limpo | bloquear provider enquanto exigir desafio |
| STM | `GET https://jurisprudencia.stm.jus.br/` | HTTP 200, portal publico JMU com sinais juridicos e inteiro teor | manter provider existente e aprofundar contrato |
| TSE/SJUR metadados | `POST https://sjur-pesquisa-api.tse.jus.br/tse/sjur-pesquisa-backend/rest/public/pesquisa/classes` | HTTP 200 JSON com classes eleitorais; endpoint semelhante para relatorias | documentar contrato parcial P1 |
| TREs/SJUR metadados | `POST https://sjur-pesquisa-api.tse.jus.br/tres/sjur-pesquisa-backend/rest/public/pesquisa/classes` | HTTP 200 JSON com classes por TRE; exemplo `TRE-SP` validado | documentar contrato parcial P1 |
| TSE/SJUR busca | `POST /public/pesquisa` | HTTP 200 JSON com mensagem de falha antirrobo, sem resultados | bloquear provider de decisoes ate fluxo limpo |
| TRT2/PJe jurisprudencia | `GET https://pje.trt2.jus.br/jurisprudencia/` e `GET /juris-backend/api/opcoes` | SPA publica e JSON de opcoes; busca/documentos retornam desafio `tokenDesafio`/`imagem` | documentar contrato parcial; nao coletar documentos |
| TRT15/TRT23 PJe | `GET /jurisprudencia/` | HTTP 403 CloudFront/request blocked em sessao limpa | bloquear provider |
| Basis/TRT2 | `GET https://basis.trt2.jus.br/discover?query=teletrabalho` | HTTP 200, repositorio DSpace com boletins, atos e doutrina | rota documental, nao provider de decisoes |
| TJAC/e-SAJ CJSG | `GET https://esaj.tjac.jus.br/cjsg/resultadoSimples.do?...` | HTTP 200 com processo, ementa, relator, orgao, datas e inteiro teor | confirmar fonte forte CJSG |
| TJCE/e-SAJ CJSG | `GET https://esaj.tjce.jus.br/cjsg/resultadoCompleta.do` | pagina oficial de consulta confirmada; HTTP direto deste ambiente sofreu reset TLS | `candidate_needs_har`; dossie proprio criado |
| TJES portal atual | `GET https://sistemas.tjes.jus.br/portaltj/Pesquisa.aspx` | timeout em 45s | inconclusivo; repetir com janela maior |
| TJES ColdFusion antigo | `GET https://aplicativos.tjes.jus.br/sistemaspublicos/consulta_jurisprudencia/det_jurisp.cfm?...` | HTTP 404 no ambiente atual, apesar de resultados antigos indexados | nao promover sem nova rota |
| TJMT jurisprudencia | `GET https://jurisprudencia.tjmt.jus.br/` | HTTP 200 SPA publica; bundle expoe API Hellsgate, metadados e relatorios | candidato forte, contrato de payload/header pendente |
| TJMT API inferida | `GET https://hellsgate-preview.tjmt.jus.br/jurisprudencia/api/consulta/1` | HTTP 401 `No API key found in request`; portal atual redireciona para `/ui/login` | `blocked_or_inconclusive`; nao usar login |
| TJPA jurisprudencia | `GET https://jurisprudencia.tjpa.jus.br/` | HTTP 200, portal publico; bundle atual expoe BFF de busca, catalogos e detalhes | candidato pronto para fixture |
| TJPA BFF busca | `POST https://jurisprudencia.tjpa.jus.br/bff/api/decisoes/buscar` | HTTP 200 JSON com resultados, facetas, campos decisorios e limite tecnico | `candidate_ready`; parser JSON pendente |
| TJPB/PJe jurisprudencia | `GET https://pje-jurisprudencia.tjpb.jus.br/` | HTTP 200 com formulario rico, campos juridicos e paginacao; outro cliente recebeu Cloudflare challenge | candidato forte com risco WAF |
| TJPE jurisprudencia | `GET https://consultajurisprudencia.app.tjpe.jus.br/api/v1/jurisprudencias?page=0&size=20` | HTTP 200, JSON paginado com decisoes, ementas/acordaos e metadados | `candidate_ready`; consultar dossie REST |
| TJPE sumulas | `GET https://portal.tjpe.jus.br/servicos/consulta/sumulas` | HTTP 200, sumulas e PDFs publicos | candidato de catalogo/precedentes |
| TJPE transparencia decisoes | `GET https://portal.tjpe.jus.br/web/transparencia/decis%C3%B5es` | HTTP 200, orienta DJEN/DJE/PJe e Consulta Jurisprudencia Web | rota documental/orientacao |
| TJPI/JusPI busca | `GET https://jurisprudencia.tjpi.jus.br/jurisprudences/search?q=dano%20moral` | HTTP 200 com resultados reais, CNJ, ementa, relator, orgao e paginacao | promover para fixture/parser HTML |
| TJRO/LIAME | `GET https://liame.tjro.jus.br/` | HTTP 200, portal de precedentes; probe marcou acesso por texto de UI, sem decisoes | candidato de precedentes, nao acordaos |
| TJRR/Juris | `GET` + `POST https://jurisprudencia.tjrr.jus.br/index.xhtml` com `menuinicial:j_idt28=dano moral` e comando `menuinicial:j_idt30` | HTTP 200, HTML com resultados reais, processo, ementa/acordao, relator e orgao; repeticao posterior sofreu timeout | `candidate_ready`; fixture e parser JSF pendentes |
| TJSE jurisprudencia judicial | `GET` do portal + `GET` do iframe de pesquisa | HTTP 200, formulario JSF/PrimeFaces com filtros ricos; resultado exige captcha | entrada oficial; manter bloqueado ate HAR limpo |

## Revalidacao complementar em 2026-08-10

Esta secao registra uma segunda bateria de probes, posterior ao mapeamento
original acima. Ela nao apaga o historico: paginas de formulario e rotas de
resultado podem ter comportamentos diferentes na mesma fonte.

| Fonte | Rota/metodo | Resultado | Decisao atual |
| --- | --- | --- | --- |
| TJRJ/eproc | `POST https://eproc1g.tjrj.jus.br/eproc/externo_controlador.php?acao=jurisprudencia@jurisprudencia/listar_resultados` com `txtPesquisa=dano moral` e `rdoCampo=I` | HTTP 200, 10 cards `resultadoItem`, processo, classe, orgao, datas e links de inteiro teor | `candidate_ready`; criar provider separado do eJURIS |
| TJRJ/eJURIS | `GET https://www3.tjrj.jus.br/ejuris/ConsultarJurisprudencia.aspx` | HTTP 200, formulario rico e texto juridico; busca de resultados ainda depende de contrato WebForms proprio | manter em investigacao; nao confundir com eproc |
| TJMG ajuda | `GET https://www5.tjmg.jus.br/jurisprudencia/ajuda.do` | HTTP 200, documentacao oficial detalhada de campos e inteiro teor | ficha de contrato, nao evidencia de busca automatizavel |
| TJMG busca | `GET https://www5.tjmg.jus.br/jurisprudencia/pesquisaPalavrasEspelhoAcordao.do?palavras=dano%20moral` | HTTP 401, pagina de captcha | bloqueado; nao implementar bypass |
| TJSC/eproc | `GET https://eprocwebcon.tjsc.jus.br/consulta1g/externo_controlador.php?acao=jurisprudencia@jurisprudencia/pesquisar` | HTTP 200, formulario publico | contrato candidato pronto; ver secao e dossie proprio |
| TJSC/eproc busca | `POST .../listar_resultados` com `txtPesquisa=dano moral` | HTTP 200, HTML com 475.091 documentos, cards, metadados e links de inteiro teor | `candidate_ready`; fixture e parser offline pendentes |

O probe TJRJ/eproc foi executado sem identidade privada, cookies exportados,
captcha ou desafio de navegador. O parser generico eproc conseguiu extrair os
cards em um teste exploratorio, mas isso nao substitui fixture, testes offline
e validacao do inteiro teor.

## Achados tecnicos

### TST

Rota de configuracao limpa:

```text
GET https://jurisprudencia.tst.jus.br/config.json
```

Campos observados:

- `base_url`: `https://jurisprudencia-backend2.tst.jus.br`
- `consulta_acordao_url`
- `consulta_despacho_url`
- `consulta_proc_url`
- `consulta_proc_pje_url`

Contrato central observado no bundle publico e reproduzido com filtro textual:

```text
POST {base_url}/rest/pesquisa-textual/{inicio}/{limite}?a=<random>
Content-Type: application/json
```

Payload com `e=responsabilidade civil` e `tipos=["ACORDAO"]` retornou JSON real com:

- `tempoGasto`
- `totalRegistros`
- `registros`
- `agregacoes`
- `registro.id`
- `registro.numero`
- `registro.tipo`
- `registro.orgao`
- `registro.nomRelator`
- `registro.numFormatado`
- `registro.dtaPublicacao`
- `registro.ementa`, `registro.dispositivo`
- `registro.inteiroTeorHtml`
- `registro.numeracaoUnica`, `registro.orgaoJudicante` e datas
- `registro.id`, usado em `/rest/documentos/{id}`

Decisao: TST e candidato pronto para fixture/parser. Antes de implementar o
provider, salvar uma resposta reduzida de sucesso, uma resposta vazia, o
documento HTML correspondente e os erros de contrato.

### TJMG

Formulario publico:

```text
GET https://www5.tjmg.jus.br/jurisprudencia/formEspelhoAcordao.do
```

Actions observadas:

```text
GET /jurisprudencia/pesquisaNumeroCNJEspelhoAcordao.do
GET /jurisprudencia/pesquisaPalavrasEspelhoAcordao.do
```

Campo principal:

```text
palavras
```

Teste direto por palavras retornou HTTP 401 com captcha. Decisao: documentar
contrato do formulario, mas nao automatizar busca enquanto a rota de resultado
exigir captcha.

### TJRJ

Rotas oficiais observadas:

```text
GET https://www.tjrj.jus.br/web/portal-conhecimento/consulta-a-jurisprudencia
GET https://www3.tjrj.jus.br/EJURIS/ConsultarJurisprudencia.aspx?Version=1.1.19.1
```

O eJURIS entrega formulario rico, com campos juridicos objetivos, mas inclui
reCAPTCHA. Decisao: nao promover busca automatizada sem fluxo publico limpo.

### TJPR

Rota publica validada:

```text
GET https://portal.tjpr.jus.br/jurisprudencia/publico/pesquisa.do?actionType=pesquisarRefinado&filtro=true
```

Sinais observados:

- HTTP 200 em sessao limpa;
- pagina de resultado com "RESULTADO DA PESQUISA";
- campos juridicos objetivos: relator, orgao julgador, ementa, acordao e
  identificadores processuais;
- paginacao e volume total de registros;
- ausencia de captcha/login no teste inicial.

Decisao: TJPR deve entrar no proximo ciclo de implementacao como provider HTML
P0. O primeiro passo tecnico e salvar fixture publica representativa com uma busca multi-area
(`dano moral`, `plano de saude`, `execucao fiscal`) e criar parser offline antes
do fetcher live.

### TJBA

Frontend publico:

```text
GET https://jurisprudencia.tjba.jus.br/
```

Backend observado no bundle publico:

```text
POST https://jurisprudenciaws.tjba.jus.br/graphql
Content-Type: application/json
```

Consulta GraphQL observada:

```graphql
query filter($decisaoFilter: DecisaoFilter!, $pageNumber: Int!, $itemsPerPage: Int!) {
  filter(
    decisaoFilter: $decisaoFilter
    pageNumber: $pageNumber
    itemsPerPage: $itemsPerPage
  ) {
    decisoes {
      dataPublicacao
      relator { id nome }
      orgaoJulgador { id nome }
      classe { id descricao }
      conteudo
      tipoDecisao
      ementa
      hash
      numeroProcesso
    }
    relatores { key value }
    orgaos { key value }
    classes { key value }
    pageCount
    itemCount
  }
}
```

Campos de filtro observados:

- `assunto`
- `numeroRecurso`
- `relator`
- `orgao`
- `classe`
- `segundoGrau`
- `turmasRecursais`
- `tipoAcordaos`
- `tipoDecisoesMonocraticas`
- `publicacoesDe`
- `publicacoesAte`
- `dataInicial`
- `dataFinal`
- `ordenadoPor`
- `orgaos`
- `relatores`
- `classes`

Teste com `assunto="dano moral"` retornou JSON juridico real com `decisoes`,
`numeroProcesso`, `ementa`, relator, orgao julgador, classe e conteudo. Decisao:
TJBA e a melhor rota nova da rodada para provider estruturado, porque entrega
GraphQL sem captcha/login e com campos canonicos diretos.

### TJSC

Pagina oficial:

```text
GET https://www.tjsc.jus.br/web/tjsc/pesquisa-jurisprudencia
```

Rota final validada por redirecionamento oficial:

```text
GET https://eprocwebcon.tjsc.jus.br/consulta1g/externo_controlador.php?acao=jurisprudencia@jurisprudencia/pesquisar
```

Sinais observados:

- HTTP 200 em sessao limpa;
- pagina de jurisprudencia eproc;
- filtros por base/origem, tipo, ementa, inteiro teor, caput, classe e periodo;
- ausencia de captcha/login no formulario inicial;
- bom potencial de reuso com familia `eproc`.

Tambem foi localizada a rota historica:

```text
GET https://busca.tjsc.jus.br/jurisprudencia/#formulario_ancora
```

Ela informa transicao para a plataforma integrada ao eproc. Decisao: priorizar
o eproc como provider principal e manter a rota antiga apenas como referencia
historica ou fallback documental.

Na validacao atual, o eproc do TJSC foi reproduzido com sessao HTTP limpa:

```text
POST https://eprocwebcon.tjsc.jus.br/consulta1g/externo_controlador.php?acao=jurisprudencia@jurisprudencia/listar_resultados
```

Payload minimo:

```text
txtPesquisa=dano moral
rdoCampo=I
hdnExibirPesquisaAvancada=
chkAgruparResultados=on
```

O retorno foi HTTP 200, HTML `iso-8859-1`, 10 cards `.resultadoItem`, total
de 475.091 documentos e campos de processo, classe, tipo documental, orgao,
relator, datas e texto decisorio. O link `download_inteiro_teor` com
`id_jurisprudencia` retornou HTTP 200 e HTML publico. O TJSC foi promovido para
`candidate_ready`; a ficha completa esta em
`docs/source-contracts/tjsc_eproc_jurisprudencia.md`.

### TJRS

Entrada publica no portal:

```text
GET https://www.tjrs.jus.br/novo/buscas-solr/?aba=jurisprudencia
```

O portal renderiza um iframe publico:

```text
GET https://www.tjrs.jus.br/buscas/jurisprudencia/?q_palavra_chave=dano%20moral&aba=jurisprudencia&q=dano%20moral&site=ementario
```

O iframe carrega uma aplicacao Angular que chama:

```text
POST https://www.tjrs.jus.br/buscas/jurisprudencia/ajax.php
Content-Type: application/x-www-form-urlencoded
```

Payload minimo validado:

```text
action=consultas_solr_ajax
metodo=buscar_resultados
parametros=aba=jurisprudencia&realizando_pesquisa=1&pagina_atual=1&q_palavra_chave=dano+moral&conteudo_busca=ementa_completa
```

Resposta observada:

- JSON/SOLR retornado como `text/html; charset=iso-8859-1`;
- `responseHeader.params`;
- `response.numFound`;
- `response.docs`;
- facets por `orgao_julgador`, `origem`, `relator_redator`,
  `ano_julgamento`, `nome_classe_cnj`, `nome_assunto_cnj`,
  `nome_tribunal`, `tipo_processo`, `mes_ano_publicacao` e
  `data_publicacao`;
- highlighting para ementa/inteiro teor;
- links de processo e documento montados no frontend.

Decisao: TJRS deve ser promovido a P0 junto de TJBA. Ele combina contrato
estruturado, alto volume, facets juridicas e resposta rapida. O parser deve
normalizar JSON com charset legado e preservar facets em `raw_metadata`.

### TNU e TRF6/eproc

Rotas publicas validadas na mesma familia tecnica do eproc:

```text
GET  https://eproctnu.cjf.jus.br/eproc/externo_controlador.php?acao=jurisprudencia@jurisprudencia/pesquisar
POST https://eproctnu.cjf.jus.br/eproc/externo_controlador.php?acao=jurisprudencia@jurisprudencia/listar_resultados

GET  https://eproc-jur.trf6.jus.br/eproc/externo_controlador.php?acao=jurisprudencia@jurisprudencia/pesquisar
POST https://eproc-jur.trf6.jus.br/eproc/externo_controlador.php?acao=jurisprudencia@jurisprudencia/listar_resultados
```

Payload minimo validado:

```text
txtPesquisa=aposentadoria
rdoCampo=I
hdnExibirPesquisaAvancada=
chkAgruparResultados=on
```

Sinais observados:

- HTTP 200 em sessao limpa;
- formulario publico sem captcha/login no fluxo testado;
- `resultadoItem` nos resultados;
- numero CNJ, classe, relator, orgao, ementa/decisao e links de inteiro teor;
- TNU com origem unica `TNU`;
- TRF6 com origens `TRF6`, `TRU6`, Turmas Recursais e Varas Federais.

Decisao: TNU, TRF2 e TRF6 devem entrar como P0 por reuso do parser/fetcher eproc ja
existente. O proximo passo tecnico e parametrizar o provider eproc por
instancia, preservando `source`, `court`, base URL, origens disponiveis e tipos
documentais.

### TRF2/eproc e CJF/TRF1

Rota publica TRF2/eproc validada:

```text
GET  https://eproc.trf2.jus.br/eproc/externo_controlador.php?acao=jurisprudencia@jurisprudencia/pesquisar
POST https://eproc.trf2.jus.br/eproc/externo_controlador.php?acao=jurisprudencia@jurisprudencia/listar_resultados
```

Payload minimo validado:

```text
txtPesquisa=aposentadoria
rdoCampo=I
hdnExibirPesquisaAvancada=
chkAgruparResultados=on
```

Sinais observados:

- HTTP 200 em sessao limpa;
- formulario publico "Jurisprudencia Justica Federal da 2a Regiao";
- origens `TRF2`, `TRU2` e Turmas Recursais;
- tipos documentais `Acordao`, `Decisao monocratica`, `Sumula`,
  `Despacho/Decisao da Vice-Presidencia` e `Sentenca`;
- resultados com `resultadoItem`, numero CNJ, relator, orgao, ementa/decisao e
  link de inteiro teor;
- ausencia de captcha/login no fluxo testado.

A rota legada `juris.trf2.jus.br` falhou DNS no ambiente atual. Como o eproc
TRF2 respondeu com conteudo juridico completo, a decisao tecnica e promover
TRF2 pela familia `eproc_jurisprudencia` e manter o legado apenas como nota de
pesquisa.

Tambem foram testadas entradas CJF/TRF1:

```text
GET https://www2.cjf.jus.br/jurisprudencia/trf1/index.xhtml
GET https://www.trf1.jus.br/trf1/pesquisa/ementario-de-jurisprudencia
```

O primeiro redireciona para um hub de jurisprudencia unificada/TNU/TRF1/CJF. O
segundo retorna ementario documental paginado. Decisao: documentar como rotas de
entrada/catalogo, mas nao implementar como provider de decisoes ate localizar
endpoint de resultado limpo.

### TJGO/Projudi

Entrada oficial observada em fontes publicas:

```text
GET https://projudi.tjgo.jus.br/ConsultaJurisprudencia
```

Contrato de busca validado:

```text
POST https://projudi.tjgo.jus.br/ConsultaJurisprudencia
Content-Type: application/x-www-form-urlencoded

PaginaAtual=2
PosicaoPaginaAtual=0
Viewstate=
Texto=dano moral
Id_Instancia=0
Id_Area=0
Id_ServentiaSubTipo=0
Id_Serventia=
Id_Usuario=
Id_ArquivoTipo=
ProcessoNumero=
DataInicial=
DataFinal=
g-recaptcha-response=
Localizar=Consultar
```

Resultado observado:

- HTTP 200 em sessao limpa;
- `1357643 resultados encontrados para o filtro da pesquisa` no teste com
  `dano moral`;
- resultados com numero CNJ, classe, magistrado/relator, unidade/orgao, data de
  julgamento e texto da decisao;
- texto integral aparece no proprio HTML de resultado;
- botao `Baixar Inteiro teor` referencia `Id_Arquivo`, mas o probe separado de
  download sem token voltou ao formulario.

Decisao: TJGO deve ser promovido como provider HTML P0 com extracao inicial a
partir dos cards de resultado. A rota de download deve ficar pendente ate haver
contrato limpo sem token/captcha. O diagnostico `probe-rota` foi ajustado para
nao classificar como bloqueio uma pagina que contem scripts globais de
Cloudflare/Turnstile mas entrega resultados juridicos reais.

### TJMA/Jurisconsult

Frontend publico:

```text
GET https://jurisconsult.tjma.jus.br/#/sg-jurisprudence-list
```

Host API observado no bundle publico:

```text
https://apijuris.tjma.jus.br/v1
```

Endpoints auxiliares validados:

```text
GET /jurisprudencia/lista_relatorios
GET /jurisprudencia/lista_todos_tipos_pesquisa?tipoRelatorio=1
GET /jurisprudencia/lista_todos_camaras?tipoRelatorio=1
GET /jurisprudencia/links_pesquisa_sumulas
```

`/jurisprudencia/lista_relatorios` retornou relatorios e rotas tecnicas:

- `/sg/jurisprudencias/processos` para acordaos;
- `/jurisprudencia/processos/pesquisa_acordaos_tr`;
- `/jurisprudencia/processos/pesquisa_monocraticas`;
- `/jurisprudencia/processos/pesquisa_monocraticas_tr`;
- `/jurisprudencia/links_pesquisa_sumulas`;
- `/jurisprudencia/processos/sentencas_pg`;
- `/jurisprudencia/processos/sentencas_je`.

Teste da busca principal sem token:

```text
GET /sg/jurisprudencias/processos?chave=dano%20moral&tipoPesquisa=1&dtaInicio=2020-01-01&dtaFim=2026-08-07&tokenG=&keyId=
```

Resultado: HTTP 400 JSON `{"error":"captcha_not_provided"}`.

Decisao: promover apenas o contrato parcial de metadados e links de sumulas/IAC/
IRDR. Nao implementar busca de acordaos/sentencas enquanto depender de captcha.

### TSE e TREs/SJUR

Frontends publicos:

```text
GET https://jurisprudencia.tse.jus.br/
GET https://jurisprudencia-tres.tse.jus.br/
```

O bundle publico revelou o host tecnico:

```text
https://sjur-pesquisa-api.tse.jus.br/{tribunal}/sjur-pesquisa-backend/rest/public/pesquisa
```

O placeholder `{tribunal}` foi observado como:

- `tse` para jurisprudencia do TSE;
- `tres` para o agregador dos TREs.

Endpoints auxiliares observados:

```text
POST /classes
POST /relatorias
POST /eleicoes
POST /normas
POST /download/
POST /pesquisaTokenValidado
POST /livre
POST /simples
POST /rede
```

Payloads de metadados validados:

```json
["TSE"]
```

```json
["TRE-SP"]
```

Sinais observados:

- `POST /classes` e `POST /relatorias` retornam JSON publico com classes e
  relatores;
- exemplos de classes: `RESPE`, `AI`, `REspEl`, `AREspEl`;
- a busca principal `POST /public/pesquisa` respondeu com mensagem de falha
  antirrobo e `content=[]`;
- a rota `/livre` testada com payload simples retornou 404 no ambiente atual.

Decisao: contrato parcial P1 para metadados eleitorais publicos. Nao promover
provider de decisoes enquanto a busca principal depender de token/antirrobo ou
validacao humana.

### TRT2/PJe jurisprudencia e Basis

Frontend publico TRT2:

```text
GET https://pje.trt2.jus.br/jurisprudencia/
```

Endpoints observados no bundle:

```text
GET  /juris-backend/api/opcoes
POST /juris-backend/api/filtros
POST /juris-backend/api/documentos
GET  /juris-backend/api/token
```

Sinais observados:

- `GET /opcoes` retorna JSON publico com regional, versao, URL de consulta PJe
  e configuracao de captcha;
- `POST /filtros` com payload incompleto retorna erro de parametros;
- `POST /documentos` retorna `tokenDesafio` e `imagem` em vez de documentos no
  fluxo limpo;
- `GET /token` retornou HTTP 200 sem conteudo util no probe.

Decisao: documentar contrato parcial e bloquear provider de documentos enquanto
o fluxo exigir desafio por imagem/token. O diagnostico `probe-rota` deve marcar
esse retorno como `access_control_or_login`, nao como rota valida.

Rota documental relacionada:

```text
GET https://basis.trt2.jus.br/discover?query=teletrabalho
```

O Basis/TRT2 e um repositorio DSpace publico com boletins, atos normativos,
doutrina e materiais correlatos. Pode virar provider documental ou de boletins,
mas nao deve ser confundido com busca de decisoes completas.

### TJAC/e-SAJ CJSG e TJCE

TJAC/CJSG validado:

```text
GET https://esaj.tjac.jus.br/cjsg/consultaCompleta.do
GET https://esaj.tjac.jus.br/cjsg/resultadoSimples.do?conversationId=&nuProcOrigem=0700309-51.2015.8.01.0001&nuRegistro=
```

Sinais observados:

- HTTP 200 em sessao limpa;
- formulario CJSG completo;
- resultado com numero CNJ, ementa, relator, orgao julgador, data de julgamento
  e publicacao;
- link/conteudo de inteiro teor publico.

Decisao: fonte forte da familia e-SAJ/CJSG. Como ja existem providers CJSG no
codigo, TJAC deve ser usado para endurecer a abstracao por familia e fixtures
reais.

TJCE/CJSG:

```text
GET https://esaj.tjce.jus.br/cjsg/consultaSimples.do
```

O ambiente atual recebeu `ConnectionResetError`/TLS EOF. Decisao: nao promover
ate haver probe limpo; repetir com janela diferente e confirmar se e bloqueio
regional, instabilidade ou requisito TLS especifico.

### STM

Rota validada:

```text
GET https://jurisprudencia.stm.jus.br/
```

Sinais observados:

- HTTP 200 em sessao limpa;
- pagina oficial JMU/STM com sinais de jurisprudencia, inteiro teor e pesquisa;
- provider `stm_jurisprudencia` ja existe no codigo.

Decisao: manter como fonte especializada relevante. O proximo passo e comparar
o contrato documentado com o provider existente e adicionar fixture publica
representativa se ainda faltar.

### TJAP/Tucujuris

Rotas testadas:

```text
GET https://services.tjap.jus.br/pages/consultar-jurisprudencia/consultar-jurisprudencia.html
GET https://tucujuris.tjap.jus.br/tucujuris/pages/consultar-jurisprudencia/consultar-jurisprudencia.html
```

Resultado observado:

- `services.tjap.jus.br` nao resolveu DNS no ambiente atual;
- `tucujuris.tjap.jus.br` respondeu desafio Cloudflare/JavaScript em sessao
  limpa.

Decisao: documentar bloqueio e nao implementar provider TJAP ate localizar rota
publica estavel sem desafio.

### Rodada estadual complementar: TJES, TJMT, TJPA, TJPB, TJPE, TJPI, TJRO,
TJRR e TJSE

A rodada complementar esta detalhada em
[state-court-route-mapping-2026-08-07.md](state-court-route-mapping-2026-08-07.md).
Ela retirou esses estados da zona de "sem candidato claro" e separou tres
grupos:

- candidatos de provider decisorio: TJPI, TJRR, TJMT, TJPA e TJPB;
- candidatos documentais/precedentes: TJSE e TJRO;
- inconclusivo: TJES.

O achado mais maduro e o TJPI/JusPI, porque a URL de busca server-side retornou
resultado real com CNJ, ementa, relator, orgao, tipo e paginacao. TJRR tambem e
forte e agora possui postback reproduzido, mas exige fixture e tratamento de
instabilidade JSF/PrimeFaces. TJMT e TJPA sao bons alvos de API moderna. O TJMT
respondeu 401 sem uma superficie publica reproduzivel, enquanto o TJPA teve o
contrato fechado por bundle e chamadas `POST`/`GET` publicas. O `GET` simples em
`/bff/api/decisoes` continua sendo incorreto, mas a busca textual valida usa
`POST /bff/api/decisoes/buscar`.

### Rodada federal complementar: CJF/TRF1, TRF5 e TSE - 2026-08-11

Esta rodada ampliou o mapeamento para fontes federais ainda sem provider
especifico no NanoJuris. Os probes foram feitos com sessoes HTTP novas, sem
cookies exportados, login, captcha ou bypass de controle:

| Fonte | Rota | Resultado | Decisao |
| --- | --- | --- | --- |
| CJF/TRF1 | `GET /trf1/index.xhtml` + `POST` JSF com `dano moral` | HTTP 200; 25.783 resultados; processo, classe, relator, orgao, datas, ementa e links PJe/arquivo | `candidate_ready`; criar provider separado da superficie unificada |
| CJF/Unificada | `GET /unificada/index.xhtml` | HTTP 200; formulario oficial com fontes STF, STJ, TNU, TRF1-5, TR e TRU | `candidate_needs_har`; falta reproduzir uma busca e separar origens |
| TRF5 | `GET /pesquisa.wsp` + `POST /resultado_pesquisa.wsp` | HTTP 200; resultados com ementas, processos, orgaos, datas e tipo documental | `candidate_ready`; criar parser HTML e fixture |
| TSE/SJUR beta | `GET` da SPA beta | HTTP 200 no shell de `jurisprudencia.tse.jus.br` e `jurisprudencia-tres.tse.jus.br`; rota direta antiga foi rejeitada | `candidate_needs_har`; localizar endpoint decisorio da nova SPA |

### Rodada de contratos publicos: TSE/SJUR 4.0 e TJSE - 2026-08-11

| Fonte | Rota observada | Evidencia | Decisao |
| --- | --- | --- | --- |
| TSE/SJUR classes | `POST https://sjur-pesquisa-api.tse.jus.br/tse/sjur-pesquisa-backend/rest/public/pesquisa/classes` com `["TSE"]` | HTTP 200 JSON com classes eleitorais, incluindo sigla e descricao | contrato de metadados valido |
| TSE/SJUR relatores | `POST .../public/pesquisa/relatorias` com `["TSE"]` | HTTP 200 JSON com nomes de relatores | contrato de metadados valido |
| TSE/SJUR eleicoes | `POST .../public/pesquisa/eleicoes` com `["TSE"]` | HTTP 200 JSON com anos eleitorais | contrato de metadados valido |
| TSE/SJUR normas | `POST .../public/pesquisa/normas` com `["TSE"]` | HTTP 200 JSON com sigla, numero, ano e tipo normativo | contrato de metadados valido |
| TSE/SJUR decisoes | `POST .../public/pesquisa` | HTTP 200 JSON, mas `Falha na verificacao antirrobo`, sem resultados | nao promover provider decisorio |
| TJSE pesquisa judicial | `GET` do portal, `GET` do iframe e `POST` JSF com termo `dano moral` | formulario publico com filtros ricos; POST retornou `Captcha invalido` | `blocked_or_inconclusive`; nao contornar protecao |

### Rodada REST estadual: TJPE - 2026-08-11

| Fonte | Rota observada | Evidencia | Decisao |
| --- | --- | --- | --- |
| TJPE catalogos | `GET /api/v1/classes`, `/assuntos`, `/relatores` e `/unidades-judiciais` | HTTP 200 JSON com catalogos completos para filtros | contrato de metadados valido |
| TJPE jurisprudencias | `GET /api/v1/jurisprudencias?page=0&size=20` | HTTP 200 JSON paginado, `X-Total-Count`, processo, classe, relator, orgao, datas e texto decisorio | `candidate_ready`; criar fixture REST |
| TJPE filtro por assunto | `GET /api/v1/jurisprudencias?page=0&size=5&tipoSentenca.in=A&assuntoCNJ.in=9098` | HTTP 200, 656 registros e objetos com ementa/acordao | `candidate_ready`; validar filtros no parser |
| TJPE processo | `GET /api/v1/processo/{codigoProcesso}/{npuSemFormatacao}` | HTTP 200 com pacote de processo; identificadores de amostra retornaram pacote vazio | contrato auxiliar, nao busca jurisprudencial principal |

O contrato detalhado esta em [cjf_jurisprudencia.md](providers/cjf_jurisprudencia/README.md)
e [trf5_jurisprudencia.md](providers/trf5_jurisprudencia/README.md). A pagina
institucional do TSE confirma as duas ferramentas de pesquisa e a evolucao da
plataforma, mas o shell SPA sozinho nao e evidencia suficiente para criar um
provider de decisoes.

### Rodada de dados abertos: TCU - 2026-08-11

| Fonte | Rota observada | Evidencia | Decisao |
| --- | --- | --- | --- |
| TCU manifesto | `GET https://sites.tcu.gov.br/dados-abertos/jurisprudencia/arquivos/jurisprudencia-arquivos.csv` | HTTP 200; manifesto delimitado por `|`, com bases, tamanhos e URLs oficiais | `candidate_ready` para adapter de dataset |
| TCU acordaos resumo | `GET .../acordao-completo/acordao-completo-resumo.csv` com `Range: bytes=0-4095` | HTTP 206; schema `KEY`, `VISAOGERAL` e registros reais com resumo HTML | `candidate_ready` |
| TCU jurisprudencia selecionada | `GET .../jurisprudencia-selecionada/jurisprudencia-selecionada.csv` com `Range` | HTTP 206; enunciado, excerto, area, tema, subtema, referencias e identificacao do acordao | `candidate_ready` |
| TCU sumulas/respostas/boletins | arquivos CSV oficiais listados pelo manifesto | HTTP 206; schemas reais para sumulas, respostas a consultas e boletim de jurisprudencia | `candidate_ready` |
| TCU pesquisa interativa | `GET /pes` e `GET /rest/publico/base/acordao-completo/documentosResumidos` | shell publico HTTP 200; endpoint de resultado respondeu pagina de bloqueio do firewall, nao JSON | `blocked_or_inconclusive`; nao contornar |

O dossie do contrato esta em
[tcu_jurisprudencia.md](providers/tcu_jurisprudencia/README.md). A decisao
separa o adapter de dados abertos da pesquisa interativa: os CSVs podem ser
sincronizados por manifest, enquanto o endpoint web nao deve ser interpretado
como resultado vazio quando retornar HTML de firewall.

### Rodada de informativos: CNJ - 2026-08-11

| Fonte | Rota observada | Evidencia | Decisao |
| --- | --- | --- | --- |
| CNJ informativos | `GET https://atos.cnj.jus.br/jurisprudencia` | HTTP 200; tabela com tipo, numero, data, itens de ementa e links PDF oficiais | `candidate_ready`; criar parser HTML/PDF |
| CNJ filtro por numero | `GET /jurisprudencia?numero=10` | HTTP 200; informativos filtrados pelo numero | filtro valido |
| CNJ filtro textual | `GET /jurisprudencia?argumento=cartorios` | HTTP 200; informativos contendo o termo no conteudo indexado | filtro valido; nao e busca de acordao individual |
| CNJ filtro por periodo | `GET /jurisprudencia?dat_publicacao_inicio=01/01/2026&dat_publicacao_fim=31/12/2026` | HTTP 200; resultados dentro do intervalo informado | filtro valido |

O dossie do contrato esta em
[cnj_jurisprudencia.md](providers/cnj_jurisprudencia/README.md). O provider
deve preservar a natureza curada do informativo e nao fabricar metadados de
processo, relator ou orgao julgador que nao estejam no PDF.

### Rodada BFF estadual: TJPA - 2026-08-11

| Fonte | Rota observada | Evidencia | Decisao |
| --- | --- | --- | --- |
| TJPA catalogos | `GET /bff/api/decisoes/filtros` | HTTP 200 JSON com origens, tipos, classes, assuntos, relatores e orgaos julgadores | contrato de metadados valido |
| TJPA busca textual | `POST /bff/api/decisoes/buscar` com `query=dano moral`, `queryType=free` e `queryScope=ementa` | HTTP 200 JSON com `content`, facetas, metadados decisorios e limite tecnico de 10.000 | `candidate_ready`; criar fixture e parser |
| TJPA filtro origem/tipo | `POST /bff/api/decisoes/buscar` usando exatamente `origens[].origem` e `tipos[].descricao` de `/filtros` | HTTP 200 JSON com resultado e total tecnico de 10.000 | filtro basico validado |
| TJPA busca textual em inteiro teor | `POST /bff/api/decisoes/buscar` com `queryScope=inteiroTeor` | HTTP 200 JSON com resultados | contrato de escopo valido; validar campos no parser |
| TJPA recentes | `GET /bff/api/decisoes/recentes` com origem, tipo, periodo e paginacao | HTTP 200 JSON com documentos ricos e limite tecnico de 10.000 | rota valida de listagem temporal |
| TJPA classe/assunto | `POST /bff/api/decisoes/pesquisar-por-classe-assunto` | datas ISO deram HTTP 400; formato `dd/MM/yyyy` foi aceito, mas ids arbitrarios deram vazio/erro | manter pendente ate fixture com ids de catalogo |

O bundle atual tambem referencia rotas de detalhe por id, processo, documento e
tema. As rotas por id e processo foram chamadas com identificadores obtidos da
resposta publica e retornaram HTTP 404; ficam pendentes de contrato correto.
Nao inventar identificadores e nao exportar dados pessoais desnecessarios para
fixtures.

### Rodada e-SAJ: TJCE - 2026-08-11

| Fonte | Rota observada | Evidencia | Decisao |
| --- | --- | --- | --- |
| TJCE consulta completa | `GET https://esaj.tjce.jus.br/cjsg/resultadoCompleta.do` | pagina oficial de jurisprudencia com pesquisa livre, ementa, classe, assunto, orgao, relator, datas, origem e tipo de publicacao | fonte oficial e contrato funcional da UI documentado |
| TJCE ajuda e-SAJ | `GET https://esaj.tjce.jus.br/WebHelp/id_consultas_jurisprudenciais.htm` | documentacao oficial confirma ementas, acordaos, inteiro teor, filtros e acesso aos dados do processo | evidencia institucional forte |
| TJCE HTTP limpo | mesma rota com sessao nova e `requests`, sem proxy de ambiente | reset TLS pelo host remoto antes da resposta | `candidate_needs_har`; nao forcar reconexao ou contornar controle |

O TJCE deve ser tratado como candidato da familia e-SAJ/CJSG, mas somente vira
`candidate_ready` depois que um HAR limpo permitir identificar formulario,
metodo, payload, paginacao e rota de detalhe. A evidencia oficial da interface
nao substitui uma fixture de resultado reproduzida por HTTP.

### Rodada de informativos: TJCE - 2026-08-11

| Fonte | Rota observada | Evidencia | Decisao |
| --- | --- | --- | --- |
| TJCE Informativos | `GET https://www.tjce.jus.br/informativo-jurisprudencia/` | HTTP 200 HTML UTF-8 com edicoes, processos, orgaos, assuntos, destaques e filtros | `candidate_ready`; criar parser curado |
| TJCE Informativos downloads | controles de edicao com PDF/RTF na interface e links PDF oficiais no HTML | downloads institucionais disponiveis sob demanda | validar fixture de PDF; nao baixar acervo no CI |

Esta superficie deve ser mantida separada do `tjce_cjsg`: informativos sao
curadoria editorial de decisoes relevantes, nao repositorio geral de acordaos.

### Rodada federal: TRF3 - 2026-08-11

| Fonte | Rota observada | Evidencia | Decisao |
| --- | --- | --- | --- |
| TRF3 pesquisa | `GET https://web.trf3.jus.br/jurisprudencia/home/index/1` | interface oficial com busca textual, operadores, processo, relator, data, classe, orgao, ementa e objeto | `ui_confirmed`; contrato de submissao pendente |
| TRF3 acordaos | `GET https://web.trf3.jus.br/acordaos/Acordao` | carta de servicos oficial descreve consulta por processo e inteiro teor | `ui_confirmed`; testar separadamente |
| TRF3 HTTP limpo | pesquisa principal com `requests`, sem proxy de ambiente | timeout de leitura em 45s | `blocked_transport`; nao repetir mesma chave |

O dossie [trf3_jurisprudencia.md](providers/trf3_jurisprudencia/README.md)
mantem a matriz de cobertura e o ledger da tentativa. A falha da pesquisa
principal nao invalida a rota de acordaos nem os links para CJF, TNU e Sumulas.

## Proximos probes recomendados

1. Validar inteiro teor live da familia eproc federal para TNU, TRF2 e TRF6,
   agora que os providers de busca ja reaproveitam o parser testado em TRF4/TJSP.
2. TJGO: criar contrato Projudi, fixture HTML publica representativa e parser offline de
   cards com inteiro teor embutido.
3. TJRS: criar contrato AJAX/SOLR, fixture JSON publica representativa e parser offline.
4. TJBA: criar contrato em `docs/source-contracts/`, fixture GraphQL publica representativa
   e parser offline.
5. TJPR: criar contrato da rota HTML, fixture de resultado e parser offline.
6. TJSC: capturar fixture HTML, validar paginacao e implementar parser proprio
   depois de comparar labels com a familia eproc federal. TRF2 permanece em
   validacao de filtros especificos.
7. TSE/TREs: manter metadados em contrato parcial e nao promover busca enquanto
   houver antirrobo/token.
8. TRT2/PJe: documentar desafio `tokenDesafio`/`imagem` e bloquear automacao de
   documentos.
9. TJMA: documentar contrato parcial de metadados e manter busca principal
   bloqueada enquanto exigir captcha.
10. TST: salvar fixture do payload textual, catalogos minimos e documento HTML
   usando termos trabalhistas (`horas extras`, `justa causa`, `equiparacao salarial`).
11. TJPI: criar fixture HTML publica representativa com `q=dano moral`, `q=idpj` e pagina 2.
12. TJRR: salvar fixture sanitizada de busca simples, mapear paginacao e
   reproduzir JSF/PrimeFaces sem cookies privados.
13. TJPA: salvar fixture de `/filtros`, `/buscar` e `/recentes`, validar filtros
   com valores exatos do catalogo e criar parser JSON offline.
14. TJMT: repetir somente se surgir nova superficie publica reproduzivel; nao
   usar login ou credencial.
15. TJPB: repetir busca real e registrar se Cloudflare/WAF aparece em sessao
   limpa.
16. TJPE: criar fixture REST, validar filtros e cadeia TLS antes de criar provider.
17. TJSE/TJRO: aprofundar como catalogos/entradas e localizar endpoint de
   resultado quando existir.
18. TJES: repetir `Pesquisa.aspx` com janela maior.
19. TRF3: usar captura automatica de rede ou testar a consulta de acordaos por
   processo; nao repetir o mesmo GET que ja sofreu timeout.
20. TCU: criar fixture minima do manifesto e dos schemas CSV, sem baixar o
   acervo historico no CI.
21. CJF/Unificada e TSE/SJUR: capturar HAR limpo para fechar origem, payload,
   paginacao e detalhe.
22. CNJ: criar fixture HTML de uma pagina, validar itens numerados e manter
   download de PDF sob demanda.
23. TJMG/TJRJ/TJAP/TRT15/TRT23: manter documentados como formulacoes ricas ou bloqueadas, mas bloquear provider
   enquanto resultado depender de captcha/reCAPTCHA/Cloudflare/reset.

## Ranking de implementacao

| Rank | Fonte | Motivo |
| --- | --- | --- |
| 1 | CJF/TRF1 | resposta limpa, 25.783 resultados e links de inteiro teor |
| 2 | TRF5 | formulario publico, ementas e filtros federais com resposta limpa |
| 3 | TNU/TRF2/TRF6 eproc | alto valor federal, rota limpa e reuso imediato do parser eproc |
| 4 | TJGO/Projudi | alto volume, resultado publico e inteiro teor embutido nos cards |
| 5 | TJRS AJAX/SOLR | JSON estruturado, facets ricas, alto volume e rota publica rapida |
| 6 | TJBA GraphQL | contrato estruturado, campos canonicos diretos, resposta limpa |
| 7 | TJPR HTML | alto volume, resultado publico e sinais juridicos completos |
| 8 | TJSC/eproc | fonte publica forte e potencial de provider por familia tecnica |
| 9 | TJAC/CJSG | rota CJSG validada e util para endurecer familia e-SAJ |
| 10 | TJPI/JusPI | busca HTML limpa com resultados reais e paginacao |
| 11 | TJRR/Juris JSF | pagina rica, sem bloqueio no GET, bom acervo estadual |
| 12 | TJPA BFF | busca textual JSON, catalogos e listagem recente reproduzidos; falta fixture e parser |
| 13 | TJMT API | portal atual exige login e rota inferida respondeu 401; nao automatizar sem nova superficie publica |
| 14 | TJPB/PJe jurisprudencia | UI rica, mas precisa estabilizar risco WAF |
| 14 | TST backend | JSON rico, filtro textual e inteiro teor HTML reproduzidos; provider implementado |
| 15 | TSE/TREs | plataforma oficial nova, mas endpoint decisorio ainda pendente |
| 16 | TRT2 metadados/opcoes | contrato parcial util para diagnostico PJe, mas documentos exigem desafio |
| 17 | TJSE/TJRO documentais | entradas uteis para sumulas, precedentes e orientacao, mas ainda sem busca decisoria limpa |
| 18 | TJMA metadados/sumulas | API limpa parcial; busca principal exige captcha |
| 19 | TJES/TJMG/TJRJ/TJAP/TRT15/TRT23 | inconclusivos, formularios ricos ou portais conhecidos, mas busca direta bloqueada/instavel |
| 20 | TJCE Informativos | superficie curada publica; falta fixture e parser, mas nao depende do CJSG instavel |
