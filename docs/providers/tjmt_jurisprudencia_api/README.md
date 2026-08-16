# TJMT Jurisprudencia API

Status: `runtime_live_validated` · papel: `primary_textual_jurisprudence`

Provider para a busca pública de jurisprudência do Tribunal de Justiça de Mato
Grosso. A fonte é uma SPA pública cujo `config.json` entrega em runtime a base
da API e o valor de aplicação usado pelo frontend. O NanoJuris não fixa esse
valor, não o persiste e não o trata como credencial de usuário.

## Identidade E Escopo

- `source_id`: `tjmt_jurisprudencia_api`.
- Fonte: Tribunal de Justiça de Mato Grosso.
- Escopo: jurisprudência textual pública, com acórdãos e decisões
  monocráticas retornados pela API do portal.
- Fora do escopo: consulta processual geral, movimentações e comunicações.

## Contrato HTTP Observado

- Portal oficial: <https://jurisprudencia.tjmt.jus.br/>
- Configuração pública: `GET /assets/config/config.json`.
- Busca: `GET {api_url}/api/consulta/Acordao`.
- Tipo alternativo observado: `GET {api_url}/api/consulta/Decisao`.
- Inteiro teor inline: campo `Documento` HTML da coleção de resultados.
- Rota de relatório observada: `/VisualizaRelatorio/RetornaDocumentoAcordao`;
  uma carga independente estável ainda não foi validada pelo provider.

Parâmetros reproduzidos:

```text
filtro.isBasica=false
filtro.indicePagina=1-based
filtro.quantidadePagina=page_size
filtro.tipoConsulta=Acordao|Decisao
filtro.termoDeBusca=<texto>
filtro.periodoDataDe=<dd/mm/aaaa>
filtro.periodoDataAte=<dd/mm/aaaa>
filtro.tipoBusca=1
filtro.ordenacao.ordenarPor=DataDecrescente
filtro.ordenacao.ordenarDataPor=Julgamento
filtro.thesaurus=false
```

O valor público `api_hellsgate_token` é lido do JSON de configuração e enviado
como parâmetro `token`, exatamente como o frontend observado. O seu valor não
é gravado em código, fixtures, trace, evidência ou documentação.

## Dados Retornados

Cada item contém `Id`, `Tipo`, `Conteudo`, `Documento` e `Processo`, além de
facetas e metadados brutos. O provider preserva o item completo em `raw`.

- `summary`: texto de `Conteudo`, com HTML removido.
- `full_text`: texto extraído de `Documento`, quando presente.
- `raw.document_html`: HTML original do campo `Documento`.
- `number`: `Processo.NumeroUnicoFormatado`.
- `rapporteur`: `Processo.NomeRelator`.
- `judging_body`: `Processo.DescricaoCamara` em `raw`.
- `judgment_date`: `Processo.DataJulgamento`, normalizada para ISO.
- `publication_date`: `Processo.DataPublicacao`, normalizada para ISO.
- `status`: `Processo.Julgamento`.

Na validação live de 2026-08-16, a consulta retornou 5/5 itens com `Documento`
HTML e extração textual. O documento medido tinha aproximadamente 28 mil
caracteres extraídos, enquanto a ementa tinha aproximadamente 5,6 mil
caracteres. Isso confirma que os campos não são equivalentes.

## Filtros E Paginação

Suportados e enviados ao contrato reproduzido:

- texto livre;
- `published_from` e `published_to`, convertidos para `dd/mm/aaaa`;
- `types` para `acordao` ou `decisao_monocratica`;
- `order_by` para ordenação já observada.

O índice remoto é 1-based. O provider preserva `page` e `page_size` na API
unificada e limita o tamanho efetivo a 100, que é o limite aceito pelo modelo
de consulta do NanoJuris. O total de acórdãos é obtido de
`CountAcordaoDocumento`, sem confundi-lo com `CountTotal`, que agrega outras
categorias.

Filtros de relator, órgão julgador, julgamento, booleanos avançados e
`updated_from/to` ainda não são declarados como suportados. Quando recebidos,
o roteamento registra a limitação; eles não são descartados silenciosamente.

## Inteiro Teor E Documentos

`supports_full_text=True` e `full_text_access=inline`. O texto é extraído do
HTML público entregue na própria busca; o HTML original permanece em `raw`.
Isso é diferente de uma URL disponível e não depende de chamada N+1.

`get_decisions()` permanece sem implementação até que a rota de relatório
independente seja reproduzida com identificador, parâmetros e resposta estáveis.

## Estados E Falhas

- HTTP 401/403: `AccessControlRequiredError`.
- HTTP 400/422: `QueryRejectedError`.
- HTTP 429: `RateLimitDetectedError`.
- HTTP 5xx ou falha de rede: `SourceUnavailableError`.
- JSON sem coleção esperada: `ParserContractChangedError`.

Cada página possui `SourceTrace` com endpoint, consulta sem o token, URL final
sanitizada, status HTTP, content-type, hash da resposta, bytes, latência e
limitações. O token nunca é incluído no trace.

## Evidencias, Fixtures E Testes

- Fixture: `tests/fixtures/tjmt_jurisprudencia_results.json`.
- Testes: `tests/test_tjmt_jurisprudencia_api.py`.
- Evidência live: `docs/validation/runs/20260816T173000Z-tjmt-jurisprudencia-api-search.json`.
- Consulta: `transporte aereo dano moral`.
- Resultado: HTTP 200, 7.578 acórdãos reportados, 5 itens na primeira página,
  5/5 com documento HTML e página 2 com IDs novos, embora possa existir
  sobreposição dinâmica entre janelas.

O provider está implementado e validado para busca textual pública, em nível
Silver. Gold depende de filtros adicionais reproduzidos, estabilidade de
paginação em várias rodadas e validação de uma rota de detalhe independente.

## Implementação E Integração

- Módulo: `src/nanojuris/providers/tjmt_jurisprudencia_api.py`.
- Classe: `TjmtJurisprudenciaApiProvider`.
- Interfaces: Python, CLI, busca unificada, Studio e MCP.
- Catálogo executável: ainda não exposto; `supports_catalog=False`.
- Configuração HTTP, SSL, timeout, User-Agent e rate limit são compartilhados.

## MCP E Agentes

Agentes devem informar que a fonte oferece texto integral inline, que o HTML
bruto é preservado e que a rota independente de detalhe ainda não foi validada.
401, 403, timeout e mudança de contrato devem ser apresentados como limitações
da fonte, nunca como ausência de jurisprudência.

## Promocao

O provider pode ser usado para pesquisa textual, extração de ementa e inteiro
teor inline. Para Gold, completar filtros de relator/órgão/data, verificar a
estabilidade de página profunda e reproduzir, ou formalmente rejeitar, o
contrato documental independente.

## Proximos passos

1. Reproduzir filtros de relator, órgão julgador e julgamento.
2. Repetir paginação profunda em rodadas controladas e medir sobreposição.
3. Validar ou rejeitar formalmente a rota de relatório independente.
