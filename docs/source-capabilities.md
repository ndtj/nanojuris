# Source Capabilities

NanoJuris declara capacidades por fonte para que advogados, pesquisadores,
pipelines e agentes de IA saibam exatamente o que cada provider cobre antes de
executar consultas.

Essa camada e deliberadamente objetiva: ela descreve busca, formatos, campos,
status de acesso e limites. Ela nao interpreta merito juridico.

Para priorizacao nacional por familia de sistema e tribunal, veja
[provider-coverage-map.md](provider-coverage-map.md).
Para maturidade, lacunas e dossies tecnicos por provider, veja
[source-contracts.md](source-contracts.md).
Para o portao de qualidade Ouro e os contratos de completude, veja
[gold-maturity.md](gold-maturity.md).
Para uso por agentes de IA com MCP local, veja
[ai-agent-usage.md](ai-agent-usage.md).

## Por que existe

Um projeto nacional e escalavel precisa responder perguntas operacionais sem
exigir leitura do codigo:

- Quais fontes estao registradas?
- Quais tribunais brasileiros existem no catalogo da lib?
- Que tipo de documento cada fonte retorna?
- Quais campos sao extraidos?
- Ha inteiro teor publico?
- O provider implementa `get_document` sem depender de bypass?
- A fonte pode exigir captcha ou login?
- Que endpoint ou rota publica sustenta a extracao?
- A fonte e adequada para CLI, lote ou MCP?

## Uso via Python

```python
from nanojuris import NanoJurisClient

client = NanoJurisClient()

for source in client.list_sources():
    print(source.source, source.display_name)
    print(source.document_types)
    print(source.extracted_fields)
```

Detalhar uma fonte:

```python
capabilities = client.get_capabilities(source="tjsp_cjsg")
print(capabilities.to_dict())
```

Listar tribunais brasileiros conhecidos por ramo, UF, familia tecnica ou status
de provider:

```python
from nanojuris import list_courts

for court in list_courts(branch="state", state="SP"):
    print(court.code, court.name, court.provider_status)
```

## Uso via CLI

Listar todas as fontes:

```bash
nanojuris fontes
nanojuris tribunais --implementados
```

Detalhar uma fonte:

```bash
nanojuris fontes --fonte tjsp_cjsg
```

Diagnostico de capacidades e limites:

```bash
nanojuris diagnostico --fonte bnp_pangea
```

Auditoria de contratos, maturidade e lacunas:

```bash
nanojuris contratos
nanojuris contratos --fonte tjdf_juris
nanojuris contratos --resumo
```

## Campos declarados

Cada provider retorna um `ProviderCapabilities` com:

- `source`: identificador interno do provider;
- `display_name`: nome legivel da fonte;
- `source_url`: URL base publica;
- `category`: categoria da fonte;
- `search_modes`: modos de busca suportados;
- `document_types`: tipos de documento cobertos;
- `content_formats`: formatos de origem;
- `canonical_records`: modelos canonicos gerados;
- `extracted_fields`: campos objetivos extraidos;
- `access_statuses`: status de acesso possiveis;
- `endpoints`: endpoints ou rotas publicas usadas;
- `supports_full_text`: se ha tentativa de obter inteiro teor publico;
- `supports_catalog`: se a fonte expoe catalogo/parametros;
- `supports_suggestions`: se a fonte expoe sugestoes;
- `supports_live_tests`: se ha teste live opcional;
- `supports_unified_search`: opt-in explicito para o federador Python;
- `supports_mcp`: se a fonte deve ser exposta no MCP;
- `supports_cli`: se a fonte deve aparecer nas interfaces CLI;
- `supports_studio`: se a fonte deve aparecer no Studio;
- `pagination_mode`: semantica de pagina (`page`, `offset`, `local_window` ou
  `unknown`);
- `completeness_contract`: evidencia usada para declarar completude da janela;

Esses quatro campos sao independentes e tem default `False`. Um provider novo
nao entra em nenhuma superficie de produto por omissao.
- `limitations`: limitacoes tecnicas conhecidas;
- `responsible_use`: cuidados de uso responsavel.

## Fontes atuais

### `bnp_pangea`

Categoria: precedentes qualificados.

Cobertura objetiva:

- texto, tribunal, especie, numero e periodo;
- precedentes, teses, questoes, status e processos paradigma;
- catalogo publico de orgaos e especies;
- sugestoes quando o endpoint publico estiver disponivel.

### `comunica_pje`

Categoria: comunicacoes judiciais publicas.

Cobertura objetiva:

- busca textual em comunicacoes do Comunica PJe/DJEN;
- filtro por tribunal via `siglaTribunal`;
- busca por numero de processo via `numeroProcesso` sem mascara;
- filtro por data de disponibilizacao via `dataDisponibilizacaoInicio` e
    `dataDisponibilizacaoFim`;
- tipo de comunicacao/documento, orgao, classe, texto, data de disponibilizacao,
  numero do processo e link publico;
- canonicalizacao como `CanonicalDecision` por compatibilidade operacional,
  preservando `type="comunicacao"` para diferenciar de acordaos.

Estado atual: provider implementado com fixture offline e busca live reproduzida
em sessao limpa para `infanticidio`, `TJSP`, `STJ`, numero de processo e filtro
por data de disponibilizacao.

### `tjdf_juris`

Categoria: jurisprudencia de tribunal.

Cobertura objetiva:

- busca textual no TJDFT/SISTJ por HTML publico;
- fluxo em duas etapas: pagina de contagem, pagina de resultados e detalhe por
    `numeroDoDocumento`;
- acordao, numero CNJ, numero de registro, relator, orgao julgador, data de
    julgamento, data de publicacao/intimacao, ementa e resultado do julgamento;
- canonicalizacao para `CanonicalDecision` e detalhe HTML via `get_document`;
- rota validada em sessao HTTP limpa, sem captcha ou login no fluxo testado.

Estado atual: provider implementado com fixture offline e rota live reproduzida
para `infanticidio` durante a descoberta baseada nos scripts CourtsBR.

### `tnu_eproc_jurisprudencia`, `trf2_eproc_jurisprudencia`, `trf6_eproc_jurisprudencia`

Categoria: jurisprudencia federal eproc.

Cobertura objetiva:

- busca textual por `POST /externo_controlador.php?acao=jurisprudencia@jurisprudencia/listar_resultados`;
- filtros publicos de texto, numero de processo, datas e tipo documental;
- TNU: origem `TNU`;
- TRF2: origens `TRF2`, `TRU2` e Turmas Recursais;
- TRF6: origens `TRF6`, `TRU6`, Turmas Recursais e Varas Federais;
- numero CNJ, tipo decisorio, classe, relator quando presente, orgao julgador,
    datas, ementa/decisao, `id_jurisprudencia` e link de inteiro teor;
- canonicalizacao para `CanonicalDecision`;
- `get_document` para a rota publica de inteiro teor por `id_jurisprudencia`,
    quando a instancia responder sem controle de acesso.

Estado atual: providers implementados com fixtures publicas representativas para
`aposentadoria`; probes live em 2026-08-07 retornaram grade A nas tres fontes,
com `resultadoItem`, ementa, relator/orgao quando disponiveis e link de inteiro
teor sem captcha/login no fluxo de busca.

### `tjgo_projudi_jurisprudencia`

Categoria: jurisprudencia de tribunal.

Cobertura objetiva:

- busca textual no PROJUDI/TJGO por `POST /ConsultaJurisprudencia`;
- filtros publicos de instancia, numero de processo, tipo de ato e datas;
- numero CNJ, magistrado/relator, orgao/unidade, tipo de ato, publicacao,
    `Id_Arquivo` e inteiro teor embutido no HTML do card;
- canonicalizacao para `CanonicalDecision`;
- texto publico preservado sem redaction automatica pelo provider;
- rota validada em sessao HTTP limpa para `dano moral`, com alto volume de
    resultados e cards reais.

Estado atual: provider implementado com fixtures reais de sucesso e
vazio/formulario sem cards. Download separado por `Id_Arquivo` segue pendente
ate haver contrato publico limpo.

### `tjms_cjsg`

Categoria: jurisprudencia de tribunal.

Cobertura objetiva:

- busca textual no TJMS/CJSG por HTML publico;
- reaproveitamento do contrato CJSG/e-SAJ ja usado em `tjsp_cjsg`;
- acordao, numero do processo, classe, assunto, comarca, relator, orgao julgador,
    data de julgamento/publicacao, ementa e URL de inteiro teor;
- canonicalizacao para `CanonicalDecision`;
- rota validada em sessao HTTP limpa para `infanticidio`, com 22 resultados
    observados.

Estado atual: provider implementado com fixture offline reaproveitando o contrato
CJSG e smoke live reproduzido durante pesquisa de projetos abertos no GitHub.

### `tjpi_juspi`

Categoria: jurisprudencia de tribunal.

Cobertura objetiva:

- busca textual no TJPI/JusPI por HTML publico server-side;
- paginacao por `page` observada nos links oficiais da propria fonte;
- filtros publicos de tipo, relator, classe, orgao e periodo quando enviados
    conforme formulario;
- numero CNJ, tipo decisorio, assunto, classe, relator, orgao/gabinete, data de
    publicacao, ementa/resumo e URL de detalhe;
- detalhe publico em `/jurisprudences/<id>/public` convertido para
    `CanonicalDocument` com hash, tamanho, trace e metadados;
- canonicalizacao para `CanonicalDecision` nos resultados.

Estado atual: provider implementado com fixtures offline para sucesso, vazio e
detalhe publico. A rota live foi reproduzida com `requests` limpo para
`dano moral`, retornando resultados reais e inteiro teor HTML publico.

### `tjsp_cjsg`

Categoria: jurisprudencia de tribunal.

Cobertura objetiva:

- busca por inteiro teor, ementa, numero e periodo;
- paginacao `trocaDePagina.do` apenas como continuacao de busca publica valida;
- acordaos, monocraticas e homologacoes quando retornados pela fonte;
- classe, assunto, relator, comarca, orgao julgador, data e URL de inteiro teor;
- `get_document` com texto limpo de HTML publico, hash, tamanho, trace e
  metadados tecnicos;
- diagnostico de retorno ao formulario, campos `recaptcha_response_token`,
- `uuidCaptcha`, rota `captchaControleAcesso`, `emptySession.jsp`, scripts de
  login e containers de resultado;
- `get_document` marca redirecionamento para login/CAS como
  `access_status=login_required`;
- deteccao de captcha/controle de acesso sem bypass.

### `tjsp_esaj_cpopg`

Categoria: consulta processual publica.

Cobertura objetiva:

- consulta de processo de primeiro grau por numero CNJ;
- busca de lista por nome da parte (`NMPARTE`) e OAB (`NUMOAB`) reproduzida com
    sessao HTTP limpa;
- modos de formulario mapeados para documento da parte (`DOCPARTE`), advogado
    (`NMADVOGADO`), precatoria (`PRECATORIA`), documento de delegacia (`DOCDELEG`)
    e CDA (`NUMCDA`), sujeitos a variacao de acesso da fonte;
- redirect oficial `search.do` para `show.do` quando a fonte encontra o caso;
- classe, assunto, foro, vara, juiz, distribuicao, controle, area, partes e
        movimentacoes em texto publico;
- partes e movimentacoes estruturadas quando o HTML publico contem seletores
    estaveis;
- resultados de lista com numero CNJ, papel, nome da parte, classe, assunto,
    data de recebimento, vara e URL publica;
- normalizacao para `CanonicalDocument` e resumo em `JurisprudenceResult`;
- deteccao de captcha, multiplas consultas simultaneas e controle de acesso sem
    bypass.

Estado atual: provider expandido para detalhe por numero CNJ e listas CPOPg.
Smoke live reproduzido para `NMPARTE` com 4 resultados e `NUMOAB` com 2
resultados durante a descoberta.

### `tjac_esaj_cpopg`

Categoria: consulta processual publica.

Cobertura objetiva:

- consulta de processo de primeiro grau por numero CNJ;
- redirect oficial `search.do` para `show.do` quando a fonte encontra o caso;
- classe, assunto, foro, vara, distribuicao, controle, area, partes e
    movimentacoes em texto publico;
- partes e movimentacoes estruturadas quando o HTML publico contem seletores
    estaveis;
- normalizacao para `CanonicalDocument` e resumo em `JurisprudenceResult`;
- deteccao de captcha, login e controle de acesso sem bypass.

Estado atual: provider implementado para detalhe por numero CNJ. Smoke limpo
reproduzido para `0001970-91.2024.8.01.0001`, com redirect oficial para
`show.do` e campos processuais publicos.

### `tjsp_nugepnac`

Categoria: precedentes qualificados de tribunal estadual.

Cobertura objetiva:

- catalogos oficiais TJSP/NugepNac de IRDR e IAC;
- pagina de detalhe por `codigoNoticia`;
- numero do tema, tipo, status, processo paradigma, assunto, orgao julgador,
    relator, datas, questao submetida e tese firmada;
- links relacionados preservados no `raw` para auditoria;
- canonicalizacao para `CanonicalPrecedent`;
- acesso limpo ao catalogo e detalhe; inteiro teor CJSG relacionado pode exigir
    verificacao de acesso e nao e contornado.

Estado atual: provider implementado com parser offline e fixture minima para
lista/detalhe de IRDR.

### `tce_sp_jurisprudencia`

Categoria: jurisprudencia administrativa e contas publicas.

Cobertura objetiva:

- repertorio publico de sumulas do TCE-SP;
- publicacoes do boletim de jurisprudencia;
- numero da sumula, enunciado, historico/fundamento quando presente, edicao do
    boletim e URL publica da publicacao;
- canonicalizacao para `CanonicalPrecedent` por representar enunciados e
    catalogos jurisprudenciais;
- bloqueio explicito da busca dinamica com reCAPTCHA observada em
    `/jurisprudencia/pesquisar`.

Estado atual: provider implementado para catalogos estaticos publicos, com
fixture offline para sumulas e boletins.

### `tre_sp_temas`

Categoria: jurisprudencia eleitoral tematica.

Cobertura objetiva:

- indice publico de temas selecionados do TRE-SP;
- paginas tematicas por slug;
- titulo do tema, resumo textual e links de decisoes/documentos selecionados;
- canonicalizacao para `CanonicalPrecedent` como catalogo curado de temas;
- fonte adequada para triagem tematica, nao para busca geral de acordaos.

Estado atual: provider implementado com parser offline para indice e pagina de
tema selecionado.

### `stj_scon`

Categoria: jurisprudencia de tribunal superior.

Cobertura objetiva inicial:

- acordaos publicos do STJ/SCON por HTML;
- classe processual, numero, registro, relator, orgao julgador, datas, ementa e
    URL de documento quando disponivel;
- parser offline com fixture publica representativa;
- canonicalizacao para `CanonicalDecision`;
- deteccao de captcha/controle de acesso sem bypass.

Estado atual: implementacao inicial. A busca live deve ser tratada como opt-in e
validada por fixture antes de expandir inteiro teor.

### `stj_informativo`

Categoria: jurisprudencia de tribunal superior.

Cobertura objetiva:

- busca textual em notas oficiais do Informativo de Jurisprudencia do STJ;
- numero do informativo, periodo, orgao julgador, processo citado, relator, data
    de julgamento, titulo e resumo da nota;
- rota publica validada sem cookies ou tokens para `infanticidio`;
- canonicalizacao como `CanonicalDecision`, preservando `type="informativo"`.

Estado atual: provider implementado com fixture offline para o Informativo n.
507 e rota live reproduzida durante a descoberta. Links de acordaos podem
depender do SCON e, se houver verificacao automatica, sao tratados como limite
da fonte.

### `stf_juris`

Categoria: jurisprudencia de tribunal superior.

Cobertura objetiva inicial:

- acordaos publicos do STF via API JSON observada no frontend oficial;
- titulo, numero processual, classe, relator, orgao julgador, datas, ementa,
    partes, legislacao citada, URL do inteiro teor e URL de acompanhamento;
- highlights retornados pela busca;
- canonicalizacao para `CanonicalDecision`;
- diagnostico separado para falha SSL local e desafio AWS WAF, sem bypass.

Estado atual: provider implementado por contrato HAR/fixture. A busca live deve
ser tratada como opt-in, porque a conexao limpa deste ambiente recebeu AWS WAF
HTTP 202 e a URL de inteiro teor retornou HTTP 403.

### `stf_informativo`

Categoria: jurisprudencia de tribunal superior.

Cobertura objetiva:

- download da planilha publica oficial `Dados_InformativosSTF.xlsx`;
- filtro local por texto e numero de processo;
- classe, numero, UF, relator, redator do acordao, orgao julgador, data,
    titulo, tese, resumo, noticia, ramo do direito, materia, repercussao geral,
    tema RG, legislacao, ODS e marcador Covid-19;
- conversao de serial Excel para ISO date;
- canonicalizacao como `CanonicalDecision`, preservando `type="informativo"`.

Estado atual: provider implementado com parser XLSX por biblioteca padrao,
fixture offline e contrato documentado. E a fonte preferencial para agentes de
IA quando a pergunta exige tese/resumo oficial do STF e nao exige voto integral.
