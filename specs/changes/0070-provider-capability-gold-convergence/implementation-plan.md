# Plano de implementação — filtros, dados e inteiro teor ouro

## Linha de base inicial

Fotografia local de 2026-09-06, a ser regenerada na Onda 0:

| Indicador | Valor observado |
| --- | ---: |
| Fontes catalogadas | 60 |
| Providers runtime | 52 |
| Candidates/família | 7/1 |
| Providers federados por padrão | 38 |
| `maturity_tier=gold` no catálogo | 14 |
| `quality_tier=gold` no scorecard | 32 |
| Estados provider/filtro `unverified` | 1.533 |
| Estados provider/filtro `native` | 250 |
| Runtime sem `supports_full_text` | 18 |
| Runtime com acesso documental fraco/ausente | 17 |
| Providers cobertos pelo sweep profundo antigo | 44 |

As divergências são parte do problema; nenhuma dessas contagens é critério de
conclusão isolado.

## Onda 0 — fonte única de verdade

1. Criar schema do ledger de capacidades.
2. Implementar `build_provider_capability_ledger.py` combinando runtime,
   catálogo, matriz unificada, documentos, fixtures e última evidência live.
3. Gerar um workpack por provider, sem duplicar prosa de dossiês.
4. Separar `legacy_quality_tier`, `maturity_tier`, cinco eixos ouro e saúde.
5. Rejeitar IDs ausentes, evidência sem data, snapshot anterior ao runtime e
   capacidades conflitantes.

Saída: denominador automático e lista exata de lacunas por provider.

## Onda 1 — contratos e instrumentação comuns

1. Adicionar modelos aditivos `EvidenceRecord`, `FilterCapability`,
   `FieldCapability`, `DocumentCapability` e `GoldAssessment`.
2. Criar registro canônico de filtros, aliases e tipos.
3. Fazer `ProviderCapabilities.filter_status()` consumir o ledger ou um overlay
   gerado, preservando compatibilidade.
4. Expor plano de filtro por fonte na resposta federada.
5. Instrumentar captura redigida de requests/responses e fingerprints.
6. Criar comparador diferencial de páginas e inventário de campos.

Saída: infraestrutura testável antes de editar dezenas de adapters.

## Onda 2 — pilotos por família

Escolher uma fonte saudável e representativa de cada família:

| Família | Piloto recomendado | Foco |
| --- | --- | --- |
| eSAJ | `tjac_cjsg` e `tjsp_cjpg` | formulários, enum, paginação e detalhe |
| eproc | `trf4_eproc_jurisprudencia` | filtros, origem, sessão e documento |
| PJe | `tjpb_pje_jurisprudencia` | payload, órgão, grau e inteiro teor |
| GraphQL | `tjba_graphql` | schema, facets e paginação zero-based |
| BFF/REST | `tjpa_jurisprudencia_bff` | filtros dependentes e detalhe |
| Projudi | `tjgo_projudi_jurisprudencia` | formulário, grau e links |
| JSF/RichFaces | `tjpe_jurisprudencia` e `tjrr_juris` | view state, AJAX e fallback |
| Solr | `tjrs_solr` | query params, facets e ordenação |
| dataset | `tcu_jurisprudencia` | schema tabular, arquivo completo e versões |

Cada piloto fecha ferramentas, fixtures e abstrações; só depois a família é
aplicada aos demais membros.

## Onda 3 — jurisprudência textual primária

Trabalhar os 33 providers em lotes de dois ou três, ordenados por retorno:

1. providers live válidos já gold no score legado;
2. providers live válidos silver;
3. providers com contrato/documento incompleto;
4. providers bloqueados, apenas após esgotar rotas oficiais alternativas.

Por provider:

- inventário completo de filtros e campos;
- teste diferencial de cada filtro suportado;
- segunda página, vazio, inválido e schema drift;
- detalhe e documento;
- paridade SDK/CLI/MCP/Studio;
- certificação nos cinco eixos.

Prioridade inicial de hardening: `tjes_cjpg`, `tjes_jurisprudencia`,
`tjes_turma_recursal`, `tjgo_projudi_jurisprudencia`,
`tjrn_jurisprudencia`, `tjrs_solr` e `stj_informativo`, atualmente abaixo de
gold no score offline apesar de serem classificados como jurisprudência textual.

## Onda 4 — fontes especializadas e precedentes

Trabalhar separadamente:

- `bnp_pangea`, `tjro_liame`, `tjsp_nugepnac`;
- `cjf_jurisprudencia`, `stf_juris`, `stj_scon`, `tjce_cjsg`,
  `tjpe_jurisprudencia`, `tjsp_cjsg`;
- `stf_informativo` e `tjma_jurisconsult`.

O gate textual é adequado ao papel da fonte. Precedente, tema ou catálogo não
é convertido em acórdão geral. Fontes hoje classificadas incorretamente devem
ter `coverage_role` reconciliado antes da federação.

## Onda 5 — curadoria, administração e datasets

Cobrir:

- `cnj_jurisprudencia`, `justica_eleitoral_sjur`, `tjce_informativos`,
  `tre_sp_temas`;
- `tce_pr_viajuris`, `tce_sp_jurisprudencia`, `tcu_jurisprudencia`;
- `stj_dados_abertos_jurisprudencia`.

Para datasets, filtros locais são legítimos somente após ingestão completa e
manifesto reproduzível. Para conteúdo curado, inteiro teor pode ser o próprio
item ou um documento relacionado; a distinção deve permanecer explícita.

## Onda 6 — candidates e família

Gerar workpacks para:

- `falcao_jt`;
- `tjap_tucujuris`;
- `tjmg_jurisprudencia`;
- `tjrj_ejuris`;
- `tjse_jurisprudencia`;
- `trf3_jurisprudencia`;
- `trt2_pje_jurisprudencia`;
- família `eproc_jurisprudencia_federal`.

Candidate só vira runtime quando contrato, fixtures, filtros, dados, documento,
falhas e live bounded estiverem comprovados. A família não conta como provider.

## Onda 7 — convergência de inteiro teor

### Grupo A — inline/detail já declarado

Validar ponta a ponta todos os providers `inline` e `detail_call`, incluindo
linkagem, MIME, hash e texto mínimo.

### Grupo B — apenas link/unknown/not implemented

Pesquisar rotas oficiais de detalhe/documento para os 17 providers com acesso
fraco ou ausente, priorizando:

`stj_dados_abertos_jurisprudencia`, `stf_juris`, `cnj_jurisprudencia`,
`cjf_jurisprudencia`, `stj_informativo`, `tce_pr_viajuris`,
`tce_sp_jurisprudencia`, `tjma_jurisconsult`, `tjro_liame`,
`tjsp_nugepnac` e `tre_sp_temas`.

### Grupo C — fonte não oferece

Registrar `not_offered_by_source` somente após pesquisa oficial, detalhe e
rotas alternativas. Não usar ementa como substituto de inteiro teor.

### Grupo D — OCR

Habilitar apenas para PDF público realmente escaneado, como extra opcional,
com confiança, idioma, páginas e provenance. OCR não é requisito quando há
texto embutido e nunca é usado para desafios de acesso.

## Onda 8 — federação e experiência de busca

1. Retornar `filter_application` por provider.
2. Mostrar na UI a interseção de filtros das fontes selecionadas.
3. Permitir modo avançado com união de filtros e indicação de suporte parcial.
4. Bloquear identificadores não aplicáveis antes da chamada.
5. Aplicar pós-filtro apenas com garantia de campo/janela.
6. Preservar ranking, deduplicação, total e completude por fonte.
7. Alinhar MCP com SDK/CLI ou publicar matriz de diferenças.

## Onda 9 — certificação e operação contínua

1. Avaliar os cinco eixos automaticamente.
2. Impedir `provider_gold` com `unverified`, fixture faltante ou evidência
   expirada.
3. Executar canários bounded por risco/família.
4. Detectar drift de formulário, bundle, schema, filtros e documentos.
5. Reabrir somente gates afetados.
6. Gerar relatório final por provider e por capacidade.

## Loop de execução por provider

1. Regerar ledger e abrir workpack.
2. Ler catálogo, dossiê, contrato, código, fixtures e testes.
3. Executar os oito passes de discovery.
4. Atualizar ledger com evidence IDs.
5. Alterar query/adapter/parser/documento.
6. Criar fixtures mínimas e testes diferenciais.
7. Executar testes focados e smoke opt-in.
8. Atualizar apenas documentação afetada.
9. Regenerar inventários ao fechar o lote.
10. Avaliar cinco eixos e promover automaticamente somente com todos os gates.

## Definition of Done do programa

```text
catalog_entries == capability_ledger_entries
runtime_entries == runtime_workpacks
unverified_filter_capabilities == 0 para provider_gold
unclassified_observed_fields == 0 para provider_gold
document_state_missing == 0
silent_filter_omissions == 0
false_empty_regressions == 0
expired_evidence_on_gold == 0
```

O relatório final deve mostrar separadamente quantos providers são contract,
data, document, engineering, operation, federation e provider gold.
