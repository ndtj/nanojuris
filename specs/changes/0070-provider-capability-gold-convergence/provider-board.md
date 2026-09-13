# Board inicial dos 60 providers

Este board é uma fotografia de planejamento, não um artefato gerado nem uma
afirmação de saúde atual. A Onda 0 deve substituí-lo por workpacks derivados do
ledger canônico. Cada linha termina somente quando filtros, campos, documentos,
falhas e interfaces estiverem em estados comprovados.

## Jurisprudência textual primária — 33

| Provider | Família | Prioridade de descoberta/implementação |
| --- | --- | --- |
| `stj_informativo` | HTML/curadoria | provar filtros de edição/tema, relação com decisões e documentos |
| `stm_jurisprudencia` | API/portal | inventariar filtros, detalhe, PDF e datas militares |
| `tjac_cjsg` | eSAJ | expandir filtros e catálogo; revalidar detalhe e inteiro teor |
| `tjal_cjsg` | eSAJ | expandir filtros e catálogo; revalidar detalhe e inteiro teor |
| `tjam_cjsg` | eSAJ | expandir filtros e catálogo; revalidar detalhe e inteiro teor |
| `tjba_graphql` | GraphQL | inventariar schema/facets, provar aliases e detalhe |
| `tjce_sjuris` | REST | mapear todos os filtros, campos inline e tipos decisórios |
| `tjdf_juris` | REST | fechar filtros avançados, detalhe e documentos SISTJ |
| `tjes_cjpg` | API/HTML | completar filtros de primeiro grau e campos inline |
| `tjes_jurisprudencia` | PJe/API | separar graus, completar filtros e campos de acórdão |
| `tjes_turma_recursal` | PJe/API | filtros próprios, identidade de turma e conteúdo inline |
| `tjgo_projudi_jurisprudencia` | Projudi | descobrir filtros além de texto/número e validar inteiro teor |
| `tjms_cjsg` | eSAJ | expandir filtros, catálogos e detalhe |
| `tjmt_jurisprudencia_api` | REST | descobrir filtros estruturais e enriquecer campos inline |
| `tjpa_jurisprudencia_bff` | BFF/REST | mapear selects dependentes, facets e todos os campos inline |
| `tjpb_pje_jurisprudencia` | PJe/JSF | provar todos os inputs, grau, órgão e detalhe/documento |
| `tjpi_juspi` | API/portal | filtros, paginação, detalhe e PDF |
| `tjpr_jurisprudencia` | HTML | localizar inteiro teor oficial e provar filtros refinados |
| `tjrj_eproc_jurisprudencia` | eproc | inventariar formulário, origem, grau, detalhe e documento |
| `tjrn_jurisprudencia` | REST | elevar filtros além de texto/número e classificar campos inline |
| `tjro_jurisprudencia` | REST | mapear filtros do portal, detalhe e inteiro teor |
| `tjrr_juris` | JSF | filtros, view state, segunda página e documento |
| `tjrs_solr` | Solr/HTML | descobrir facets e recuperar inteiro teor oficial |
| `tjsc_eproc_jurisprudencia` | eproc | inventariar filtros, primeiro/segundo grau e documento |
| `tjsp_cjpg` | eSAJ | filtros de sentença, comarca/foro e conteúdo inline |
| `tjsp_eproc_jurisprudencia` | eproc | origem, filtros, detalhe e documento por grau |
| `tjto_jurisprudencia` | REST/HTML | inventariar filtros, instância, detalhe e documento |
| `tnu_eproc_jurisprudencia` | eproc | catálogo de filtros, detalhe e documento nacional |
| `trf2_eproc_jurisprudencia` | eproc | catálogo de filtros, instância e documento |
| `trf4_eproc_jurisprudencia` | eproc | corrigir baixa declaração de filtros e revalidar documento |
| `trf5_jurisprudencia` | HTML/API | completar filtros e detalhe/documento |
| `trf6_eproc_jurisprudencia` | eproc | catálogo de filtros, detalhe e documento |
| `tst_jurisprudencia` | REST | usar como referência de contrato amplo e validar detalhe |

## Precedentes, especializadas e contexto — 11

| Provider | Papel | Prioridade de descoberta/implementação |
| --- | --- | --- |
| `bnp_pangea` | precedente | filtros de tribunal/tipo/status; decisões vinculadas, sem falso full text |
| `tjro_liame` | precedente | filtros contextuais e relação com decisões; implementar detalhe se público |
| `tjsp_nugepnac` | precedente | temas/status/tipo, detalhe e documentos oficiais |
| `cjf_jurisprudencia` | especializada | revalidar superfície TRF1, filtros, bloqueio e PDF oficial |
| `stf_informativo` | informativo | catálogo/edição/tema, arquivo e TLS explícito |
| `stf_juris` | jurisprudência STF | rota pública, filtros, detalhe e documento sem contornar transporte |
| `stj_scon` | jurisprudência STJ | filtros SCON, detalhe e documento; manter bloqueio explícito |
| `tjce_cjsg` | CJSG | revalidar eSAJ, filtros e detalhe quando transporte permitir |
| `tjma_jurisconsult` | catálogo contextual | localizar busca decisória; não promover catálogo como jurisprudência |
| `tjpe_jurisprudencia` | JSF/REST | reconciliar status atual, completar filtros e validar inline/detalhe |
| `tjsp_cjsg` | eSAJ | revalidar fluxo público, filtros e detalhe sem bypass |

## Curadoria, administração e datasets — 8

| Provider | Papel | Prioridade de descoberta/implementação |
| --- | --- | --- |
| `cnj_jurisprudencia` | curadoria | filtros do portal, PDFs relacionados e metadados editoriais |
| `justica_eleitoral_sjur` | eleitoral | separar catálogos de busca decisória e mapear filtros eleitorais |
| `tjce_informativos` | curadoria | edições, temas, documentos e estado TLS |
| `tre_sp_temas` | curadoria eleitoral | temas, eleições, documentos e disponibilidade |
| `tce_pr_viajuris` | administrativo/dataset | schema, filtros locais reproduzíveis e link documental |
| `tce_sp_jurisprudencia` | administrativo | localizar corpus decisório, filtros e documentos |
| `tcu_jurisprudencia` | administrativo/dataset | unir schemas publicados, filtros locais e acórdão completo |
| `stj_dados_abertos_jurisprudencia` | dataset | inventariar datasets/recursos, schema, versões e inteiro teor |

## Candidates e família — 8

| Provider | Estado | Critério de avanço |
| --- | --- | --- |
| `falcao_jt` | candidate | fonte oficial trabalhista, contrato, filtros, dados e documentos |
| `tjap_tucujuris` | candidate | acesso público legítimo, filtros e decisão textual |
| `tjmg_jurisprudencia` | candidate | rota sem bypass, parser, filtros e inteiro teor |
| `tjrj_ejuris` | candidate | decidir complementaridade com eproc e provar contrato próprio |
| `tjse_jurisprudencia` | candidate | localizar fonte oficial, implementar e certificar |
| `trf3_jurisprudencia` | candidate | rota oficial, filtros, detalhe e documentos |
| `trt2_pje_jurisprudencia` | candidate | superfície PJe pública, filtros e documentos trabalhistas |
| `eproc_jurisprudencia_federal` | family | manter apenas abstração; certificar cada implementação concreta |

## Ordem de fechamento dentro de cada linha

```text
discovery -> filter contract -> field map -> pagination/order
          -> detail/document -> errors -> fixtures/tests
          -> interfaces/federation -> gold assessment
```

