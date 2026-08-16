# TJCE SJURIS

Status: `runtime_live_validated` · papel: `primary_textual_jurisprudence`

Provider para a busca pública de jurisprudência do Sistema SJURIS do Tribunal
de Justiça do Ceará. Esta fonte é distinta do `tjce_cjsg`: o SJURIS é uma SPA
Angular com gateway REST e devolve resultados do PJe, enquanto o CJSG é a
superfície e-SAJ legada.

## Fonte e contrato confirmado

- Portal oficial: <https://sjuris.tjce.jus.br/>
- Gateway observado pelo portal: `https://gateway.tjce.jus.br/sjuris/api/v1`
- Busca: `POST /jurisprudencia/?page={pagina_zero_based}&size={tamanho}`
- Corpo: JSON UTF-8 compacto, com `dataJulgamento`, `busca`, `ordenacao`,
  `nomeDocumento`, `baseDocumento` e `origem`.
- Resposta: envelope JSON com `pagina.content`, `totalElements`,
  `totalPages`, `number`, `size`, `first`, `last` e `empty`.

Payload reproduzido na interface pública:

```json
{
  "dataJulgamento": [],
  "busca": "transporte aereo dano moral",
  "ordenacao": "order1",
  "nomeDocumento": ["ACÓRDÃO"],
  "baseDocumento": ["2º GRAU"],
  "origem": ["PJE"]
}
```

O transporte HTTP usa páginas zero-based. A API de alto nível usa páginas
one-based e converte `page=1` para `page=0` no gateway.

## Dados entregues

Cada item pode conter `id`, `idDocumento`, processo, classe, órgão julgador,
magistrado, datas, ementa, conteúdo, partes, assuntos e outros campos brutos.
O provider preserva o item completo em `raw`.

- `summary`: `ementa`.
- `full_text`: `conteudo`, quando a fonte o devolve.
- `judgment_date`: `dataJulgamento`, normalizada de `[ano, mes, dia]` para ISO.
- `publication_date`: `dataPublicacao`; `n/d` permanece ausente no campo
  canônico e preservado no bruto.
- `raw.pdfAutenticadoBase64`: PDF inline quando presente no item.
- `raw.pdf_content_sha256` e `raw.pdf_response_bytes`: calculados somente
  quando o base64 é válido e contém bytes.

O texto integral é inline no resultado e foi confirmado live. O campo PDF
também foi observado no contrato da resposta, mas pode estar ausente em itens
individuais; não há URL pública de detalhe confirmada.

## Filtros e limites

Declarados e mapeados:

- texto livre;
- `exact_phrase`, `all_words`, `any_words` e `without_words`, compostos com
  os operadores visíveis `e`, `ou` e `não`;
- tipos documentais conhecidos: acórdão, decisão monocrática e súmula;
- `source_origins`, quando a origem aceita pela interface for informada.

Ainda não declarados como suportados:

- data de julgamento;
- relator;
- órgão julgador;
- seleção de base documental.

Esses filtros aparecem na interface, mas o payload não vazio ainda não foi
reproduzido. O NanoJuris registra a limitação em `SourceTrace` e no catálogo.

O tamanho remoto foi validado com `size=5` e `size=20`. Requisições com
`size=50` e `size=100` retornaram HTTP 504 na validação de 2026-08-16, por
isso o provider limita o tamanho efetivo a 20. O tamanho pedido continua no
trace.

## Documentos e detalhe

`supports_full_text=True` e `full_text_access=inline`. O provider não inventa
`get_document()` ou `get_decisions()`: ambos permanecem sem implementação até
que uma rota de detalhe independente seja reproduzida. Um PDF base64 inline é
preservado em `raw`; isso não é apresentado como download por URL.

## Erros e rastreabilidade

- HTTP 401/403: `AccessControlRequiredError`.
- HTTP 400/422: `QueryRejectedError`.
- HTTP 429: `RateLimitDetectedError`.
- HTTP 5xx ou falha de rede: `SourceUnavailableError`.
- envelope sem `pagina.content` ou JSON inválido: `ParserContractChangedError`.

Cada página inclui `SourceTrace` com endpoint, payload, URL final, status HTTP,
content-type, hash da resposta, bytes, latência e limitações observadas.

## Validação e testes

- Fixture: `tests/fixtures/tjce_sjuris_results.json`.
- Testes: `tests/test_tjce_sjuris.py`.
- Evidência live: `docs/validation/runs/20260816T111431Z-tjce-sjuris-search.json`.
- Consulta de validação: `transporte aereo dano moral`.
- Resultado observado: total 266; 5 itens na página 1; 5 IDs novos na página 2;
  texto integral presente nos 5 itens da página 1.

O provider está implementado e validado para busca textual pública, mas ainda
não é Gold: filtros avançados, disponibilidade do PDF por item e uma rota de
detalhe independente permanecem pontos de aprofundamento.

## Identidade E Escopo

- `source_id`: `tjce_sjuris`.
- Fonte: SJURIS do Tribunal de Justiça do Ceará.
- Escopo: jurisprudência textual pública, com resultados do PJe observados na
  consulta e possibilidade de integração progressiva de outras bases.
- Fora do escopo: consulta processual geral, movimentações e comunicações.

## Contrato HTTP Observado

A rota operacional reproduzida é `POST /jurisprudencia/` no gateway público,
com `page` zero-based, `size` e corpo JSON UTF-8 compacto. A resposta é um
envelope com `pagina.content`; rotas de catálogo são públicas, mas não fazem
parte da busca executável deste provider.

## Modelo De Dados

O identificador é formado pelo `id` da fonte, com fallback para `idDocumento`.
Ementa, conteúdo, datas, processo, órgão, magistrado e o item bruto são
preservados conforme o mapeamento descrito acima. Nenhuma data é inferida a
partir de outra data.

## Estados E Falhas

Sucesso, vazio real, 400/422, 401/403, 429, 5xx e mudança de envelope têm
classificações distintas no runtime. Timeout, bloqueio e falha de contrato não
são retornados como zero resultados.

## Evidencias, Fixtures E Testes

O fixture local reproduz o envelope Spring-style, texto integral, data em vetor
e PDF inline. A suíte cobre payload, paginação, identidade, datas, hash do PDF,
raiz inválida e todos os grupos de status HTTP. A evidência live está no JSON
referenciado na seção de validação.

## Implementacao E Capacidades

- Módulo: `src/nanojuris/providers/tjce_sjuris.py`.
- Classe: `TjceSjurisProvider`.
- Interfaces: Python, CLI, busca unificada, Studio e MCP.
- Catálogo: rota observada, normalização ainda não exposta como catálogo
  executável (`supports_catalog=False`).
- Rate limit, timeout, SSL e User-Agent usam a configuração compartilhada.

## MCP E Agentes

Agentes devem consultar o contrato antes da fonte e informar que o texto é
inline, que o PDF pode estar ausente por item e que não existe detalhe
independente validado. Os resultados devem carregar a fonte e o `SourceTrace`.

## Promocao

O provider pode ser usado para busca textual pública e permanece em nível
Silver. Gold depende de evidência adicional para filtros de data/relator,
disponibilidade do PDF por item e uma rota de detalhe independente, quando a
fonte a oferecer.

## Proximos passos

1. Capturar payload não vazio para data, relator, órgão e base.
2. Revalidar a disponibilidade de `pdfAutenticadoBase64` em uma amostra maior.
3. Investigar uma rota de detalhe pública sem inferir URLs a partir de campos.
4. Implementar catálogo normalizado somente após reproduzir suas respostas.
