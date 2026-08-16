# TJTO Jurisprudencia 4.0

Status: `runtime_implemented; live contract replayed` | papel: `primary_textual_jurisprudence`

Provider para a pesquisa publica de jurisprudencia do Tribunal de Justica do
Estado do Tocantins. A fonte entrega ementas e metadados em HTML e permite
carregar o inteiro teor sob demanda.

## Identidade E Escopo

- `source_id`: `tjto_jurisprudencia`.
- Portal oficial: <https://jurisprudencia.tjto.jus.br/>.
- Escopo: acordaos, decisoes monocraticas e sentencas expostos pela
  Jurisprudencia 4.0.
- Fora do escopo: consulta processual geral e comunicacoes judiciais.

## Contrato HTTP Observado

- Busca inicial: `GET /consulta.php?q=<termo>`.
- Busca paginada reproduzida: `POST /consulta.php` com formulario URL encoded.
- Pagina: `start`, zero-based, e `rows`, tamanho da janela.
- Texto: `q`; busca restrita a ementa: `soementa=on`.
- Corpus: `tipo_decisao_acordao`, `tipo_decisao_sentenca` e
  `dec_monocrativa_is2G_true`.
- Instancia: `tip_criterio_inst` (`1`, `2` ou vazio).
- Ordenacao: `tip_criterio_data` (`RELEV`, `DESC`, `ASC`).
- Numero de processo: `numero_processo`.
- Filtros de formulario observados: `fq_classe[...]`, `fq_assuntos[...]`,
  `fq_competencia[...]` e `fq_magistrado[...]`.
- O portal exige User-Agent de navegador como parte do contrato HTTP publico;
  isso nao envolve credencial de usuario.

## Dados Retornados

O card HTML fornece processo, classe, tipo de julgamento, assuntos,
competencia, relator/juiz, data de autuacao, data de julgamento e ementa.
O `raw.card_html` preserva o card original.

- `id`: `tjto-jurisprudencia-<uuid>` quando o uuid esta presente.
- `number`: numero CNJ encontrado no cabecalho do card.
- `summary`: texto apos `EMENTA`.
- `judgment_date`: data de julgamento normalizada para ISO.
- `raw.filing_date`: data de autuacao original.
- `raw.case_class`, `raw.subject`, `raw.competence` e `raw.document_uuid`.
- Total: contador textual `(N resultados)` quando presente na pagina.

## Filtros E Paginaçao

Implementados na interface comum: texto, frase exata, numero, relator, tipos,
instancia via `source_origin`, ordenacao, pagina, tamanho e `fetch_details`.

O formulario tambem possui filtros de classe, assunto e competencia. Eles estao
documentados como observados, mas ainda nao sao campos tipados de
`JurisprudenceQuery`; nao devem ser inventados nem enviados por conveniencia.

## Inteiro Teor E Documentos

O resultado traz um uuid no `onclick` do botao `Inteiro Teor`. O provider chama
`GET /documento.php?uuid=<uuid>` sob demanda. Embora a interface use o nome
`viewFileDoc.php`, a resposta reproduzida redireciona para `documento.php` e
retorna HTML completo. O provider preserva bytes, content-type, tamanho e
SHA-256 em `CanonicalDocument`; nao declara PDF.

Com `fetch_details=False`, nenhuma rota documental e chamada. Com
`fetch_details=True`, o texto extraido e anexado ao resultado e os metadados
binarios permanecem em `raw`.

## Estados E Falhas

- `401/403`: `AccessControlRequiredError`.
- `400/422`: `QueryRejectedError`.
- `429`: `RateLimitDetectedError`.
- `5xx` ou falha de rede: `SourceUnavailableError`.
- HTML sem cards quando existe total: `ParserContractChangedError`.

Timeout, bloqueio e resposta sem cards nunca sao convertidos em vazio real.

## Evidencias, Fixtures E Testes

- Fixture: `tests/fixtures/tjto_jurisprudencia_results.json`.
- Testes: `tests/test_tjto_jurisprudencia.py`.
- Evidencia live: `docs/validation/runs/20260816T125603Z-tjto-tjma-tjro-live.json`.
- Rodada: 95.942 resultados, cinco itens na primeira pagina, cinco IDs novos na
  segunda e documento HTML carregado sob demanda.
- Uma revalidacao posterior apenas da raiz em navegador headless recebeu 403
  antes da busca; ela nao reproduziu o contrato POST com User-Agent de navegador
  e permanece registrada como evidência de variabilidade de acesso, nao como
  resultado vazio.

## Implementaçao E Integraçao

- Modulo: `src/nanojuris/providers/tjto_jurisprudencia.py`.
- Classe: `TjtoJurisprudenciaProvider`.
- Interfaces: Python, CLI, busca unificada, Studio e MCP.
- Configuracao: `NanoJurisConfig.tjto_jurisprudencia_url`.

## MCP E Agentes

Agentes devem distinguir ementa de documento carregado. O status do inteiro
teor deve ser `document_loaded` somente depois da chamada documental. O escopo
deve mencionar que o documento observado e HTML, nao PDF.

## Promocao

Provider elegivel para Gold textual apos repeticao de validacoes live, testes
dos filtros de classe/assunto/competencia quando a query comum os suportar e
verificacao de estabilidade do contrato documental em mais de uma rodada.

## Proximos Passos

- repetir a validacao live em uma segunda janela;
- tipar filtros de classe, assunto e competencia quando o modelo comum os suportar;
- comparar ids e datas em paginas profundas;
- confirmar a estabilidade do documento HTML em mais de um registro.
