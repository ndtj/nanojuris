# Contrato de fonte — `tjrj_banco_sentencas`

## Fonte oficial

`GET https://portaltj.tjrj.jus.br/documents/10136/18187/banco-sentencas.pdf`

O corpo deve ser PDF (`%PDF-`) e permanece limitado a 5 MB e 300 paginas.
Cada consulta faz uma leitura bounded; nao existe paginacao remota nem total
autoritativo.

## Contrato

- Metodo e rota: `GET /documents/10136/18187/banco-sentencas.pdf`.
- Resposta aceita: PDF oficial com assinatura `%PDF-`, no maximo 5 MiB e 300
  paginas.
- A busca e uma janela local sobre o PDF; a fonte nao declara total
  autoritativo nem cursor remoto.
- Erros HTTP, timeout, TLS, PDF invalido e schema inesperado permanecem estados
  explicitos e nunca sao convertidos em resultado vazio.

## Identidade

Registros sao aceitos somente quando o texto do PDF contem numero CNJ e o
escopo oficial da colecao permite inferir `authority=TJRJ`, `branch=state`,
`degree=first`, `instance=first`, `collection=TJRJ_BANCO_SENTENCAS` e
`document_type=sentenca`.

## Documentos observados

Anotacoes sao aceitas apenas para HTTPS no host `www4.tjrj.jus.br`, sob
`/AtosOficiais/bancodesentencas/`, com extensao `.doc` ou `.docx`. A resposta e
validada pelo pipeline compartilhado. HTTP 503, 403, 429, timeout, TLS ou
schema invalido permanecem estados explicitos.

## Filtros e limites

Termo, frase exata, numero e `without_words` sao pos-filtros locais. Grau,
instancia, ramo, autoridade e colecao sao filtros de escopo. Classes, datas,
relator, orgao e partes nao sao suportados. A ordem e a do PDF e o limite
local e 100 registros por consulta.

## Dados

Cada registro preserva `source`, numero CNJ, autoridade, ramo, grau, instancia,
colecao, tipo documental, resumo extraido, URL documental observada, `raw` e
`SourceTrace`. Ausencia de texto ou de documento nao e preenchida por
inferencia. A colecao e curada e nao representa o acervo integral de primeiro
grau do TJRJ.

## Estados

O indice PDF publicamente alcancavel e classificado como `partial` quando os
links documentais observados retornam indisponibilidade. `source_unavailable`,
`access_control_required`, `rate_limited`, `timeout`, `tls_error` e
`schema_invalid` sao mantidos no trace. Somente uma declaracao oficial de
ausencia poderia produzir `authoritative_empty`.

## Federacao

`supports_unified_search=false` e `opt_in_unified_search=true`. A fonte nao
deve ser promovida para o rollout padrao sem nova evidencia documental e
revisao humana da natureza curada da colecao.

## Fixtures

Fixtures de contrato: `tests/fixtures/tjrj_banco_sentencas_index.json`,
`tjrj_banco_sentencas_empty.json`, `tjrj_banco_sentencas_blocked.json` e
`tjrj_banco_sentencas_schema_invalid.json`.

## MCP e diagnostico

O provider pode ser consultado explicitamente por CLI, MCP e Studio. O
diagnostico deve exibir a natureza curada, `total_unknown`, o estado de cada
documento e o trace do PDF. Ele nao deve apresentar a colecao como CJPG
completa nem seguir links fora da allowlist.

## Proximos passos

1. Repetir a verificacao bounded do indice somente conforme a janela de
   frescor operacional.
2. Reavaliar um documento oficial quando o host deixar de responder 503.
3. Manter `opt_in_only` ate revisao humana da natureza curada e da retencao.
4. Nao habilitar cobertura geral CJPG com base neste indice selecionado.
