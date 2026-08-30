# Status das fontes

O NanoJuris distingue três perguntas que costumam ser confundidas:

| Estado | Significado |
| --- | --- |
| **Implementado** | Existe um adapter registrado no pacote e exposto pelas interfaces suportadas. |
| **Validado** | O parser, o contrato e os cenários offline possuem testes e fixtures. |
| **Live** | Uma chamada pública respondeu em uma verificação identificada por data, rede e consulta. |

Uma fonte pode ser implementada e validada sem estar disponível live no momento
da consulta. Tribunais podem alterar rotas, aplicar limites, exigir captcha ou
responder de forma diferente conforme a rede. Por isso, o NanoJuris preserva a
limitação observada em vez de convertê-la em falso sucesso.

## Catálogo operacional

O [registry](registry/providers.json) é a fonte machine-readable de providers
implementados, candidatos e famílias. Para consultar o contrato runtime:

```bash
nanojuris fontes
nanojuris diagnostico --fonte tjdf_juris
nanojuris contratos --resumo
nanojuris contratos --fonte tjdf_juris
```

Para uma visão humana da cobertura, consulte o [mapa de cobertura](provider-coverage-map.md)
e o [auditório documental](provider-documentation-audit.md). Os relatórios de
validação registram a evidência live sem prometer disponibilidade permanente.

A rodada live mais recente esta em [live-validation-latest.md](live-validation-latest.md).

### Perfis de selecao no Studio

O Studio expoe o catalogo inteiro, mas oferece tres perfis para que a primeira
consulta seja rapida e compreensivel:

| Perfil | Fontes | Uso |
| --- | ---: | --- |
| `maduras` | 7 | primeira consulta com contratos de menor risco operacional |
| `jurisprudencia` | 34 | cobertura recomendada, incluindo fontes avancadas e restritas |
| `todas` | 40 | auditoria ampla do catalogo; o roteador explica pulos e falhas |

O perfil nao altera o contrato do provider nem transforma uma fonte restrita
em disponivel. Para agentes, use `list_sources`, `source_contracts` e o campo
`routing_summary` da busca unificada antes de interpretar a completude.

## Estados de acesso

Quando uma consulta é executada, os estados relevantes podem incluir:

| Estado | Interpretação operacional |
| --- | --- |
| `public` | A resposta foi obtida sem controle de acesso observado. |
| `partial` | A fonte respondeu, mas não comprovou todos os campos ou a completude. |
| `access_control_required` | A fonte apresentou captcha, WAF ou outra barreira. |
| `login_required` | A rota exigiu autenticação. |
| `rate_limited` | A fonte limitou a frequência ou o volume. |
| `source_unavailable` | A rota não respondeu ou apresentou erro transitório. |

Esses estados descrevem a aquisição, não a validade jurídica do conteúdo.

## Exemplos de leitura

```text
tjdf_juris
  implementação: registrada
  validação: fixture + contrato
  live: evidência datada; consultar diagnóstico antes de lote

stf_juris
  implementação: registrada
  validação: fixture + contrato observado
  live: condicionado à resposta da fonte e a controles externos

stj_scon
  implementação: registrada
  validação: parser offline
  live: experimental; conferir o dossiê antes de depender da fonte
```

Os exemplos acima são categorias de maturidade, não um monitoramento em tempo
real. A execução atual deve ser verificada no ambiente do usuário.

## Limitações conhecidas por fonte (verificação live 2026-08-30)

Sweep pelo pipeline da plataforma (`search_many(canonical=True)`, termo
`responsabilidade civil`). Das 46 fontes federadas, 27 retornaram resultados
canônicos limpos. As demais se classificam assim — **nenhuma é bug em aberto do
parser**:

| Fonte | Situação | Natureza |
| --- | --- | --- |
| `bnp_pangea` | **corrigido** — `/precedentes` passou a exigir `orgaos` e `tipos`; o provider os preenche com o catálogo completo | contrato da fonte |
| `tce_pr_viajuris` | **corrigido** — o CSV anual mudou de schema (`DsTipoAto;NrAto;AnoAto;…`) | contrato da fonte |
| `cnj_jurisprudencia` | **corrigido** — o filtro `argumento` casa a frase literalmente; consultas multi-palavra agora enviam o token mais seletivo e filtram o restante client-side (com dobra de acento) | contrato da fonte |
| `tjsp_cjsg`, `stj_scon`, `cjf_jurisprudencia`, `tjma_jurisconsult` | `access_control_required` — captcha / WAF / Cloudflare | controle de acesso (nunca contornado); fora do conjunto padrão |
| `tre_sp_temas` | HTTP 403 na rota de temas | controle de acesso |
| `stf_juris`, `stf_informativo` | `source_unavailable` — verificação SSL falha nesta rede | ambiente local; revalidar de rede limpa |
| `tjpe_jurisprudencia`, `tjce_cjsg` | `source_unavailable` — conexão recusada/reset | rede transitória |
| `tjac_cjsg` | e-SAJ do TJAC devolve `totalResultadoAba-A=0` e `emptySession.jsp` (HTTP 404) para toda consulta; os 3 provedores CJSG irmãos (`tjms`, `tjal`, `tjam`) funcionam com o mesmo código | indisponibilidade no servidor do TJAC; o provider degrada para resultado vazio limpo |
| `stj_dados_abertos_jurisprudencia` | `UnsupportedQueryError` — a fonte não oferece busca online; requer `sync` de um recurso e busca no índice local | por design |
| `justica_eleitoral_sjur` | `UnsupportedQueryError` — só catálogo promovido; busca decisória aguarda contrato reproduzível | por design |
| `tjsp_nugepnac`, `tce_sp_jurisprudencia` | retornam vazio sem `SourceTrace` de rota real | endpoint provavelmente descontinuado; revalidar |

## Critério para produção

Antes de incorporar uma fonte em uma coleta importante:

1. confira o `source_id` e o dossiê específico;
2. rode `nanojuris diagnostico --fonte <source_id>`;
3. confirme busca, paginação, documentos e limites;
4. preserve `SourceTrace`, erros parciais e `run_id`;
5. registre a data da verificação no relatório do seu próprio dataset.

Para novos providers, o contrato completo está em
[provider-dossier-template.md](provider-dossier-template.md) e o processo de
descoberta está no [route-mapping-playbook.md](route-mapping-playbook.md).
