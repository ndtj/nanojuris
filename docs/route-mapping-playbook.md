# Route Mapping Playbook v4

Este playbook orienta a descoberta rapida de rotas publicas viaveis para novos
providers de jurisprudencia. O objetivo nao e raspar qualquer pagina: e encontrar
contratos publicos, auditaveis e juridicamente uteis.

## Principio operacional

Uma rota so deve avancar para provider quando retornar conteudo juridico real em
sessao HTTP limpa, sem cookies exportados do navegador, captcha, login, token
privado, segredo de justica ou contorno de controle de acesso. Isso nao deve
impedir a descoberta: uma falha em uma rota nunca encerra a investigacao da
fonte. O mapeamento deve continuar por catalogos, busca, detalhes, documentos,
informativos, datasets e superficies tecnicas alternativas.

O fluxo recomendado e:

1. Encontrar a pagina oficial de jurisprudencia.
2. Fazer uma busca manual simples no navegador.
3. Usar Network/HAR apenas para entender endpoints, metodos e parametros.
4. Reproduzir a rota com `nanojuris probe-rota`.
5. Classificar a rota por score.
6. Criar o dossie canonico em `docs/providers/<provider>/README.md`, atualizar o
   registro central e manter a copia de compatibilidade em `docs/source-contracts/`.
7. Salvar fixture offline publica representativa.
8. Implementar parser offline.
9. Implementar provider com diagnostics e testes.

## Playbook v4: mapeamento completo de contrato

O objetivo de uma rodada nao e apenas encontrar uma rota que retorna um
resultado. O objetivo e fechar o mapa da fonte: entradas, busca, filtros,
catalogos, paginacao, ordenacao, detalhe, documento, canais auxiliares,
respostas vazias, falhas e limites. Uma rota funcional pode ser promovida para
provider mesmo que outra superficie esteja bloqueada, mas a fonte so pode ser
marcada como `mapped_broadly` quando todas as superficies aplicaveis tiverem
estado explicito.

### Regra de nao perda de informacao

Toda descoberta deve ser guardada em tres camadas relacionadas:

1. **Inventario de rotas:** uma linha por URL, metodo e superficie.
2. **Contrato da rota:** parametros, payload, resposta, campos, limites e
   erros observados.
3. **Decisao de implementacao:** o que o runtime suporta, o que permanece
   apenas documentado e qual experimento fecha a lacuna.

Nunca substituir uma descoberta antiga por uma nova classificacao. Uma rota
que funcionou em uma data e falhou depois deve manter as duas evidencias,
incluindo o motivo da divergencia.

### Ciclo fechado por fonte

Executar estas fases em ordem, sem encerrar a fonte depois da primeira resposta
positiva:

| Fase | Pergunta | Saida obrigatoria |
| --- | --- | --- |
| 0. Identidade | qual orgao, acervo e URL oficial? | ficha de escopo e autoridade |
| 1. Superficies | quais entradas e canais existem? | inventario de rotas |
| 2. Busca minima | existe resultado juridico em sessao limpa? | probe de sucesso ou falha classificada |
| 3. Contrato de entrada | quais nomes, tipos e valores sao aceitos? | tabela de parametros/payload |
| 4. Cobertura de filtros | cada filtro muda ou restringe o retorno? | matriz de filtros efetivos |
| 5. Paginacao | como funcionam pagina, offset, limite e total? | matriz de pagina e ordenacao |
| 6. Canais de saida | ha detalhe, inteiro teor, PDF, processo ou modais? | grafo de links e dependencias |
| 7. Estados | como a fonte responde a vazio, erro, bloqueio e lentidao? | matriz de falhas |
| 8. Promocao | o que pode virar runtime agora? | dossie, fixture, testes e decisao |

Uma chamada positiva da fase 2 nunca autoriza presumir que as fases 4 a 7
funcionam. O caso TRF4 mostrou que uma busca pode expor total remoto e rota
AJAX sem que o replay AJAX esteja pronto; o caso STM mostrou que o portal pode
aceitar `start`/`rows` e devolver total remoto, enquanto o parser antigo ainda
recortava apenas a primeira pagina.

### Matriz de superficies e canais

Para cada fonte, preencher todos os itens abaixo com `operacional`, `observado`,
`bloqueado`, `nao_aplicavel` ou `desconhecido`:

| Grupo | Canais que devem ser procurados |
| --- | --- |
| entrada | portal, pagina de ajuda, sitemap, robots, links institucionais |
| busca | texto livre, frase exata, processo, recentes, busca por campos |
| filtros | classe, assunto, relator, orgao, origem, tipo, datas, status |
| catalogos | listas, facetas, autocomplete, enums, codigos e dependencias |
| navegacao | pagina 2, ultima pagina, ordenacao, tamanho, cursor, offset |
| decisao | card, detalhe por ID/UUID, resultados agrupados, destaque |
| documento | inteiro teor, PDF, HTML, ementa, arquivo, download sob demanda |
| processo | link processual, acompanhamento, metadados de processo |
| auxiliares | notas, indexacao, referencia legislativa, citacoes, relacionados |
| curadoria | sumulas, informativos, temas, repetitivos, precedentes, datasets |
| operacao | cache, rate limit, timeout, content type, charset, compressao |

Um botao ou endpoint observado em HTML/JavaScript entra no inventario mesmo
quando nao funciona isoladamente. Rotas filhas devem registrar a dependencia:
sessao, hidden fields, ViewState, CSRF, UUID, processo ou ID retornado pela
busca.

## Protocolo de contrato completo

### 1. Inventariar a entrada sem fazer suposicoes

Registrar URL oficial, URL final, subdominio, redirecionamentos, titulo,
orgao, ramo, acervo, data da observacao e links de ajuda. Consultar tambem
documentacao oficial, bundles, HTML, formularios e scripts. Projetos externos
podem indicar caminhos historicos, mas nunca sao evidencia de funcionamento
atual.

### 2. Capturar a busca minima e a busca vazia

Executar uma consulta pequena com termo juridico natural e outra que tenha
zero resultados esperado. Para cada uma guardar apenas o necessario para
reproduzir o contrato, sem cookies ou credenciais. Confirmar:

- status, URL final, content type, charset e tamanho;
- numero de resultados e marcadores de vazio;
- sinais juridicos objetivos: processo, classe, ementa, relator, data ou
  decisao;
- se o retorno e resultado, formulario, bloqueio, erro ou shell de SPA.

`HTTP 200` sem registro juridico nao e busca valida. HTML com formulario vazio
nao e resultado vazio automaticamente.

### 3. Fechar a tabela de parametros

Para cada input, select, checkbox, radio, query parameter, campo JSON ou
variavel GraphQL, registrar:

| Campo | Tipo | Obrigatorio | Valores | Testado | Efetivo | Runtime |
| --- | --- | --- | --- | --- | --- | --- |
| nome exato | string/date/list/object | sim/nao | catalogo ou exemplo | sim/nao | sim/nao/desconhecido | sim/nao |

As colunas `observado` e `efetivo` sao diferentes. Um campo pode aparecer no
formulario e ser ignorado pelo backend. Um link de faceta pode conter
`fq_classe`, mas so deve ser marcado como filtro efetivo depois de comparar a
resposta com e sem o valor. O dossie deve separar filtros da fonte, filtros
expostos no `JurisprudenceQuery` e filtros especificos ainda nao implementados.

Para campos catalogados, capturar nome, codigo, texto exibido, cardinalidade,
dependencias e exemplo de valor. Nao armazenar a lista inteira se ela contiver
dados pessoais; registrar contagem e uma fixture minima representativa.

### 4. Fechar a matriz de paginacao e ordenacao

Nunca assumir que `page=2` equivale a `offset=page_size`. Testar e registrar:

| Item | Teste minimo |
| --- | --- |
| base | pagina/offset/cursor e se e zero ou one-based |
| tamanho | valores exibidos pela UI e limite aceito pelo backend |
| total | campo remoto, marcador textual, ausencia ou contagem parcial |
| pagina 2 | primeiro ID diferente e continuidade da ordenacao |
| ultima pagina | comportamento de fim, vazio e indice maximo |
| ordenacao | padrao, crescente, decrescente e campo aceito |
| rota filha | parametros e estado exigidos pela paginacao AJAX |
| truncamento | resposta parcial, limite de bytes e timeout apos headers |

A rota inicial e a rota AJAX de paginacao sao contratos separados. Se o
JavaScript serializa o formulario inteiro, reproduzir o formulario completo
antes de chamar a rota filha. Uma rota AJAX que retorna apenas a moldura de
resultados deve ficar como `observed_not_operational`, nao como paginacao
implementada.

### 5. Fechar o grafo de detalhe e documento

Para cada resultado de sucesso, selecionar um identificador retornado pela
fonte e seguir, em ordem:

```text
resultado -> detalhe -> documento/inteiro teor -> canais auxiliares
```

Registrar se cada salto exige ID, UUID, numero CNJ, processo, sessao publica,
hidden fields ou token normal do fluxo. Testar pelo menos um documento HTML e
um PDF quando ambos forem oferecidos. Diferenciar ementa, trecho destacado,
resumo editorial e inteiro teor. URLs de processo, notas, indexacao,
referencia legislativa e documentos relacionados entram no inventario mesmo
quando o MCP ainda nao os consulta.

### 6. Fechar estados, limites e transporte

Cada rota operacional deve ter pelo menos estes casos classificados:

```text
sucesso pequeno | vazio | filtro invalido | pagina invalida |
rate limit | timeout antes de headers | timeout apos headers |
HTTP 401/403 | captcha/login/WAF | HTTP 404 | HTML/schema alterado
```

Registrar connect timeout, read timeout, tempo ate o primeiro byte, tamanho,
resposta completa, redirect, TLS/DNS e URL final. Timeout depois de headers
significa que existe evidencia parcial; nao significa nem "sem dados" nem
"contrato confirmado". Repetir uma unica vez com intervalo e depois trocar de
superficie, nao insistir indefinidamente.

## Bateria de probes por fonte

O conjunto minimo para declarar `mapped_broadly` e:

1. termo amplo do ramo;
2. termo especifico do ramo;
3. busca vazia esperada;
4. filtro por processo ou identificador quando existir;
5. filtro por catalogo, data, classe, assunto, relator ou orgao;
6. pagina 2 com tamanho pequeno;
7. detalhe e inteiro teor de ID retornado;
8. canal auxiliar ou classificacao explicita como nao observado;
9. erro ou bloqueio controlado;
10. uma chamada repetida para verificar estabilidade sem aumentar carga.

Se um probe nao se aplica, registrar `nao_aplicavel` e a justificativa. Nunca
marcar como completo apenas porque o termo `idpj` retornou dados.

## Criterio de completude do mapeamento

Uma fonte so pode receber `mapped_broadly` quando:

- nao existe superficie aplicavel em `desconhecido`;
- toda rota operacional tem metodo, entrada, resposta, campos, limites e
  estados de erro documentados;
- todos os filtros observados estao classificados como efetivos, inefetivos,
  nao reproduzidos ou fora do modelo runtime;
- pagina 2, total e limite foram testados ou marcados com evidencia da lacuna;
- detalhe, documento e canais auxiliares foram procurados com ID real;
- a matriz distingue HTML shell, vazio, bloqueio, timeout e contrato alterado;
- cada afirmacao de funcionamento tem fixture ou evidencia live datada;
- o dossie diz explicitamente o que o provider faz, o que nao faz e por que.

`mapped_broadly` nao significa que toda rota e automatizavel. Significa que o
projeto percorreu o ecossistema conhecido e tornou as lacunas auditaveis.

## Estrategia de descoberta sem bloqueio prematuro

O playbook trabalha com duas trilhas simultaneas:

- **descoberta ampla:** registra qualquer entrada, endpoint ou contrato
  observado, mesmo que ainda nao possa virar provider;
- **validacao progressiva:** tenta elevar a evidencia ate uma chamada HTTP
  reproduzivel, sem apagar os achados parciais.

A ordem de tentativa para cada fonte e:

1. Portal e paginas oficiais.
2. Ajuda, carta de servicos, FAQ, sitemap e links de download.
3. HTML, formularios, scripts inline e bundles JavaScript.
4. OpenAPI, Swagger, GraphQL introspection publica e endpoints de catalogo.
5. Busca, filtros, recentes, detalhe, processo e documento.
6. Datasets, informativos, sumulas, precedentes e repositorios institucionais.
7. Captura automatica de rede em navegador publico, somente quando necessario.
8. Replay HTTP limpo da chamada descoberta.

Se uma etapa falhar, avancar para a proxima superficie e registrar a falha. Um
`404` na busca nao deve impedir a pesquisa de catalogos; um reset TLS no portal
nao deve impedir a verificacao de PDFs, subdominios oficiais ou datasets; uma
rota de detalhe quebrada nao invalida uma busca que retorna ementas.

## Mapa de cobertura por fonte

Cada fonte deve possuir uma matriz, mesmo que varias celulas estejam pendentes:

| Superficie | Estado | Evidencia | Proximo teste |
| --- | --- | --- | --- |
| entrada | descoberto/confirmado | URL e pagina oficial | revalidar acesso |
| busca textual | desconhecido/confirmado/reproduzivel | metodo e resposta | testar termo por ramo |
| filtros/catalogos | desconhecido/parcial/completo | valores e resposta | selecionar valor exato |
| recentes | desconhecido/confirmado | pagina e limite | testar periodo/paginacao |
| detalhe | desconhecido/observado/operacional | id retornado pela busca | testar id real |
| processo/documento | desconhecido/confirmado | rota e formato | testar referencia publica |
| inteiro teor/PDF | desconhecido/confirmado | link e tipo | validar download sob demanda |
| precedentes/informativos | nao aplicavel/confirmado | item curado | criar provider documental |
| limites/erros | desconhecido/mapeado | status e mensagem | fixture de contrato |

O status da fonte deve ser calculado a partir da matriz, e nao de uma unica
rota. Assim, uma fonte pode ter busca bloqueada e ainda oferecer um provider de
informativos ou catalogos.

## Estados de rota

Usar estados mais precisos que um simples aprovado/reprovado:

- `discovered`: apareceu em pagina, bundle ou documentacao;
- `ui_confirmed`: formulario ou resultado visivel na interface oficial;
- `response_confirmed`: chamada retornou resposta com sinais juridicos;
- `replayable`: chamada reproduzida por HTTP limpo;
- `contract_ready`: metodo, payload, campos, limites e erros documentados;
- `partial`: somente parte da superficie funciona;
- `blocked_control`: captcha, login, WAF ou antirrobo;
- `blocked_transport`: DNS, TLS, timeout ou instabilidade;
- `observed_not_operational`: rota aparece no frontend, mas nao funciona com
  os identificadores e payloads publicos testados;
- `unknown`: ainda nao investigada.

Estados parciais nunca devem ser descartados. Eles alimentam o backlog e podem
ser promovidos quando a fonte mudar.

## Rotina de tentativas

Para evitar falsos negativos:

- testar uma vez com cliente HTTP limpo e timeout moderado;
- repetir no maximo uma vez com intervalo, sem aumentar agressivamente a carga;
- comparar URL final, DNS, certificado, status, content type e tamanho;
- testar uma superficie oficial alternativa, quando existir;
- separar erro do ambiente local de resposta efetiva da fonte;
- nao desligar verificacao TLS, nao forcar proxy e nao contornar desafio;
- marcar o resultado como inconclusivo quando a evidencia nao permitir decisao.

O objetivo e aumentar cobertura, nao transformar repeticoes em pressao sobre o
tribunal.

## Ledger de tentativas e deduplicacao

Antes de qualquer probe, consultar o historico da fonte. Uma tentativa e
identificada por:

```text
source + normalized_url + method + payload_hash + client_profile
```

O `client_profile` deve indicar apenas a classe do cliente, como `requests`
limpo, navegador publico ou web fetcher; nunca armazenar cookie, token ou
identidade privada.

Regras:

- nao repetir a mesma chave com o mesmo perfil e o mesmo resultado;
- repetir somente quando houver nova janela temporal, nova rota oficial,
  payload diferente, evidencia de mudanca do frontend ou perfil diferente;
- registrar motivo da repeticao antes do probe;
- consolidar resultados equivalentes em uma unica entrada;
- manter tentativas anteriores como historico, sem reclassificar silenciosamente
  uma falha antiga;
- quando uma chamada falhar, testar outra superficie da mesma fonte em vez de
  insistir indefinidamente na mesma URL.

O relatorio de cada rodada deve informar `attempt_id`, `dedupe_key`, data,
perfil, resultado e proximo passo. Isso evita ciclos de timeout, reset TLS ou
404 sem ganho de evidencia.

## Contrato minimo e contrato completo

O mapeamento pode ser util antes do contrato completo. Registrar primeiro o
contrato minimo observado e evolui-lo:

1. URL e superficie.
2. Metodo e parametros conhecidos.
3. Tipo de resposta.
4. Marcadores juridicos.
5. Estado da rota.
6. Campos e limites ainda desconhecidos.

Somente a promocao para `contract_ready` exige payload completo, paginacao,
filtros, resposta vazia, erros, detalhe e documento. Isso permite mapear todo o
ecossistema sem prometer providers antes da hora.

## Playbook v3: niveis de evidencia

O mapeamento deve separar fonte, rota e provider. Uma fonte pode ser oficial e
uma rota pode aparecer no bundle sem que exista ainda um contrato HTTP
operacional.

| Nivel | Evidencia | Promocao permitida |
| --- | --- | --- |
| A | HTTP limpo retornou conteudo juridico real e repetivel | contrato e fixture; provider apos parser |
| B | navegador/web confirmou resultado, mas cliente HTTP falhou ou nao foi reproduzido | ficha pendente; exigir HAR ou nova reproducao |
| C | bundle, documentacao ou formulario revelou endpoint | apenas hipotese de rota |
| D | pagina institucional, busca indexada ou link documental sem resultado consultavel | somente registro de descoberta |

Regra: documentacao oficial prova existencia e escopo da fonte, mas nao prova
que a automacao esta pronta. Rota encontrada no JavaScript tambem e evidencia
de descoberta, nao de funcionamento.

## Decisao rapida por camada

Investigar nesta ordem:

1. **Fonte:** URL oficial, autoridade e tipo de acervo.
2. **Entrada:** portal, help, bundle ou catalogo publico.
3. **Busca:** metodo, payload, headers e resposta.
4. **Catalogo:** valores exatos de origem, tipo, classe e assunto.
5. **Resultado:** campos juridicos, volume, pagina e ordenacao.
6. **Detalhe:** testar somente com id/processo retornado pela propria busca.
7. **Documento:** inteiro teor ou PDF publico, quando existir.

Uma rota de detalhe mencionada no bundle, mas que responde 404 com um
identificador valido, permanece como `observed_not_operational` ate que o
contrato correto seja localizado. Nunca inventar id para validar detalhe.

## HAR: quando usar

HAR nao e obrigatorio para APIs JSON que ja podem ser reproduzidas por HTTP
limpo. Ele e recomendado quando a busca depende de formulario, JSF, WebForms,
SPA, postback, token de sessao publica ou varias chamadas AJAX. O HAR deve ser
usado para descobrir o fluxo normal, nunca para exportar cookie privado, token
de usuario ou contornar captcha/WAF.

## Diagnostico de acesso

Registrar a camada exata da falha:

| Sintoma | Classificacao inicial | Tratamento |
| --- | --- | --- |
| HTTP 401/403 | acesso controlado ou credencial | nao contornar; procurar superficie publica normal |
| HTTP 404 | rota/metodo/base possivelmente incorretos | conferir bundle, metodo e caminho |
| captcha/WAF/antirrobo | controle de acesso | bloquear automacao |
| timeout | indisponibilidade ou instabilidade | repetir uma vez com limite; depois classificar |
| reset TLS/DNS | falha de transporte ou ambiente | testar superficie oficial alternativa; nao forcar reconexao |
| HTML sem resultado | formulario ou resposta vazia | diferenciar por marcadores de resultado e status |

O relatorio deve preservar status HTTP, tipo de conteudo, tamanho, URL final,
tempo limite e erro de transporte, sem registrar cookies ou segredos.

## Score de prioridade

Pontuar cada candidato de 0 a 5 em valor juridico, qualidade da evidencia,
estabilidade, completude dos campos e reuso tecnico. Subtrair de 0 a 5 o risco
de bloqueio/contrato fragil. Priorizar pelo total, mas nunca promover uma fonte
com bloqueio ativo apenas por ter score alto.

## Fixture e dados publicos

Fixtures devem reproduzir o contrato e preservar os campos publicos necessarios
ao teste, sem mascaramento silencioso no runtime. Ao mesmo tempo, nao devem
carregar nomes, documentos ou textos pessoais que nao sejam necessarios para
validar o parser. O provider deve preservar os dados publicos retornados pela
fonte; a reducao de fixture e uma decisao de teste, nao uma alteracao da
resposta live.

## Comando padrao

```bash
nanojuris probe-rota "https://tribunal.exemplo.jus.br/jurisprudencia?q=idpj" \
  --expect "IDPJ" \
  --expect "Ementa"
```

Para rotas POST com formulario:

```bash
nanojuris probe-rota "https://tribunal.exemplo.jus.br/search" \
  --metodo POST \
  --data "q=idpj" \
  --data "pagina=1" \
  --expect "Relator"
```

Para API JSON:

```bash
nanojuris probe-rota "https://api.tribunal.exemplo.jus.br/jurisprudencia" \
  --metodo POST \
  --json "{\"q\":\"idpj\",\"page\":1}" \
  --expect "ementa"
```

### Respostas lentas ou grandes

O probe faz leitura em streaming e separa o timeout de conexao do timeout de
leitura. Isso permite distinguir uma rota que ainda entrega conteudo de uma
rota que nao recebeu headers. Por padrao, no maximo 5 MB sao lidos durante o
diagnostico; esse limite nao altera o provider nem a resposta live.

```bash
nanojuris probe-rota "https://api.tribunal.exemplo.jus.br/jurisprudencia" \
  --metodo POST \
  --json-file payload.json \
  --connect-timeout 15 \
  --read-timeout 90 \
  --max-bytes 20000000 \
  --expect "ementa"
```

O JSON do probe preserva `content_length`, `content_bytes`,
`time_to_first_byte_ms`, `response_complete`, `content_truncated` e
`transport_status`. Quando headers e parte do corpo foram recebidos, o status
e `partial_response`: os sinais juridicos encontrados permanecem disponiveis,
mas a rota nao e promovida como valida ate que a resposta completa seja
confirmada. `timeout_before_headers` significa que nenhum header chegou;
`timeout_after_headers` significa que a fonte iniciou a resposta e ficou lenta
durante a leitura. Assim, timeout nao e interpretado automaticamente como
ausencia de dados nem como contrato confirmado.

`--json` aceita objeto ou array JSON. Para endpoints de metadados que recebem
lista de tribunais, por exemplo, o payload pode ser:

```json
["TSE"]
```

Em PowerShell ou payloads maiores, prefira arquivo JSON para evitar problemas de
escape e preservar aspas internas:

```bash
nanojuris probe-rota "https://api.tribunal.exemplo.jus.br/jurisprudencia" \
  --metodo POST \
  --json-file payload.json \
  --expect "totalRegistros"
```

## Bateria de termos

`idpj` e apenas um smoke test civil/empresarial. O mapeamento serio deve usar
uma bateria por ramo, porque algumas fontes ranqueiam melhor ou validam payloads
com termos mais naturais ao acervo.

| Ramo/fonte | Termos iniciais |
| --- | --- |
| TJs estaduais | `dano moral`, `plano de saude`, `inventario`, `idpj`, `execucao fiscal` |
| TST/TRTs | `horas extras`, `justa causa`, `equiparacao salarial`, `adicional de insalubridade` |
| TRFs/TNU | `aposentadoria`, `beneficio previdenciario`, `execucao fiscal`, `mandado de seguranca` |
| STJ/STF | `repetitivo`, `repercussao geral`, `icms`, `habeas corpus`, `recurso especial` |
| TSE/TREs | `abuso de poder`, `propaganda eleitoral`, `registro de candidatura` |
| STM/JMU | `desercao`, `insubmissao`, `habeas corpus` |

## Interpretacao do score

O probe retorna `route_status`, `score`, `quality_grade`, sinais juridicos,
sinais de acesso e uma recomendacao.

| Grade | Significado | Acao |
| --- | --- | --- |
| A | Rota forte, com conteudo juridico e bons sinais tecnicos | criar contrato e fixture |
| B | Rota promissora, mas precisa aprofundar paginacao/campos | pesquisar mais antes do provider |
| C | Rota fraca ou incompleta | registrar, mas nao priorizar |
| D | Bloqueada, indisponivel ou sem valor juridico suficiente | descartar ou revisitar depois |

Status principais:

- `live_valid`: rota retornou conteudo juridico real sem bloqueio.
- `candidate`: resposta limpa, mas ainda sem evidencia juridica suficiente.
- `access_control_or_login`: ha captcha, login, antirrobo, sessao ou WAF.
- `not_found`: rota candidata nao existe no formato testado.
- `source_unavailable`: fonte indisponivel, recusada ou com erro HTTP/rede.
- `observed_not_operational`: rota aparece no frontend, mas nao funciona com
  identificadores e payloads publicos reproduzidos.

## Sinais de rota boa

Priorizar rotas que retornem:

- JSON, XML ou HTML sem estado fragil;
- numero CNJ, classe, assunto, relator, orgao julgador e datas;
- ementa, tese, sumula, tema, precedente ou decisao;
- paginacao clara;
- link publico de inteiro teor;
- comportamento repetivel com `requests` limpo.

## Sinais de bloqueio

Nao promover rotas que dependam de:

- captcha, reCAPTCHA, Turnstile ou antirrobo;
- login, CAS, SSO ou area autenticada;
- cookies de navegador ou token extraido de HAR;
- segredo de justica;
- rota que apenas ecoa formulario sem resultado juridico.

## Priorizacao nacional

Ordem recomendada para mapear proximas rotas:

| Prioridade | Alvo | Motivo |
| --- | --- | --- |
| P0 | TST | alto valor pratico e lacuna nacional trabalhista |
| P0 | TRF1, TRF3, TRF5, TRF6 | completa Justica Federal junto com TRF4 |
| P0 | TJMG, TJRJ, TJRS, TJPR, TJSC | grandes acervos estaduais |
| P1 | TSE | jurisprudencia eleitoral nacional |
| P1 | TJBA, TJPE, TJGO, TJCE | volume estadual e relevancia regional |
| P1 | TREs principais | cobertura eleitoral regional |
| P2 | TJs restantes | completude nacional |
| P2 | TNU/CJF e CNJ | uniformizacao e decisao administrativa |

## Checklist de promocao

Antes de abrir PR de provider:

- `probe-rota` mostra `live_valid` ou uma justificativa tecnica clara;
- contrato documenta endpoint, metodo, payload, paginacao e campos;
- fixture offline contem conteudo publico representativo, sem cookies, tokens ou
  segredos locais de navegador;
- parser offline cobre resultado vazio, resultado valido e mudanca de contrato;
- provider declara capabilities e responsible use;
- testes nao dependem de rede por padrao;
- teste live opcional fica marcado com `pytest.mark.live`;
- mensagens de erro separam indisponibilidade, captcha/login e parser quebrado.
- matriz separa busca, catalogo, detalhe, documento e limites tecnicos;
- resultado vazio foi distinguido de erro HTTP, reset TLS e controle de acesso;
- filtros foram testados com valores exatos dos catalogos da fonte;
- o dossie registra nivel de evidencia A/B/C/D e a decisao de promocao.

## Definicao de mapeamento amplo concluido

Uma fonte pode ser marcada como `mapped_broadly` quando:

- todas as URLs oficiais conhecidas foram inventariadas;
- cada superficie recebeu um estado, evidencia e proximo teste;
- busca, catalogo, detalhe, documento e conteudo curado foram avaliados;
- bloqueios foram localizados na camada correta;
- contratos parciais foram preservados no dossie;
- nao existem celulas sem classificacao na matriz da fonte.

`mapped_broadly` nao significa que todas as rotas sao reproduziveis. Significa
que o projeto conhece o que existe, o que funciona, o que falta e por que uma
rota ainda nao pode ser implementada.

## Artefato de inventario

Cada rodada deve produzir uma entrada no inventario com esta estrutura logica:

```yaml
source: tribunal-ou-orgao
route_id: tribunal-ou-orgao.search.initial
surface: search|catalog|detail|document|curated|dataset
surface_group: search|filters|pagination|decision|document|auxiliary
url: https://...
method: GET|POST|GRAPHQL|UNKNOWN
state: discovered
evidence: C
evidence_refs: [fixture-or-live-record]
content_type: text/html
charset: utf-8
input_contract: partial|complete|unknown
response_contract: partial|complete|unknown
pagination:
  mode: none|page|offset|cursor|ajax|unknown
  base: zero|one|not_applicable|unknown
  page_sizes: [10, 25, 50, 100]
  remote_total: observed|absent|partial|unknown
filters:
  - name: classe
    observed: true
    effective: unknown
    runtime: false
channels:
  detail: observed|operational|blocked|not_applicable|unknown
  full_text: observed|operational|blocked|not_applicable|unknown
  pdf: observed|operational|blocked|not_applicable|unknown
  auxiliary: [not_observed]
legal_signals: [ementa, processo]
auth: public|login|captcha|unknown
contract: partial|complete|unknown
runtime_support: implemented|candidate|documented_only|blocked
attempts: 1
next_probe: "identificar payload de busca"
observed_at: YYYY-MM-DD
```

O inventario e a fonte de verdade da descoberta. O provider so e criado depois
que o inventario, o dossie, a fixture e os testes estiverem coerentes.
