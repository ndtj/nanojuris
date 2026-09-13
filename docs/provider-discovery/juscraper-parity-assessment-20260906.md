# Paridade Juscraper × NanoJuris — 2026-09-06

Esta avaliação compara o checkout upstream fixado em
`604c1dd70d6f313011cc1079790febe6c71807e2` com o runtime NanoJuris. A análise
é de contrato e técnica; não copia código, cookies ou respostas e não transforma
um HTTP 200 em prova de conteúdo.

## Resultado por superfície CJSG

| Tribunal | Estratégia observada no Juscraper | Equivalente NanoJuris | Situação |
| --- | --- | --- | --- |
| TJAC, TJAL, TJAM, TJMS | eSAJ/HTML, sessão e paginação | providers dedicados CJSG | runtime + live válido |
| TJBA | GraphQL/JSON | `tjba_graphql` | runtime + live válido |
| TJDFT | API/HTML | `tjdf_juris` | runtime + live válido |
| TJES | PJe2G/HTML | `tjes_jurisprudencia` | runtime + live válido |
| TJGO | PROJUDI, POST form e offset | `tjgo_projudi_jurisprudencia` | HTTP 200 sem registros no smoke; total não confirmado |
| TJMT | API JSON | `tjmt_jurisprudencia_api` | runtime + live válido |
| TJPA | BFF JSON | `tjpa_jurisprudencia_bff` | runtime + live válido |
| TJPB | PJe/JSON | `tjpb_pje_jurisprudencia` | runtime + live válido |
| TJPI | JusPI/HTML | `tjpi_juspi` | runtime + live válido |
| TJPR | portal HTML | `tjpr_jurisprudencia` | resposta com ACESSO RESTRITO; não promovido |
| TJRN | portal HTML | `tjrn_jurisprudencia` | runtime; grau ainda misto |
| TJRO | portal/HTML | `tjro_jurisprudencia` | runtime; grau ainda misto |
| TJRR | portal HTML | `tjrr_juris` | runtime; contrato de paginação pendente |
| TJRS | Solr/JSON | `tjrs_solr` | runtime + live válido |
| TJSC | eproc form/AJAX | `tjsc_eproc_jurisprudencia` | revisão de contrato eproc |
| TJRJ | WebForms/XHR JSON | `tjrj_ejuris` | runtime + live válido; origem 1 (segundo grau) |
| TJTO | POST offset + `tip_criterio_inst=2` | `tjto_jurisprudencia` | promovido CJSG; live válido |
| TJCE | eSAJ + TLS SECLEVEL=1 | `tjce_cjsg` | smoke upstream e NanoJuris com dados; gate de federação separado |
| TJPE | JSF/RichFaces + ViewState/AJAX | `tjpe_jurisprudencia` | smoke upstream com dados; contrato diferencial pendente |
| TJSP | eSAJ + `resultadoCompleta.do`/sessão | `tjsp_cjsg` | smoke upstream e NanoJuris com dados; gate de federação separado |
| TJAP | Tucujuris + Turnstile | `tjap_tucujuris` (opt-in diagnóstico) | contrato/payload alinhados; consulta bloqueada sem token server-side |
| TJMG | CJSG HTML + CAPTCHA numérico | `tjmg_jurisprudencia` (opt-in diagnóstico) | descoberta de formulário alinhada; submissão bloqueada sem validação humana |
| TJMG (alternativa oficial) | Biblioteca Digital DSpace (REST/JSON + bitstream PDF) | `tjmg_dspace_jurisprudencia` | runtime + live válido; contrato independente, escopo CJSG explícito por coleção |

## Técnicas preservadas

- eSAJ: sessão persistente, campos ocultos/ViewState, POST de pesquisa,
  endpoint de paginação e diagnóstico de controle de acesso.
- TJCE: adaptador TLS dedicado com `SECLEVEL=1`, sem desativar verificação de
  certificado.
- TJPE: fluxo JSF/RichFaces em quatro etapas (GET, POST, escolha do tipo e
  AJAX), com ViewState e cookies na mesma sessão.
- TJSP: POST de submissão seguido de `trocaDePagina.do`, `conversationId` e
  download opcional do acórdão; CAPTCHA/controle permanece erro explícito.
- eproc (TJRJ/TJSC): formulário HTML, paginação AJAX, identificador nativo e
  rota separada de inteiro teor.
- APIs (TJBA/TJMT/TJPA/TJPB): payloads específicos, JSON estrito, retry,
  limite de tamanho e parser independente.
- TJGO/TJTO: POST com paginação por offset, escopo de segundo grau explícito e
  rejeição de cartões sem evidência de grau.

## Conclusão operacional

Os equivalentes classificados como `covered_by_existing_runtime` possuem
implementação NanoJuris independente e o mesmo padrão de transporte necessário;
isso não significa que todos tenham contrato CJSG completo. O smoke atual
confirmou dados em TJCE, TJPE e TJSP, mas a promoção/federação continua sujeita
aos gates de contrato, qualidade e rollout. TJRN, TJRO, TJRR e TJSC permanecem
fora da contagem estrita 27/27 até fechar grau, paginação ou diferencial de
contrato. TJAP e TJMG (no caso do formulário do Juscraper) não devem ser marcados como
“funcionais” sem fonte pública elegível. O TJMG possui, contudo, uma alternativa
oficial independente na Biblioteca Digital DSpace: `tjmg_dspace_jurisprudencia`
foi executado com resposta JSON, registros de segundo grau e bitstream PDF
público; ele não é uma equivalência de rota ao formulário CAPTCHA do Juscraper,
mas atende os gates técnicos da superfície CJSG nas coleções declaradas.

O fluxo TJRJ/eJURIS observado no Juscraper agora possui adapter NanoJuris
independente, chamada live bounded e integração federada padrão. A matriz
continua creditando a cobertura obrigatória de TJRJ pelo binding eproc, sem
contar duas vezes a superfície complementar.

Fontes de evidência geradas:

- `docs/provider-discovery/juscraper-court-inventory-20260906.json`;
- `docs/provider-discovery/juscraper-semantic-diff-20260906.json`;
- `docs/provider-discovery/juscraper-reuse-audit-20260906.json`.

## Recheck live 2026-09-06

O checkout upstream foi instalado em ambiente temporário e sua suíte passou
`1795 passed, 32 skipped` (220 testes de integração deselecionados pela
configuração padrão). Um smoke de uma página foi executado para 23 tribunais;
os estados detalhados, inclusive zeros não confirmados e respostas com acesso
restrito, estão em `juscraper-live-smoke-20260906.json`.

O smoke revelou que o POST inicial do e-SAJ é apenas um acknowledgement e pode
conter marcações de captcha mesmo quando o GET seguinte entrega resultados. O
NanoJuris foi alinhado a esse fluxo (headers/UA compatíveis, campos ocultos
completos e diagnóstico aplicado ao GET), sem bypass. TJAC, TJAL, TJAM, TJMS,
TJCE e TJSP foram rechecados localmente com página pública completa.

Este recheck supersede classificações estáticas anteriores de bloqueio quando
há evidência live posterior: TJCE, TJPE e TJSP retornaram dados upstream; TJTO
retornou HTTP 403; TJPR retornou conteúdo de acesso restrito; TJGO e TJRO
retornaram zero não confirmado; TJPA e TJSC retornaram dados com lacunas de
qualidade. Nenhum provider foi promovido automaticamente apenas por este
smoke.

Evidência adicional: `docs/provider-discovery/juscraper-live-smoke-20260906.json`.

Os contratos específicos de TJAP/TJMG do checkout upstream também foram
executados em ambiente temporário: 43 testes de parser, filtros, paginação e
tratamento de erro passaram. Os adapters NanoJuris independentes agora expõem
esses contratos em modo opt-in diagnóstico, mas preservam os limites live: TJAP
permanece bloqueado por Turnstile e TJMG exige CAPTCHA numérico. O resultado
bounded está em `docs/provider-discovery/juscraper-captcha-boundary-live-20260906.json`;
essas fontes continuam fora da federação padrão até existir rota pública
reproduzível sem contornar controle de acesso.
