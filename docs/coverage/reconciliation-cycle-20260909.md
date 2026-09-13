# Reconciliação nacional — ciclo 2026-09-09

Este registro documenta somente as correções de identidade e inventário deste
ciclo. Nenhum provider foi promovido por inferência e nenhum bloqueio foi
convertido em resultado vazio.

## Alterações

1. `cjf_jurisprudencia` foi vinculado à superfície `TRF1/federal/second/`
   `JURISPRUDENCIA`. A rechecagem live atual continua `access_control_required`,
   portanto o estado é `blocked_access` e a federação permanece desabilitada.
2. `access_control_required` passou a ser tratado como `blocked_access` na
   matriz de grau, da mesma forma que `access_controlled`.
3. O gerador da matriz de tarefas deixou de criar linhas artificiais
   `branch=federal` para STJ e STM. As superfícies canônicas agora usam,
   respectivamente, `branch=superior` e `branch=military`.

## Inventário após a geração

| Métrica | Valor |
|---|---:|
| Superfícies | 249 |
| Superfícies core | 155 |
| Superfícies condicionais | 94 |
| Providers catalogados | 73 |
| Órfãos de catálogo | 19 |
| Core sem provider | 52 |
| Bloqueadas | 35 |
| Em descoberta | 145 |
| Federadas | 66 |
| GOLD | 66 |
| CJPG | 8/27 |
| CJSG | 25/27 |
| Fila de descoberta | 183 |

O único desvio do registro de estados é o provider diagnóstico do TJMA sem
binding de runtime; ele permanece explícito e não é contado como cobertura.

## Verificação

- `python -m pytest -q`: **1614 passed, 26 skipped**;
- `python tools/validate_sdd.py`: aprovado;
- Ruff e formatação: aprovados;
- mypy: aprovado;
- compileall: aprovado;
- `git diff --check`: aprovado, apenas avisos de normalização CRLF/LF.

Artefatos regenerados: catálogo de providers, matriz de grau, registro de
estados, matriz nacional de tarefas, mapa de lacunas, workpacks, programa
estadual, manifesto técnico e auditoria de tarefas.

Não houve commit, push, tag, release, deploy, Terraform apply ou alteração em
produção.

## Hardening local adicional — BNP/Pangea

O provider público `bnp_pangea` foi migrado das chamadas diretas da sessão para
`SharedHttpClient`. A política agora aplica allowlist HTTPS do host configurado,
timeout, limite de 4 MB, rate limit e circuito compartilhados, sem retry
automático para preservar decisões de rate limit/gateway da API. O parser JSON,
o preenchimento do catálogo, a paginação e os estados HTTP existentes foram
mantidos; 400 continua sendo consulta rejeitada, 429 rate limit, 5xx fonte
indisponível e resposta inválida mudança de schema.

Verificação local e live bounded:

- `python -m pytest -q tests/test_bnp_pangea.py` — **26 passed**;
- `$env:NANOJURIS_RUN_LIVE='1'; python -m pytest -q tests/test_bnp_pangea_live.py` —
  **3 passed** (catálogo, busca limitada e busca sem filtros explícitos).

Essa alteração reduz uma superfície de transporte direto, mas não promove o BNP
como jurisprudência geral: ele continua classificado como fonte de precedentes
qualificados, com inteiro teor não disponível no contrato atual.

## Descoberta bounded de rotas CJPG

Em 2026-09-09 foi executada uma varredura de entrada oficial dos 27 TJs, com
GET de homepage e no máximo dois scripts por tribunal, timeout de 8 segundos,
sem submissão de formulários, credenciais ou contorno de controles. Foram
observadas 22 homepages alcançáveis, 3 com controle de acesso e 2 com erro de
transporte. O inventário encontrou 179 URLs candidatas a jurisprudência; elas
continuam apenas como descoberta, pois não provam contrato CJPG, filtros,
paginação ou inteiro teor. O artefato redigido é
`docs/provider-discovery/first-degree-route-inventory-20260909.json`.

Uma checagem bounded da entrada pública do TJPR retornou uma página de acesso
restrito/erro de handler, sem contrato decisório público reproduzível; ela não
foi promovida nem tratada como vazio.

Rechecagem adicional do TJPR: a entrada oficial `sentenca-digital` abriu a
rota pÃºblica `/pesquisa_sentenca/publico/sentenca.do`. Uma consulta bounded por
identificador CNJ estruturado retornou HTTP 200 e “Nenhum registro apresentado”.
Isso Ã© vazio autoritativo somente para aquele identificador, nÃ£o prova um
corpus CJPG e nÃ£o foi promovido. A evidÃªncia redigida estÃ¡ em
`docs/provider-discovery/tjpr-sentenca-digital-live-20260909.json`.

Uma segunda passada bounded habilitou a sonda de candidatos (atÃ© trÃªs GETs
por tribunal). Ela observou 23 homepages alcanÃ§Ã¡veis, 3 com controle de acesso
e 1 erro de transporte; somente 15 candidatos chegaram a ser sondados, com 12
respostas HTTP 200 e 3 erros de transporte. As respostas 200 sÃ£o pÃ¡ginas de
entrada/ementÃ¡rio e nÃ£o foram tratadas como contratos CJPG. O inventÃ¡rio
redigido estÃ¡ em
`docs/provider-discovery/first-degree-route-inventory-probed-20260909.json`.

O provider jÃ¡ existente `tjal_esmal_banco_sentencas` tambÃ©m foi revalidado
com uma consulta pÃºblica limitada: HTTP 200, dois registros de primeiro grau
com links PDF oficiais e extraÃ§Ã£o completa. O total permanece desconhecido por
contrato da coleÃ§Ã£o curada; a evidÃªncia corrente Ã©
`docs/provider-discovery/tjal-esmal-banco-sentencas-live-20260909.json`.

## AtualizaÃ§Ã£o final do inventÃ¡rio â€” 2026-09-09

ApÃ³s a revalidaÃ§Ã£o do TRT8 PJe e o fechamento da decisÃ£o de rollout, os
geradores atuais registram: **75 providers catalogados, 69 em runtime, 5
candidatos, 1 famÃ­lia; 249 superfÃ­cies (155 core/94 condicionais); 68
superfÃ­cies federadas; 37 bloqueadas e 141 em descoberta; CJPG 8/27 e CJSG
25/27**. O auditor de tarefas registra **86 abertas: 65 externas, 21 humanas e
nenhuma local**.

O TRT8 estÃ¡ `federated_live` na federaÃ§Ã£o local apÃ³s uma chamada oficial
bounded de 30 segundos com filtros explÃ­citos de segundo grau. T009 foi fechado;
nenhum timeout ou bloqueio foi convertido em vazio e nenhuma alteraÃ§Ã£o de
produÃ§Ã£o foi realizada.
## Ciclo de decisões operacionais — 2026-09-09

O registro canônico deste ciclo é `docs/coverage/decision-record-20260909.json`.
Os geradores foram executados após as decisões: o programa CJSG atual registra
25/27 autoridades completas e 2 em rechecagem; a matriz gerada contém 151
superfícies. Esses números substituem projeções narrativas anteriores e devem
ser lidos junto do ledger gerado, que preserva owner, escopo, retenção,
frequência e política de promoção.

Foram preparadas 80 linhas de revisão (8 consultas × top 10) em
`docs/benchmarks/live-ranking-review-matrix-20260909.md`. Como o snapshot live
não persiste corpos nem IDs canônicos, os pré-rótulos estão sem nota e não
alteram a avaliação; a validação do mantenedor continua necessária.

## Fechamento técnico TRT8 — 2026-09-09

O TRT8 PJe passou a `federated_live` após uma chamada pública bounded com
timeout de 30 segundos, resposta HTTP 200 e filtros explícitos de segundo grau.
As superfícies nacionais foram regeneradas: 75 providers catalogados, 69 em
runtime, 5 candidatos e 1 família; 68 superfícies federadas no mapa nacional.
O gate de CJSG estadual permanece 25/27 porque o TRT8 é ramo trabalhista e não
entra no denominador dos 27 TJs. Nenhuma decisão foi convertida em vazio e não
houve commit, push, release, deploy ou alteração de produção.
