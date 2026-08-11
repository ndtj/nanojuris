# Route Mapping Playbook

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
surface: search|catalog|detail|document|curated|dataset
url: https://...
method: GET|POST|GRAPHQL|UNKNOWN
state: discovered
evidence: C
content_type: text/html
legal_signals: [ementa, processo]
auth: public|login|captcha|unknown
contract: partial|complete|unknown
next_probe: "identificar payload de busca"
observed_at: YYYY-MM-DD
```

O inventario e a fonte de verdade da descoberta. O provider so e criado depois
que o inventario, o dossie, a fixture e os testes estiverem coerentes.
