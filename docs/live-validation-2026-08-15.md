# Validacao Live de Providers - 2026-08-15

Esta rodada foi executada em 2026-08-15 com a consulta textual
`responsabilidade civil` e `page_size=1`. A validacao usa chamadas publicas
pequenas, nao altera dados nas fontes e nao usa cookie pessoal, login, captcha,
proxy de contorno ou bypass.

## Resultado

| Provider | Estado | Retornados | Total informado | Paginacao | Latencia aproximada | Observacao |
| --- | --- | ---: | ---: | --- | ---: | --- |
| `tjdf_juris` | `valid` | 1 | 131875 | `page` | 2,7 s | contrato e conteudo normalizados |
| `tjrs_solr` | `valid` | 1 | 692019 | `offset` | 1,3 s | JSON SOLR com resultado e trace |
| `tst_jurisprudencia` | `valid` | 1 | 841967 | `offset` | 1,7 s | API REST com resultado e trace |
| `trf4_eproc_jurisprudencia` | `source_unavailable` | 0 | - | - | 20,1 s | timeout de conexao; repetir em outra rede |
| `tcu_jurisprudencia` | `valid` | 1 | 1 | `unknown` | 15,2 s | busca no CSV publico de resumo |

## O que foi verificado

Para cada fonte, o validador conferiu:

- `SearchPage.source` correspondente ao provider;
- `SourceTrace` presente;
- pagina e tamanho solicitados preservados;
- total nao negativo quando informado;
- identificadores, fonte, conteudo juridico e trace dos resultados;
- estado de completude conservador, sem tratar uma pagina parcial como coleta total.

## Interpretacao

Quatro providers passaram a verificacao live desta rodada. O TRF4 nao foi
classificado como provider quebrado: a falha foi `SourceUnavailableError` por
timeout de conexao na rota publica. Esse estado deve ser revalidado antes de
uma coleta, e nao substituido por resultado vazio.

Os totais informados pelas fontes sao volumes remotos observados para a
consulta, nao quantidade coletada nesta rodada. A coleta retornou uma janela de
um registro por provider.

## Reproducao

```bash
python -m nanojuris.cli validar \
  --fontes tjdf_juris,tjrs_solr,tst_jurisprudencia,trf4_eproc_jurisprudencia,tcu_jurisprudencia \
  --texto "responsabilidade civil" \
  --timeout 60
```

Os tempos e estados podem mudar conforme rede, disponibilidade, limites e
controles externos da fonte.
