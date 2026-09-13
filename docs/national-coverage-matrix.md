# Matriz Nacional De Cobertura

Atualizada em 2026-09-01. Esta matriz separa a existência institucional de cada
tribunal da disponibilidade de provider. O catálogo nacional individualiza 94
autoridades de tribunal; isso não equivale a 94 providers implementados.

## Tribunais Estaduais

| Tribunal | Estado | Superficie principal | Estado do mapeamento | Proximo passo |
| --- | --- | --- | --- | --- |
| TJAC | AC | e-SAJ/CJSG | implementado | ampliar filtros e documentos |
| TJAL | AL | e-SAJ/CJSG | implementado | ampliar fixtures e monitorar |
| TJAM | AM | e-SAJ/CJSG | implementado | monitorar disponibilidade |
| TJAP | AP | Tucujuris | bloqueado/inconclusivo | nova rota publica sem desafio |
| TJBA | BA | GraphQL | implementado | monitorar vazio, pagina e detalhe live |
| TJCE | CE | e-SAJ/CJSG | candidato com HAR | reproduzir formulario apos reset TLS |
| TJDFT | DF | SISTJ | implementado | ampliar paginacao e documentos |
| TJES | ES | portal atual e busca legada | candidato com HAR | validar fluxo e ementarios |
| TJGO | GO | Projudi | implementado | validar paginacao live |
| TJMA | MA | JurisConsult | parcial/metadados | manter busca geral bloqueada por captcha |
| TJMG | MG | Espelho de Acordao | bloqueado por captcha | buscar superficie oficial alternativa |
| TJMS | MS | e-SAJ/CJSG | implementado | ampliar filtros e documentos |
| TJMT | MT | SPA/API Hellsgate | bloqueado/inconclusivo | somente nova rota publica |
| TJPA | PA | BFF REST | candidato pronto | fixtures de filtros e detalhe |
| TJPB | PB | PJe jurisprudencia | candidato com HAR | confirmar resultado sem WAF |
| TJPE | PE | consulta REST/sumulas | candidato pronto/parcial | fechar fixture decisoria |
| TJPI | PI | JusPI | implementado | monitorar e ampliar filtros |
| TJPR | PR | pesquisa HTML | candidato pronto | fixture, parser e paginacao |
| TJRJ | RJ | eproc e eJURIS | eproc candidato; eJURIS bloqueado | separar bases e validar fixture |
| TJRN | RN | portal unificado | bloqueado/inconclusivo | HAR da busca publica |
| TJRO | RO | LIAME | documental | adapter de precedentes; localizar busca de acordaos |
| TJRR | RR | Juris JSF | implementado | monitorar vazio, estado expirado e detalhe |
| TJRS | RS | AJAX/SOLR | candidato pronto | fixture JSON e parser ISO-8859-1 |
| TJSC | SC | eproc | candidato pronto | fixture e parser estadual |
| TJSE | SE | JSF/PrimeFaces | bloqueado por captcha | HAR normal; nao contornar desafio |
| TJSP | SP | e-SAJ/CJSG e eproc | implementado parcial | ampliar bases e documentos |
| TJTO | TO | consulta HTML indexada | candidato com HAR | reproduzir query, filtros e detalhe |

## Leitura Dos Estados

- `implementado`: existe provider, fixture e dossie no repositorio;
- `candidato pronto`: houve resposta publica com sinais decisorios reais, mas
  ainda falta transformar o contrato em provider;
- `candidato com HAR`: a superficie e oficial e promissora, mas o payload ou
  postback ainda nao foi reproduzido em HTTP limpo;
- `parcial/documental`: a fonte entrega catalogos, precedentes ou informativos,
  mas nao uma busca geral de acordaos confirmada;
- `bloqueado/inconclusivo`: houve captcha, WAF, 401/403, timeout ou instabilidade.

## Tribunais Regionais Eleitorais

Os 27 TREs estão individualizados no catálogo nacional. O único provider
eleitoral textual/temático atualmente registrado é `tre_sp_temas`, associado ao
TRE-SP; os demais permanecem `planned` até contrato público, fixture e teste
próprios.

`TRE-AC`, `TRE-AL`, `TRE-AP`, `TRE-AM`, `TRE-BA`, `TRE-CE`, `TRE-DF`,
`TRE-ES`, `TRE-GO`, `TRE-MA`, `TRE-MT`, `TRE-MS`, `TRE-MG`, `TRE-PA`,
`TRE-PB`, `TRE-PR`, `TRE-PE`, `TRE-PI`, `TRE-RJ`, `TRE-RN`, `TRE-RS`,
`TRE-RO`, `TRE-RR`, `TRE-SC`, `TRE-SP`, `TRE-SE`, `TRE-TO`.

## Justiça Militar Estadual

O catálogo também individualiza os três tribunais estaduais reconhecidos pelo
CNJ: `TJM-MG`, `TJM-SP` e `TJM-RS`. Eles estão catalogados como `planned`; não
há provider de jurisprudência textual promovido para eles nesta rodada.

## Cobertura Por Ramos Nacionais

| Ramo | Fontes mapeadas | Situacao |
| --- | --- | --- |
| Constitucional/superior | STF, STJ, TST, STM | providers iniciais e fontes curadas |
| Federal | CJF/TNU, TRF1, TRF2, TRF3, TRF4, TRF5, TRF6 | familia eproc, contratos ou candidatos |
| Trabalhista | TST, Falcao/JT, TRT2 e demais TRTs | TST implementado; Falcao/PJe em pesquisa |
| Eleitoral | TSE e 27 TREs | TRE-SP com curadoria temática; demais autoridades catalogadas, sem provider geral |
| Militar estadual | TJM-MG, TJM-SP e TJM-RS | autoridades catalogadas; providers de jurisprudência ainda não promovidos |
| Controle externo | TCU e TCE-SP | datasets e jurisprudencia administrativa |
| Conselho | CNJ | informativos e fontes estruturadas em expansao |

## Regra De Fechamento

O Brasil sera considerado `mapped_broadly` quando cada linha tiver URL oficial,
superficie, evidencia, estado de acesso, contrato minimo, lacunas e proximo
passo. A implementacao de providers segue outra fila e exige fixture, parser,
testes offline e comportamento de erro.
