# Registro de decisões de baixo risco — 2026-09-09

Este registro acompanha o inventário executável em
`docs/coverage/open-task-audit-current.json`. Ele separa decisões técnicas que
podem ser tomadas automaticamente de dependências que exigem prova externa ou
responsável humano. Nenhuma decisão deste arquivo autoriza publicação,
deploy, alteração de produção ou contorno de controle de acesso.

## Decisões técnicas aplicadas

| Decisão | Regra adotada | Evidência |
|---|---|---|

| Transporte de API pública | Usar `SharedHttpClient` com allowlist HTTPS, timeout, limite de bytes, rate limit e circuito; sem retry em POST ou em APIs que expõem decisões de gateway/rate limit | `src/nanojuris/providers/bnp_pangea.py`; 26 testes unitários e 3 testes live bounded |
| Erro externo | Preservar 403, 429, CAPTCHA, WAF, Turnstile, timeout, TLS, redirecionamento fora da allowlist e schema inválido como estados explícitos | contratos de transporte e testes de regressão |
| Fonte contextual | Não promover automaticamente catálogo, precedente qualificado, boletim, banco curado ou metadado como jurisprudência geral | `coverage_matrix.py`, manifesto e mapa nacional |
| Identidade institucional | Preferir autoridade/ramo/grau/coleção canônicos do registro de estado; não renomear provider legado sem migração | reconciliação TRF1, STJ e STM de 2026-09-09 |
| Federação | Promover somente quando runtime, contrato, live, fixtures, qualidade e trace estiverem comprovados; candidatos e bloqueados ficam fora do rollout | `build_promotion_manifest.py` e smoke federado |
| Inventário | Tratar os JSONs gerados como fonte de verdade; não editar matriz, mapa ou workpack manualmente | geradores nacionais e auditoria de tarefas |

## Hardening local — adapters opt-in dos 27 TREs (2026-09-09)

O adapter `TreSjurJurisprudenciaProvider` passou a classificar o tipo de
decisão de forma conservadora: sentenças e rótulos desconhecidos são
rejeitados localmente e não podem entrar como segundo grau. Quando ocorre
essa filtragem, o total remoto deixa de ser tratado como autoritativo e a
página permanece incompleta, evitando falso vazio ou falsa completude.

Os 27 adapters por UF ficam disponíveis somente em
`NanoJurisClient(include_candidate_providers=True)`. O cliente padrão não os
roteia; cada UF ainda depende de paginação, inteiro teor, fixtures e smoke
federado independentes. A matriz continua apontando o agregado SJUR como
pendente, sem alterar a contagem de cobertura ouro.

O probe bounded de paginação do TRE-SP respondeu duas vezes HTTP 200 com a
mesma janela de dez IDs, apenas em ordem diferente, e `totalRegistros=10` em
ambas. A classificação é `remote_page_ignored_duplicate_window`; a segunda
página não foi considerada comprovada.

## Inventário bounded — SJUR dos 27 TREs

Foi executada uma consulta pública de baixa frequência, sem credenciais e sem
contorno, contra a rota oficial por tribunal do SJUR. O resultado está em
`docs/provider-discovery/tre-sjur-route-inventory-live-20260909.json`.

- 26 TREs retornaram HTTP 200 com registros que contêm ementa ou decisão
  textual;
- TRE-RR retornou HTTP 200 com `totalRegistros=0`, classificado como vazio
  autoritativo apenas para o termo bounded usado;
- a resposta foi mantida como metadados redigidos (hash, tamanho, campos e
  contagem), sem persistir corpo decisório;
- a descoberta não promove adapters nem afirma cobertura integral: ainda faltam
  contrato por UF, filtros, paginação, documento, fixtures e smoke federado;
- temas, eleições, catálogos e dados administrativos permanecem separados de
  jurisprudência textual.

Decisão: fechar o inventário TSE/TRE (0098/T053) e abrir a implementação em
lote de um a três TREs, começando por TRE-SP, TRE-AC e TRE-AL. Manter qualquer
falha futura como bloqueio, timeout, schema ou vazio explícito; nunca como
resultado silencioso.

O lote documental foi iniciado em `docs/provider-discovery/tre-sjur-gold-live-20260909.json`.
TRE-SP teve uma decisão observada com PDF oficial válido; duas tentativas
subsequentes (TRE-AC e TRE-AL) receberam mensagem explícita de excesso de
requisições e foram classificadas como `rate_limited`, sem repetição. Portanto
o contrato de documento está comprovado para uma amostra do lote, mas não há
promoção automática dos três providers antes de fixtures, filtros e teste de
rate-limit estarem fechados.

Foi criado o adapter de família opt-in em
`src/nanojuris/providers/tse_sjur_jurisprudencia.py`, com isolamento por
`TRE-XX`, sem registro no cliente padrão. Isso reduz duplicação de código sem
inflar a federação nem afirmar cobertura antes dos gates por UF.

## Nova evidência — TRT8 PJe (2026-09-09)

Foi confirmada uma superfície pública oficial de jurisprudência do TRT8 no
PJe, com filtros de segunda instância e acórdão, paginação, consulta de
detalhe e inteiro teor HTML. A evidência redigida está em
`docs/provider-discovery/trt8-pje-jurisprudencia-live-20260909.json` e o
adapter independente em `src/nanojuris/providers/trt8_pje_jurisprudencia.py`.

O registro inicial acima foi supersedido: após a chamada bounded de 30 segundos
(`trt8-pje-federated-smoke-20260909-timeout30.json`) com HTTP 200, filtros
explícitos de segundo grau/acórdão, fixtures completas e gates locais aprovados,
o TRT8 passou a `live_validated`/`federation_enabled` na federação local.
Bloqueios, schema inválido e timeout continuam estados distintos.

O inventário atual registra 81 providers (72 em runtime, 8 candidatos e 1
família), 249 superfícies e 68 superfícies federadas no mapa nacional. O
TJMRS foi adicionado como runtime opt-in de processo exato, sem alterar a
federação padrão.

## Decisões que permanecem automaticamente adiadas

As tarefas globais de cobertura continuam abertas porque descrevem um escopo
nacional e dependem de novas fontes oficiais ou revisão humana. O código deve
continuar avançando por lotes de fontes reproduzíveis, mas não é seguro marcar
como concluído um requisito que ainda depende de todas as superfícies:

- `0098/T058` — fechar contrato, adapter, fixtures e validação canônica por
  fonte reproduzível;
- `0098/T059` — executar smoke opt-in e promover somente fontes que passem os
  oito gates.

`0098/T014` e `0098/T017` foram fechadas para a família eproc implementada,
com parser independente, transporte compartilhado e detalhe bounded cobertos
por 56 testes e evidência live de TNU/TRF2/TRF6. Isso não encerra T058/T059:
fontes candidatas ou sem rota reproduzível continuam fora da federação.

## Inventário de dependências não automatizáveis

O auditor atual registra **99 tarefas abertas**:

| Classe | Quantidade | Regra de decisão |
|---|---:|---|
| `external_source` | 74 | Executar uma chamada oficial bounded por lote; se houver bloqueio, registrar a evidência e manter o estado explícito. Nunca transformar bloqueio em vazio. |
| `human_review` | 25 | Não simular licença, retenção, owner, relevância, escopo condicional ou autorização de promoção. |
| `local_evidence` | 0 | Todas as decisões técnicas locais identificadas nesta rodada foram resolvidas ou reclassificadas com evidência. |

O detalhamento por pacote, tarefa, descrição e próxima ação está em
`open-task-audit-current.json` e em `open-task-audit-current.md`. As categorias
não são equivalentes: uma fonte pode ter adapter local e continuar bloqueada
externamente ou aguardando revisão humana.

## Descoberta externa — TRT3 Ementário (2026-09-09)

O repositório oficial do TRT3 expôs a coleção `Ementário de Jurisprudência` e
um volume PDF público (n. 12, dezembro de 2016). A entrada respondeu HTTP 200
e o PDF respondeu `application/pdf`, com 35 páginas e texto extraível por
amostra. A evidência redigida está em
`docs/provider-discovery/trt3-ementario-live-20260909.json`.

Decisão de baixo risco: classificar como `curated_context`/`candidate_static_ementario_only`.
O volume é uma publicação estática de ementas, não uma busca geral com filtros,
paginação ou total autoritativo. Não criar adapter de jurisprudência geral nem
habilitar federação até que uma rota de consulta reproduzível seja comprovada.

## Descoberta bounded - TJSC/CJPG (2026-09-09)

As duas entradas oficiais consultadas (`/pesquisa-jurisprudencia` e
`/jurisprudencia`) responderam HTTP 200, mas expuseram somente shell de portal,
sem registros decisórios, formulários, paginação, rota de documento ou contrato
de API. Ambas continham marcador de CAPTCHA. A evidência sanitizada está em
`docs/provider-discovery/tjsc-cjpg-route-live-20260909.json`.

Decisão de baixo risco: manter a superfície `TJSC/CJPG` como `candidate` e
`contract_status=not_proven`; não reutilizar o adapter eproc de segundo grau e
não criar adapter baseado apenas no shell. Nenhum bypass, credencial ou sessão
controlada foi usado.

## Descoberta bounded - TJDFT/CJPG (2026-09-09)

As entradas oficiais do TJDFT responderam HTTP 200, mas o único formulário
encontrado aponta para `@@search` com `SearchableText`, isto é, busca contextual
do portal. Não foram observados registros decisórios de primeiro grau,
paginação, total ou rota de documento. A evidência sanitizada está em
`docs/provider-discovery/tjdft-cjpg-route-live-20260909.json`.

Decisão de baixo risco: manter `TJDFT/CJPG` como `candidate` e
`contract_status=not_proven`; não transformar a busca contextual em adapter de
jurisprudência textual nem habilitá-la na federação.

## Decisão de escopo - STJ Dados Abertos (2026-09-09)

`stj_dados_abertos_jurisprudencia` continua sendo a única superfície
`live_validated` ainda não federada. A rechecagem do catálogo CKAN e do
pareamento de inteiro teor confirma que os arquivos são públicos e de boa
qualidade, mas o STJ não oferece busca jurídica remota sobre o conteúdo dos
recursos. Os filtros jurídicos só existem depois de uma sincronização e de um
índice local explícito.

Decisão técnica: não habilitar a fonte na busca federada remota, pois isso
exigiria baixar/pesquisar um corpus local e contrariaria o modo live sem índice.
Manter as operações explícitas de catálogo, plano de sincronização e ingestão
local, com estado `live_not_federated` e diagnóstico visível.

## Decisões fixadas pelo mantenedor — ciclo 2026-09-09

Estas escolhas são a fonte operacional para os SDDs 0077, 0089, 0091, 0092,
0098 e 0099. Elas não substituem revisão humana de licença, retenção,
rotulagem ou autorização externa.

- **Escopo:** core e superfícies condicionais são inventariados; TCEs, TJMs,
  coleções curadas e fontes especializadas só entram no padrão após os oito
  gates e prova de jurisprudência textual.
- **Coleções curadas:** bancos de sentenças, boletins e ementários continuam
  contextuais/opt-in e não competem automaticamente com jurisprudência geral.
- **Promoção:** aprovação técnica habilita apenas o manifesto/federação local;
  release, deploy e produção permanecem bloqueados.
- **Operação:** cache live efêmero de 10 minutos, telemetria agregada por 30
  dias, sem corpus pesquisável persistente e sem inteiro teor bruto fora do
  fluxo autorizado; fixtures sanitizadas e sem credenciais/cookies.
- **Frequência:** intervalo mínimo de 2 segundos por provider, sem paralelismo
  no mesmo host, até três páginas por sonda e respeito a `Retry-After`.
- **Responsável:** mantenedor NanoJuris. Contatos externos são pacotes para
  envio manual, nunca envio automático.
- **Ranking:** manter nDCG@10 +25%, irrelevantes no top 5 reduzidos em 50% e
  <=10%, filtros explícitos 100%, identificador exato em primeiro e p95 abaixo
  de 150 ms.
- **Rótulos:** o agente pode preparar pré-rótulos, mas não os converte em
  aprovação humana; a amostra é 8 consultas x top 10 (80 linhas).

## Nova decisão técnica — TJMRS (2026-09-09)

A rota oficial `GET /abreJurisprudencia.php?processo=<CNJ>` respondeu duas
vezes com acórdão textual de segundo grau, e uma vez com vazio autoritativo.
Foi criado `tjmrs_jurisprudencia` com transporte compartilhado, fixtures,
parser canônico e `CanonicalDocument`. A fonte entra no runtime como opt-in,
mas permanece fora da federação padrão por não oferecer busca geral, paginação
ou total de corpus comprovados. A evidência redigida é
`docs/provider-discovery/tjmrs-jurisprudencia-live-20260909.json` e o SDD é
`specs/changes/0101-tjmrs-jurisprudencia/`.

Esta decisão não exige ação humana imediata. Uma futura promoção padrão só
deverá ser decidida se o TJMRS publicar um contrato geral reproduzível; não se
deve inferir isso a partir da rota de processo exato.

Implementação executável: `src/nanojuris/governance.py` expõe
`DEFAULT_OPERATIONAL_POLICY`; o detalhe serializado está em
`docs/coverage/decision-record-20260909.json`.

## Rechecagem técnica — TJMMG (2026-09-10)

O portal oficial do TJMMG expõe metadados públicos de classes e relatores em
`GET /jurisprudencia/get`. A investigação confirmou que consultas amplas e um
número inexistente podem retornar dezenas de megabytes, mas número CNJ exato e
janela fechada de julgamento retornaram envelopes `collection` bounded com
ementa, texto, identificador, relator e data. A rota oficial de PDF por
`NomeArquivo` também respondeu `application/pdf` válido e com texto extraível.
Tudo foi sondado sem credenciais, CAPTCHA ou persistência do corpo; a evidência
redigida está em
`docs/provider-discovery/tjm-mg-jurisprudencia-api-live-20260909.json`.

Decisão técnica: manter `tjmmg_jurisprudencia_api` como runtime opt-in, com
guard obrigatório de número exato ou intervalo fechado, parser canônico e
`CanonicalDocument` explícito. Não habilitar federação padrão porque a fonte
continua sem paginação server-side para texto amplo. Resposta excedente, schema,
timeout e bloqueio continuam estados explícitos; somente `collection: []` de
consulta bounded é vazio autoritativo. Repetição periódica e aprovação humana
de retenção/licença permanecem pendentes.

## Snapshot nacional vigente

## Reconciliação das superfícies militares (2026-09-10)

As três linhas militares que estavam sem provider na matriz nacional foram
reconciliadas com evidência explícita:

- `TJMMG/PORTAL` → `tjmmg_jurisprudencia_api`, contrato bounded por número/janela
  fechada; buscas amplas seguem sem limite seguro e fora da federação padrão;
- `TJMSP/PORTAL` → `tjmsp_jurisprudencia`, bloqueio HTTP 403 explícito;
- `TJMRS/PORTAL` → `tjmrs_jurisprudencia`, documento público validado, porém
  sem busca textual geral/paginação, portanto `live_not_federated`.

Essas associações reduzem o inventário de providers órfãos e o número de
superfícies core sem provider, mas não aumentam a cobertura federada. A matriz
continua exigindo os oito gates para qualquer promoção.

## Rechecagem técnica — TJMSP (2026-09-10)

O portal oficial `https://jurisprudencia-client.tjmsp.jus.br/` respondeu HTTP
403 em sondagem bounded sem credenciais. O adapter diagnóstico
`tjmsp_jurisprudencia` preserva o estado `access_control_required`, sem criar
resultados sintéticos ou classificar a resposta como vazio. A fonte permanece
opt-in, fora da federação padrão, até que o TJMSP forneça uma rota pública
documentada ou uma alternativa institucional autorizada.

Evidência: `docs/provider-discovery/tjmsp-jurisprudencia-live-recheck-20260910.json`.

## Reconciliação de inventário — TNU/PORTAL (2026-09-09)

O inventário genérico de tribunais superiores cria uma linha `TNU/PORTAL`, mas
a evidência oficial `docs/provider-discovery/tnu-public-module-live-20260909.json`
mostra que a busca textual pública, a paginação e o inteiro teor estão no
módulo EPROC da TNU. A chamada bounded retornou registros com
`degree=second`/`instance=second`, origem TNU e documento HTML público.

Decisão técnica de baixo risco: manter `TNU/PORTAL` visível para completude do
inventário, mas reconciliá-lo explicitamente como alias de
`TNU/EPROC` (`tnu_eproc_jurisprudencia`). Isso evita contar um segundo provider
ou registrar uma lacuna artificial; não altera rota, parser ou rollout.

## Classificação de bloqueio — TRT3/TRT4 (2026-09-09)

As páginas oficiais dos TRT3 e TRT4 confirmam superfícies textuais de
jurisprudência de segundo grau, mas as rotas públicas de consulta retornaram
HTTP 403 da CloudFront em chamadas bounded sem credenciais. As evidências são
`docs/provider-discovery/trt3-jurisprudencia-route-live-20260909.json` e
`docs/provider-discovery/trt4-jurisprudencia-route-live-20260909.json`.

Decisão técnica: registrar ambas como `blocked_or_unavailable`, preservar a
entrada oficial e não criar adapter contra a página de bloqueio. A rechecagem
só deve ocorrer após mudança observável na disponibilidade ou uma rota oficial
pública alternativa; HTTP 403 não representa busca vazia.

## Correção de rota pública — TNU/eproc (2026-09-09)

O módulo público de jurisprudência anunciado pelo CJF usa
`https://eproctnu-jur.cjf.jus.br/eproc`, enquanto o host legado
`eproctnu.cjf.jus.br/eproc` redireciona para SSO. A configuração do provider foi
corrigida para a rota pública. Uma busca bounded por `aposentadoria` retornou
HTTP 200, 10 cards e total informado; três registros foram normalizados como
`degree=second`/`instance=second`. O detalhe de um registro retornou HTTP 200,
HTML textual e inteiro teor extraível.

Evidência: `docs/provider-discovery/tnu-public-module-live-20260909.json`.
Decisão: manter a promoção técnica já existente e corrigir somente o endpoint;
nenhum bypass, credencial ou sessão autenticada foi usado.

## Rechecagem de inteiro teor — seis providers públicos (2026-09-09)

Uma consulta bounded de baixa frequência (`responsabilidade civil`, página 1,
um resultado) foi seguida de uma chamada oficial de documento para TJMG,
TJMG/EJEF, TJRJ/EJURIS, TJRN, TJRO e TJTO. Todos retornaram resultado de
segundo grau e documento público extraível, com hash e tamanho lógico
registrados. TJRN entrega o texto inline; TJTO entrega um `CanonicalDocument`;
os demais usam rota de detalhe ou download oficial.

Evidência redigida: `docs/provider-discovery/gold-document-probe-live-20260909.json`.
Decisão: aceitar a evidência como rechecagem técnica de inteiro teor, sem
declarar cobertura integral, estabilidade permanente ou aprovação jurídica.
Nenhum desafio, credencial, proxy ou bypass foi usado.

## Correção de transporte — TJMS/CJPG (2026-09-09)

O binding TJMS reutilizava corretamente o parser e-SAJ de primeiro grau, mas o
construtor herdado mantinha a allowlist do host TJSP. Isso fazia a requisição
oficial `https://esaj.tjms.jus.br/cjpg/pesquisar.do` ser rejeitada localmente
antes do transporte. A subclasse agora reconfigura a política compartilhada
para `esaj.tjms.jus.br`, sem ampliar hosts ou relaxar TLS.

Uma chamada bounded respondeu HTTP 200, total 317.418, um registro de primeiro
grau e 20.421 caracteres de inteiro teor inline. Evidência:
`docs/provider-discovery/tjms-cjpg-transport-detail-live-20260909.json`.
Decisão: manter TJMS/CJPG federado, atualizar sua evidência live e não alterar
o escopo CJSG.

- 249 superfícies mapeadas (155 core, 94 condicionais);
- 81 providers catalogados, 22 órfãos ainda explícitos no mapa;
- 46 superfícies core sem provider;
- 39 bloqueadas ou indisponíveis;
- 137 superfícies em descoberta e 181 itens na fila de descoberta;
- 68 superfícies tecnicamente federadas/GOLD;
- CJPG: 8/27; CJSG: 25/27;
- suíte: 1.695 aprovados, 26 skips opt-in/ambiente após o fechamento do TRT3.

A varredura bounded de 27 entradas oficiais dos TJs encontrou 179 URLs
candidatas a rotas CJPG. Elas foram registradas como descoberta, não como
contrato ou cobertura: [first-degree-route-inventory-20260909.json](../provider-discovery/first-degree-route-inventory-20260909.json).

O TJPR teve uma rechecagem adicional da entrada oficial de SentenÃ§a Digital.
Ela confirmou a rota pÃºblica e uma resposta de vazio autoritativo para um
identificador CNJ especÃ­fico, mas nÃ£o confirmou corpus geral, texto decisÃ³rio
ou documento. O provider permanece `discovery_only`; a evidÃªncia estÃ¡ em
[tjpr-sentenca-digital-live-20260909.json](../provider-discovery/tjpr-sentenca-digital-live-20260909.json).

A sonda complementar de candidatos, limitada a trÃªs GETs por tribunal,
registrou 12 respostas acessÃ­veis e 3 falhas de transporte entre 15 rotas
efetivamente sondadas. Nenhuma resposta foi promovida sem contrato decisÃ³rio;
o inventÃ¡rio completo estÃ¡ em
[first-degree-route-inventory-probed-20260909.json](../provider-discovery/first-degree-route-inventory-probed-20260909.json).

O TJAL/ESMAL foi revalidado sem alteraÃ§Ã£o de escopo: a consulta retorna
sentenÃ§as de primeiro grau e documentos PDF oficiais, mas a coleÃ§Ã£o continua
curada e sem total autoritativo. O provider segue habilitado como fonte parcial,
sem ser contado como acervo CJPG exaustivo; a evidÃªncia corrente Ã©
[tjal-esmal-banco-sentencas-live-20260909.json](../provider-discovery/tjal-esmal-banco-sentencas-live-20260909.json).

## Probe bounded adicional — TJBA/CJPG (2026-09-09)

A rota oficial `http://www2.tjba.jus.br/jurisprudencianet/index.wsp`, encontrada
no portal do TJBA, respondeu HTTP 503 sem texto decisório. A superfície fica
`source_unavailable`, sem contrato ou adapter, e não entra na federação. A
evidência está em
`docs/provider-discovery/tjba-cjpg-route-live-20260909.json`.

## Próximo lote recomendado

### Descoberta oficial TRT6 — 2026-09-09

O portal público de Consulta de Acórdãos do TRT6 expõe formulário textual,
filtros por processo, redator, órgão e datas, além de paginação no JavaScript,
mas exige resposta reCAPTCHA antes do POST de pesquisa. Sem uma resposta
fornecida por usuário ou fluxo autorizado, não há contrato reproduzível de
resultados. A fonte foi registrada como `access_blocked`, sem adapter ou
federação, em `docs/provider-discovery/trt6-acordaos-route-live-20260909.json`.

Continuar por uma a três fontes com rota oficial reproduzível, priorizando
superfícies `core_ready_state` ainda não federadas. Para cada lote: contrato,
fixture, parser independente, detalhe/documento bounded, smoke opt-in, geração
dos inventários e gates focados. Fontes com CAPTCHA, WAF, Turnstile, login,
TLS, 403 ou 429 permanecem em `blocked_or_unavailable` até existir uma rota
oficial pública diferente.

Sem commit, push, tag, release, deploy, Terraform apply ou alteração em
produção.

## Decisão de baixo risco aplicada — TSE SJUR

Foi criado o provider `tse_sjur_jurisprudencia`, separado do provider de
catálogo `justica_eleitoral_sjur`. A rota pública oficial respondeu com um
registro textual identificável e foi registrada em
`docs/provider-discovery/tse-sjur-search-live-20260909.json`.

Decisão atual: `runtime=implemented`, `live_status=valid`,
`supports_unified_search=false` e `federation_status=disabled`. As páginas 1,
2 e 3 ignoraram `pagina`/`tamanho` e devolveram a mesma resposta de 132
registros; a capacidade permanece `pagination_mode=none`. O PDF oficial foi
validado para um identificador observado. O adapter agora é instanciado pelo
cliente padrão para uso explícito, sem ser roteado pela federação padrão; a
promoção para federação continua condicionada à comprovação de paginação
remota segura. Essa atualização fecha `0100/T009` como promoção técnica de
runtime, sem declarar completude do corpus ou aprovação humana.

## Rechecagem bounded — CJSG (2026-09-09)

Foi executada uma única sonda pública de baixa frequência para os oito bindings
CJSG já existentes, com `responsabilidade civil`, página 1 e um registro por
fonte. Sete buscas retornaram dados HTTP 200; TJPE permaneceu
`source_unavailable`. Nos detalhes, quatro documentos foram obtidos
publicamente e três retornaram `access_control_required` (TJAC, TJAL e TJAM).
Nenhum controle foi contornado e nenhum estado foi convertido em vazio.

Evidência: `docs/provider-discovery/cjsg-live-20260909-cycle82.json`.
Decisão: atualizar a evidência live, manter os gates e o rollout existentes e
preservar bloqueios de detalhe explicitamente.

## Rechecagem bounded — TRT2/BASIS (2026-09-09)

A coleção pública de boletins do TRT2 respondeu HTTP 200, mas não retornou
registros para `responsabilidade civil` e não declarou total autoritativo.
O estado foi registrado como `unconfirmed_empty`, sem promoção para o corpus
geral do TRT2 e sem alteração do rollout opt-in.

Evidência: `docs/provider-discovery/trt2-basis-live-recheck-20260909.json`.

## Rechecagem oficial — TJCE/CJPG (2026-09-09)

A rota oficial e-SAJ de primeiro grau foi consultada com uma página pequena e
termo jurídico neutro. O host encerrou a conexão TLS antes de devolver uma
resposta; nenhum resultado foi observado. A evidência foi registrada em
`docs/provider-discovery/tjce-cjpg-route-live-20260909.json` como
`transport_blocked`, sem adapter ou promoção. Esse estado não representa vazio
autoritativo e não houve tentativa de contornar a proteção.

## Descoberta e rechecagem bounded — TRT3/Jurisprudência (2026-09-09)

O portal oficial do TRT3 confirma a superfície de “Acórdãos na íntegra” e
aponta para pesquisa textual e pesquisa por número de processo. As duas rotas
oficiais vinculadas responderam HTTP 403 com a página padrão de bloqueio do
CloudFront. O estado foi registrado como `access_blocked`, sem contrato
executável, adapter ou federação. Não houve credenciais, CAPTCHA, WAF ou
CloudFront bypass.

Evidência: `docs/provider-discovery/trt3-jurisprudencia-route-live-20260909.json`.

Decisão: manter a superfície no inventário como descoberta oficial bloqueada;
não classificá-la como vazia e não promover um provider até que uma rota pública
reproduzível ou um fluxo autorizado pelo usuário esteja disponível.

## Descoberta e rechecagem bounded — TRT4/Jurisprudência (2026-09-09)

O TRT4 documenta oficialmente pesquisa textual em decisões publicadas e mantém
um host específico para jurisprudência e documentos de acórdãos. O host de
pesquisa, seu caminho de aplicação e a rota de documento conhecida responderam
HTTP 403 com bloqueio padrão do CloudFront. A superfície fica
`access_blocked`, sem adapter, contrato executável ou federação; nenhum controle
foi contornado.

Evidência: `docs/provider-discovery/trt4-jurisprudencia-route-live-20260909.json`.

## Revalidação bounded — TJES/CJPG (2026-09-09)

A API pública oficial do TJES foi revalidada no core `pje1g`, separado do
`pje2g`. As páginas 1 e 2 de uma consulta pequena retornaram HTTP 200, total
conhecido, registros de primeiro grau e inteiro teor inline. Os identificadores
e hashes foram preservados sem gravar o corpo das decisões.

Evidência: `docs/provider-discovery/tjes-cjpg-live-20260909.json`.

Decisão: manter `tjes_cjpg` como fonte CJPG federada, atualizar o live check e
preservar o limite de 20 registros por página. A evidência confirma o contrato
existente; não mistura CJPG com CJSG, turma recursal ou consulta processual.

## Decisão de baixo risco — TRT8 rollout (2026-09-09)

O registro anterior de duas tentativas expiradas foi supersedido. A terceira
chamada pública bounded, com timeout de 30 segundos, foi válida e fechou T009.
O adapter TRT8 PJe está habilitado apenas na federação local técnica; release,
deploy, produção e aprovação jurídica continuam fora do escopo.

## Correção de decisão — TRT8 rollout bounded (2026-09-09)

Uma nova chamada pública única, com timeout bounded de 30 segundos e os filtros
explícitos `2ª Instância`/`Acórdão`, respondeu HTTP 200 em 12,7 s e retornou um
registro válido de um total declarado de 46.181. O corpo não foi persistido;
somente hash, tamanho, contagem e `SourceTrace` foram registrados em
`docs/provider-discovery/trt8-pje-federated-smoke-20260909-timeout30.json`.

Com as fixtures de sucesso, segunda página, detalhe, vazio, bloqueio e schema
inválido já presentes, o TRT8 passou os gates técnicos locais e foi promovido
para a federação local determinística. A promoção não autoriza release, deploy,
produção ou aprovação jurídica; estes continuam pendentes do mantenedor.
### TRT6 — binding diagnóstico (2026-09-10)

O provider `trt6_jurisprudencia` foi criado para as entradas oficiais PJe e
Consulta de Acórdãos. A busca live retornou validação de reCAPTCHA; portanto o
estado permanece `access_control_required`, candidato/opt-in e fora da
federação. Nenhum token foi gerado, resolvido, armazenado ou reutilizado.
### Família SJUR/TRE — SDD 0107

Foi criado o binding de família `tre_sjur_jurisprudencia` em modo opt-in,
exigindo `authority=TRE-XX` para selecionar uma UF. O dispatcher reutiliza o
adapter específico, rejeita paginação não comprovada e mantém a federação
padrão desabilitada até validar detalhe/PDF e completude por UF.
### Família eproc federal - SDD 0108

Foi criado o binding de família `eproc_jurisprudencia_federal` em modo opt-in,
exigindo autoridade explícita (`TNU`, `TRF2`, `TRF4` ou `TRF6`). O dispatcher
reutiliza os adapters específicos e preserva o host, a paginação e o
`SourceTrace` de cada instalação. Não há pesquisa federal agregada nem
promoção automática; cada instalação permanece sujeita aos próprios gates
live e de inteiro teor.

### TRT3 — volume curado de ementário (2026-09-10)

Foi validado o provider `trt3_ementario_jurisprudencia` contra o PDF oficial
do TRT3. A sonda bounded retornou 3 registros de um volume localmente completo
de 9 ementas, com `degree=second`, `instance=second`, `branch=labor`, PDF
extraível de 35 páginas e documento público recuperável. A fonte é uma coleção
curada estática, não uma busca geral do TRT3; por isso permanece opt-in e fora
da federação padrão. Nenhuma credencial, CAPTCHA, proxy ou bypass foi usado.
Evidência: `docs/provider-discovery/trt3-ementario-live-20260909.json`.

### TRE-SP — revalidação SJUR bounded (2026-09-10)

Uma nova chamada pública única contra a rota oficial do TRE-SP respondeu HTTP
200 e retornou três registros textuais classificados como segundo grau. Um dos
identificadores observados entregou PDF oficial válido de sete páginas, com
extração completa. A paginação remota continua não comprovada e o binding
permanece opt-in; a evidência não altera a federação padrão nem a contagem de
SJUR ouro.

Evidência: `docs/provider-discovery/tre-sp-sjur-live-20260910.json`.
