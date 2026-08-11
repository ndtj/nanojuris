# Providers

O indice tecnico completo por provider esta em
[docs/providers/](providers/README.md). O catalogo machine-readable para
humanos, CI e agentes esta em
[docs/registry/providers.json](registry/providers.json). Esta pagina continua
sendo a visao narrativa e operacional dos providers; o dossie individual e a
fonte canonica de detalhes de cada contrato.

Cada provider deve declarar suas capacidades objetivas por meio de
`ProviderCapabilities`. Isso permite descoberta por Python, CLI e MCP sem
executar uma busca real.

```bash
nanojuris fontes
nanojuris diagnostico --fonte bnp_pangea
```

Detalhes do contrato estao em [source-capabilities.md](source-capabilities.md).
Novos providers devem usar os contratos de aquisicao e parsing descritos em
[extraction-pipeline.md](extraction-pipeline.md).
O checklist completo para implementar novas fontes esta em
[provider-development.md](provider-development.md).
Antes de implementar uma rota nova, use o fluxo economico de descoberta em
[source-discovery.md](source-discovery.md).

## Providers oficiais de SP adicionados

As fontes abaixo foram priorizadas porque expoem conteudo oficial em HTML
publico, acessivel com sessao HTTP limpa e sem captcha/login no fluxo
automatizado.

### `tjsp_nugepnac`

Provider para catalogos oficiais TJSP/NugepNac de IRDR e IAC.

Rotas publicas usadas:

```text
GET /NugepNac/Irdr
GET /NugepNac/Iac
GET /NugepNac/(Irdr|Iac)/DetalheTema?codigoNoticia=<id>&pagina=1
```

Campos extraidos: numero do tema, tipo de precedente, status, processo
paradigma, assunto, orgao julgador, relator, datas, questao submetida,
tese firmada e links relacionados. O resultado canonico e
`CanonicalPrecedent`.

Limitacao importante: as paginas de detalhe sao publicas, mas alguns links de
acordaos CJSG podem redirecionar para verificacao de acesso. O provider nao
tenta contornar captcha, login ou controles de acesso.

### `tce_sp_jurisprudencia`

Provider para repertorio publico de sumulas e publicacoes do boletim de
jurisprudencia do TCE-SP.

Rotas publicas usadas:

```text
GET /boletim-de-jurisprudencia/sumulas
GET /boletim-de-jurisprudencia/publicacoes
GET /boletim-de-jurisprudencia/indice-alfabetico-remissivo
```

Campos extraidos: numero da sumula, enunciado, historico/fundamento quando
disponivel, edicao do boletim e URL publica da publicacao. O resultado canonico
e `CanonicalPrecedent`.

Limitacao importante: a busca dinamica `/jurisprudencia/pesquisar` usa
reCAPTCHA no fluxo observado e nao e automatizada. O provider cobre os
catalogos estaticos publicos.

### `tre_sp_temas`

Provider para paginas publicas de temas selecionados de jurisprudencia do
TRE-SP.

Rotas publicas usadas:

```text
GET /jurisprudencia/temas-selecionados-1
GET /jurisprudencia/arquivos-da-secao-de-jurisprudencia-sp/temas-selecionados/<slug>
```

Campos extraidos: tema, resumo textual da pagina, links de decisoes/documentos
selecionados e URL publica de origem. O resultado canonico e
`CanonicalPrecedent`.

Limitacao importante: e uma fonte tematica curada, nao uma busca geral de
acordaos eleitorais. Links de inteiro teor podem apontar para sistemas externos.

## `comunica_pje`

Provider para comunicacoes judiciais publicas do Comunica PJe/DJEN.

Endpoint publico usado:

```text
GET /api/v1/comunicacao
```

### Escopo

O provider nao e uma base de acordaos ou jurisprudencia consolidada. Ele cobre
publicacoes/comunicacoes objetivas, como intimacoes e editais, com texto,
tribunal, orgao, classe, numero do processo e link publico quando a API retorna.

Filtros reproduzidos com sessao HTTP limpa:

```text
texto
siglaTribunal
numeroProcesso
dataDisponibilizacaoInicio
dataDisponibilizacaoFim
pagina
size
```

Exemplo validado na descoberta:

```text
GET https://comunicaapi.pje.jus.br/api/v1/comunicacao?texto=infanticidio&pagina=0&size=5
```

Retornou JSON publico com `count=1260`; com `siglaTribunal=TJSP`, retornou
`count=131`; com `siglaTribunal=STJ`, retornou `count=53`. A variante acentuada
`infanticidio` retornou a mesma contagem observada.

O filtro por data de disponibilizacao tambem foi validado com sessao limpa:

```text
dataDisponibilizacaoInicio=2026-07-31&dataDisponibilizacaoFim=2026-07-31
```

Para `infanticidio`, retornou `count=1` e item com
`data_disponibilizacao=2026-07-31`. Os parametros curtos `data_inicio` e
`data_fim` foram testados e nao filtraram a resposta observada.

### Uso

```bash
nanojuris buscar "infanticidio" --fonte comunica_pje --orgaos TJSP --limite 5
nanojuris buscar "infanticidio" --fonte comunica_pje --publicacao-de 2026-07-31 --publicacao-ate 2026-07-31
nanojuris buscar "" --fonte comunica_pje --numero 1500780-26.2025.8.26.0603
```

Python:

```python
from nanojuris import NanoJurisClient

client = NanoJurisClient()
page = client.search(
  "infanticidio",
  source="comunica_pje",
  courts=["TJSP"],
  published_from="2026-07-31",
  published_to="2026-07-31",
)
records = client.search_canonical("infanticidio", source="comunica_pje")
```

Campos extraidos:

```text
communication_id
court
case_number
case_class
publication_date
communication_type
source_body
summary
document_url
```

Limitacoes:

- comunicacoes judiciais nao substituem acordaos, sentencas ou inteiro teor;
- a API pode devolver ate 100 itens mesmo quando `size` menor e o provider limita
  localmente;
- `numeroProcesso` deve ser enviado apenas com digitos.

## `tjdf_juris`

Provider para jurisprudencia publica do TJDFT/SISTJ.

Rotas publicas usadas:

```text
GET /IndexadorAcordaos-web/sistj?nomeDaPagina=buscaLivre
GET /IndexadorAcordaos-web/sistj?nomeDaPagina=buscaLivre2
GET /IndexadorAcordaos-web/sistj?comando=abrirDadosDoAcordao&numeroDoDocumento=<id>
```

### Escopo

O provider cobre acordaos e bases publicas indexadas pelo SISTJ/TJDFT. A
descoberta foi validada com sessao HTTP limpa usando termo `infanticidio`, com
31 resultados observados e IDs de documento expostos na pagina de resultados.

Campos enviados:

```text
argumentoDePesquisa
ementa
numero
dataInicio
dataFim
numeroDaPaginaAtual
quantidadeDeRegistros
```

Campos extraidos do detalhe:

```text
registry_number
case_number
case_class
rapporteur
judging_body
judgment_date
publication_date
summary
decision_outcome
document_url
```

### Uso

```bash
nanojuris buscar "infanticidio" --fonte tjdf_juris --limite 5
```

Python:

```python
from nanojuris import NanoJurisClient

client = NanoJurisClient()
page = client.search("infanticidio", source="tjdf_juris", page_size=5)
records = client.search_canonical("infanticidio", source="tjdf_juris")
```

Limitacoes:

- contrato HTML legado, sujeito a mudancas de layout;
- inteiro teor PJe pode depender de link/documento externo;
- coletas paginadas devem respeitar rate limit e preservar `numeroDoDocumento`.

## `tjac_cjsg`

Provider para jurisprudencia publica do TJAC/CJSG, descoberto por probe limpo na
familia e-SAJ/CJSG e validado com sessao HTTP sem cookies de navegador.

Rotas publicas usadas:

```text
POST /resultadoCompleta.do
GET  /getArquivo.do?cdAcordao=<id>&cdForo=<foro>
```

Payload minimo validado:

```text
dados.buscaInteiroTeor
dados.buscaEmenta
dados.nuProcOrigem
dados.dtJulgamentoInicio
dados.dtJulgamentoFim
dados.origensSelecionadas
tipoDecisaoSelecionados
dados.ordenarPor
```

Exemplo validado:

```bash
nanojuris buscar "infanticidio" --fonte tjac_cjsg --limite 5
```

Na descoberta limpa, o TJAC/CJSG retornou `5` resultados para `infanticidio`,
sem captcha no fluxo testado. O parser CJSG leu numero do processo, classe,
assunto, relator, orgao julgador, datas, ementa e link de inteiro teor.

## `tjal_cjsg`

Provider para jurisprudencia publica do TJAL/CJSG, descoberto por probe limpo na
familia e-SAJ/CJSG e validado com sessao HTTP sem cookies de navegador.

Rotas publicas usadas:

```text
POST /resultadoCompleta.do
GET  /getArquivo.do?cdAcordao=<id>&cdForo=<foro>
```

Payload minimo validado:

```text
dados.buscaInteiroTeor
dados.buscaEmenta
dados.nuProcOrigem
dados.dtJulgamentoInicio
dados.dtJulgamentoFim
dados.origensSelecionadas
tipoDecisaoSelecionados
dados.ordenarPor
```

Exemplo validado:

```bash
nanojuris buscar "infanticidio" --fonte tjal_cjsg --limite 5
```

Na descoberta limpa, o TJAL/CJSG retornou `12` resultados para `infanticidio`,
sem captcha no fluxo testado. O parser CJSG leu numero do processo, classe,
assunto, relator, orgao julgador, datas, ementa e link de inteiro teor.

## `tjam_cjsg`

Provider para jurisprudencia publica do TJAM/CJSG, descoberto por probe limpo na
familia e-SAJ/CJSG e validado com sessao HTTP sem cookies de navegador.

Rotas publicas usadas:

```text
POST /resultadoCompleta.do
GET  /getArquivo.do?cdAcordao=<id>&cdForo=<foro>
```

Payload minimo validado:

```text
dados.buscaInteiroTeor
dados.buscaEmenta
dados.nuProcOrigem
dados.dtJulgamentoInicio
dados.dtJulgamentoFim
dados.origensSelecionadas
tipoDecisaoSelecionados
dados.ordenarPor
```

Exemplo validado:

```bash
nanojuris buscar "infanticidio" --fonte tjam_cjsg --limite 5
```

Na descoberta limpa, o TJAM/CJSG retornou `12` resultados para `infanticidio`,
sem captcha no fluxo testado. O parser CJSG leu numero do processo, classe,
assunto, relator, orgao julgador, datas, ementa e link de inteiro teor.

## `tjms_cjsg`

Provider para jurisprudencia publica do TJMS/CJSG, descoberto a partir de
projetos abertos de scraping e validado com sessao HTTP limpa.

Rotas publicas usadas:

```text
POST /resultadoCompleta.do
GET  /trocaDePagina.do?tipoDeDecisao=<tipo>&pagina=<n>&conversationId=
GET  /getArquivo.do?cdAcordao=<id>&cdForo=<foro>
```

Payload minimo validado:

```text
dados.buscaInteiroTeor
dados.buscaEmenta
dados.nuProcOrigem
dados.dtJulgamentoInicio
dados.dtJulgamentoFim
dados.origensSelecionadas
tipoDecisaoSelecionados
dados.ordenarPor
```

Exemplo validado:

```bash
nanojuris buscar "infanticidio" --fonte tjms_cjsg --limite 5
```

Na descoberta limpa, o TJMS/CJSG retornou `22` resultados para `infanticidio`,
sem captcha no fluxo testado, e o parser CJSG leu classe, assunto, comarca,
relator, orgao julgador, datas, ementa e link de inteiro teor.

## `tjpi_juspi`

Provider para jurisprudencia publica do TJPI/JusPI.

Rotas publicas usadas:

```text
GET /jurisprudences/search?q=<termo>
GET /jurisprudences/search?page=<n>&q=<termo>
GET /jurisprudences/<id>/public
```

Campos enviados:

```text
q
page
tipo
relator
classe
orgao
data_min
data_max
```

Campos extraidos:

```text
public_id
case_number
decision_type
subject
case_class
rapporteur
judging_body
publication_date
summary
document_url
full_text
```

Exemplo validado:

```bash
nanojuris buscar "dano moral" --fonte tjpi_juspi --limite 5
nanojuris documento "tjpi-juspi-35510999" --fonte tjpi_juspi
```

Na descoberta limpa, o TJPI/JusPI retornou HTML publico por GET simples, com
resultados decisorios reais, paginacao e links de detalhe em
`/jurisprudences/<id>/public`. O provider normaliza resultados para
`CanonicalDecision` e o detalhe publico para `CanonicalDocument`, sem baixar PDF
e sem usar sessao autenticada.

## `tjgo_projudi_jurisprudencia`

Provider para jurisprudencia publica do PROJUDI/TJGO.

Rotas publicas usadas:

```text
GET  /ConsultaJurisprudencia
POST /ConsultaJurisprudencia
```

Payload minimo validado:

```text
PaginaAtual
PosicaoPaginaAtual
Texto
Id_Instancia
Id_Area
Id_ServentiaSubTipo
ProcessoNumero
DataInicial
DataFinal
Localizar=Consultar
```

Campos extraidos:

```text
case_number
decision_type
rapporteur
judging_body
publication_date
summary
full_text
file_id
```

Exemplo validado:

```bash
nanojuris buscar "dano moral" --fonte tjgo_projudi_jurisprudencia --limite 5
```

Na descoberta limpa, o TJGO/Projudi retornou HTML publico por POST, com mais de
1,3 milhao de resultados para `dano moral`, cards `div.search-result`, numero
CNJ, magistrado, orgao/unidade, tipo de ato, data de publicacao e inteiro teor
embutido no proprio resultado. O provider preserva o texto publico retornado
pela fonte sem redaction automatica.

A rota separada de download por `Id_Arquivo` voltou ao formulario em probe sem
token, por isso permanece pendente e nao e usada pelo provider atual.

## `stm_jurisprudencia`

Provider para jurisprudencia publica do STM/JMU, descoberto por probe limpo no
portal `https://jurisprudencia.stm.jus.br`.

Rotas publicas usadas:

```text
GET /consulta.php?search_filter_option=jurisprudencia&search_filter=busca_avancada&...
GET https://eproc2g.stm.jus.br/eproc_2g_prod/externo_controlador.php?acao=visualizar_acordao&uuid=<uuid>
```

Parametros principais:

```text
q
fqx_ementa
fqx_inteiro_teor
fqx_numero_jurisprudencia
fqx_data_publicacao_inicio
fqx_data_publicacao_fim
fqx_data_decisao_inicio
fqx_data_decisao_fim
```

Campos extraidos:

```text
case_number
case_class
rapporteur
subject
judgment_date
publication_date
summary
document_url
uuid
```

Exemplo validado:

```bash
nanojuris buscar "desercao" --fonte stm_jurisprudencia --limite 5
```

Na descoberta limpa, o STM/JMU retornou HTML publico sem captcha, com paineis
`div.panel.panel-default`, ementa em `blockquote`, metadados em `dl` e botao
`Inteiro Teor` apontando para URL publica do eproc/STM. O provider declara
suporte a `get_document` para o HTML de inteiro teor publico.

## `trf4_eproc_jurisprudencia`

Provider para jurisprudencia publica do eproc/TRF4, descoberto por probe limpo em
`https://jurisprudencia.trf4.jus.br`.

Rotas publicas usadas:

```text
POST /externo_controlador.php?acao=jurisprudencia@jurisprudencia/listar_resultados
GET  /externo_controlador.php?acao=jurisprudencia@jurisprudencia/download_inteiro_teor&id_jurisprudencia=<id>
```

Campos enviados:

```text
txtPesquisa
rdoCampo
txtProcesso
dtDecisaoInicio
dtDecisaoFim
dtPublicacaoInicio
dtPublicacaoFim
chkAgruparResultados
```

Campos extraidos:

```text
case_number
decision_type
case_class
rapporteur
judging_body
judgment_date
publication_date
summary
document_url
full_text_url
id_jurisprudencia
```

Exemplo validado:

```bash
nanojuris buscar "desercao" --fonte trf4_eproc_jurisprudencia --limite 5
```

Na descoberta limpa, o eproc/TRF4 retornou HTML publico sem captcha, com cards
`.resultadoItem`, numero CNJ, classe, orgao julgador, relator, datas, trecho de
decisao e link de inteiro teor. A rota de download do inteiro teor retornou HTML
publico validado, entao o provider declara suporte a `get_document`.

## `tnu_eproc_jurisprudencia`, `trf2_eproc_jurisprudencia`, `trf6_eproc_jurisprudencia`

Providers para jurisprudencia publica federal em instancias eproc da TNU, TRF2
e TRF6. Eles compartilham a mesma familia tecnica e o mesmo parser de cards
HTML usado pelo eproc, mas expoem fontes separadas para facilitar roteamento por
MCP, CLI e estudos jurimetricos.

Rotas publicas usadas:

```text
POST /externo_controlador.php?acao=jurisprudencia@jurisprudencia/listar_resultados
GET  /externo_controlador.php?acao=jurisprudencia@jurisprudencia/download_inteiro_teor&id_jurisprudencia=<id>
```

Bases:

```text
TNU  https://eproctnu.cjf.jus.br/eproc
TRF2 https://eproc.trf2.jus.br/eproc
TRF6 https://eproc-jur.trf6.jus.br/eproc
```

Campos extraidos:

```text
case_number
decision_type
case_class
rapporteur
judging_body
judgment_date
publication_date
summary
document_url
full_text_url
id_jurisprudencia
```

Exemplos:

```bash
nanojuris buscar "aposentadoria" --fonte tnu_eproc_jurisprudencia --limite 5
nanojuris buscar "aposentadoria" --fonte trf2_eproc_jurisprudencia --limite 5
nanojuris buscar "aposentadoria" --fonte trf6_eproc_jurisprudencia --limite 5
```

Na validacao live de 2026-08-07, as tres fontes responderam HTTP 200, sem
captcha/login, com `resultadoItem`, numero CNJ, ementa/decisao e link de inteiro
teor. As fixtures publicas representativas ficam em
`tests/fixtures/tnu_eproc_aposentadoria.html`,
`tests/fixtures/trf2_eproc_aposentadoria.html` e
`tests/fixtures/trf6_eproc_aposentadoria.html`.

## `bnp_pangea`

Provider inicial do NanoJuris.

Endpoints publicos usados:

```text
GET  /parametros
GET  /sugestoes?texto=<termo>
POST /precedentes
GET  /precedentes/{id}/decisoes
```

### Contrato publico

O provider expoe tres niveis de acesso:

```python
client.get_parameters()
client.get_catalog()
client.list_suggestions("icms")
client.get_document("tjsp-cjsg-20787558-0", source="tjsp_cjsg")
client.get_document("0003938-14.2017.8.26.0323", source="tjsp_esaj_cpopg")
```

`get_document` deve ser implementado apenas quando a fonte oficial oferece
inteiro teor publico sem login, captcha ou acesso restrito. O retorno deve ser um
`CanonicalDocument` com `sha256`, `byte_size`, `source_trace` e
`extraction_trace` sempre que possivel.

`get_parameters()` retorna o JSON bruto da fonte, util para auditoria tecnica.
`get_catalog()` converte orgaos e especies para modelos estaveis:

```text
ProviderCatalog
  courts: list[ProviderOption]
  species: list[ProviderOption]
  species_groups: list[dict]
  source_trace: SourceTrace
```

`list_suggestions()` usa o endpoint de sugestoes referenciado pelo frontend. Se
a fonte responder `404`, o recurso e tratado como indisponivel e retorna lista
vazia, sem interromper buscas ou catalogo.

Campos de filtro:

```text
buscaGeral
todasPalavras
quaisquerPalavras
semPalavras
trechoExato
atualizacaoDesde
atualizacaoAte
cancelados
ordenacao
nr
orgaos
tipos
pagina
tamanhoPagina
```

### Orgaos

Os orgaos sao identificados por siglas publicas como:

```text
STF
STJ
TST
STM
TNU
TRF01..TRF06
TJSP
TRT02
```

Alguns orgaos podem aparecer marcados pela fonte como `semPrecedentes`. O
NanoJuris representa isso como `ProviderOption.disabled`.

### Especies

Especies comuns ja cobertas por fixtures:

```text
RG    Tema de Repercussao Geral
RR    Recurso Especial Repetitivo
IAC   Incidente de Assuncao de Competencia
IRDR  Incidente de Resolucao de Demandas Repetitivas
SUM   Sumula
SV    Sumula Vinculante
```

### CLI

Parametros brutos:

```bash
nanojuris parametros
```

Catalogo normalizado:

```bash
nanojuris parametros --catalogo
```

Sugestoes, quando disponiveis:

```bash
nanojuris sugestoes "icms"
```

Busca:

```bash
nanojuris buscar "ICMS" --orgaos STF,STJ --tipos RG,RR --limite 5
```

CSV de extracao objetiva:

```bash
nanojuris buscar "ICMS" --orgaos STF,STJ --tipos RG,RR --limite 5 --formato csv
```

### Testes live opcionais

Os testes live ficam desligados por padrao e consultam fonte publica real apenas
quando explicitamente habilitados:

```bash
$env:NANOJURIS_RUN_LIVE = "1"
python -m pytest -m live
```

## `stj_scon`

Provider inicial para acordaos publicos do STJ/SCON.

Escopo atual:

```text
GET /SCON/acordaos/
```

O provider declara capabilities, possui parser offline com fixture publica representativa e
normaliza resultados para `JurisprudenceResult` e `CanonicalDecision`.

Campos extraidos no contrato inicial:

```text
case_number
registry_number
decision_type
case_class
rapporteur
judging_body
judgment_date
publication_date
summary
document_url
```

Limitacoes:

- primeira versao foca acordaos SCON;
- inteiro teor sera ampliado em etapa posterior;
- o provider nao reinterpreta operadores oficiais do STJ;
- captcha, login ou controle de acesso sao tratados como estado da fonte, sem
  bypass.

Ficha publica: [stj-source-profile.md](stj-source-profile.md).
Pesquisa tecnica: [stj-provider-research.md](stj-provider-research.md).

### Pesquisa tecnica STJ

A primeira pesquisa tecnica para o STJ esta em [stj-provider-research.md](stj-provider-research.md). Ela separa os fluxos de SCON, precedentes qualificados e publicacoes, define criterios de fixture e marca o escopo inicial como SCON para acordaos.

## `stj_informativo`

Provider para notas publicas do Informativo de Jurisprudencia do STJ.

Escopo atual:

```text
GET /jurisprudencia/externo/informativo/?acao=pesquisar&livre=<termo>&operador=E&b=INFJ&tp=T
```

Campos extraidos:

```text
informativo
period
case_number
rapporteur
judging_body
judgment_date
title
summary
document_url
```

Exemplo validado:

```bash
nanojuris buscar "infanticidio" --fonte stj_informativo --limite 5
```

Use este provider para conteudo curado de informativos e teses resumidas. Para
busca integral de acordaos, combine com `stj_scon` quando a fonte responder sem
verificacao automatica. Links de inteiro teor podem apontar para rotas SCON
protegidas; o provider nao implementa bypass.

Ficha publica: [dossie do provider](providers/stj_informativo/README.md).

## `stf_juris`

Provider inicial para acordaos publicos do STF por API JSON observada no
frontend oficial de jurisprudencia.

Escopo atual:

```text
POST /api/search/search
```

O provider declara capabilities, possui fixture JSON publica representativa, normaliza
resultados para `JurisprudenceResult` e gera `CanonicalDecision`.

Campos extraidos no contrato inicial:

```text
case_number
registry_id
decision_type
case_class
rapporteur
judging_body
judgment_date
publication_date
summary
full_text_url
process_url
is_repercussao_geral
highlights
```

Limitacoes:

- a API limpa pode retornar AWS WAF challenge HTTP 202;
- alguns ambientes podem falhar na validacao SSL do dominio;
- inteiro teor do portal STF fica como URL ate responder sem HTTP 403 em sessao
  limpa;
- nao ha bypass de WAF, captcha, cookies ou desafios JavaScript.

Ficha publica: [dossie do provider](providers/stf_juris/README.md).

## `tst_jurisprudencia`

Provider implementado para a pesquisa textual publica do Tribunal Superior do
Trabalho.

### Escopo

```text
GET /config.json
POST /rest/pesquisa-textual/{inicio}/{limite}
GET /rest/documentos/{id}
```

O frontend oficial publica a base atual da API em `config.json`. O provider
usa o contrato REST JSON observado no frontend, limita a pagina a 100 itens e
recusa consultas vazias para evitar varredura acidental do acervo.

Campos extraidos:

```text
case_number
registry_id
decision_type
case_class
rapporteur
judging_body
judgment_date
publication_date
summary
disposition
document_url
```

Uso:

```bash
nanojuris buscar "horas extras" --fonte tst_jurisprudencia --limite 5
nanojuris documento "tst-jurisprudencia-<id-publico>" --fonte tst_jurisprudencia
```

Python:

```python
from nanojuris import NanoJurisClient

client = NanoJurisClient()
page = client.search("justa causa", source="tst_jurisprudencia", page_size=5)
document = client.get_document(page.results[0].id, source="tst_jurisprudencia")
```

O inteiro teor e retornado como HTML publico e preserva o link oficial no
`SourceTrace`. A fonte e especializada em jurisprudencia trabalhista; erros
de acesso, rate limit e mudanca de contrato sao reportados sem bypass.

Ficha tecnica: [dossie do provider](providers/tst_jurisprudencia/README.md).

## `stf_informativo`

Provider para a planilha publica estruturada do Informativo STF.

Escopo atual:

```text
GET /arquivo/cms/informativoSTF/anexo/Informativo_Dados/Dados_InformativosSTF.xlsx
```

Campos extraidos:

```text
informativo
case_number
case_class
rapporteur
redator_acordao
judging_body
judgment_date
title
thesis
summary
news
law_branch
matter
is_repercussao_geral
tema_rg
legislation
ods
```

Exemplo:

```bash
nanojuris buscar "ICMS" --fonte stf_informativo --limite 5
nanojuris buscar "" --fonte stf_informativo --numero "ADI 7632"
```

Este e o caminho mais estavel para conteudo juridico valido do STF quando a API
JSON de jurisprudencia estiver sob AWS WAF. Ele entrega teses e resumos
oficiais sem exigir download de PDF.

Ficha publica: [dossie do provider](providers/stf_informativo/README.md).

## `tjsp_cjsg`

Provider para a Consulta de Jurisprudencia do TJSP/CJSG.

### Escopo

```text
POST /cjsg/resultadoCompleta.do
GET  /cjsg/trocaDePagina.do?tipoDeDecisao=<tipo>&pagina=<n>
GET  /cjsg/getArquivo.do?cdAcordao=<id>&cdForo=<foro>
```

O provider busca a consulta completa publica e normaliza o HTML de resultados
para `JurisprudenceResult`. A paginacao por `trocaDePagina.do` so e usada como
continuacao de uma busca principal publica e valida na mesma sessao; se a fonte
retornar captcha, formulario de controle ou `emptySession.jsp`, o provider para.

Campos extraidos:

```text
numero do processo/recurso
cdAcordao
cdForo
ementa
classe
assunto
relator
comarca
orgao julgador
data de registro
URL de inteiro teor
status de acesso do documento
```

### Uso

```bash
nanojuris buscar "infanticidio" --fonte tjsp_cjsg --tipos acordao --limite 5
```

Python:

```python
from nanojuris import NanoJurisClient

client = NanoJurisClient()
page = client.search("infanticidio", source="tjsp_cjsg", types=["acordao"])
```

### Controle de acesso

O TJSP/CJSG pode exigir captcha, sessao ativa, login ou outro controle. O
NanoJuris nao implementa bypass. Quando isso acontece na busca, o provider
levanta `AccessControlRequiredError`. Quando `getArquivo.do` redireciona para
verificacao de login/CAS, `get_document` retorna documento parcial com
`access_status=login_required`, em vez de marcar texto vazio como publico.

### Teste live opcional

```bash
$env:NANOJURIS_RUN_TJSP_LIVE = "1"
python -m pytest tests/test_tjsp_cjsg_live.py
```

## `tjsp_eproc_jurisprudencia`

Provider para a jurisprudencia publica do eproc/TJSP.

### Escopo

```text
POST /externo_controlador.php?acao=jurisprudencia@jurisprudencia/listar_resultados
```

O provider busca resultados publicos de jurisprudencia do eproc/TJSP e normaliza
cards `.resultadoItem` para `JurisprudenceResult` e `CanonicalDecision`. O texto
extraido vem do proprio card publico de resultado.

Campos enviados:

```text
txtPesquisa
rdoCampo
txtProcesso
dtDecisaoInicio
dtDecisaoFim
dtPublicacaoInicio
dtPublicacaoFim
selOrigem[]
selTipoDocumento[]
```

Campos extraidos:

```text
case_number
decision_type
case_class
rapporteur
judging_body
judgment_date
publication_date
summary
document_url
full_text_url
id_jurisprudencia
source_origin
```

Filtros oficiais validados:

```text
source_origin="colegio_recursal" -> selOrigem[]=3
source_origin="primeiro_grau" -> selOrigem[]=4
source_origin="segundo_grau" -> selOrigem[]=5
types=["acordao"] -> selTipoDocumento[]=1
types=["sentenca"] -> selTipoDocumento[]=5
```

Para pesquisas de jurisprudencia de maior qualidade em SP, prefira combinar
`source_origin="segundo_grau"` com `types=["acordao"]`. Na descoberta limpa,
essa combinacao reduziu a mistura com sentencas de primeiro grau e retornou
cards de acordaos de camaras do TJSP.

`full_text_url` e preservado como metadado quando a fonte publica o informa, mas
na validacao live a rota de inteiro teor separada redirecionou/retornou controle
de acesso. Por isso o provider nao declara suporte a `get_document` para esta
fonte.

### Uso

```bash
nanojuris buscar "infanticidio" --fonte tjsp_eproc_jurisprudencia --limite 5
nanojuris buscar "" --fonte tjsp_eproc_jurisprudencia --numero 4002141-42.2025.8.26.0132
```

Python:

```python
from nanojuris import NanoJurisClient

client = NanoJurisClient()
page = client.search("infanticidio", source="tjsp_eproc_jurisprudencia", page_size=5)
page = client.search(
  "desconsideracao personalidade juridica",
  source="tjsp_eproc_jurisprudencia",
  source_origin="segundo_grau",
  types=["acordao"],
  page_size=5,
)
records = client.search_canonical("infanticidio", source="tjsp_eproc_jurisprudencia")
```

### Controle de acesso

A rota foi validada com `requests` limpo, mas pode mudar hashes, filtros ou
exigir controle de acesso. O NanoJuris nao reutiliza cookies de navegador e nao
implementa bypass.

## `tjsp_esaj_cpopg`

Provider para consulta processual publica de primeiro grau no e-SAJ/TJSP.

### Escopo

```text
GET /cpopg/search.do?cbPesquisa=NUMPROC&...
GET /cpopg/search.do?cbPesquisa=NMPARTE&dadosConsulta.valorConsulta=<nome>
GET /cpopg/search.do?cbPesquisa=NUMOAB&dadosConsulta.valorConsulta=<oab>
GET /cpopg/show.do?processo.codigo=<codigo>&processo.foro=<foro>&processo.numero=<numero>
```

O fluxo por numero CNJ consulta `search.do`, segue o redirect oficial para
`show.do` e normaliza o HTML publico como `CanonicalDocument`. As buscas por
lista usam o seletor oficial `cbPesquisa`; nome da parte (`NMPARTE`) e OAB
(`NUMOAB`) foram reproduzidos com sessao HTTP limpa. Os demais modos expostos
pelo formulario ficam mapeados na API para descoberta responsavel e podem variar
conforme a fonte.

Modos de busca declarados:

```text
case_number -> NUMPROC
party_name -> NMPARTE
party_document -> DOCPARTE
lawyer_name -> NMADVOGADO
oab -> NUMOAB
precatory_number -> PRECATORIA
police_document -> DOCDELEG
cda -> NUMCDA
```

Campos extraidos:

```text
numero do processo
status
classe
assunto
foro
vara
juiz
distribuicao
controle
area
partes em texto publico
movimentacoes em texto publico
partes estruturadas quando o HTML permite
movimentacoes estruturadas quando o HTML permite
papel/nome da parte em resultados de lista
data de recebimento em resultados de lista
URL publica final
```

### Uso

```bash
nanojuris documento "0003938-14.2017.8.26.0323" --fonte tjsp_esaj_cpopg
nanojuris buscar "" --fonte tjsp_esaj_cpopg --numero "0003938-14.2017.8.26.0323"
nanojuris buscar "" --fonte tjsp_esaj_cpopg --parte "ANDERSON DE AZEVEDO GONCALVES" --limite 4
nanojuris buscar "" --fonte tjsp_esaj_cpopg --oab "123456" --limite 2
nanojuris buscar "" --fonte tjsp_esaj_cpopg --parte "ANDERSON DE AZEVEDO GONCALVES" --detalhar --limite 1
```

Python:

```python
from nanojuris import NanoJurisClient

client = NanoJurisClient()
page = client.search(
  "",
  source="tjsp_esaj_cpopg",
  party_name="ANDERSON DE AZEVEDO GONCALVES",
  page_size=4,
)
page_with_detail = client.search(
  "",
  source="tjsp_esaj_cpopg",
  party_name="ANDERSON DE AZEVEDO GONCALVES",
  fetch_details=True,
  page_size=1,
)
document = client.get_document(
  "0003938-14.2017.8.26.0323",
  source="tjsp_esaj_cpopg",
)
```

### Controle de acesso

O provider usa apenas sessao HTTP limpa. Autos, anexos, segredo de justica,
login, captcha e validacoes adicionais sao tratados como limite da fonte, sem
bypass.

Buscas por lista podem acionar mensagem de multiplas consultas simultaneas ou
controle de acesso. Nesses casos o provider falha de forma explicita, sem tentar
reaproveitar cookies, resolver captcha ou simular sessao de navegador.

O teste live aceita dois comportamentos corretos:

- resultados publicos parseados;
- controle de acesso detectado explicitamente.

## `tjac_esaj_cpopg`

Provider para consulta processual publica de primeiro grau no e-SAJ/TJAC.

### Escopo

```text
GET /cpopg/search.do?cbPesquisa=NUMPROC&...
GET /cpopg/show.do?processo.codigo=<codigo>&processo.foro=<foro>&processo.numero=<numero>
```

O fluxo por numero CNJ consulta `search.do`, segue o redirect oficial para
`show.do` e normaliza o HTML publico como `CanonicalDocument`. Nesta primeira
promocao, apenas busca por numero CNJ foi declarada para TJAC; buscas por
nome/OAB ficam pendentes de probe limpo proprio.

Probe limpo promovido:

```text
0001970-91.2024.8.01.0001 -> show.do publico com classe, assunto, foro, vara,
partes, movimentacoes e URL final oficial.
```

Campos extraidos:

```text
numero do processo
status
classe
assunto
foro
vara
distribuicao
controle
area
partes em texto publico
movimentacoes em texto publico
partes estruturadas quando o HTML permite
movimentacoes estruturadas quando o HTML permite
URL publica final
```

### Uso

```bash
nanojuris documento "0001970-91.2024.8.01.0001" --fonte tjac_esaj_cpopg
nanojuris buscar "" --fonte tjac_esaj_cpopg --numero "0001970-91.2024.8.01.0001"
```

Python:

```python
from nanojuris import NanoJurisClient

client = NanoJurisClient()
document = client.get_document(
  "0001970-91.2024.8.01.0001",
  source="tjac_esaj_cpopg",
)
```

### Controle de acesso

O provider usa apenas sessao HTTP limpa. Autos, anexos, segredo de justica,
login, captcha e validacoes adicionais sao tratados como limite da fonte, sem
bypass.
