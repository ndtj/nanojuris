# `tce_pr_viajuris`

## Identidade

- Fonte oficial: ViaJuris Dados Abertos do Tribunal de Contas do Parana.
- Categoria: `administrative_jurisprudence`.
- Status: provider runtime para snapshot CSV publico.
- URL: `https://viajuris.tce.pr.gov.br`.

## Contrato

```text
GET /DadosAbertos/DadosAbertos/DownloadArquivo?nomeArquivo={year}_acordaos_base_de_dados.csv
```

O arquivo e CSV delimitado por ponto e virgula. O parser aceita UTF-8 com BOM,
CP1252 e Latin-1, exige uma coluna de identificador explicita e mapeia
ementa, processo, datas e `UrlPDF` quando presentes. A busca e local sobre o
snapshot baixado; pagina e tamanho sao aplicados depois do filtro textual.

`get_catalog(year=...)` descreve o arquivo anual sem baixa-lo. O link PDF so e
aceito quando pertence ao host oficial ViaJuris. Nenhum dado pessoal e criado
ou inferido.

## Estados e limites

HTTP 401/403 e controle de acesso, 429 e limite, 5xx e indisponibilidade e
resposta vazia ou schema sem identificador e mudanca de contrato. O provider
nao baixa PDFs, nao automatiza a consulta interativa e preserva hash/tamanho
do CSV em `SourceTrace`.

## Fixtures e testes

Fixture sanitizada: `tests/fixtures/tce_pr_viajuris_acordaos.csv`.
Regressao: `tests/test_tce_pr_viajuris.py`.

## Dados retornados

Cada linha valida e normalizada como `CanonicalDecision`, preservando em `raw`
as colunas originais do CSV. O identificador da fonte, processo, ementa, datas,
link oficial e hash do snapshot sao mantidos para rastreabilidade. O provider
nao afirma inteiro teor quando a linha fornece somente um link PDF.

## MCP e agentes

Usar para jurisprudencia administrativa do TCE-PR quando o snapshot anual
estiver disponivel. O agente deve informar o ano do arquivo e distinguir busca
local no CSV de consulta online; nao deve baixar documentos em lote.

## Proximos passos

- [ ] Adicionar fixtures de snapshot vazio e de schema sem identificador.
- [ ] Confirmar variacoes anuais de colunas e codificacao.
- [ ] Validar o contrato de links PDF sem ampliar o escopo para download.
