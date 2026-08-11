# Validacao Live Da Busca Unificada 2026-08-11

Esta rodada valida o caminho critico de pesquisa unificada antes do fechamento
da release. As consultas foram executadas com `page_size=2`, timeout de 45
segundos, SSL habilitado e `trust_env=False`, sem cookies exportados, login,
captcha, proxy de contorno ou sessao de navegador.

Os resultados sao observacoes da rede no momento da execucao. Nao representam
garantia de disponibilidade, cobertura integral ou estabilidade permanente das
fontes publicas.

## Busca textual agregada

Consulta: `desconsideracao da personalidade juridica`.

| Grupo | Fontes chamadas | Resultados normalizados | Erros |
| --- | --- | ---: | --- |
| Estaduais JSON/SOLR | `tjpb_pje_jurisprudencia`, `tjpa_jurisprudencia_bff`, `tjrs_solr` | 6 | 0 |
| eproc/federal | `tjrj_eproc_jurisprudencia`, `tjsc_eproc_jurisprudencia`, `trf5_jurisprudencia`, `cjf_jurisprudencia` | 8 | 0 |

Todas as sete fontes foram efetivamente consultadas, retornaram resultados
canonicamente normalizados e apareceram como `searched` no
`routing_summary`. Nenhuma fonte foi erroneamente classificada como falha.

## Rodada padrao nacional

Tambem foi executada a mesma consulta sem informar `sources`, usando o conjunto
padrao completo. O cliente selecionou e consultou **31 fontes** das categorias
jurisprudenciais registradas, retornando **22 resultados normalizados**.

As cinco falhas foram preservadas em `errors`:

| Fonte | Diagnostico |
| --- | --- |
| `bnp_pangea` | HTTP 400 para esta expressao; o contrato BNP exige uma combinacao de consulta aceita pelo endpoint |
| `stf_informativo` | falha de verificacao SSL local |
| `stf_juris` | falha de verificacao SSL local |
| `stj_scon` | controle de acesso da fonte |
| `tjsp_cjsg` | captcha ou outro controle de acesso |

Essas falhas nao retiram as fontes do conjunto unificado. O resultado parcial
continua utilizavel e auditavel porque cada fonte chamada aparece como
`searched_sources` ou em `errors`. Fontes de processo, comunicacoes e fontes
candidatas nao sao chamadas por essa selecao padrao.

## Busca por numero CNJ

Consulta: `0802253-46.2017.8.15.2003`, enviada tambem no filtro `number`.

- `tjpb_pje_jurisprudencia` e `tjrs_solr` foram consultados porque declaram o
  filtro `number`.
- `tjpa_jurisprudencia_bff` foi pulado com
  `identifier_filter_not_supported`, pois seu contrato atual declara busca
  textual, mas nao filtro por numero.
- O resultado agregado foi zero, sem erro e sem falso positivo.

Esse comportamento e intencional: uma busca unificada nao deve transformar uma
semelhanca textual em correspondencia exata de processo. O campo
`skipped_sources` preserva a razao para humanos e agentes de IA.

## Reproducao controlada

```powershell
@'
from nanojuris.client import NanoJurisClient
from nanojuris.config import NanoJurisConfig

client = NanoJurisClient(
    config=NanoJurisConfig(timeout=45, rate_limit_interval=0, trust_env=False)
)
payload = client.search_many(
    "desconsideracao da personalidade juridica",
    sources=["tjpb_pje_jurisprudencia", "tjpa_jurisprudencia_bff", "tjrs_solr"],
    page_size=2,
)
print(payload["searched_sources"])
print(payload["skipped_sources"])
print(payload["errors"])
print(payload["total_returned"])
'@ | .\.venv\Scripts\python.exe -
```

Testes live sao opt-in e nao substituem fixtures offline. Nunca versionar
tokens, cookies, respostas integrais ou dados de sessao.
