# TJES Turma Recursal

Status: `implemented; live_validated; federation_enabled`.

## Identidade

Fonte oficial do Tribunal de Justica do Espirito Santo. O provider consulta
exclusivamente a collection publica `turma_recursal_legado`, que representa
decisoes das Turmas Recursais. Esta superficie e independente de CJPG (`pje1g`)
e CJSG (`pje2g`) e nunca e contada como uma dessas collections.

## Contrato

- Portal: `https://sistemas.tjes.jus.br/consulta-jurisprudencia/`.
- Rota: `GET /consulta-jurisprudencia/api/search`.
- Parametros: `core=turma_recursal_legado`, `q`, `page`, `per_page`.
- Limite local conservador: `per_page <= 20`.
- Paginacao: offset, com `total`, `page` e `per_page` quando informados.
- Texto: inteiro teor inline no campo `cont_ementa`.

## Dados canonicos

`id` e usado como identificador estavel; `num_processo` como numero; `classe_processo`
como classe; `nome_juiz` como relator; `orgao_julgador` como orgao; o primeiro
valor de `data_julgamento` como data de julgamento. O payload original e todos
os campos desconhecidos permanecem em `raw`. O resultado usa
`collection=TURMA_RECURSAL`, `degree=specialized` e
`instance=turma_recursal` para impedir mistura semantica.

## Estados e limites

- Pagina vazia com `total=0` e uma resposta vazia valida.
- HTTP 401/403, 429, 5xx, timeout, resposta nao-JSON e schema drift geram
  estados de erro explicitos; nunca sao convertidos em lista vazia.
- O provider nao contorna CAPTCHA, WAF, login ou limites de frequencia.
- A disponibilidade publica nao equivale a autorizacao de redistribuicao em
  escala. Revisao de reuso, licenca e retencao e gate humano separado.

## Fixtures

- `tests/fixtures/tjes_turma_recursal_success.json`
- `tests/fixtures/tjes_turma_recursal_empty.json`
- `tests/fixtures/tjes_turma_recursal_invalid.json`
- `tests/fixtures/tjes_turma_recursal_schema_drift.json`

As fixtures usam IDs, nomes e texto sinteticos; nenhum corpo live e persistido.

## Uso e federacao

```python
from nanojuris import NanoJurisClient
from nanojuris.config import NanoJurisConfig

client = NanoJurisClient(NanoJurisConfig(unified_opt_in_sources=("tjes_turma_recursal",)))
page = client.search("responsabilidade civil", source="tjes_turma_recursal")
```

`supports_unified_search` e `True` e `opt_in_unified_search` e `False` para o
runtime local/federado. A superficie e textual, possui fixtures reproduziveis
e chamada live bounded validada. Release, redistribuicao e deploy permanecem
fora do escopo desta promocao.

## MCP

A fonte pode ser consultada explicitamente por `source="tjes_turma_recursal"`.
O `SourceTrace` e o estado de completude devem ser exibidos ao consumidor.

## Proximos passos

- repetir smoke bounded em cada ciclo;
- acompanhar schema e paginacao;
- acompanhar schema e paginacao;
- promover somente o runtime local/federado; release e deploy exigem etapa
  operacional separada.

## Validacao live

Em 2026-09-05, a rota oficial respondeu HTTP 200 para
`core=turma_recursal_legado`, `q=dano moral`, `page=1`, `per_page=2`, com
documentos textuais e total declarado. O corpo foi analisado em memoria; a
evidencia persistida contem apenas metadados e hash. Repetir com
`NANOJURIS_RUN_LIVE=1`.

## Checklist

- [x] rota publica e core separados reproduzidos;
- [x] parser, canonicalizacao, trace e classificacao de erros;
- [x] fixtures sanitizadas e testes offline;
- [x] teste live bounded e gated;
- [x] decisao do operador: nenhuma autorizacao judicial ou gate interno
  adicional e exigido para o uso tecnico local/federado da fonte publica;
- [x] federacao padrao do runtime habilitada; release/deploy permanecem fora
  do escopo.
