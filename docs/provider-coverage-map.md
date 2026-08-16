# Provider Coverage Map

Este documento mapeia o contexto brasileiro de obtencao publica de dados de
jurisprudencia para orientar a expansao da NanoJuris. Ele nao promete cobertura
total imediata; separa fontes implementadas, fontes prioritarias e familias de
sistemas que exigem pesquisa por tribunal.

Escopo da NanoJuris: extrair dados publicos, normalizar, persistir e expor por
Python, CLI, exporters e MCP. O projeto nao deve contornar captcha, login,
segredo de justica ou controles de acesso.

## Familias de obtencao publica

| Familia | Exemplos | Melhor uso | Complexidade | Observacoes |
| --- | --- | --- | --- | --- |
| APIs publicas/documentadas | BNP/Pangea e APIs jurisprudenciais | precedentes qualificados e jurisprudencia textual | media | melhor ponto de partida quando endpoints aceitam payloads estaveis |
| Portais de jurisprudencia dos tribunais superiores | STF, STJ, TST, TSE, STM | acordaos, sumulas, repetitivos, repercussao geral | media/alta | cada tribunal tem contratos e filtros proprios |
| Portais HTML legados | TJSP/CJSG, e-SAJ, consultas estaduais | jurisprudencia estadual e inteiro teor quando publico | alta | HTML muda, pode haver captcha/controle de acesso |
| Plataformas de jurisprudencia | eproc, PJe, Projudi, e-SAJ CJSG | acordaos, ementas e inteiro teor publico | alta | frequentemente exigem validacao humana ou limitam documentos |
| Dados abertos e repositórios institucionais | STJ dados abertos e portais institucionais | bases historicas, metadados e estudos | media | requer dicionario de campos e versionamento de datasets |

## Prioridade de implementacao

| Prioridade | Fonte/familia | Justificativa | Saida esperada |
| --- | --- | --- | --- |
| P0 | BNP/Pangea | ja implementado; precedentes qualificados nacionais | `CanonicalPrecedent`, decisoes vinculadas quando disponiveis |
| P0 | TJDFT/SISTJ | ja implementado; rota limpa validada a partir de inteligencia CourtsBR | acordaos como `CanonicalDecision` e detalhe HTML publico |
| P0 | TJMS/CJSG | ja implementado; rota limpa validada a partir de projeto aberto TJMS/e-SAJ | acordaos como `CanonicalDecision` e inteiro teor quando publico |
| P0 | TJSP/CJSG | ja implementado parcialmente; maior tribunal estadual; HTML real validado | `CanonicalDecision`, `CanonicalDocument` quando publico |
| P0 | TJSP/NugepNac | ja implementado; catalogo oficial limpo de IRDR/IAC | `CanonicalPrecedent` com tema, questao e tese |
| P0 | TCE-SP jurisprudencia estatica | ja implementado; sumulas e boletins publicos sem captcha | `CanonicalPrecedent` administrativo |
| P0 | TRE-SP temas selecionados | ja implementado; curadoria tematica eleitoral publica | `CanonicalPrecedent` tematico |
| P0 | TJRS jurisprudencia AJAX/SOLR | rota publica estruturada validada; retorna docs, facets, highlighting e volume total | `CanonicalDecision` via JSON/SOLR |
| P0 | TJBA jurisprudencia GraphQL | provider implementado; rota publica estruturada, catalogos, facets e inteiro teor por UUID | `CanonicalDecision` e `CanonicalDocument` via GraphQL/HTML |
| P0 | TJPR jurisprudencia HTML | rota publica validada com resultado, relator, orgao julgador, ementa e paginacao | `CanonicalDecision` via parser HTML |
| P0 | TJSC/eproc jurisprudencia | formulario eproc publico validado com 475.091 documentos, cards decisorios e inteiro teor HTML | `CanonicalDecision` e `CanonicalDocument` via familia eproc |
| P0 | TNU/eproc jurisprudencia | ja implementado; POST publico validado em `listar_resultados`; reuso direto da familia eproc | `CanonicalDecision` federal/TNU com inteiro teor publico quando disponivel |
| P0 | TRF2/eproc jurisprudencia | ja implementado; POST publico validado em `listar_resultados`; cobre TRF2, TRU2 e Turmas Recursais | `CanonicalDecision` federal com origens eproc |
| P0 | TRF6/eproc jurisprudencia | ja implementado; POST publico validado em `listar_resultados`; cobre TRF6, TRU6, Turmas Recursais e Varas Federais | `CanonicalDecision` federal com origens eproc |
| P0 | TJGO/Projudi jurisprudencia | ja implementado; POST publico validado, alto volume, processo, orgao, magistrado, decisao e inteiro teor embutido | `CanonicalDecision` via parser HTML Projudi |
| P0 | TJAC/e-SAJ CJSG | resultado simples publico validado com ementa, relator, orgao, datas e inteiro teor | `CanonicalDecision` via familia CJSG/e-SAJ |
| P0 | TJPI/JusPI jurisprudencia | ja implementado; GET publico de busca e detalhe HTML retornam conteudo decisorio valido | `CanonicalDecision` e `CanonicalDocument` via parser HTML |
| P1 | TJRR/Juris JSF | provider implementado com GET, postback JSF/PrimeFaces, fixture sanitizada e parser offline; disponibilidade live deve ser monitorada | `CanonicalDecision` e `CanonicalDocument` via contrato JSF observado |
| P1 | TJMT jurisprudencia API Hellsgate | revalidacao atual redirecionou o portal para `/ui/login` e a API inferida respondeu 401; evidencia antiga mantida apenas como historico | nao automatizar sem nova rota publica reproduzivel |
| P1 | TJPA jurisprudencia BFF | `POST /bff/api/decisoes/buscar` retornou JSON decisorio real; catalogos e recentes tambem respondem publicamente | `CanonicalDecision` via JSON apos fixtures, filtros e detalhe |
| P1 | TJCE/e-SAJ CJSG | pagina oficial documenta busca completa, ementas, acordaos, filtros e inteiro teor; acesso HTTP local sofreu reset TLS | `CanonicalDecision` via familia CJSG apos HAR e fixture |
| P1 | TJCE Informativos | pagina HTML oficial retornou edicoes, itens com processo/assunto/orgao e links PDF | `CanonicalPrecedent` curado via parser HTML/PDF |
| P1 | TRF3 jurisprudencia | interface oficial confirma pesquisa textual, filtros, JEF/Turmas Recursais e consulta de acordaos; cliente HTTP sofreu timeout | `CanonicalDecision` e `CanonicalDocument` apos captura e replay |
| P1 | TJPB/PJe jurisprudencia | formulario publico com campos juridicos e paginacao; comportamento WAF variou por cliente | provider somente apos fixture de resultado real sem desafio |
| P0 | STJ jurisprudencia/SCON e Dados Abertos | `stj_scon` para busca textual e `stj_dados_abertos_jurisprudencia` para catalogo CKAN e plano de sincronizacao | acordaos como `CanonicalDecision`; datasets para indice local posterior |
| P0 | STF jurisprudencia | provider inicial `stf_juris` via API JSON observada por HAR; WAF/SSL diagnosticados | acordaos como `CanonicalDecision`; inteiro teor como URL ate validar documento sem 403 |
| P0 | TST jurisprudencia | provider implementado com API REST publica, busca textual, filtros e inteiro teor HTML | `CanonicalDecision` trabalhista e `CanonicalDocument` sob demanda |
| P1 | TJPE sumulas e orientacao de decisoes | paginas publicas para sumulas, transparencia e Consulta Jurisprudencia Web; ainda sem endpoint limpo de acordaos | catalogo documental/precedentes locais |
| P1 | TJSE jurisprudencia judicial | pagina oficial publica de jurisprudencia judicial; falta rota final de resultado | entrada documental e candidato de provider |
| P1 | TJRO/LIAME | portal publico de precedentes/temas com filtros por tribunal, especie e situacao | `CanonicalPrecedent`/catalogo, nao acordaos |
| P1 | TJAP/Tucujuris | consulta institucional historicamente integrada para acordaos, turmas recursais e sumulas; acesso atual exige nova validacao | catalogo ou `CanonicalDecision` apos rota limpa |
| P1 | TJRN/Jurisprudencia | portal unificado anunciado para PJe/SAJ e primeiro/segundo graus; probe atual respondeu 403 | `CanonicalDecision` apos HAR e replay limpo |
| P1 | TJTO/Jurisprudencia | consulta indexada mostra processo, classe, relator, ementa, tese e referencias; replay pendente | `CanonicalDecision` apos contrato HTTP |
| P1 | TJES/Jurisprudencia | resultado legado oficial indexado e ementarios PDF; portal atual instavel | `CanonicalDecision` legado ou `CanonicalPrecedent` documental |
| P1 | TJMG/Espelho de Acordao | formulario e ajuda oficiais; busca textual respondeu captcha/401 | provider somente com nova superficie publica limpa |
| P1 | TCU jurisprudencia e dados abertos | manifesto e CSVs oficiais com acordaos, jurisprudencia selecionada, sumulas, respostas e boletins | adapter de dataset para `CanonicalDecision`/`CanonicalPrecedent`; pesquisa web separada |
| P1 | CNJ informativos de jurisprudencia | pagina HTML oficial com filtros, paginacao e PDFs dos informativos | `CanonicalPrecedent`/conteudo curado; nao e busca geral de acordaos |
| P2 | TJES jurisprudencia | portal atual `Pesquisa.aspx` deu timeout e rota ColdFusion antiga retornou 404 | repetir probe antes de promover |
| P1 | TJMA/Jurisconsult metadados e sumulas | API publica limpa para relatorios, tipos, orgaos e links de sumulas/IAC/IRDR; busca principal exige captcha | `CanonicalPrecedent`/catalogo parcial; nao automatizar acordaos sem fluxo limpo |
| P1 | TSE/TREs SJUR metadados | backend oficial identificado; classes e relatorias retornam JSON publico, mas busca principal retornou antirrobo | catalogo/filtros eleitorais; decisoes somente se fluxo limpo existir |
| P1 | TRT2/PJe jurisprudencia metadados | SPA e `/juris-backend/api/opcoes` publicos; documentos retornam `tokenDesafio`/`imagem` | contrato parcial e diagnostico de acesso; nao coletar documentos |
| P1 | CJF/TRF1 hub e ementario | hub publico e ementario documental; ainda sem endpoint limpo de resultado | rota documental/catalogo |
| P2 | TST/TSE/STM | ramos especializados com alta demanda de pesquisa | decisoes e precedentes por ramo |
| P2 | TRFs e TJs via familia de sistema | ampliar cobertura regional com reuso de parsers | providers por sistema antes de providers por tribunal |

## Estrategia por sistema, nao por pagina isolada

A cobertura ampla do Brasil deve priorizar familias tecnicas reutilizaveis:

- `bnp_pangea`: API JSON de precedentes;
- `tjdf_juris`: HTML SISTJ/TJDFT para acordaos e bases indexadas;
- `tjms_cjsg`: HTML e-SAJ/CJSG do TJMS;
- `tjgo_projudi_jurisprudencia`: HTML publico PROJUDI/TJGO com POST de busca,
  cards decisorios e inteiro teor embutido no resultado;
- `tjpi_juspi`: HTML publico JusPI/TJPI com busca server-side, paginacao e
  detalhe publico em `/jurisprudences/<id>/public`;
- `tjsp_cjsg`: HTML ESAJ/CJSG de jurisprudencia;
- `tjsp_nugepnac`: catalogos oficiais TJSP/NugepNac de precedentes;
- `tce_sp_jurisprudencia`: catalogos estaticos TCE-SP de sumulas e boletins;
- `tre_sp_temas`: curadoria tematica publica do TRE-SP;
- `tjrs_solr`: AJAX publico baseado em SOLR para jurisprudencia do TJRS;
- `tjba_graphql`: GraphQL publico de jurisprudencia do TJBA;
- `tjpr_juris`: HTML publico de jurisprudencia do TJPR;
- `eproc_jurisprudencia`: familia eproc para TJSC e tribunais que exponham
  pesquisa publica equivalente; TNU, TRF2 e TRF6 ja possuem providers
  concretos registrados como `tnu_eproc_jurisprudencia`,
  `trf2_eproc_jurisprudencia` e `trf6_eproc_jurisprudencia`;
- `projudi_jurisprudencia`: familia PROJUDI para jurisprudencia/atos judiciais,
  iniciada por TJGO com POST limpo e parser de cards HTML;
- `juris_jsf`: familia JSF/PrimeFaces de jurisprudencia, observada no TJRR,
  exige reproducao responsavel do postback da propria sessao publica;
- `jurisprudencia_spa_api`: frontends modernos com APIs BFF/REST observadas em
  TJMT e TJPA; TJPA ja possui busca textual publica reproduzida, enquanto
  TJMT permanece bloqueado ate nova rota publica validada;
- `pje_jurisprudencia_estadual`: instancias estaduais de pesquisa PJe como
  TJPB; alto valor, mas dependem de estabilidade sem desafio WAF/captcha;
- `tjma_jurisconsult`: API publica parcial para metadados, filtros e links de
  precedentes/sumulas; busca principal fica bloqueada enquanto exigir captcha;
- `tcu_jurisprudencia_abertos`: manifesto e datasets CSV publicos do TCU para
  acordaos, jurisprudencia selecionada, sumulas, respostas e boletins; a
  pesquisa interativa possui contrato de frontend, mas pode ser protegida por
  firewall e deve permanecer separada do adapter de dados abertos;
- `cnj_informativos`: HTML paginado e PDFs oficiais de informativos do CNJ;
  tratar como jurisprudencia curada e nao como repositorio geral de decisoes;
- `justica_eleitoral_sjur`: API publica parcial para classes/relatorias do
  TSE/TREs; busca principal fica bloqueada enquanto exigir antirrobo/token;
- `pje_jurisprudencia`: familia PJe com metadados/opcoes publicos em algumas
  instancias, mas alto risco de desafio humano em documentos;
- `esaj`: familia Softplan/e-SAJ para tribunais que compartilham padroes;
- `eproc`: familia eproc, com pesquisa publica quando disponivel;
- `pje`: familia PJe, normalmente com maior incidencia de controle de acesso;
- `stj_scon`, `stf_juris`, `tst_jurisprudencia`: providers por tribunal
  superior quando o contrato for proprio.

Esse desenho reduz duplicacao: quando dois tribunais compartilham a mesma
familia tecnica, a NanoJuris deve reaproveitar fetcher, parser e canonical mapper
sempre que o contrato real permitir.

O catalogo publico expõe `source_system` para descoberta por Python, CLI e MCP:

```bash
nanojuris tribunais --sistema esaj_cjsg
```

```python
from nanojuris import list_courts

print([court.code for court in list_courts(source_system="esaj_cjsg")])
```

## Metodologia de pesquisa de fonte

O fluxo operacional detalhado, com score de qualidade e comando `probe-rota`,
esta em [route-mapping-playbook.md](route-mapping-playbook.md).

Antes de implementar um provider, preencher uma ficha tecnica com:

- URL inicial oficial;
- endpoints observados;
- metodo HTTP;
- nomes de parametros de query e formulario, sem valores sensiveis;
- paginacao;
- campos juridicos objetivos disponiveis;
- documentos e formatos retornados;
- sinais de captcha, login, segredo de justica ou bloqueio;
- payload minimo responsavel;
- fixture offline publica representativa;
- teste live opcional e desligado por padrao.

HARs, DevTools e browser network podem ser usados como ferramenta local de
pesquisa, mas nao devem entrar no pacote, nos testes ou em fixtures sem
revisao rigorosa para remover cookies, tokens e segredos locais, preservando o conteudo publico da fonte. O artefato publico deve ser a ficha de fonte e o provider
testado, nao o HAR bruto.

## Evidencia ESAJ/TJSP a partir de pesquisa local

Pesquisa local com HAR do portal ESAJ/TJSP de jurisprudencia indicou estas rotas
publicas relevantes:

| Rota | Metodo | Tipo | Campos observados | Classificacao |
| --- | --- | --- | --- | --- |
| `/cjsg/resultadoCompleta.do` | POST | HTML | `dados.buscaInteiroTeor`, `dados.buscaEmenta`, `dados.nuProcOrigem`, `dados.dtJulgamentoInicio`, `dados.dtJulgamentoFim`, `tipoDecisaoSelecionados`, `dados.ordenarPor`, alem de campos de captcha quando exigidos | alta oportunidade com controle de acesso possivel |
| `/cjsg/captchaControleAcesso.do` | POST | JSON | `uuidCaptcha`, `conversationId` | controle de acesso; nao implementar bypass |
| `/sajcas/conteudoIdentificacao` | GET | HTML | `script` | identidade/login; nao usar como rota de extracao |

Conclusao: o provider TJSP/CJSG deve continuar usando payloads de busca
estruturados apenas quando a fonte publica responder sem exigir validacao humana.
Quando a resposta indicar captcha ou outro controle, o comportamento correto e
interromper com erro claro e `AccessStatus.ACCESS_CONTROL_REQUIRED`.

## Matriz de UX por publico

| Publico | Necessidade | UX esperada |
| --- | --- | --- |
| Advogados | localizar decisoes e inteiro teor publico com origem confiavel | comandos simples, Markdown, links/traces e mensagens claras de acesso |
| Desenvolvedores | integrar fontes heterogeneas com contratos estaveis | API Python tipada, erros acionaveis, fixtures e docs de provider |
| Jurimetristas | montar datasets reproduziveis por tribunal, ramo e periodo | CSV/JSONL, SQLite, `ResearchRun`, filtros por tribunal/UF/ramo |
| Analistas de dados | auditar e versionar coletas | hashes, `SourceTrace`, `ExtractionTrace`, deduplicacao e exports paginados |
| Agentes de IA | descobrir fontes, limites e dados sem interpretar merito | MCP com `list_sources`, `list_courts`, busca, store, export e `get_document` |

## Lacunas prioritarias

1. Completar `official_url` e `source_system` no catalogo `CourtInfo`.
2. Aprofundar bases adicionais do `stf_juris`: decisoes, sumulas e informativos.
3. Expandir `stj_scon` para inteiro teor publico quando a fonte responder sem
  controle de acesso.
4. Validar live a rota de inteiro teor das instancias federais eproc
  TNU/TRF2/TRF6 por `id_jurisprudencia`.
5. Converter a rodada estadual
  [state-court-route-mapping-2026-08-07.md](state-court-route-mapping-2026-08-07.md)
  em fixtures para TJRR, TJMT, TJPA e TJPB; TJPI ja foi promovido.
6. Separar provider por familia de sistema quando houver reaproveitamento real.
7. Criar benchmark de completude por provider e campo canonico.
8. Definir contrato de plugin externo para providers fora do core.
