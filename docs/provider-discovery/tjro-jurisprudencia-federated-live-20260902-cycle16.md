# TJRO — smoke federado live (ciclo 16)

Data: `2026-09-02` · chamada pública bounded · corpo da resposta não retido.

Após o registro padrão do provider, `NanoJurisClient.search_many` foi executado
com `sources=["tjro_jurisprudencia"]`, texto `responsabilidade civil` e
`page_size=1`.

| Fonte | HTTP | Registros retornados | Total remoto | Paginação | Erros |
| --- | ---: | ---: | ---: | --- | --- |
| `tjro_jurisprudencia` | 200 | 1 | 1.905.968 | offset | nenhum |

O resultado foi canonicalizado e classificado como `searched`/`valid`. Esta
evidência confirma a integração do TJRO na federação padrão, mas não certifica
filtros ainda não contratados (classe, órgão, grau e tipo), nem autoriza deploy.
