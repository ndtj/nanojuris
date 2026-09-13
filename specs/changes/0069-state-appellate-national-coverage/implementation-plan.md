# Plano de implementacao 27/27

Este documento e o roteiro para o modelo executor. O estado detalhado e as 216
tarefas estao no JSON gerado `docs/coverage/state-appellate-program-20260905.json`.

## Onda A - baseline ja comprovado

| TJ | Provider | Trabalho |
| --- | --- | --- |
| TJAC | `tjac_cjsg` | manter contrato, fixture e live periodico |
| TJAL | `tjal_cjsg` | manter contrato, fixture e live periodico |
| TJAM | `tjam_cjsg` | manter contrato, fixture e live periodico |
| TJBA | `tjba_graphql` | contrato explicito de segundo grau, filtros e trace |
| TJES | `tjes_jurisprudencia` | manter `pje2g` isolado de CJPG/turma recursal |
| TJMS | `tjms_cjsg` | manter contrato, fixture e live periodico |
| TJMT | `tjmt_jurisprudencia_api` | contrato explicito de segundo grau e tipo documental |
| TJPA | `tjpa_jurisprudencia_bff` | contrato explicito de segundo grau e limite tecnico |

Saida: os oito workpacks continuam 8/8 depois da suite e de smoke bounded.

## Onda B1 - APIs com live valido

| Ordem | TJ | Provider atual | Foco do contrato de segundo grau |
| ---: | --- | --- | --- |
| 1 | TJBA | `tjba_graphql` | `instancia`, tipos decisorios e pagina zero-based |
| 2 | TJDFT | `tjdf_juris` | SISTJ/API, acordaos e turma recursal sem mistura |
| 3 | TJMT | `tjmt_jurisprudencia_api` | instancia no payload e identidade do acordao |
| 4 | TJPA | `tjpa_jurisprudencia_bff` | grau, total, pagina e schema BFF |
| 5 | TJPB | `tjpb_pje_jurisprudencia` | endpoint PJe, grau e challenge explicito |
| 6 | TJRN | `tjrn_jurisprudencia` | filtrar/provar `grau=second` por registro |

Para cada linha: abrir SDD individual, capturar fixtures sanitizadas, provar
pagina 2 e vazio autoritativo, adicionar teste que rejeita primeiro grau,
executar live bounded e somente entao alterar o binding da matriz.

## Onda B2 - portais publicos com live valido

| Ordem | TJ | Provider atual | Foco do contrato de segundo grau |
| ---: | --- | --- | --- |
| 7 | TJGO | `tjgo_projudi_jurisprudencia` | separar acordaos de sentencas/decisoes mistas |
| 8 | TJPI | `tjpi_juspi` | provar instancia, total desconhecido e documento |
| 9 | TJPR | `tjpr_jurisprudencia` | acordao, ordenacao e inteiro teor |
| 10 | TJRR | `tjrr_juris` | JSF, view state, pagina 2 e vazio real |
| 11 | TJRS | `tjrs_solr` | filtros Solr, grau e identidade documental |
| 12 | TJTO | `tjto_jurisprudencia` | `tip_criterio_inst=2` e detalhe de ementa |

## Onda B3 - eproc e binding incorreto

| Ordem | TJ | Provider/acao | Foco |
| ---: | --- | --- | --- |
| 13 | TJRJ | `tjrj_eproc_jurisprudencia` | provar tipo/grau no resultado e estados de acesso |
| 14 | TJSC | `tjsc_eproc_jurisprudencia` | provar segundo grau sem misturar sentencas |
| 15 | TJRO | trocar candidato CJSG de `tjro_liame` para `tjro_jurisprudencia` | Liame e precedente contextual; nao conta como jurisprudencia geral |

TJRO e um reparo prioritario da fonte unica de verdade. O binding atual aponta
para Liame porque ele aparece primeiro na declaracao, embora exista provider
textual separado. Nao alterar contagem antes de provar segundo grau no provider
textual.

## Onda C - bloqueios e alternativas oficiais

| TJ | Estado atual | Trabalho permitido |
| --- | --- | --- |
| TJAP | Turnstile/CAPTCHA | procurar API/portal oficial alternativo; manter bloqueado se inexistente |
| TJCE | transporte CJSG bloqueado | testar `tjce_sjuris` como alternativa somente se publicar acordaos gerais de segundo grau |
| TJPE | transporte bloqueado | reproduzir fluxo oficial observado no Juscraper sem relaxar TLS nem ocultar challenge |
| TJSP | CJSG com controle de acesso | avaliar eproc/rota oficial alternativa; nunca automatizar CAPTCHA |

Um bloqueio persistente e resultado valido do workpack, mas nao satisfaz 27/27.
O executor deve registrar HTTP/TLS/content-type de forma redigida e encerrar a
tentativa bounded.

## Onda D - gaps de adapter

| Ordem | TJ | Estado | Plano |
| ---: | --- | --- | --- |
| 1 | TJMG | candidato `tjmg_jurisprudencia` | aproveitar apenas seletores/rotas publicas; rejeitar OCR de CAPTCHA |
| 2 | TJMA | sem provider textual CJSG | distinguir `tjma_jurisconsult` catalogo de uma busca decisoria oficial |
| 3 | TJSE | sem provider | pesquisar portal/API oficial e criar adapter independente |

TJMA e TJSE nao aparecem como classes CJSG no snapshot Juscraper. A pesquisa
deve partir do tribunal, registrar indisponibilidade se for o caso e nunca
inventar endpoint.

## Loop por tribunal

1. Ler AGENTS, este pacote, dossie, source contract, provider e testes.
2. Criar/atualizar pacote SDD individual antes do codigo.
3. Reproduzir no maximo consultas bounded e sem credencial.
4. Implementar transporte via runtime compartilhado e parser independente.
5. Adicionar fixtures de sucesso, vazio, invalido, bloqueio e schema drift.
6. Validar filtros, pagina 2, ordem, identidade, grau e documento.
7. Executar testes focados, Ruff, mypy e teste federado opt-in.
8. Atualizar capacidades/dossie/contrato e rodar os geradores canonicos.
9. Executar suite completa e `validate_sdd.py`.
10. Promover somente se os oito gates ficarem completos; caso contrario,
    preservar o motivo e seguir para o proximo tribunal.

## Comandos de encerramento por lote

```text
python tools/audit_provider_docs.py --write
python tools/build_provider_coverage.py --write
python tools/build_degree_coverage.py --write
python tools/build_surface_state_registry.py --write
python tools/build_state_appellate_program.py --write
python tools/build_promotion_manifest.py --write
python tools/validate_sdd.py
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
python -m mypy src
```

## Condicao final

O programa termina somente quando:

- `summary.complete_8_of_8 == 27`;
- nenhum TJ esta em `adapter_discovery`, `contract_hardening` ou
  `blocked_recheck`;
- cada provider retorna jurisprudencia textual de segundo grau ou a meta foi
  formalmente revista pelo usuario por indisponibilidade institucional;
- a consulta federada informa resultados/estado por fonte sem falso vazio;
- testes, qualidade, SDD e artefatos gerados estao verdes e coerentes.
