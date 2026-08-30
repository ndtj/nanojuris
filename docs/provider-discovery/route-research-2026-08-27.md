# Pesquisa de rotas oficiais de jurisprudência — 2026-08-27

Esta pesquisa é um artefato de planejamento local. Ela não representa
deploy, não guarda cookies/tokens e não autoriza contornar CAPTCHA, WAF,
limites de frequência ou autenticação. Uma rota somente pode ser promovida
após resposta jurídica reproduzível, fixture sanitizada, parser canônico e
teste offline.

## Resultado executivo

O maior ganho de baixo risco é consolidar superfícies oficiais já
estruturadas, não criar adaptadores para páginas que apenas exibem um
formulário. A API pública de jurisprudência do TJDFT é a única rota nova com
contrato JSON oficial suficientemente claro para implementação imediata; a
integração foi mantida no provider `tjdf_juris` e é opt-in. O STJ oferece
datasets JSON/CSV/ZIP via CKAN e deve continuar no pipeline de sincronização
local, sem ser duplicado como busca online.

As demais fontes abaixo têm uma interface oficial útil, mas ainda não
fornecem contrato de resultados reproduzido no ambiente local. Elas devem
permanecer explicitamente pendentes ou bloqueadas, em vez de serem tratadas
como zero resultados.

## Matriz priorizada

| Prioridade | Fonte e rota oficial | Método/formato | Conteúdo | Estado local | Próxima ação segura |
| --- | --- | --- | --- | --- | --- |
| P0 | TJDFT `https://jurisdf.tjdft.jus.br/api/v1/pesquisa` | POST JSON | Acórdãos e decisões, `hits`, `registros`, ementa, relator, órgão, datas e inteiro teor quando publicado | **Implementado opt-in** em `tjdf_juris`; fixtures e parser cobertos | Manter monitoramento de schema e ampliar fixtures de paginação/erro |
| P1 | STJ CKAN `https://dadosabertos.web.stj.jus.br/api/3/action/package_search` e `package_show` | GET JSON + recursos CSV/JSON/ZIP | Espelhos, íntegra e metadados de jurisprudência | **Implementado como catálogo/sincronização local**; não é busca interativa | Adicionar manifesto de checksum/data e ingestão incremental, sem duplicar provider |
| P1 | TCU `https://sites.tcu.gov.br/dados-abertos/jurisprudencia/` | CSV oficial + catálogo | Acórdãos, súmulas, boletins e respostas a consultas | **Implementado**; pesquisa interativa separada por firewall | Continuar usando CSV como fonte primária e registrar atualização |
| P1 | TJPE `https://portal.tjpe.jus.br/web/jurisprudencia/busca` | UI oficial; exportações documentais | Busca/relatórios e informativos | Provider existente; nenhuma API de jurisprudência textual pública reproduzida | Capturar contrato público de exportação ou feed de informativos; não usar DataJud como substituto |
| P1 | TJPB `https://pje-jurisprudencia.tjpb.jus.br/` | POST `/api/jurisprudencia/pesquisar` com sessão e `_token` | Acervo PJe de segundo grau | Implementado, mas controlado por sessão/token e instável live | Fixture de sucesso obtida em fluxo público permitido; sem simular token |
| P1 | TSE/TRE SJUR `https://sjur-pesquisa-api.tse.jus.br/{tribunal}/sjur-pesquisa-backend/rest/public/pesquisa` | POST JSON | Catálogos públicos; busca decisória ainda separada | Catálogos implementados; busca geral não promovida | Reproduzir busca sem desafio e registrar contrato por tribunal |
| P2 | TJCE/TJSP CJSG e-SAJ | POST/GET HTML | Acórdãos e inteiro teor | Adapters existentes; controles de acesso observados em live | Manter diagnóstico; não contornar CAPTCHA/WAF |
| P2 | STF `https://jurisprudencia.stf.jus.br/api/search/search` | POST JSON | Jurisprudência STF | Adapter existente; falha live de TLS/WAF em parte das janelas | Confirmar certificado/cadeia e contrato em rede autorizada; não desabilitar verificação TLS |
| P2 | TRF3 `https://web.trf3.jus.br/jurisprudencia/home/index/1` | UI/WebForms; detalhe por processo | Pesquisa textual e documentos | Candidato; timeout limpo, sem payload/resultado reproduzido | Captura pública normal de rede e fixtures antes de implementar |
| P2 | TJMG `https://www5.tjmg.jus.br/jurisprudencia/formEspelhoAcordao.do` | WebForms | Espelhos de acórdãos e inteiro teor | Candidato; busca textual respondeu desafio/captcha | Não automatizar enquanto o controle permanecer; procurar exportação oficial |
| P2 | TJRN `https://jurisprudencia.tjrn.jus.br/` | SPA; rota não confirmada | Acervo unificado PJe/SAJ | Candidato; raiz 200, bundles/consulta 403 | Obter contrato de rede de sessão pública, sem replay de credenciais |
| P2 | TJSE `https://www.tjse.jus.br/Dgorg/paginas/jurisprudencia/consultarJurisprudencia.tjse` | POST JSF/PrimeFaces | Acórdãos e decisões | Candidato; resposta `Captcha inválido` | Não promover sem fixture de resultado legitimamente obtida |
| P2 | TJRJ eJURIS `https://www3.tjrj.jus.br/EJURIS/ConsultarJurisprudencia.aspx` | WebForms | Acórdãos/decisões monocráticas/ementários, ementa e PDF | Candidato; reCAPTCHA e schema não reproduzido | Manter fora da federação; buscar acervo documental oficial alternativo |
| P2 | TJES `https://sistemas.tjes.jus.br/portaltj/Pesquisa.aspx` | ASP.NET; legado ColdFusion 404 | Acórdãos/ementários | Candidato; portal 503 e legado 404 na validação histórica | Considerar apenas PDFs oficiais de ementários como fonte curada separada |
| Fora do escopo | CNJ DataJud `https://api-publica.datajud.cnj.jus.br/api_publica_<tribunal>/_search` | GET/POST Elasticsearch com chave | Metadados processuais e movimentações | **Não implementar em NanoJuris** | Pertence ao produto processual NanoJud; não é substituto de jurisprudência textual |

## Rotas verificadas na plataforma NanoJuris

O inventário live já registrado em
`docs/validation/runs/20260828T010539Z-platform-live-summary.json` cobre o
contrato da plataforma (`/api/v1/sources`, `/api/v1/search`, leitor,
`/bff/assistant` e rotas administrativas). Isso não equivale a testar todos os
providers: a busca federada consultou 41 fontes, obteve dados em 31 e
classificou 10 falhas por tipo. O resultado do provider deve continuar sendo
avaliado por sua própria fixture e `SourceTrace`.

Falhas live históricas que exigem tratamento explícito:

- controle de acesso: CJF, STJ SCON, TJCE CJSG, TJPB PJe e TJSP CJSG;
- transporte/TLS: STF Informativos, STF Juris e TJPE;
- consulta rejeitada: BNP Pangea;
- fonte indisponível: TRE-SP temas.

Nenhum desses estados pode ser convertido em lista vazia ou compensado com
uma rota não oficial.

## Atualização da Justiça Eleitoral (TSE/TRE)

O portal oficial confirma que o SJUR mantém acórdãos, resoluções, decisões
monocráticas e decisões sem resolução do TSE, além de sentenças e decisões dos
TREs após publicação. A página também confirma dois shells públicos: a nova
interface do TSE (`https://jurisprudencia.tse.jus.br/`) e a pesquisa simultânea
dos TREs (`https://jurisprudencia-tres.tse.jus.br/`). A documentação oficial
descreve espelho com dados descritivos/temáticos, ementa e link para inteiro
teor, além de filtros e operadores jurídicos.

O inventário local confirmou as rotas de catálogo do backend SJUR para
classes, relatores, eleições e normas, porém não deve inferir a rota de busca
decisória apenas do bundle da SPA. A busca geral permanece `pending_contract`
até que o POST e a resposta de resultados sejam capturados numa sessão pública
normal e reproduzidos sem cookie ou token humano. A área de pesquisa também
oferece produtos documentais independentes (Infojur, coletânea por assunto,
revista, julgados históricos e súmulas); eles devem ser providers documentais
separados, não fallbacks silenciosos da busca de acórdãos.

**Classificação:** catálogos SJUR implementáveis (já cobertos); busca TSE/TRE
`pending_contract`; não promover a nova SPA até fixture de sucesso, vazio,
paginação, detalhe e inteiro teor. A própria página institucional orienta que
cada tribunal responde por sua base de jurisprudência e que o espelho inclui
ementa e metadados ([fonte oficial TSE](https://www.tse.jus.br/jurisprudencia/jurisprudencia-da-justica-eleitoral)).

### Rotas SJUR confirmadas no frontend oficial

Foi feita uma inspeção somente dos arquivos JavaScript públicos carregados por
`https://jurisprudencia.tse.jus.br/` (sem executar login, sem reutilizar cookies
e sem contornar o desafio). O bundle declara a base
`https://sjur-pesquisa-api.tse.jus.br/{tribunal}/sjur-pesquisa-backend/rest/` e
expõe as seguintes superfícies. O segmento `{tribunal}` deve ser resolvido
para um índice oficial do TSE ou TRE; não se deve misturar resultados de
tribunais em um único `source_id`.

| Rota | Método/formato | Escopo | Estado/recomendação |
| --- | --- | --- | --- |
| `/public/pesquisa/rede` | GET, JSON | Origem/tribunais disponíveis para a rede | **Implementável candidato**; capturar uma resposta pública e criar fixture antes de ativar |
| `/public/pesquisa/classes` | POST JSON | Catálogo de classes | **Implementável**; já coberto pelo provider de catálogos |
| `/public/pesquisa/relatorias` | POST JSON | Catálogo de relatores | **Implementável**; já coberto pelo provider de catálogos |
| `/public/pesquisa/eleicoes` | POST JSON | Catálogo de eleições | **Implementável**; já coberto pelo provider de catálogos |
| `/public/pesquisa/normas` | POST JSON | Catálogo de normas | **Implementável**; já coberto pelo provider de catálogos |
| `/public/pesquisa`, `/public/pesquisa/livre`, `/public/pesquisa/simples` | POST JSON | Busca de acórdãos, resoluções e decisões | **Bloqueada/pending_contract**: a SPA executa CAPTCHA e acrescenta `captchaToken`; não automatizar nem armazenar token humano |
| `/public/pesquisa/pesquisaTokenValidado` | POST JSON | Busca após validação do desafio | **Bloqueada** pelo mesmo controle; não é alternativa autônoma |
| `/public/pesquisa/download/` | POST JSON (`{"id": "..."}`) | Download associado a um resultado | **Pendente**: exige `id` de resultado e fixture de MIME/conteúdo |
| `https://sjur-servicos.tse.jus.br/sjur-servicos/rest/download/pdf/{id}` | GET | Inteiro teor PDF | **Pendente**: somente implementar com identificador público obtido legitimamente e validação de PDF |

O bundle também informa paginação zero-based (`pagina`), tamanho configurável
(1, 10, 25, 50, 100 ou 250), limite de 10.000 registros, tribunais como
lista e ordenações `dj_desc`, `dj_asc`, `dp_desc` e `dp_asc`. A resposta
consumida pela interface usa, no mínimo, `content`, `totalRegistros`, `mensagem`
e `aggs`; isso é evidência de mapeamento, não contrato suficiente para
produção sem fixtures. A interface sempre habilita CAPTCHA para a pesquisa,
portanto as rotas de busca devem permanecer classificadas como bloqueadas até
que o TSE publique uma API de serviço sem desafio ou forneça um mecanismo de
exportação autorizado.

**Evidência oficial:** [página institucional de jurisprudência do TSE](https://www.tse.jus.br/jurisprudencia/jurisprudencia-da-justica-eleitoral),
[pesquisa oficial](https://www.tse.jus.br/jurisprudencia/pesquisa-de-jurisprudencia),
[interface SJUR](https://jurisprudencia.tse.jus.br/). A inspeção do frontend
foi usada apenas para descobrir caminhos públicos; não substitui documentação
de API, não autoriza replay de tokens e não altera o catálogo gerado.

## Atualização do TJRJ

O Portal do Conhecimento do TJRJ confirmou uma separação importante que deve
ser preservada no catálogo: o eJURIS legado reúne decisões oriundas do eJUD,
enquanto o eproc contém decisões do novo sistema a partir de 05/02/2026. O
tribunal informa que as bases ainda serão unificadas em fase futura
([fonte oficial](https://www.tjrj.jus.br/web/portal-conhecimento/consulta-a-jurisprudencia)).

No eJURIS, a ajuda oficial descreve filtros de texto, número CNJ/antigo,
origem, competência, magistrado, órgão julgador e tipos Acórdão, Decisão
Monocrática e Ementário, além de opção de inteiro teor em PDF
([ajuda oficial](https://www3.tjrj.jus.br/ejuris/AjudaConsultaJuris.aspx)).
Isso melhora o mapeamento sem mudar o estado de integração: o formulário
WebForms possui reCAPTCHA, e não há resposta decisória reproduzida sem o
desafio. Portanto, o eJURIS permanece `blocked_control`/`pending_contract`;
o provider eproc já existente deve continuar sendo tratado como acervo
distinto, com `source_id` próprio.

## Atualização do TJES

As páginas oficiais do TJES confirmam o valor jurídico dos ementários
trimestrais como acervo selecionado de acórdãos, com número de processo,
relator, órgão e ementa. A rota PDF é adequada para uma futura fonte
documental curada, mas não para uma busca federada sem catálogo de edições,
checksum e parser de PDF. A busca interativa continua sem contrato reproduzido
(portal atual 503; rota ColdFusion histórica 404). Classificação: busca
`blocked_transport`; ementário PDF `candidate_document_only`.

### Atualização live: nova consulta pública JSON do TJES

Em 28/08/2026, a página oficial atual
[`sistemas.tjes.jus.br/consulta-jurisprudencia/`](https://sistemas.tjes.jus.br/consulta-jurisprudencia/)
carregou um frontend público que referencia a API no mesmo domínio. Uma
chamada de baixa frequência, sem autenticação, confirmou o seguinte contrato
observável:

| Rota | Método e parâmetros | Resposta observada | Estado |
| --- | --- | --- | --- |
| `/consulta-jurisprudencia/api/health` | GET | HTTP 200 JSON; `service: ok`, 5 cores ativas e contagens documentais | Implementável como health/diagnóstico |
| `/consulta-jurisprudencia/api/cores` | GET | HTTP 200 JSON; cores `pje1g`, `pje2g`, `pje2g_mono`, `legado` e `turma_recursal_legado`, com campos de faceta e totais | Implementável como descoberta de catálogo |
| `/consulta-jurisprudencia/api/facets?core=pje2g` | GET | HTTP 200 JSON; facetas de classe, jurisdição, magistrado, órgão e assunto | Implementável como metadados; respeitar cache |
| `/consulta-jurisprudencia/api/search?core=pje2g&q=gratuidade%20de%20justi%C3%A7a&page=1&per_page=1` | GET | HTTP 200 JSON, 1 documento e `total: 166448`; resposta possui ementa/acórdão e metadados | **Candidato P1 para adapter**, após fixtures e limite confirmado |

O endpoint de busca também respondeu, sem autenticação, para `pje1g` e
`legado`. A resposta usa `docs`, `facets`, `page`, `per_page`, `total` e
`total_pages` no nível superior. Os documentos PJe expõem, entre outros,
`nr_processo`, `classe_judicial`, `magistrado`, `orgao_julgador`,
`ementa`/`ementa_html` e `acordao`/`acordao_html` (1º grau expõe
`inteiro_teor`/`inteiro_teor_html`); o legado expõe
`numero_processo_legado`, `nome_desembargador`, datas de julgamento/publicação
e conteúdo decisório em HTML/RTF. Isso é evidência suficiente para iniciar um
adapter local com `SourceTrace`, mas não autoriza inferir estabilidade de
schema, limite de página, ordenação ou política de reutilização.

O endpoint foi descoberto no JavaScript distribuído pela própria página oficial
(não houve enumeração agressiva nem acesso ao Solr interno). O campo `url`
retornado por `/health` aponta para uma rede privada; ele não deve ser usado
pelo cliente. Somente a URL HTTPS pública acima deve entrar no adapter.

**Classificação revisada:** `implementable_candidate / public_json_contract`;
promover apenas depois de gravar fixtures sanitizadas de sucesso, vazio, erro
de parâmetro, paginação e cada core; confirmar `per_page` máximo e rate limit;
mapear datas/identidade para `CanonicalDecision`; e obter revisão das
condições de reutilização. Não há licença explícita de redistribuição
identificada na página; disponibilidade pública não deve ser tratada como
licença.

Evidências live: [frontend oficial](https://sistemas.tjes.jus.br/consulta-jurisprudencia/),
[health JSON](https://sistemas.tjes.jus.br/consulta-jurisprudencia/api/health),
[cores JSON](https://sistemas.tjes.jus.br/consulta-jurisprudencia/api/cores),
[facetas do 2º grau](https://sistemas.tjes.jus.br/consulta-jurisprudencia/api/facets?core=pje2g)
e [ementários oficiais](https://www.tjes.jus.br/publicacoes/revista-jurisprudencia-ementario/).

### TRT-2: busca PJe versus acervo documental oficial

O PJe de jurisprudência do TRT-2 continua com contrato apenas parcial: `/opcoes`
e `/filtros` são públicos, mas `/documentos` retorna desafio com `tokenDesafio`
e imagem mesmo em requisição limpa. Logo, não há coleta automatizável de
decisões sem interação legítima do usuário.

Há, contudo, acervo documental oficial independente: [Boletins de
Jurisprudência](https://trt2.jus.br/geral/tribunal2/Boletim/indice_boletins.html),
[Ementários do Tribunal Pleno](https://trt2.jus.br/geral/tribunal2/Ementario/Tribunal_Pleno.html),
[Jurisprudência Consolidada](https://www.trt2.jus.br/geral/tribunal2/Juris_Consolidada/Juris_Consol_Ant.html)
e o catálogo [BASIS TRT2](https://basis.trt2.jus.br/handle/123456789/16181/browse).
As páginas e os PDFs contêm ementas oficiais e, em alguns boletins, links para
o inteiro teor. Não foi encontrado feed JSON/CSV, manifesto de versões ou
licença explícita de redistribuição. Classificação: `candidate_document_only`,
com ingestão futura por catálogo/PDF, checksum, parser e revisão jurídica; não
promover como busca online nem presumir que o HTML estável seja uma API.

## Critério de promoção "ouro"

Uma nova rota só passa para runtime quando todos os itens forem comprovados:

1. fonte e finalidade institucionais confirmadas;
2. método, URL, payload, filtros, limites, ordenação e paginação reproduzidos;
3. sucesso, vazio, consulta inválida, controle de acesso, rate limit, timeout
   e mudança de schema classificados;
4. identidade estável, datas, ementa/inteiro teor e campos ausentes mapeados
   para `CanonicalDecision`;
5. fixtures pequenas e sanitizadas para sucesso, vazio e falha;
6. `SourceTrace` preserva rota, status, consulta e completude sem segredos;
7. SDD, testes, documentação do provider, contrato e catálogo gerado
   atualizados.

## Segunda rodada: TRF3, TJMG, TJRN, TJSE, TJRJ e TJES

Esta rodada separou claramente rota de consulta, rota de detalhe e fonte
documental. A ausência de um resultado reproduzível não é tratada como acervo
vazio.

| Fonte | Rota/artefato oficial | O que foi confirmado | Classificação |
| --- | --- | --- | --- |
| TRF3 | `https://web.trf3.jus.br/jurisprudencia/` e detalhe `https://web.trf3.jus.br/acordaos/Acordao` | Formulário público com processo, relator, data, classe, órgão, ementa, indexação, sistema interamericano e legislação; também aponta CJF/TNU e súmulas. GET limpo não entregou payload de resultados no tempo de validação. | **Pendente**: necessita captura normal de sucesso, vazio, paginação e detalhe; não implementar por suposição de HTML |
| TJMG | `https://www5.tjmg.jus.br/jurisprudencia/formEspelhoAcordao.do`, com buscas por número ou palavras | Ajuda oficial confirma CNJ/número antigo, classe, relator, órgão, comarca, datas, ementa e inteiro teor. A consulta textual observada exigiu controle/captcha. | **Bloqueada**: procurar exportação oficial; não automatizar desafio |
| TJRN | `https://jurisprudencia.tjrn.jus.br/` | Portal público anuncia acervo PJe e legado SAJ, com filtros textuais, ementa, classe, processo, grau e origem. A raiz respondeu, mas bundles/consulta retornaram 403 e não houve schema verificável. | **Bloqueada/inconclusiva**: requer contrato de rede público documentado |
| TJSE | `https://www.tjse.jus.br/portal/consultas/jurisprudencia/judicial` e `https://www.tjse.jus.br/Dgorg/paginas/jurisprudencia/consultarJurisprudencia.tjse` | Página e formulário JSF/PrimeFaces públicos, com busca textual e filtros; POST de teste devolveu “Captcha inválido”. | **Bloqueada**: não fazer replay sem desafio nem registrar token |
| TJRJ eJURIS | `https://www3.tjrj.jus.br/EJURIS/ConsultarJurisprudencia.aspx` | Ajuda oficial confirma acórdão, decisão monocrática, ementário, ementa e inteiro teor PDF. Portal oficial informa que eproc contém decisões a partir de 05/02/2026 e ainda é base distinta. | **Bloqueada/pending_contract** para eJURIS; manter eJURIS e eproc em `source_id` separados |
| TJES | `https://sistemas.tjes.jus.br/portaltj/Pesquisa.aspx` e ementários oficiais em PDF | Portal interativo respondeu 503 na validação; rota ColdFusion histórica respondeu 404. Ementários trimestrais são fontes documentais oficiais com processo, relator, órgão e ementa. | **Bloqueada** para busca; **candidate_document_only** para PDFs, condicionada a catálogo, checksum e parser |

### Decisão de integração

Nenhuma das seis fontes forneceu nesta rodada um contrato JSON/CSV de busca
textual, público e reproduzível sem controle. Portanto, não foi criado adapter
de runtime, não foram inventadas rotas alternativas e nenhuma falha foi
rebaixada para “zero resultados”. As ações de menor risco são: (a) manter os
providers existentes com `SourceTrace` explícito; (b) procurar exportações
oficiais e feeds documentais; (c) promover somente após fixtures sanitizadas e
teste offline do `CanonicalDecision`.

Fontes institucionais desta rodada: [TRF3](https://web.trf3.jus.br/jurisprudencia/),
[ajuda TJMG](https://www5.tjmg.jus.br/jurisprudencia/ajuda.do),
[portal TJRJ](https://www.tjrj.jus.br/web/portal-conhecimento/consulta-a-jurisprudencia),
[ajuda eJURIS](https://www3.tjrj.jus.br/ejuris/AjudaConsultaJuris.aspx),
[ementário TJES 2015](https://www.tjes.jus.br/wp-content/uploads/Revista_Ement_Juris_JAN_FEV_MAR_2015.pdf)
e [ementário TJES 2014](https://www.tjes.jus.br/wp-content/uploads/Revista_Ement_Juris_JUL_AGO_SET_2014.pdf).

## Auditoria adicional: TRT2, TJAP e Falcão JT

### TRT2 PJe Jurisprudência — contrato parcial reproduzível

O frontend oficial `https://pje.trt2.jus.br/jurisprudencia/` publica a versão
`1.5.0-i1` em `GET /juris-backend/api/opcoes`. A resposta pública observada foi
HTTP 200, JSON, contendo `regional`, `pjeConsultaUrl`, `captchaOption` e
versão. O bundle também confirma:

| Rota | Método/payload | Resultado público observado | Classificação |
| --- | --- | --- | --- |
| `/juris-backend/api/opcoes` | GET sem corpo | HTTP 200; JSON de configuração e versão | **Implementável como health/config**, sem decisão |
| `/juris-backend/api/filtros` | POST JSON com `timestamp`, `browserIpAddress`, `browserVia`, `name`, `ordenarPor`, `paginationSize`, `paginationPosition` e `fragmentSize` | HTTP 200; JSON com `hits`, `documents` e `aggregations`; chamada com valores neutros retornou `hits: 40027349` e agregações | **Candidato parcial**: catálogos/metadados reproduzíveis |
| `/juris-backend/api/documentos` | POST JSON; bundle usa filtros e parâmetros de paginação | HTTP 200, mas resposta contém `tokenDesafio` e imagem CAPTCHA | **Bloqueada** para coleta de decisões; não automatizar desafio |
| `/juris-backend/api/documentos/{id}` | POST; detalhe recebe token ou resposta de desafio | Não testada sem identificador legítimo; depende do mesmo controle | **Pendente/bloqueada** |
| `/juris-backend/api/token` | GET sem corpo | HTTP 200 sem conteúdo útil | **Não utilizar** |

O payload inicial documentado pelo próprio bundle inclui, além dos campos
acima, `dataPublicacaoStart`, `dataPublicacaoEnd`, `DataDistribuicaoStart`,
`DataDistribuicaoEnd`, `andField`, `orField`, `notField`, `andFieldEmenta`,
`andFieldDispositivo`, `anoProcesso`, `assunto`, `classeJudicial`,
`magistrado`, `meioTramitacao`, `orgaoJulgador`,
`orgaoJulgadorColegiado`, `tipoDocumento`, `browserUserAgent` e
`browserReferer`. Esses nomes foram observados no frontend, mas o contrato de
decisões não pode ser fechado sem sucesso sem desafio. Estado geral:
`partial_contract/blocked_access`; manter o provider fora da busca executável.

### TJAP Tucujuris

As duas entradas oficiais continuam sem contrato reproduzível. A consulta
`https://tucujuris.tjap.jus.br/tucujuris/pages/consultar-jurisprudencia/consultar-jurisprudencia.html`
respondeu HTTP 403 com Cloudflare; `services.tjap.jus.br` não resolveu DNS na
chamada controlada. Não foram executadas tentativas de contorno, descoberta
agressiva de assets ou replay de sessão. Estado: `blocked_access`; sem
payload, paginação, limite ou fixture de decisão.

### Falcão JT

O TRT9 confirma institucionalmente que o Falcão é repositório nacional da
Justiça do Trabalho, com sentenças, acórdãos, decisões monocráticas, decisões
de admissibilidade e precedentes. A entrada oficial
`https://jurisprudencia.jt.jus.br/` respondeu HTTP 403 CloudFront na chamada
pública de baixa frequência. Sem HTML/JS público acessível não há método,
payload, exportação, limite ou schema a promover. Estado: `blocked_access`;
manter TST/TRTs existentes como fontes independentes.

Evidências: [jurisprudência TRT2](https://pje.trt2.jus.br/jurisprudencia/),
[opções TRT2](https://pje.trt2.jus.br/juris-backend/api/opcoes),
[Tucujuris TJAP](https://tucujuris.tjap.jus.br/tucujuris/pages/consultar-jurisprudencia/consultar-jurisprudencia.html),
[Falcão JT](https://jurisprudencia.jt.jus.br/) e [descrição oficial do Falcão pelo TRT9](https://www.trt9.jus.br/portal/pagina.xhtml?pagina=FALCAO&secao=168).

## Novas superfícies oficiais fora do catálogo atual

### TCE-PR — exportação CSV de acórdãos

O portal ViaJuris do Tribunal de Contas do Paraná publica uma base de dados
abertos semanal, com acórdãos do ano corrente, dicionário de dados e arquivos
históricos por ano. A página de bases lista os arquivos de 1998 até 2026 e
expõe os campos `DsTipoAto`, `NrAto`, `AnoAto`, `NrProcesso`, `DsTitulo`,
`DsResumo`, `DsColegiado`, `DtPublicacaoDOE`, `DtSessao`, `NmRelator`,
`Termos`, `ReferenciaLegislativas`, `DsTema` e `UrlPDF`.

| Rota | Método/formato | Limite/atualização | Estado/recomendação |
| --- | --- | --- | --- |
| `https://viajuris.tce.pr.gov.br/DadosAbertos/DadosAbertos` | GET HTML de catálogo | Atualização semanal; ano corrente | **Implementável como sincronização documental** |
| `https://viajuris.tce.pr.gov.br/DadosAbertos/DadosAbertos/DownloadArquivo?nomeArquivo={ano}_acordaos_base_de_dados.csv` | GET, CSV delimitado por `;` | Arquivo por ano; resposta de 2026 observada com 2,29 MiB e HTTP 200 | **Implementável P1**, após fixture, checksum e parser de datas/acentuação |
| `https://viajuris.tce.pr.gov.br/DadosAbertos/DadosAbertos/DownloadArquivo?nomeArquivo=dicionario_de_dados.xlsx` | GET, XLSX | Dicionário publicado pelo portal | **Obrigatório para o contrato**; não tratar o CSV sem validar o dicionário |

Uma chamada pública controlada ao arquivo de 2026 retornou `application/octet-stream`
com `Content-Disposition` de CSV e linhas de acórdãos contendo resumo, relator,
ementa temática e `UrlPDF`. O arquivo é uma exportação oficial, não uma busca
interativa; o adapter deve fazer ingestão incremental e preservar o ano/URL
como identidade, sem supor que o registro seja decisão judicial comum. A
fonte deve ser categorizada como `court_jurisprudence` de tribunal de contas,
mantendo separação de TCU/TCE-SP.

**Evidência:** [catálogo de dados abertos TCE-PR](https://viajuris.tce.pr.gov.br/DadosAbertos/DadosAbertos),
[bases anuais](https://viajuris.tce.pr.gov.br/DadosAbertos/DadosAbertos/BaseDados)
e [arquivo CSV público de 2026](https://viajuris.tce.pr.gov.br/DadosAbertos/DadosAbertos/DownloadArquivo?nomeArquivo=2026_acordaos_base_de_dados.csv).

#### Manifesto mínimo recomendado para a sincronização

O catálogo oficial fornece as datas de atualização por arquivo, mas não
expõe ETag ou checksum HTTP confiável. O sincronizador deve manter um
manifesto local com: URL, ano, data observada no catálogo, `Content-Length`,
`Content-Type`, SHA-256 do arquivo baixado, número de linhas, cabeçalho bruto e
versão do dicionário. A resposta pública observada para o dicionário foi HTTP
200, `application/octet-stream`, tamanho 18.848 bytes e
`Content-Disposition: dicionario_de_dados.xlsx`.

O fluxo seguro é: consultar o catálogo semanalmente; baixar para staging;
validar o cabeçalho contra o dicionário; calcular SHA-256; rejeitar mudança de
colunas ou delimitador sem revisão; e só então promover a nova partição anual.
Não há necessidade de chamada por registro nem de scraping da interface de
pesquisa. Esse manifesto também torna a reexecução auditável quando o
tribunal substituir o arquivo do ano corrente.

### TCE-GO — endpoint JSON de jurisprudência

O Swagger oficial do Portal de Dados Abertos documenta
`POST https://transparencia-api.tce.go.gov.br/api/Transparencia/TceJuris`, grupo
“Jurisprudência e Processos”, atualização diária e espectro anual. O Swagger
declara resposta JSON (`application/json`/`text/json`), sem parâmetros ou
corpo documentado. A chamada pública `POST {}` retornou HTTP 200, mas o payload
foi um erro do backend (“Connection failed ... WebSocketConnectionNotAccepted”)
em vez de registros. Estado: **bloqueada/instável**, não implementar até uma
resposta de sucesso reproduzível, limites e schema de item serem publicados.

**Evidência:** [Swagger oficial TCE-GO](https://transparencia-api.tce.go.gov.br/swagger/docs/v1)
e [interface Swagger](https://transparencia-api.tce.go.gov.br/swagger/ui/index).

### TCE-CE — portal público sem contrato de exportação

O TCE Ceará mantém consulta oficial de decisões por palavra-chave/documento,
com decisões transitadas em julgado a partir de janeiro de 2014. Também há
boletins em PDF/DOC. Nesta rodada não foi encontrada uma especificação pública
de API de jurisprudência nem exportação estruturada reproduzível; a API de
Dados Abertos do SIM é de transparência municipal e não deve ser usada como
substituto. Estado: **pendente**, sem adapter.

**Evidência:** [consulta oficial de decisões TCE-CE](https://www.tce.ce.gov.br/decisoes-do-tce-ce),
[portal de jurisprudência](https://tcewsapi.tce.ce.gov.br/paginas/jurisdicionadoJurisprudenciaPortal.xhtml)
e [API SIM, fora do escopo jurisprudencial](https://api-dados-abertos.tce.ce.gov.br/sim/).

## Fechamento dos nove candidatos restantes

| Candidato | Rota pública equivalente pesquisada | Método/payload/formato | Estado para a NanoJuris |
| --- | --- | --- | --- |
| TJPE | Portal de jurisprudência e página de acesso automatizado | UI; MNI/WSDL é consulta processual e DataJud exige chave; não há payload textual de jurisprudência | **Pendente**; não usar DataJud como substituto |
| TJPB | `POST /api/jurisprudencia/pesquisar` no portal PJe | POST com sessão e `_token`; HTML/JSON dependente de sessão | **Bloqueado por controle de sessão** |
| TSE/TRE | SJUR REST público e shell oficial | POST JSON para busca/catálogos; busca acrescenta CAPTCHA; catálogos têm rotas estáveis | **Catálogos implementáveis; busca bloqueada** |
| TRF3 | Formulário oficial e `/acordaos/Acordao` | UI/HTML; detalhe público por identificador; sem payload de pesquisa reproduzível | **Pendente** |
| TJMG | `formEspelhoAcordao.do` e rotas por número/palavras | WebForms/HTML; consulta textual apresentou captcha | **Bloqueado** |
| TJRN | SPA `jurisprudencia.tjrn.jus.br` | Portal/JS; bundles e consulta retornaram 403 | **Bloqueado/inconclusivo** |
| TJSE | Formulário `consultarJurisprudencia.tjse` | JSF/PrimeFaces POST; resposta de teste “Captcha inválido” | **Bloqueado** |
| TJRJ | eJURIS e portal eproc | WebForms/HTML e PDF; eJURIS usa reCAPTCHA; eproc é base separada | **Bloqueado/pending_contract** |
| TJES | Portal atual e ementários oficiais | Portal 503/legado 404; PDFs trimestrais catalogáveis | **Busca bloqueada; PDF candidato documental** |

O único novo equivalente com evidência de baixo risco foi o CSV anual do
TCE-PR, descrito acima. TCE-GO tem rota JSON documentada, mas falhou no
backend, e TCE-CE não publicou contrato estruturado. Nenhum dos nove
candidatos deve ser marcado como “sem resultados” por causa desses controles.

## Fontes oficiais consultadas

- [API pública de jurisprudência do TJDFT](https://www.tjdft.jus.br/transparencia/tecnologia-da-informacao-e-comunicacao/dados-abertos/webservice-ou-api)
- [Documentação JSON do TJDFT](https://www.tjdft.jus.br/transparencia/tecnologia-da-informacao-e-comunicacao/dados-abertos/documentacao_api_seti_transparencia.pdf/@@download/file/Documentação_API_SETI_Transparência.pdf)
- [Portal de Dados Abertos do STJ](https://dadosabertos.web.stj.jus.br/)
- [Datasets de jurisprudência do STJ](https://dadosabertos.web.stj.jus.br/group/jurisprudencia)
- [Webservices e dados abertos do TCU](https://sites.tcu.gov.br/dados-abertos/webservices-tcu/)
- [Pesquisa de jurisprudência do TRF3](https://web.trf3.jus.br/jurisprudencia/)
- [Ajuda oficial da pesquisa do TJMG](https://www5.tjmg.jus.br/jurisprudencia/ajuda.do)
- [API pública DataJud (fora do escopo)](https://datajud-wiki.cnj.jus.br/api-publica/endpoints/)
