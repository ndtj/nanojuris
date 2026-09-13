# `tjma_informativos`

## Identidade

- Fonte oficial: `https://www.tjma.jus.br/midia/pje/pagina/hotsite/509874`.
- Superficie: informativos oficiais curados do Tribunal de Justica do Maranhao.
- Colecao: `INFORMATIVO`; ramo `state`; grau e instancia `second`.
- Papel: `curated_context`, nao substitui o repositorio geral de acordaos CJSG.
- Estado: runtime local, acesso publico bounded e federacao opt-in.

## Contrato observado

```text
GET https://www.tjma.jus.br/midia/pje/pagina/hotsite/509874
GET https://novogerenciador.tjma.jus.br/storage/.../*.pdf
```

A pagina publica links PDF para edicoes mensais. A edicao `2026_08` foi validada
com HTTP 200, `application/pdf`, assinatura `%PDF`, 5.756.596 bytes e 777
paginas. A primeira pagina identifica o TJMA, o informativo e camaras de direito
criminal, privado e publico. Isso comprova escopo curado de segundo grau, mas nao
cobertura integral do CJSG. Evidencia: `docs/provider-discovery/tjma-informativos-live-20260908.json`.

## Implementacao

- Adapter: `src/nanojuris/providers/tjma_informativos.py`.
- Fixture: `tests/fixtures/tjma_informativos_success.html`.
- Testes: `tests/test_tjma_informativos.py`.
- `get_document` usa `DocumentReference` e transporte compartilhado com allowlist,
  MIME, magic bytes, limite, hash e extracao.
- A busca lista edicoes e nao baixa PDFs durante a busca normal.

## Filtros e limites

Filtros comprovados: `page`, `authority`, `branch`, `degree`, `instance`,
`collection` e `document_type` por escopo validado. Texto, numero de processo,
classe, orgao, relator e datas de decisao sao `unsupported`; o `SearchPage`
explicita a limitacao. `total_known=false`, pois a fonte nao publica total
historico autoritativo; a janela e a ordenacao por periodo ficam no trace.

## Dados

Cada edicao preserva periodo, titulo, autoridade, ramo, grau, instancia,
colecao, tipo documental, URL oficial, `raw`, `SourceTrace` e proveniencia dos
campos. O inteiro teor permanece no PDF oficial e e extraido sob demanda.

## Estados

HTML de desafio ou 403/401 e `access_blocked`; 429 e `rate_limited`; erro de
rede ou 5xx e `source_unavailable`; ausencia de links PDF apos HTTP 200 e
`schema_invalid`; pagina oficialmente sem edicoes e `authoritative_empty`.
Nenhum bloqueio e convertido em vazio.

## Fixtures

- `tests/fixtures/tjma_informativos_success.html`: PDFs oficiais, RTF editavel e
  host externo rejeitado.
- `tests/test_tjma_informativos.py`: parser, escopo, documento sob demanda,
  capacidades, falhas HTTP e drift de schema.
- A evidencia live preserva hash, tamanho, MIME, assinatura e paginas, sem
  armazenar o PDF completo.

## Transporte compartilhado (2026-09-08)

A listagem HTML oficial agora usa `SharedHttpClient`, com allowlist TJMA,
limite de 8 MB, redirecionamentos limitados, timeout, rate limit e circuito.
O download PDF sob demanda jÃ¡ usava o pipeline documental compartilhado. Erros
401/403/429, TLS, timeout, schema, redirecionamento e excesso de bytes continuam
explÃ­citos e nÃ£o viram ediÃ§Ãµes vazias; nÃ£o hÃ¡ retry automÃ¡tico no catÃ¡logo.

## Federacao

`supports_unified_search=false` e `opt_in_unified_search=true`. A fonte pode
complementar uma busca explicitamente selecionada, mas nao conta como CJSG geral.

## MCP e agentes

Pode ser exposta como fonte curada, sempre mostrando edicao e link oficial.
Agentes nao devem apresenta-la como acordao individual, precedente vinculante ou
acervo integral.

## Acesso responsavel

Usar somente paginas e PDFs oficiais, em baixa frequencia e sem coleta em massa.
Nao automatizar desafios, reutilizar tokens/cookies ou fazer rotacao de proxies.

## Proximos passos

1. Revalidar a pagina e um PDF em baixa frequencia conforme TTL da evidencia.
2. Manter a colecao opt-in ate revisao tecnica e humana de rollout.
3. Nao expandir filtros de assunto/processo sem contrato oficial observado.
