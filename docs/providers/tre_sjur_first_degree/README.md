# tre_sjur_first_degree

## Identidade

- Fonte oficial: SJUR/TREs, mantido pelo Tribunal Superior Eleitoral.
- Categoria: `electoral_jurisprudence`.
- Escopo: uma autoridade regional por consulta, informada como `TRE-XX` ou
  `TREXX`.
- Entrada oficial: `https://jurisprudencia-tres.tse.jus.br/`.
- API observada: `https://sjur-pesquisa-api.tse.jus.br/{tre}/sjur-pesquisa-backend/rest/public/pesquisa/simples`.
- Superficie: decisoes explicitamente rotuladas como `Sentenca` ou primeiro
  grau. Registros de acordao, decisao monocratica ou tipo desconhecido sao
  rejeitados neste binding.

## Contrato executavel

`TreSjurFirstDegreeFamilyProvider` delega para um adapter por UF e exige
`JurisprudenceQuery.authority`. O payload publico usa `termoPesquisa` como DSL
JSON, `pagina`, `tamanho` e `tribunais`; a selecao de grau e feita localmente
com base no rotulo publicado pela fonte.

Todo registro aceito preserva autoridade, ramo eleitoral, `degree=first`,
`instance=first`, colecao `SJUR`, classe, numero, relator, datas, ementa,
decisao, identificador e `SourceTrace`. A consulta nao mistura o binding de
primeiro grau com `tre_sjur_jurisprudencia` (segundo grau).

## Dados e estados

- A resposta pode conter registros de primeiro e segundo grau; o parser filtra
  somente rotulos explicitos de sentenca/primeiro grau.
- `HTTP 403`, CAPTCHA, WAF, timeout, TLS, HTTP 429 ou schema inesperado sao
  estados de acesso/transporte/schema e nunca sao convertidos em lista vazia.
- O total remoto e a paginacao nao foram comprovados: sondagens bounded
  repetiram a janela para paginas diferentes. O adapter declara
  `total_known=false` e rejeita `page != 1`.
- A evidencia observada foi TRE-MG com registros de `Sentenca` e `Acórdão`:
  `docs/provider-discovery/tre-sjur-first-degree-live-20260911.json`.
- A sondagem multi-UF bounded de 2026-09-12 consultou os 27 TREs em série,
  sem persistir corpos. TRE-MG foi a única resposta com rótulo explícito de
  primeiro grau (950 de 1.000 registros); 23 TREs retornaram apenas rótulos de
  segundo grau, TRE-SC retornou total zero e TRE-GO/TRE-PB excederam o limite
  de resposta. A evidência não promove a família nem comprova paginação:
  `docs/provider-discovery/tre-sjur-first-degree-multi-uf-live-20260912.json`.
- A rota oficial respeita o filtro `descricaoTipoDecisao.keyword=Sentença`:
  uma sondagem serial das 27 UFs retornou janela textual filtrada somente no
  TRE-MG; os outros 26 TREs retornaram total zero autoritativo. Evidência:
  `docs/provider-discovery/tre-sjur-type-filter-live-20260912.json`.
- Uma sonda textual independente em 27 UFs (13/09/2026) confirmou que o termo
  `sentença`, sem o filtro de tipo, pode retornar apenas decisões de segundo
  grau (26 janelas) ou rótulos não classificáveis (1 janela). O parser rejeita
  esses registros e a evidência não é tratada como vazio de primeiro grau:
  `docs/provider-discovery/tre-sjur-first-degree-sweep-live-20260913.json`.
- A amostra bounded mais recente do TRE-MG, com `document_type=sentenca`,
  retornou um registro explicitamente de primeiro grau (HTTP 200). A resposta
  foi reduzida a metadados e hash em
  `docs/provider-discovery/tre-mg-first-degree-live-20260913.json`.
- Quando o registro não possui URL PDF pública, o `get_document` agora expõe o
  `textoDecisao`/`textoEmenta` retornado pela mesma busca como documento
  `text/plain`, mantendo a proveniência e sem fabricar uma URL.
- A familia continua opt-in; a evidencia de uma UF nao promove as demais.

## Limites e promocao

O provider nao participa da federacao padrao. Cada TRE precisa comprovar
contrato de paginação, fixtures de sucesso/vazio/erro, filtros, detalhe ou
inteiro teor valido, qualidade canonica e smoke federado antes de promoção.
Nenhum cookie, token, proxy ou bypass e utilizado.

## Fixtures, testes e interfaces

- Fixture sanitizada: `tests/fixtures/tre_sjur_first_degree_success.json`.
- Testes: `tests/test_tre_sjur_jurisprudencia.py`.
- O binding possui interfaces CLI/MCP/Studio de diagnostico, mas
  `unified_search=false` e `opt_in_unified_search=true`.
- A familia aceita somente `authority=TRE-XX`; nao existe escopo agregado
  implicito.

## MCP

O contrato pode ser inspecionado por `source_contracts` e a consulta pode ser
executada somente com uma autoridade explicita. O MCP deve preservar
`access_status`, `extraction_status`, `total_known=false` e os traces por UF;
nao deve encaminhar a familia para a busca federada padrao.

## Proximos passos

- [ ] Validar paginação ou documentar formalmente a janela unica por UF.
- [ ] Validar documentos oficiais por UF e MIME/tamanho antes de promover.
- [ ] Revisar legalidade, retenção e decisão humana de federação.

## Evidencia

- `docs/provider-discovery/tre-sjur-first-degree-live-20260911.json`
- `docs/provider-discovery/tre-ac-mg-sjur-pagination-live-20260911.json`
- `docs/provider-discovery/tre-sjur-first-degree-multi-uf-live-20260912.json`
- `docs/provider-discovery/tre-sjur-type-filter-live-20260912.json`
- `docs/provider-discovery/tre-sjur-first-degree-sweep-live-20260913.json`
- `docs/provider-discovery/tre-mg-first-degree-live-20260913.json`
- `docs/providers/tre_sjur_jurisprudencia/README.md` (familia de segundo grau)
