# Contrato de fonte — `tjac_banco_sentencas`

## Fonte oficial

`GET https://www.tjac.jus.br/coger/banco-de-sentencas/`

O TJAC/Corregedoria publica uma página HTML com links oficiais para sentenças
selecionadas em PDF. Esta é uma coleção editorial de primeiro grau (CJPG), não
um índice geral de todas as sentenças do tribunal.

## Identidade

Cada registro aceito é explicitamente `authority=TJAC`, `branch=state`,
`degree=first`, `instance=first`, `collection=CJPG` e
`document_type=sentenca`. O número CNJ é extraído do texto visível ou do nome
do arquivo quando presente; links sem número recebem um identificador estável
derivado da URL.

## Contrato

- Método: `GET /coger/banco-de-sentencas/`.
- A resposta deve ser HTML UTF-8 não vazio; somente links HTTPS no host
  `www.tjac.jus.br` com extensão `.pdf` são aceitos.
- A página não fornece total autoritativo nem cursor remoto. A paginação é uma
  janela local da ordem HTML (`local_html_window`) limitada a 100 registros e
  20 por página.
- O PDF é obtido apenas sob demanda, depois de o link ter sido observado na
  busca, com limite de 8 MiB e validação pelo transporte compartilhado.

## Filtros e dados

Texto, frase exata e número são pós-filtros locais sobre o contexto HTML.
Grau, instância, ramo, autoridade e coleção são filtros de escopo validados.
Classes, datas, relator, órgão, partes e filtros processuais não são
suportados. Cada resultado preserva resumo/contexto, URL documental, `raw`,
`SourceTrace`, proveniência de campos e estado de acesso.

## Dados canônicos

O parser preserva identificador estável, número CNJ quando publicado, contexto
visível, URL oficial do PDF, autoridade, ramo, grau, instância, coleção e tipo
documental. O inteiro teor permanece como documento remoto; o fluxo de leitura
valida MIME, tamanho e assinatura antes de extrair texto.

## Estados e limites

HTTP 401/403/407/451, 429, timeout, TLS, HTML vazio, schema inesperado e PDF
inválido permanecem estados explícitos. Nenhum desses estados é convertido em
lista vazia. A ausência de correspondência no HTML observado é apenas
`total_unknown`, nunca uma afirmação de ausência no acervo.

## Fixtures

Os testes usam `tests/fixtures/tjac_banco_sentencas_index.html`, uma cópia
sanitizada da estrutura (sem o corpo integral de decisões). Respostas PDF são
simuladas com cabeçalho mínimo nos testes de transporte; o PDF live não é
armazenado no repositório.

## Federação e uso

`supports_unified_search=false` e `opt_in_unified_search=true`. A coleção pode
ser consultada explicitamente por CLI, MCP ou Studio, mas não substitui a
jurisprudência geral do e-SAJ nem entra no rollout federado padrão.

## MCP e diagnóstico

O provider pode ser consultado explicitamente por MCP, CLI e Studio. O
diagnóstico exibe `total_unknown`, a natureza curada da coleção, o estado do
documento e o `SourceTrace`, sem apresentar o banco como cobertura integral.

## Evidência live

`docs/provider-discovery/tjac-banco-sentencas-live-20260912.json` registra
somente metadados da página e de um PDF oficial validado (status, tamanho,
hash e tipo MIME), sem persistir o corpo documental.

## Próximos passos

1. Repetir sondas bounded respeitando o intervalo configurado por host.
2. Revalidar a estrutura quando o TJAC publicar uma nova página.
3. Manter a natureza curada e opt-in explícita; não declarar cobertura CJPG
   integral a partir deste banco.
