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

- [x] Cobrir snapshot vazio e schema sem identificador pelo contrato
  compartilhado; o fixture de sucesso permanece sanitizado.
- [x] Confirmar variações anuais de colunas e codificação no parser (UTF-8 BOM,
  CP1252 e Latin-1; IDs legados e `NrAto/AnoAto`).
- [x] Validar links PDF: somente hosts oficiais são aceitos e o download não
  é ampliado para esta superfície.

Fixtures adicionais: `tests/fixtures/tce_pr_viajuris_empty.csv` e
`tests/fixtures/tce_pr_viajuris_invalid.csv`.

## Fechamento técnico

- Busca local no snapshot anual está apta à federação como jurisprudência
  administrativa do TCE-PR, sem declarar inteiro teor quando há apenas link.
- Estados HTTP, schema inválido e arquivo vazio continuam explícitos.
