# Public Provider Discovery - 2026-08-10

## Objetivo

Este registro separa fontes oficiais que entregam jurisprudencia sem login ou
token privado das fontes que apenas possuem um portal publico, mas exigem
captcha, WAF, estado de navegador ou ainda nao tiveram a rota de resultados
reproduzida.

O criterio de promocao continua sendo uma chamada HTTP limpa, sem cookies
pessoais, login, CAPTCHA solving, browser stealth ou bypass, com pelo menos um
campo juridico objetivo no retorno.

## Estado registrado nesta pesquisa

Este documento e um snapshot historico de 2026-08-10. Naquele momento, 26
providers estavam registrados no cliente principal e 6 contratos estavam
classificados como prontos para agentes. O estado atual deve ser lido no
[registro vivo de providers](registry/providers.json): a rodada seguinte
elevou o projeto para 34 providers implementados e 20 candidatos.
- O cadastro de um provider nao significa disponibilidade permanente: a fonte
  pode estar indisponivel, sob controle de acesso ou com contrato alterado.
- A busca unificada deve expor `SourceTrace`, erros por fonte e a diferenca
  entre resultado vazio e fonte bloqueada.

### Providers ja utilizaveis em fluxo publico

As familias abaixo ja possuem provider, fixture ou validacao limpa no projeto:

| Familia | Fontes | Saida principal |
| --- | --- | --- |
| eproc federal | TNU, TRF2, TRF4 e TRF6 | acordaos, ementas e links de inteiro teor |
| e-SAJ/CJSG | TJAC, TJAL, TJAM, TJMS e TJSP quando liberado | ementas, metadados e links publicos |
| portais estaduais | TJDFT, TJGO/Projudi e TJPI/JusPI | decisoes e, quando publico, documento |
| superiores/especializados | STM, STF Informativo e STJ Informativo | decisoes, teses e notas oficiais |
| catalogos publicos | TJSP/NugepNac, TCE-SP e TRE-SP temas | precedentes e curadorias tematicas |

BNP/Pangea e Comunica PJe/DJEN continuam uteis, mas pertencem a categorias
distintas: precedentes qualificados e comunicacoes judiciais. Eles nao devem
ser apresentados como busca geral de acordaos.

## Proxima leva: fontes sem autenticacao com maior valor

| Ordem | Fonte | Evidencia publica | Conteudo | Decisao |
| --- | --- | --- | --- | --- |
| 1 | TST | `GET /config.json`, catalogos REST, busca textual e `GET /rest/documentos/{id}` retornaram conteudo juridico real | jurisprudencia trabalhista nacional | `implemented`; monitorar contrato live |
| 2 | TJRS | portal oficial declara acesso a decisoes de 2o grau; rota AJAX/SOLR retornou JSON com `numFound`, documentos, facets e highlighting | acordaos do TJRS | promover para provider JSON |
| 3 | TJBA | portal oficial publico e GraphQL retornou decisoes com ementa, processo, relator e orgao julgador; detalhes `/inteiroTeor/<uuid>` sao publicos | jurisprudencia estadual e turmas recursais | promover para provider GraphQL |
| 4 | TJPR | pesquisa oficial publica retornou resultados, relator, orgao julgador, processo, data e ementa, com paginacao | jurisprudencia estadual e Corte IDH indexada | promover para provider HTML |
| 5 | TJRJ/eproc | GET publico e POST eproc reproduzido com `dano moral`; 10 cards com processo, classe, orgao, datas e links | jurisprudencia estadual recente do eproc | promover para provider eproc apos fixtures |
| 6 | CJF/TRF1 | POST JSF/PrimeFaces com `dano moral` retornou 25.783 resultados e links de inteiro teor | jurisprudencia federal e base unificada | promover apos fixtures separadas |
| 7 | TRF5 | POST do formulario publico retornou resultados, ementas, orgao, datas e processos | jurisprudencia federal, TRU e turmas recursais | promover apos fixture HTML |
| 8 | TJPE | API REST oficial retornou JSON paginado com decisoes, ementas, acordaos, classes, relatores e orgaos | jurisprudencia estadual | promover apos fixture REST e validacao TLS |
| 9 | TJSC/eproc | POST publico retornou HTML com 475.091 documentos, cards decisorios e link de inteiro teor | jurisprudencia estadual | promover apos fixture HTML e parser eproc |
| 10 | TJPA | BFF oficial retornou resultados JSON ricos, catalogos e recentes em sessao limpa | jurisprudencia estadual | promover apos fixtures e parser JSON |
| 11 | Falcao/JT | repositorio nacional descrito por TRT9/CNJ; GET da raiz retornou 403 CloudFront neste ambiente | jurisprudencia trabalhista nacional | prioridade alta, mas bloqueado ate contrato publico reproduzivel |
| 12 | TCU dados abertos | manifesto e CSVs oficiais retornaram schema e registros reais; pesquisa interativa existe, mas o endpoint de resultados respondeu pagina de firewall | acordaos, jurisprudencia selecionada, sumulas, respostas e boletins de controle externo | promover adapter de dataset; manter busca interativa separada |
| 13 | CNJ informativos | HTML oficial paginado retornou filtros, itens de ementa e links PDF; consultas por numero, argumento e periodo responderam HTTP 200 | informativos curados do CNJ | promover parser HTML/PDF sob demanda |

O TJPR foi revalidado no portal oficial com resultado de milhoes de registros
e campos decisorios visiveis. O TJRS tambem foi revalidado no portal oficial,
que identifica a consulta como acesso a integra das decisoes de segundo grau e
informa que a busca usa SOLR. [TJPR - pesquisa publica](https://portal.tjpr.jus.br/jurisprudencia/publico/pesquisa.do?actionType=pesquisarRefinado&filtro=true)
e [TJRS - pesquisa oficial](https://www.tjrs.jus.br/buscas/jurisprudencia/).

O portal do TJBA continua publicamente acessivel e possui resultados de
inteiro teor indexados no host oficial. [TJBA - jurisprudencia](https://jurisprudencia.tjba.jus.br/)
e [TJBA - exemplo de inteiro teor publico](https://jurisprudenciaws.tjba.jus.br/inteiroTeor/831bc363-c057-3941-a5d6-79584cb02536).

### Probes limpos desta rodada

Os probes abaixo foram executados pelo `nanojuris probe-rota` com as variaveis
de proxy do ambiente desabilitadas. Nenhum usou cookie, login, CAPTCHA ou
cabecalho privado:

| Fonte | Rota testada | HTTP | Resultado |
| --- | --- | --- | --- |
| TST | `POST https://jurisprudencia-backend2.tst.jus.br/rest/pesquisa-textual/1/2` com payload textual publico | 200 | JSON com `totalRegistros`, `registros`, `agregacoes`, ementa, dispositivo e metadados decisorios; detalhe `/rest/documentos/{id}` retornou HTML |
| TJRS | `POST https://www.tjrs.jus.br/buscas/jurisprudencia/ajax.php` com `dano moral` | 200 | JSON/SOLR com `numFound=612125`, documentos, facets e highlighting |
| TJPR | `GET https://portal.tjpr.jus.br/jurisprudencia/publico/pesquisa.do?actionType=pesquisarRefinado&filtro=true` | 200 | HTML com resultado, processo, relator, orgao, ementa e paginacao |
| TJBA | `GET https://jurisprudenciaws.tjba.jus.br/inteiroTeor/831bc363-c057-3941-a5d6-79584cb02536` | 200 | HTML de decisao publica com processo, relator, orgao e inteiro teor |
| TJSC/eproc | `POST https://eprocwebcon.tjsc.jus.br/consulta1g/externo_controlador.php?acao=jurisprudencia@jurisprudencia/listar_resultados` com `dano moral` | 200 | HTML `iso-8859-1`, 475.091 documentos, 10 cards, metadados e link `download_inteiro_teor` |

O `GET /config.json` do TST tambem respondeu HTTP 200 e publicou as URLs
oficiais de pesquisa e consulta de acordao. A resposta da busca TST com `{}`
foi usada somente para confirmar o contrato; o provider deve sempre exigir
termo, filtro ou numero antes de executar consultas reais.

## Fontes que continuam em mapeamento

| Grupo | Fontes | Motivo para nao promover agora |
| --- | --- | --- |
| filtros/detalhes pendentes | TJPA | busca textual, catalogos, recentes e filtro basico origem/tipo ja reproduzidos; classe/assunto e detalhe ainda precisam de fixtures/contrato |
| portal atualmente protegido | TJMT | revalidacao redirecionou para `/ui/login`; API inferida respondeu 401 e nao deve receber credencial |
| estabilizacao de postback | TJRR | postback publico ja retornou resultados, mas uma repeticao sofreu timeout; falta fixture e teste de estabilidade |
| risco de WAF | TJPB | formulario publico existe, mas ainda falta resposta decisoria reproduzivel sem desafio |
| busca com CAPTCHA | TJMG, TJRJ/eJURIS, TJMA, TRT2/PJe | nao automatizar validacao humana nem tentar contornar antirrobo |
| portal ou catalogo documental | TJRO | conteudo publico existe, mas ainda nao ha busca decisoria limpa comprovada |
| busca com contrato parcial | TSE/SJUR beta | SPA oficial responde, mas endpoint de resultados ainda nao foi reproduzido |
| metadados publicos com busca protegida | TSE/SJUR 4.0 | classes, relatores, eleicoes e normas retornam JSON; decisoes exigem validacao antirrobo |
| formulario publico com protecao | TJSE | JSF/PrimeFaces rico, mas a busca automatizada retorna `Captcha invalido` |
| inconclusivos | TJES, TJCE, TRF3 | timeout, reset TLS ou rota instavel; repetir em janela controlada |
| repositorio nacional bloqueado | Falcao/JT | fonte institucionalmente forte, mas GET 403/CloudFront no probe atual | repetir em janela controlada; nao fazer bypass |
| pesquisa interativa protegida | TCU | pagina publica, mas endpoint de resultados retornou bloqueio do firewall; dados abertos continuam acessiveis | usar manifesto/CSV; nao classificar bloqueio como busca vazia |

## Contrato minimo antes do codigo

Para cada uma das quatro fontes prioritarias, a equipe deve fechar:

1. URL oficial de entrada e rota de detalhe.
2. Metodo, payload minimo, paginacao, ordenacao e limites.
3. Campos canonicos: processo, classe, orgao, relator, datas, ementa e link do
   documento.
4. Fixture de sucesso, vazio, erro HTTP e controle de acesso.
5. Parser offline antes do fetcher live.
6. Teste live opt-in com limite pequeno e rate limit.
7. Diagnostico que diferencie `empty`, indisponibilidade, contrato alterado e
   `access_control_required`.

## Sequencia recomendada

1. CJF/TRF1: capturar fixture JSF e separar a base TRF1 da busca unificada.
2. TRF5: criar parser HTML e fixture de resultados com tipos documentais.
3. TST: ampliar fixtures e monitorar o provider JSON nacional ja implementado.
4. TJBA: implementar o contrato GraphQL estruturado, incluindo detalhe de
   inteiro teor por UUID.
5. TJRS: implementar o adapter SOLR preservando facets e highlighting no campo
   bruto, sem perder a normalizacao canonica.
6. TJPR: implementar o parser HTML e paginacao, mantendo links oficiais de
   detalhe e o texto retornado pela fonte.
7. TJRJ/eproc: capturar fixture pequena e adaptar a familia eproc para a base
   estadual, mantendo o eJURIS legado como fonte separada.
8. TJSC/eproc: fechar fixture e parser da instancia estadual, reaproveitando a
   familia eproc apenas depois de comparar labels, origens e detalhe.
9. Falcao/JT: investigar contrato nacional somente com acesso publico normal;
   se permanecer bloqueado, manter TST e providers individuais como caminho
   oficial de pesquisa trabalhista.
10. Depois disso, retomar TSE e TJMT com novos HARs limpos apenas quando houver
   necessidade real de payload ou postback. O TJPA ja possui payload textual
   reproduzido e deve seguir para fixture/parser.

## Regra de produto

Uma fonte somente pode ser chamada de "sem autenticacao" quando a consulta de
resultado puder ser reproduzida sem identidade privada, token de usuario,
captcha, desafio de navegador ou cookie exportado. API publica com chave fixa
embutida no frontend deve ser classificada separadamente e investigada quanto
ao contrato e aos termos da fonte antes de ser incorporada.
