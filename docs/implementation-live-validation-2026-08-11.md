# Implementation Live Validation 2026-08-11

Rodada controlada dos oito providers promovidos na sequencia tecnica. Todas as
chamadas usaram `requests`, `trust_env=False`, SSL habilitado, sem cookies
exportados, login, captcha, proxy de contorno ou sessao de navegador.

Os totais sao observacoes do momento e nao representam garantia de cobertura,
estabilidade futura ou coleta integral.

## Resultados

| Provider | Operacao | HTTP | Evidencia normalizada |
| --- | --- | ---: | --- |
| `tjpb_pje_jurisprudencia` | busca `dano moral`, page size 1 | 200 | total `48534`, 1 resultado, processo `0802253-46.2017.8.15.2003` |
| `tjpa_jurisprudencia_bff` | busca `dano moral`, page size 1 | 200 | total `10000`, 1 resultado, processo `0000873-49.2010.8.14.0013` |
| `tjrs_solr` | busca `dano moral`, page size 1 | 200 | total `612403`, 1 resultado, resposta SOLR JSON |
| `tcu_jurisprudencia` | leitura do manifesto oficial | 200 | `42` bases/datasets catalogados |
| `tjrj_eproc_jurisprudencia` | busca `dano moral`, page size 1 | 200 | 10 resultados retornados pela fonte, 1 normalizado, processo `0821016-57.2023.8.19.0004` |
| `tjsc_eproc_jurisprudencia` | busca `dano moral`, page size 1 | 200 | 10 resultados retornados pela fonte, 1 normalizado, processo `5002450-32.2021.8.24.0103` |
| `trf5_jurisprudencia` | busca `dano moral`, page size 1 | 200 | 1 resultado normalizado, processo `0500731-14.2013.4.05.8501` |
| `cjf_jurisprudencia` | busca TRF1 `dano moral` + `ACORDAO`, page size 1 | 200 | total `7483`, 1 resultado, processo `1008804-85.2023.4.01.4100` |

## Interpretacao

- TJPB, TJPA e TJRS confirmaram os envelopes JSON/dataset usados pelos parsers.
- TJRJ e TJSC confirmaram o fluxo eproc compartilhado com identificadores e
  hosts proprios por tribunal.
- O TCU foi validado pelo manifesto para evitar uma varredura repetitiva do CSV
  de acordaos, que possui dezenas de megabytes.
- O teste live nao substitui fixtures offline nem autoriza bypass de controles
  de acesso. Detalhe e inteiro teor permanecem explicitamente indisponiveis nos
  providers que ainda nao possuem esse contrato validado.

## Reproducao

Use consultas pequenas, `page_size=1`, timeout conservador e `trust_env=False`
somente quando o proxy local estiver interferindo. Nunca versionar tokens,
cookies ou respostas integrais de fontes publicas.
