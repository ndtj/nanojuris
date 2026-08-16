# `stf_juris`

## Identidade

- Fonte oficial: pesquisa publica de jurisprudencia do STF.
- Categoria: `court_jurisprudence`.
- Familia tecnica: `api_json_jurisprudencia_superior`.
- Uso preferencial: acordaos do STF quando a API JSON responder em sessao
  publica limpa.
- Nivel atual esperado: 3.

## Contrato observado

O HAR `jurisprudencia.stf.jus.br2.har`, analisado em 06/08/2026, registrou uma
busca publica por `infanticidio` no frontend oficial do STF.

Endpoint principal observado:

```text
POST https://jurisprudencia.stf.jus.br/api/search/search
Content-Type: application/json
Accept: application/json, text/plain, */*
Origin: https://jurisprudencia.stf.jus.br
Referer: https://jurisprudencia.stf.jus.br/pages/search
```

O corpo da requisicao segue formato proximo a Elasticsearch:

```text
query.bool.filter[].query_string.query
query.bool.filter[].query_string.fields
_source
size
from
sort
highlight
track_total_hits
```

Campos de busca relevantes observados:

- `titulo.plural`;
- `processo_codigo_completo.plural`;
- `ementa_texto.plural`;
- `decisao_texto.plural`;
- `sumula_texto.plural`;
- `documental_tese_texto.plural`;
- `documental_tese_tema_texto.plural`;
- `documental_legislacao_citada_texto.plural`;
- `documental_jurisprudencia_citada_texto.plural`;
- `partes_lista_texto.plural`;
- `ministro_facet.plural`;
- `orgao_julgador.plural`.

Campos de retorno promovidos pelo provider:

- `base`;
- `id`;
- `titulo`;
- `processo_codigo_completo`;
- `processo_numero`;
- `processo_classe_processual_unificada_sigla`;
- `processo_classe_processual_unificada_extenso`;
- `relator_processo_nome`;
- `relator_acordao_nome`;
- `ministro_facet`;
- `orgao_julgador`;
- `julgamento_data`;
- `publicacao_data`;
- `ementa_texto`;
- `acordao_ata`;
- `decisao_texto`;
- `inteiro_teor_url`;
- `acompanhamento_processual_url`;
- `dje_url`;
- `partes_lista_texto`;
- `documental_legislacao_citada_texto`;
- `documental_indexacao_texto`;
- `documental_assunto_texto`;
- `documental_tese_texto`;
- `documental_tese_tema_texto`;
- `is_repercussao_geral`.

## Resposta JSON

A resposta observada possui raiz com:

```text
result
search_id
```

Dentro de `result`, o contrato usado pelo provider e:

```text
hits.total.value
hits.hits[]._source
hits.hits[].highlight
aggregations.<nome>.buckets[]
```

A fixture publica `tests/fixtures/stf_juris_infanticidio.json` foi reduzida para
dois resultados e preserva o formato real de `hits`, `highlight` e
`aggregations`.

## Dados

O contrato observado separa tres camadas de conteudo:

| Grupo | Campos de origem | Uso canonico |
| --- | --- | --- |
| Identificacao | `id`, `base`, `titulo`, `processo_codigo_completo`, `processo_numero` | identificador estavel, numero processual e titulo exibivel |
| Classe e orgao | `processo_classe_processual_unificada_sigla`, `processo_classe_processual_unificada_extenso`, `orgao_julgador` | classe, tipo decisorio e orgao julgador |
| Relatoria | `relator_processo_nome`, `relator_acordao_nome`, `ministro_facet` | relator preferencial e faceta de ministro |
| Datas | `julgamento_data`, `publicacao_data` | `judgment_date` e `publication_date`, preservando valor bruto quando formato divergir |
| Conteudo textual | `ementa_texto`, `decisao_texto`, `sumula_texto`, `documental_tese_texto` | ementa, decisao, sumula ou tese conforme a base retornada |
| Contexto documental | `partes_lista_texto`, `documental_legislacao_citada_texto`, `documental_jurisprudencia_citada_texto`, `documental_indexacao_texto`, `documental_assunto_texto` | campos auxiliares em `raw` e campos canonicos quando houver correspondencia direta |
| URLs | `inteiro_teor_url`, `acompanhamento_processual_url`, `dje_url` | links oficiais preservados com access status independente |
| Facetas | `aggregations.<nome>.buckets[]` | catalogos de filtros e diagnostico, nao resultados decisorios |

Regras de normalizacao:

- `publication_date` deve vir de `publicacao_data`, nunca de data de
  atualizacao da coleta;
- `judgment_date` deve vir de `julgamento_data`;
- `source_updated_at` e `retrieved_at` devem permanecer separados quando
  existirem;
- `highlight` serve para explicar por que o resultado foi retornado, mas nao
  substitui ementa, decisao ou texto integral;
- `inteiro_teor_url` nao prova disponibilidade do documento; acesso ao inteiro
  teor deve ser validado em rota propria.

## Estados de resposta

| Estado | Como o provider deve tratar |
| --- | --- |
| Resultado publico JSON | Retornar `SearchPage` com `CanonicalDecision` derivavel. |
| Zero resultado JSON | Retornar `SearchPage` vazia quando `hits.hits` vier vazio. |
| AWS WAF challenge | Levantar `AccessControlRequiredError`; nao tentar bypass. |
| Falha SSL local | Levantar `SourceUnavailableError` com diagnostico explicito. |
| HTTP 429 | Levantar `RateLimitDetectedError`. |
| HTTP 5xx | Levantar `SourceUnavailableError`. |
| JSON fora do contrato | Levantar `ParserContractChangedError`. |

## Teste de conexao limpa

Em 06/08/2026, uma chamada limpa com `requests` e verificacao SSL habilitada
falhou neste ambiente com erro de cadeia de certificado:

```text
CERTIFICATE_VERIFY_FAILED unable to get local issuer certificate
```

Um teste diagnostico com verificacao SSL desabilitada apenas para investigacao
retornou:

```text
HTTP 202
x-amzn-waf-action: challenge
Content-Type: text/html
corpo vazio
```

Conclusao: o contrato da API existe e foi observado por HAR, mas o acesso
automatizado limpo pode exigir validacao AWS WAF. A NanoJuris deve reportar esse
estado sem contorno.

## Inteiro teor e portal STF

O campo `inteiro_teor_url` observado no HAR apontou para:

```text
https://portal.stf.jus.br/jurisprudencia/obterInteiroTeor.asp?idDocumento=<id>
```

Teste limpo em 06/08/2026:

- com verificacao SSL habilitada: falha local de certificado;
- com verificacao SSL desabilitada apenas para diagnostico: HTTP 403.

Por isso `stf_juris` preserva a URL do inteiro teor, mas ainda nao promove
`get_document` nem promete download/leitura do documento.

O HAR `portal.stf.jus.br.har` nao trouxe uma chamada util de jurisprudencia para
o provider. As entradas relevantes eram chamadas externas de YouTube/analytics,
sem contrato STF reutilizavel.

## MCP e agentes

Recomendacao: fonte estrategica de altissimo valor, mas com risco operacional
alto. O agente deve:

- consultar `source_contracts("stf_juris")` antes da busca;
- usar `page_size` pequeno;
- explicar falha SSL e AWS WAF como estado da fonte, nao como ausencia de
  jurisprudencia;
- preservar `SourceTrace`;
- nao prometer inteiro teor enquanto o portal retornar HTTP 403 em sessao limpa;
- sugerir fontes alternativas, como `bnp_pangea`, quando o objetivo for
  repercussao geral ou precedentes qualificados STF.

## Fixtures esperadas

- `tests/fixtures/stf_juris_infanticidio.json` implementada;
- `tests/fixtures/stf_juris_empty.json` implementada;
- `tests/fixtures/stf_juris_waf.html` implementada;
- futura fixture de bases adicionais quando o frontend expuser `decisoes`,
  `sumulas` ou `informativos`;
- futura fixture de inteiro teor somente se a URL publica responder sem WAF,
  captcha, login, cookie herdado ou bypass.

## Proximos passos

- [x] Capturar HAR publico da API JSON.
- [x] Reduzir headers ao minimo necessario.
- [x] Implementar parser puro para contrato JSON observado.
- [x] Adicionar diagnostico de AWS WAF e SSL.
- [x] Declarar capabilities e integrar ao cliente padrao.
- [x] Cobrir pagina vazia e resposta AWS WAF com fixtures offline.
- [ ] Validar bases adicionais do frontend.
- [ ] Criar teste live opt-in para registrar `AccessControlRequiredError` quando
  a origem exigir WAF.
- [ ] Promover inteiro teor apenas se houver resposta publica limpa sem HTTP
  403.

## Validacao live 2026-08-11

Depois de corrigir o provider para respeitar `NanoJurisConfig.verify_ssl`, a
chamada com SSL desabilitado apenas para diagnostico chegou a resposta da
fonte e foi classificada como `AccessControlRequiredError` por desafio AWS WAF.
Isso confirma que a falha SSL local e distinta do controle de acesso. Nao ha
bypass nem promocao de inteiro teor.

Veja a matriz completa em
[live-validation-2026-08-11.md](https://github.com/ndtj/nanojuris/blob/main/docs/live-validation-2026-08-11.md).
