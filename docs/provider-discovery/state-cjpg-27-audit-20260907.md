# Auditoria CJPG dos 27 tribunais estaduais — 2026-09-07

Esta auditoria consolida as rotas oficiais públicas verificadas nos artefatos
de descoberta de 2026-09-07. `implemented` significa que existe contrato
técnico, identidade explícita de primeiro grau, fixture e evidência live. Um
portal, ementário, consulta processual ou resposta HTTP 200 sem identidade de
primeiro grau não é contado como CJPG.

## Resultado

Há **7/27** superfícies CJPG comprovadas:

| Tribunal | Provider | Rota/sinal de primeiro grau | Estado |
|---|---|---|---|
| TJAP | `tjap_banco_sentencas` | Banco oficial de Sentenças; unidade vara/juizado/comarca/ofício | implementado |
| TJES | `tjes_cjpg` | core público `pje1g` | implementado |
| TJGO | `tjgo_projudi_jurisprudencia` | `Id_Instancia=16`; vara/juizado/comarca/UPJ | implementado |
| TJMS | `tjms_cjpg` | e-SAJ `/cjpg/pesquisar.do` | implementado |
| TJRO | `tjro_jurisprudencia` | `grau_jurisdicao=[1]`; origem `PJEPG` | implementado |
| TJSP | `tjsp_cjpg` | e-SAJ `/cjpg/` | implementado |
| TJTO | `tjto_jurisprudencia` | `tip_criterio_inst=1`; sentenças | implementado |

## Auditoria dos demais tribunais

| Tribunal | Resultado da verificação | Próxima ação legítima |
|---|---|---|
| TJAC | Ementário/PDF acessível, mas grau não identificado e sem busca CJPG | localizar contrato oficial de decisões de varas; não contar PDF |
| TJAL | nenhum contrato CJPG público comprovado no inventário | pesquisa oficial periódica |
| TJAM | portal de jurisprudência e CPOP são shell/consulta processual | procurar busca decisória, não usar CPOP |
| TJBA | Banco de Sentenças oficial via Projudi foi encontrado; formulário de primeiro grau é público, mas POST exige CAPTCHA e não houve resultado reproduzível sem desafio | manter `blocked_access`; procurar somente API/export oficial sem CAPTCHA ou contrato de integração autorizado |
| TJCE | informativos/ementários não são corpus CJPG | procurar rota oficial de sentenças |
| TJDFT | API pública validada apenas com base `acordaos`/segundo grau | não converter API geral em CJPG |
| TJMA | JurisConsult exige CAPTCHA na rota de resultados; demais rotas são contexto/processo | aguardar rota pública sem desafio |
| TJMG | formulário oficial de sentenças exige CAPTCHA numérico (HTTP 401) | revalidar somente rota oficial sem CAPTCHA |
| TJMT | nenhum contrato CJPG público comprovado | pesquisa oficial periódica |
| TJPA | Banco oficial de Sentenças confirmado, mas a própria página declara acesso restrito a magistrados; nenhuma rota pública reproduzível | manter `blocked_access`; revalidar apenas se o TJPA publicar busca/API sem autenticação ou export autorizado |
| TJPB | portal principal bloqueado/sem contrato CJPG observado | revalidar fonte oficial quando acessível |
| TJPE | nenhum contrato CJPG; superfícies disponíveis referem-se ao segundo grau | pesquisar rota oficial de sentenças |
| TJPI | nenhum contrato CJPG público comprovado | pesquisa oficial periódica |
| TJPR | Sentença Digital é programa/contexto; portal de jurisprudência não explicita grau | não confundir consulta processual com CJPG |
| TJRJ | eproc em host `eproc1g` retornou acórdãos de segundo grau | manter `pending_contract`; procurar rota 1G decisória distinta |
| TJRN | consultas bounded responderam HTTP 403 | manter `blocked_access`; não tratar como vazio |
| TJRR | portal de jurisprudência sem prova de unidade de primeiro grau | pesquisa oficial periódica |
| TJRS | banco legado retornou DNS/404; busca institucional é corpus misto sem identidade de sentença | manter gap até corpus oficial dedicado |
| TJSC | eproc `consulta1g` retornou decisões do tribunal/turmas recursais (segundo grau) | manter `pending_contract`; não promover CJPG |
| TJSE | nenhuma fonte oficial CJPG reproduzível no inventário | pesquisar rota decisória oficial |

## Paridade com Juscraper

O checkout verificado de Juscraper implementa superfícies `cjpg` somente para
TJES, TJSP e TJTO. Os módulos `cpopg` dos demais tribunais são consulta
processual, não jurisprudência textual de primeiro grau. NanoJuris já cobre
esses três e adiciona, com contrato independente, TJAP, TJGO, TJMS e TJRO.

## Evidências

- Inventário amplo: `first-degree-route-inventory-20260907.json`.
- Probes de candidatos: `first-degree-candidate-probes-live-20260907.json`.
- Rechecagem complementar: `first-degree-secondary-probes-live-20260907.json`.
- TJMG CAPTCHA: `tjmg-cjpg-route-live-20260907.json`.
- TJRN 403: `tjrn-first-degree-recheck-20260907.json`.
- TJRJ/TJSC eproc: `state-first-degree-eproc-recheck-20260907.json` e
  `tjsc-first-degree-eproc-boundary-live-20260907.json`.
- TJBA bundle/API: `tjba-first-degree-route-live-20260907.json` e
  `tjba-cjpg-banco-sentencas-live-20260907.json` registram a rota pública e o
  bloqueio do POST por CAPTCHA; não houve resultado reproduzível sem desafio.
- TJAM, TJAL e TJPR: `cjpg-candidate-route-audit-20260907-bounded.json` registra
  a rechecagem bounded das rotas oficiais. Nenhuma apresentou corpus público
  reproduzível de decisões textuais de primeiro grau; as superfícies observadas
  são grupos de segundo grau, turmas recursais ou contexto processual.
- TJAP, TJGO, TJMS, TJRO e TJTO possuem evidências específicas referenciadas
  no catálogo/matriz e nos respectivos dossiês.
- TJBA possui uma rota pública de formulário CJPG (`ConclusoesRealizadas?instancia=1`),
  mas a fonte exige CAPTCHA antes de aceitar a consulta. A descoberta é registrada
  em `tjba-cjpg-banco-sentencas-live-20260907.json` e não foi promovida.

Nenhum CAPTCHA, WAF, login, token, cookie, proxy ou limite foi contornado.
