# Validacao Live da Pesquisa Unificada - 2026-08-12

## Escopo

Foi executada uma consulta controlada com o termo:

```text
desconsideracao da personalidade juridica
```

Configuracao: todos os 34 providers registrados, `page_size=2`, concorrencia
limitada pelo cliente, timeout global de 90 segundos, intervalo de 250 ms por
provider e `trust_env=False`. A consulta usou apenas rotas publicas declaradas
pelos adapters.

## Resultado observado

- 34 fontes solicitadas;
- 31 fontes consultadas;
- 3 fontes corretamente ignoradas por nao declararem jurisprudencia unificada:
  `comunica_pje`, `tjac_esaj_cpopg` e `tjsp_esaj_cpopg`;
- 5 fontes falharam sem interromper a federacao: `bnp_pangea` (consulta rejeitada
  pela fonte com HTTP 400),
  `stf_informativo` e `stf_juris` (SSL local), `stj_scon` (controle de acesso) e
  `tjsp_cjsg` (captcha/controle de acesso);
- 43 resultados foram coletados e deduplicados na janela observada;
- 2 resultados foram entregues na pagina federada solicitada;
- `collection_complete=false`, corretamente, porque houve falhas, fontes
  ignoradas e janelas parciais.

## O que mudou no contrato Ouro

Os providers com contrato de paginação conhecido agora retornam:

- `pagination_mode`: `page`, `offset` ou `local_window`;
- `is_complete=false` quando a pagina representa apenas parte do total;
- `is_complete=true` somente quando a janela alcanca o total autoritativo;
- `is_complete=null` quando a fonte nao informa total confiavel.

Na mesma rodada, os nove providers da frente Ouro reportaram o seguinte:

| Provider | Modo | Total reportado | Retornados | Completo |
| --- | --- | ---: | ---: | --- |
| `tjdf_juris` | page | 9.585 | 2 | nao |
| `tjgo_projudi_jurisprudencia` | page | 356 | 2 | nao |
| `tjpi_juspi` | page | 4.258 | 2 | nao |
| `tjpa_jurisprudencia_bff` | page | 10.000 | 2 | nao |
| `tjpb_pje_jurisprudencia` | page | 416 | 2 | nao |
| `tjrs_solr` | offset | 17.025 | 2 | nao |
| `tst_jurisprudencia` | offset | 82.073 | 2 | nao |
| `stm_jurisprudencia` | offset | 55 | 2 | nao |
| `stj_informativo` | local_window | 22 | 2 | nao |

Esses totais sao os valores retornados pelas fontes para o termo e a janela
daquela execucao. Eles nao representam o total nacional nem uma garantia
permanente de disponibilidade.

## Pendencias priorizadas

1. Expandir a matriz de payloads aceitos e rejeitados pelo BNP.
2. Corrigir a cadeia de certificados do ambiente que consulta os endpoints STF,
   sem desativar verificacao TLS no uso normal.
3. Manter SCON e CJSG como fontes parciais enquanto o controle de acesso existir.
4. Validar segunda pagina por provider em uma rotina live separada, preservando
   a mesma query e comparando ids, total, ordem e intervalo.
5. Promover `collection_complete` apenas em consultas cujo conjunto de fontes e
   janelas esteja comprovadamente fechado.
