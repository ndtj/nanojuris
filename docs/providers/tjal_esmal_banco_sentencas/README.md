# TJAL ESMAL Banco de Sentencas

## Identidade

- `source_id`: `tjal_esmal_banco_sentencas`
- autoridade: `TJAL`
- ramo: `state`
- grau/instancia: `first` / `first`
- colecao: `TJAL_ESMAL_CJPG`
- tipo documental: `sentenca`
- lifecycle: runtime, federated partial source

## Contrato

- Busca: `GET https://esmal.tjal.jus.br/indexS.php?pag=ler`.
- Parametros: `cat`, `text` e `p`; categorias observadas: `A`, `C`, `P`, `E`,
  `V`, `T`, `D` e `J`.
- Documentos: links PDF observados no resultado, somente no host
  `intranetlegado.tjal.jus.br`, sob `/bancodesentencas/arquivos/`.
- Limites: resposta HTML de 2 MB, PDF de 10 MB, 300 paginas remotas e no
  maximo 100 registros por janela local.
- O adapter usa `SharedHttpClient` com GET bounded, allowlist HTTPS, timeout,
  retry transitório e circuit breaker local, além de rate limit. Nao enumera
  arquivos, consulta processo, resolve CAPTCHA ou tenta contornar WAF/controle
  de acesso.

## Dados

Cada resultado preserva titulo/ementa curta, data publicada pela tabela, URL
PDF, `raw`, `SourceTrace`, hash da resposta e identidade canonica de primeiro
grau. Campos nao publicados pela ESMAL permanecem ausentes, nunca inventados.

## Estados e limites

A fonte publica uma colecao curada e nao informa total autoritativo. Uma pagina
sem linhas e representada com `total_known=false` e `extraction_status=empty`,
sem ser convertida em ausencia nacional de jurisprudencia. HTTP 403/429,
timeout, TLS, redirecionamento fora da allowlist e HTML incompativel sao erros
explicitos. O inteiro teor so e buscado quando o PDF foi observado na busca.

## Fixtures

- `tests/fixtures/tjal_esmal_success.html`
- `tests/fixtures/tjal_esmal_empty.html`
- `tests/fixtures/tjal_esmal_invalid.html`
- `tests/fixtures/tjal_esmal_invalid.pdf`
- `tests/test_tjal_esmal_banco_sentencas.py`

O transporte compartilhado valida MIME, assinatura, tamanho e preserva bytes,
hash e trace. OCR nao e executado.

## MCP e interfaces

O provider declara CLI, MCP e Studio e participa da busca unificada como fonte
parcial. A colecao curada, o `total_known=false` e a ausencia de cobertura
integral de primeiro grau permanecem explícitos.

## Proximos passos

1. Revalidacao live periodica com baixa frequencia.
2. Revisao humana continua da retencao dos PDFs.
3. Nao interpretar a presenca federada como cobertura integral do CJPG.
