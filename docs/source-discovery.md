# Source Discovery Workflow

Este fluxo existe para descobrir rotas publicas validas com baixo custo antes de
alterar o core do projeto. A regra operacional e: primeiro reproduzir a entrada
com uma sessao HTTP limpa, depois criar fixture, so entao implementar provider.

Projetos abertos de scraping podem ser usados como mapa de endpoints, payloads e
seletores, desde que a NanoJuris valide tudo novamente com sessao limpa e nao
copie fluxos de captcha, login, cookie ou browser stealth. A ficha
[github-scraper-research.md](github-scraper-research.md) registra essa frente.

Para o mapeamento completo de uma fonte, este documento deve ser lido junto
com o [Route Mapping Playbook v4](route-mapping-playbook.md). Ele adiciona a
matriz obrigatoria de filtros efetivos, paginacao, detalhe, inteiro teor,
canais auxiliares, estados de transporte e criterio de `mapped_broadly`.

A rodada de pesquisa mais recente esta em
[provider-discovery-2026-08-12.md](provider-discovery-2026-08-12.md). Ela
registra novas superficies e separa rotas observadas de contratos prontos para
implementacao.

## Sequencia recomendada

1. Registrar a entrada feita no navegador: URL inicial, numero/termo pesquisado,
   tribunal, sistema e resultado esperado.
2. Testar a mesma rota com `nanojuris probe-rota`, sem cookies,
   cabecalhos privados, HAR, token, captcha solving ou sessao exportada.
3. Confirmar os sinais objetivos:
   - HTTP 200 ou redirect oficial esperado;
   - `final_url` coerente com a fonte;
   - texto esperado presente no HTML;
   - ausencia de bloqueio como pagina exclusiva de captcha, Cloudflare,
     Turnstile, login obrigatorio ou erro de sessao;
   - campos juridicos objetivos visiveis no HTML publico.
4. Salvar uma fixture publica representativa com um exemplo publico minimo.
5. Implementar parser offline contra a fixture.
6. Implementar fetch responsavel no provider.
7. Adicionar diagnostics, capabilities e teste live opcional desligado por
   padrao.

## Criterios para promover uma rota

Uma rota pode virar provider quando a equipe consegue reproduzir a consulta com
`requests` limpo e identificar pelo menos um campo juridico objetivo no corpo da
resposta, como numero do processo, classe, assunto, relator, comarca, orgao
julgador, ementa, tese, movimentacao ou URL publica de documento.

Se a rota exigir captcha, login, token voluvel, Cloudflare/Turnstile ou estado
de navegador, ela deve ser registrada como descoberta bloqueada. O projeto pode
ter parser de HTML salvo legitimamente, mas nao deve automatizar bypass.

## Exemplo

```bash
nanojuris probe-rota \
  "https://esaj.tjsp.jus.br/cpopg/search.do?cbPesquisa=NUMPROC&numeroDigitoAnoUnificado=0003938-14.2017&foroNumeroUnificado=0323&dadosConsulta.valorConsultaNuUnificado=0003938-14.2017.8.26.0323&dadosConsulta.valorConsulta=0003938-14.2017.8.26.0323&dadosConsulta.tipoNuProcesso=UNIFICADO" \
  --expect "0003938-14.2017.8.26.0323" \
  --expect "Ação Penal"
```

Saida esperada: JSON com status, URL final, tamanho, hash, titulo, sinais de
acesso, sinais juridicos, score, `quality_grade`, `route_status` e presenca dos
textos esperados. Se o texto esperado aparecer apenas em formulario ou pagina com
captcha/login/recaptcha, o probe deve retornar `ok: false` e
`route_status: access_control_or_login`.

O playbook completo de priorizacao, score e promocao de rotas esta em
[route-mapping-playbook.md](route-mapping-playbook.md).

## Registro de descoberta: 2026-08-02

### Promovido: Comunica PJe/DJEN

Rota publica:

```text
https://comunicaapi.pje.jus.br/api/v1/comunicacao
```

Probes limpos:

```text
texto=infanticidio&pagina=0&size=5 -> HTTP 200, JSON, count=1260
texto=infanticidio&siglaTribunal=TJSP -> HTTP 200, count=131
texto=infanticidio&siglaTribunal=STJ -> HTTP 200, count=53
numeroProcesso=15007802620258260603 -> HTTP 200, count=3
texto=infanticidio&dataDisponibilizacaoInicio=2026-07-31&dataDisponibilizacaoFim=2026-07-31 -> HTTP 200, count=1
```

Campos observados: `id`, `data_disponibilizacao`, `siglaTribunal`,
`tipoComunicacao`, `nomeOrgao`, `texto`, `numero_processo`, `link`,
`tipoDocumento`, `nomeClasse`, `numeroprocessocommascara`, `destinatarios` e
`destinatarioadvogados`.

Classificacao: provider `comunica_pje`, categoria `judicial_communications`.
Nao e fonte de acordaos; e fonte publica de comunicacoes/publicacoes.

Parametros testados e nao promovidos: `data_inicio` e `data_fim` nao filtraram a
resposta observada; `/api/v1/comunicacao/tipos` retornou HTTP 422; e
`/api/v1/tribunais` retornou HTTP 404.

Analise consolidada de expansao dos providers existentes:
[provider-expansion-analysis-2026-08-02.md](provider-expansion-analysis-2026-08-02.md).

### Promovido: TJAC/CJSG

Probe limpo em 2026-08-03:

```text
POST https://esaj.tjac.jus.br/cjsg/resultadoCompleta.do
dados.buscaInteiroTeor=infanticidio
```

Resultado observado: HTTP 200, HTML com `downloadEmenta`, `divDadosResultado-A`
e `tdResultados`, sem sinais de captcha no fluxo testado. O parser CJSG
normalizou 2 itens da primeira pagina de 5 resultados, incluindo
`tjac-cjsg-2471822-0` e link publico `getArquivo.do?cdAcordao=2471822&cdForo=0`.

Decisao: promover como provider `tjac_cjsg`, categoria
`court_jurisprudence`, reaproveitando o parser CJSG comum.

### Promovido: TJAC/e-SAJ CPOPg

Probe limpo em 2026-08-03:

```text
GET https://esaj.tjac.jus.br/cpopg/search.do
cbPesquisa=NUMPROC
dadosConsulta.valorConsultaNuUnificado=0001970-91.2024.8.01.0001
```

Resultado observado: HTTP 200 com redirect oficial para
`/cpopg/show.do?processo.codigo=01000F4XS0000&processo.foro=1&processo.numero=0001970-91.2024.8.01.0001`.
O HTML contem numero CNJ, classe `Recurso em Sentido Estrito`, status
`Arquivado`, assunto `Homicídio Simples`, foro Rio Branco, vara, partes e
movimentacoes. A pagina inclui scripts de login/captcha do e-SAJ, mas o conteudo
processual publico apareceu no corpo sem exigir resolucao de captcha.

Decisao: promover como provider `tjac_esaj_cpopg`, categoria `case_lookup`,
limitado inicialmente a busca por numero CNJ. Nome/OAB e outros modos ficam
pendentes de probe limpo proprio.

### Promovido: TJAL/CJSG

Probe limpo em 2026-08-03:

```text
POST https://www2.tjal.jus.br/cjsg/resultadoCompleta.do
dados.buscaInteiroTeor=infanticidio
```

Resultado observado: HTTP 200, HTML com `downloadEmenta`, `divDadosResultado-A`
e `tdResultados`, sem sinais de captcha no fluxo testado. O parser CJSG
normalizou 2 itens da primeira pagina de 12 resultados, incluindo
`tjal-cjsg-716164-0` e link publico `getArquivo.do?cdAcordao=716164&cdForo=0`.

Decisao: promover como provider `tjal_cjsg`, categoria
`court_jurisprudence`, reaproveitando o parser CJSG comum.

### Promovido: TJAM/CJSG

Probe limpo em 2026-08-03:

```text
POST https://consultasaj.tjam.jus.br/cjsg/resultadoCompleta.do
dados.buscaInteiroTeor=infanticidio
```

Resultado observado: HTTP 200, HTML com `downloadEmenta`, `divDadosResultado-A`
e `tdResultados`, sem sinais de captcha no fluxo testado. O parser CJSG
normalizou 2 itens da primeira pagina de 12 resultados, incluindo
`tjam-cjsg-3287961-0` e link publico `getArquivo.do?cdAcordao=3287961&cdForo=0`.

Decisao: promover como provider `tjam_cjsg`, categoria
`court_jurisprudence`, reaproveitando o parser CJSG comum.

### Promovido: TJMS/CJSG

Rota publica validada a partir de pesquisa em projetos abertos:

```text
https://esaj.tjms.jus.br/cjsg/resultadoCompleta.do
```

Probe limpo:

```text
dados.buscaInteiroTeor=infanticidio -> HTTP 200, HTML CJSG, 22 resultados
```

O parser CJSG existente leu classe, assunto, comarca, relator, orgao julgador,
datas, ementa e `getArquivo.do?cdAcordao=<id>&cdForo=0`. Classificacao:
provider `tjms_cjsg`, categoria `court_jurisprudence`.

### Promovido: STM/JMU Jurisprudencia

Probe limpo em 2026-08-03:

```text
GET https://jurisprudencia.stm.jus.br/consulta.php?search_filter_option=jurisprudencia&search_filter=busca_avancada&q=&fqx_ementa=deser%C3%A7%C3%A3o
```

Resultado observado: HTTP 200, HTML publico sem sinais de captcha ou reCAPTCHA,
com `25` paineis de resultado na primeira pagina. Cada painel contem numero CNJ,
classe, relator, assunto, datas, ementa em `blockquote`, UUID e botao
`Inteiro Teor` apontando para
`https://eproc2g.stm.jus.br/eproc_2g_prod/externo_controlador.php?acao=visualizar_acordao&uuid=<uuid>`.

Decisao: promover como provider `stm_jurisprudencia`, categoria
`court_jurisprudence`, com `get_document` para o HTML publico de inteiro teor.

### Promovido: TRF4/eproc Jurisprudencia

Probe limpo em 2026-08-03:

```text
GET  https://jurisprudencia.trf4.jus.br/
POST https://jurisprudencia.trf4.jus.br/eproc2trf4/externo_controlador.php?acao=jurisprudencia@jurisprudencia/listar_resultados
txtPesquisa=deserção&rdoCampo=I
```

Resultado observado: HTTP 200, HTML publico sem sinais de captcha ou reCAPTCHA,
com `10` cards `.resultadoItem` na primeira pagina e indicacao textual de
`Documento 1 de 21090`. Os cards trazem numero CNJ, classe, UF, orgao julgador,
datas, relator, resumo da decisao, link de acompanhamento processual e
`data-link` para `download_inteiro_teor&id_jurisprudencia=<id>`.

Probe de inteiro teor:

```text
GET https://jurisprudencia.trf4.jus.br/eproc2trf4/externo_controlador.php?acao=jurisprudencia@jurisprudencia/download_inteiro_teor&id_jurisprudencia=41785517964304066196063791796
```

Resultado observado: HTTP 200, HTML publico, sem captcha/login, contendo
`5037898-36.2025.4.04.0000`, `deserção` e texto de decisao.

Decisao: promover como provider `trf4_eproc_jurisprudencia`, categoria
`court_jurisprudence`, reaproveitando parser eproc parametrizado e declarando
`get_document` para inteiro teor publico.

### Expandido: TJSP/e-SAJ CPOPg

Rotas publicas validas:

```text
https://esaj.tjsp.jus.br/cpopg/search.do
https://esaj.tjsp.jus.br/cpopg/show.do
```

Probes limpos:

```text
cbPesquisa=NUMPROC&dadosConsulta.valorConsultaNuUnificado=0003938-14.2017.8.26.0323 -> detalhe publico
cbPesquisa=NMPARTE&dadosConsulta.valorConsulta=ANDERSON DE AZEVEDO GONCALVES -> 4 links de processo
cbPesquisa=NUMOAB&dadosConsulta.valorConsulta=123456 -> lista publica parseavel
```

Campos observados em lista: numero CNJ, papel da parte, nome, classe, assunto,
data de recebimento, vara e link `show.do`. Campos observados no detalhe:
classe, area, assunto, distribuicao, controle, foro, vara, juiz, situacao,
partes e movimentacoes.

Classificacao: provider `tjsp_esaj_cpopg`, categoria `case_lookup`. Os demais
modos expostos pelo formulario foram mapeados, mas devem continuar sujeitos a
smoke limpo antes de qualquer promessa de estabilidade.

### Promovido: TJSP/NugepNac IRDR/IAC

Rotas publicas oficiais:

```text
GET https://www.tjsp.jus.br/NugepNac/Irdr
GET https://www.tjsp.jus.br/NugepNac/Iac
GET https://www.tjsp.jus.br/NugepNac/(Irdr|Iac)/DetalheTema?codigoNoticia=<id>&pagina=1
```

Resultado observado: paginas HTML institucionais publicas, sem captcha/login no
catalogo e no detalhe do tema. O detalhe contem campos juridicos objetivos como
processo paradigma, assunto, orgao julgador, relator, datas, suspensao, questao
submetida e tese firmada.

Decisao: promover como provider `tjsp_nugepnac`, categoria `court_precedents`,
canonicalizado como `CanonicalPrecedent`. Links de acordaos CJSG relacionados
continuam classificados como parciais quando redirecionam para verificacao de
acesso.

### Promovido: TCE-SP Jurisprudencia Estatica

Rotas publicas oficiais:

```text
GET https://www.tce.sp.gov.br/boletim-de-jurisprudencia/sumulas
GET https://www.tce.sp.gov.br/boletim-de-jurisprudencia/publicacoes
GET https://www.tce.sp.gov.br/boletim-de-jurisprudencia/indice-alfabetico-remissivo
```

Resultado observado: paginas HTML publicas com repertorio de sumulas e lista de
boletins de jurisprudencia. A busca dinamica `/jurisprudencia/pesquisar` contem
reCAPTCHA no fluxo observado e nao foi promovida.

Decisao: promover como provider `tce_sp_jurisprudencia`, categoria
`administrative_jurisprudence`, cobrindo catalogos estaticos publicos de sumulas
e boletins.

### Promovido: TRE-SP Temas Selecionados

Rotas publicas oficiais:

```text
GET https://www.tre-sp.jus.br/jurisprudencia/temas-selecionados-1
GET https://www.tre-sp.jus.br/jurisprudencia/arquivos-da-secao-de-jurisprudencia-sp/temas-selecionados/<slug>
```

Resultado observado: indice e paginas tematicas publicas, sem captcha/login no
fluxo estatico. As paginas contem tema, resumo textual e links de decisoes ou
documentos selecionados.

Decisao: promover como provider `tre_sp_temas`, categoria
`electoral_jurisprudence`, para curadoria tematica eleitoral paulista. Nao e
busca geral de acordaos.

## Registro de descoberta: 2026-08-07 - estados antes pouco mapeados

A rodada complementar esta consolidada em
[state-court-route-mapping-2026-08-07.md](state-court-route-mapping-2026-08-07.md).
Ela revisou TJES, TJMT, TJPA, TJPB, TJPE, TJPI, TJRO, TJRR e TJSE sem depender
dos antigos palpites CJSG.

Achados promovidos para a fila tecnica:

| Fonte | Rota oficial | Classificacao |
| --- | --- | --- |
| TJPI/JusPI | `https://jurisprudencia.tjpi.jus.br/jurisprudences/search?q=dano%20moral` | candidato forte de provider HTML |
| TJRR/Juris | `https://jurisprudencia.tjrr.jus.br/index.xhtml` | postback publico reproduzido; candidato pronto para fixture JSF |
| TJMT/Jurisprudencia | `https://jurisprudencia.tjmt.jus.br/` | candidato de API moderna; header/payload pendente |
| TJPA/Jurisprudencia | `https://jurisprudencia.tjpa.jus.br/` | BFF publico com busca textual JSON, catalogos e recentes; candidato pronto para fixture |
| TJCE/CJSG | `https://esaj.tjce.jus.br/cjsg/resultadoCompleta.do` | consulta e-SAJ oficial com filtros ricos e inteiro teor documentado; candidato precisa HAR apos reset TLS |
| TJCE Informativos | `https://www.tjce.jus.br/informativo-jurisprudencia/` | HTML oficial HTTP 200 com edicoes, destaques, metadados decisorios e PDFs | candidato pronto para fixture curada |
| TRF3 Jurisprudencia | `https://web.trf3.jus.br/jurisprudencia/home/index/1` | interface oficial com pesquisa, filtros e links CJF/TNU/Sumulas; HTTP limpo excedeu 45s | candidato nivel B, requer captura de rede |
| TJPB/PJe Jurisprudencia | `https://pje-jurisprudencia.tjpb.jus.br/` | candidato PJe com risco WAF a validar |
| TJPE | `https://portal.tjpe.jus.br/servicos/consulta/sumulas` | catalogo publico de sumulas/precedentes |
| TJSE | `https://www.tjse.jus.br/portal/consultas/jurisprudencia/judicial` | entrada oficial de jurisprudencia judicial |
| TJRO/LIAME | `https://liame.tjro.jus.br/` | candidato de precedentes/catalogo |

TJES permaneceu inconclusivo: `https://sistemas.tjes.jus.br/portaltj/Pesquisa.aspx`
deu timeout em 45s, e a rota ColdFusion antiga retornou HTTP 404. Deve ser
retestado com janela maior antes de qualquer provider.

### Bloqueado ou pendente

| Fonte | Resultado do probe limpo | Classificacao |
| --- | --- | --- |
| TJSP/CJSG GET com termo | HTTP 200, termo ecoado, mas `captcha`, `recaptcha` e `login` presentes | acesso controlado; nao promover por esse GET |
| STJ/SCON GET | HTTP 403 com verificacao automatica/JavaScript/cookies | acesso controlado sem bypass |
| DataJud/CNJ API publica | HTTP 401, `missing authentication credentials`, aceita Basic/Bearer/ApiKey | requer credencial/APIKey |
| STF jurisprudencia SPA | HAR posterior revelou `POST /api/search/search`; teste limpo ainda encontrou SSL/WAF HTTP 202 | provider inicial `stf_juris` implementado com fixture e diagnostico sem bypass |
| BNP/Pangea termos criminais | HTTP 400 para `infanticidio`/`homicidio`, embora outros termos funcionem | aprofundar validacao de payload/diagnostico |
| TJMS/CJSG data de publicacao | `dados.dtPublicacaoInicio/Fim=01/01/1900..31/12/2099` zerou busca que sem data retornou 22 resultados | nao promover sem novo contrato validado |
| TST jurisprudencia SPA | `https://jurisprudencia.tst.jus.br/config.json` retorna `base_url=https://jurisprudencia-backend2.tst.jus.br`; `POST /rest/pesquisa-textual/1/2` responde JSON quando payload nao filtra, mas campos reais da SPA (`e`, `ou`, `termoExato`, `ementa`) retornaram HTTP 400 com corpo vazio | candidato tecnico; precisa reproduzir payload exato da SPA antes de provider |
| TCU pesquisa textual | SPA `https://pesquisa.apps.tcu.gov.br/` retorna HTTP 200; bundle aponta `/api/publico/entidades/busca`; GET retorna HTTP 405 e `Allow: POST,OPTIONS` | candidato tecnico; precisa reproduzir payload POST publico antes de provider |
| TSE jurisprudencia por assunto | `https://www.tse.jus.br/jurisprudencia/jurisprudencia-por-assunto` retorna HTTP 200 com pagina institucional publica e links de servicos de jurisprudencia | candidato documental/tematico; pode virar catalogo estatico apos fixture |
| TSE jurisprudencia SPA | bundle Angular aponta para `https://sjur-pesquisa-api.tse.jus.br/{tribunal}/sjur-pesquisa-backend/rest/public/pesquisa`; `POST /public/pesquisa` com JSON de busca retorna HTTP 200 com `Falha na verificação antirrobô.` e resultados vazios | acesso antirrobo; nao promover sem fluxo publico limpo sem captcha |
| TJAL/TJAM e-SAJ CPOPg com numeros CJSG | `0805753-97.2025.8.02.0000` e `0003949-10.2024.8.04.0000` retornaram formulario com mensagem de inexistencia para CPOPg 1G | nao promover sem numero publico de primeiro grau ou rota CPOSg validada |
| TJMS e-SAJ CPOPg com numero CJSG | `0000008-16.2011.8.12.0055` retornou pagina E-SAJ sem numero/processo no corpo | nao promover sem nova rota ou caso publico validado |
| TJAL/TJAC e-SAJ CPOSg5 | `/cposg5/search.do` retornou HTTP 200 e ecoou numeros de processo, mas como formulario com mensagem `O campo Número do Processo deve ser preenchido`, nao como detalhe publico | candidato; precisa payload/rota real de detalhe CPOSg antes de provider |
| TJAM e-SAJ CPOSg | `/cposg/search.do` e `/cposg/open.do` retornaram HTTP 503; `/cposg5/search.do` redirecionou para portal | fonte instavel/nao promovida |
| TNU/CJF | `https://www.cjf.jus.br/jurisprudencia/tnu/` fechou a conexao sem resposta no probe limpo | nao promover sem nova rota publica estavel |
| TJRJ/eJuris | `https://www3.tjrj.jus.br/ejuris/ConsultarJurisprudencia.aspx` retorna WebForms publico com `__VIEWSTATE`, campos de pesquisa e script `https://www.google.com/recaptcha/api.js?render=...` | diagnostics-first; nao promover sem fluxo limpo sem reCAPTCHA |
| TJCE/CJSG | conexao resetada pelo host remoto em `https://esaj.tjce.jus.br/cjsg/resultadoCompleta.do`; pagina oficial e documentacao permanecem acessiveis por outras superficies | candidato com contrato pendente; ver dossie proprio e nao forcar reset |
| TJSC/CJSG | DNS falhou para `https://esaj.tjsc.jus.br/cjsg/resultadoCompleta.do` | endpoint candidato invalido |
| TJBA/CJSG | falha de handshake SSL em `https://esaj.tjba.jus.br/cjsg/resultadoCompleta.do` | nao promover sem perfil SSL/endpoint correto |
| TJRN/CJSG | HTTP 403 Access Denied em `https://esaj.tjrn.jus.br/cjsg/resultadoCompleta.do` | acesso bloqueado no probe limpo |
| TJAP/TJPE/TJSE/CJSG | HTTP 404 nos endpoints `/cjsg/resultadoCompleta.do` testados | endpoints CJSG invalidos; TJPE/TJSE ja possuem novas entradas oficiais documentais |
| TJES/CJSG | HTTP 503 em `https://sistemas.tjes.jus.br/cjsg/resultadoCompleta.do` | endpoint CJSG indisponivel; portal atual `Pesquisa.aspx` ainda inconclusivo |
| TJMA/CJSG | HTTP 404 em `https://jurisconsult.tjma.jus.br/cjsg/resultadoCompleta.do` | endpoint candidato invalido |
| TJRO/CJSG | conexao fechada sem resposta em `https://webapp.tjro.jus.br/cjsg/resultadoCompleta.do` | nao promover CJSG; LIAME foi documentado como rota de precedentes |
| TJMT/TJPA/TJRR/CJSG | HTTP 405 nos endpoints `/cjsg/resultadoCompleta.do` testados | nao usar CJSG; novas rotas oficiais TJMT/TJPA/TJRR foram documentadas |
| TJTO/CJSG | HTTP 403 em `https://jurisprudencia.tjto.jus.br/cjsg/resultadoCompleta.do` | acesso bloqueado no probe limpo |
