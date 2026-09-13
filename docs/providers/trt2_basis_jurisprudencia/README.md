# Contrato de fonte: `trt2_basis_jurisprudencia`

## Identidade

| Campo | Valor |
| --- | --- |
| Autoridade | TRT2 |
| Ramo | `labor` |
| Grau/instância | `second` |
| Coleção | `CJSG_CURATED_BULLETIN` |
| Host oficial | `basis.trt2.jus.br` |
| Escopo DSpace | `123456789/16181` |

## Busca

`GET https://basis.trt2.jus.br/discover` com:

```text
rpp=100
etal=0
group_by=none
scope=123456789/16181
query=<texto, frase exata ou número>
page=<página zero-based>
```

O parser aceita apenas cartões `.ds-artifact-item` cujo título corresponda a
“Boletim de Jurisprudência do TRT2”. O identificador é o último segmento
numérico do link `/handle/123456789/<id>`. O número CNJ trabalhista é extraído
quando presente no trecho indexado. A data `DD/MM/YYYY` do bloco informativo é
normalizada para ISO.

`total_known` é sempre `false`: o DSpace não fornece total confiável depois da
seleção por título. Uma página sem cartões é `unconfirmed_empty` e mantém
`is_complete=false`; somente uma página com registros sem página seguinte é
considerada a última janela observada. `is_complete` depende da paginação observada. A resposta
preserva `SourceTrace`, hash, bytes, latência e URL final.

## Documento

O link `/bitstream/handle/...` deve permanecer no host oficial e responder com
bytes iniciados por `%PDF`. O limite é 40 MiB. A extração usa o pipeline
canônico de documentos (`trt2_basis_jurisprudencia.pdf`) e preserva o PDF bruto,
MIME, URL, hash e rastreio. PDF vazio, MIME incompatível ou resposta externa
produzem status de extração/acesso explícito e não uma decisão vazia.

## Erros e limitações

- timeout/TLS/rede: `source_unavailable`;
- 403/401/407/451: `access_control_required`;
- 429: `rate_limited`;
- não-2xx restante: `source_unavailable`;
- HTML sem cartões/página inesperada: `schema_invalid`;
- host ou esquema fora da allowlist: consulta rejeitada.

Esta é uma publicação curada de boletins, não o índice completo de acórdãos do
PJe. Classe, relator, órgão e datas de julgamento não são filtros comprovados.
Chamadas públicas são bounded; não se usa CAPTCHA solver, rotação de proxy,
replay de cookies/tokens ou relaxamento de TLS.
