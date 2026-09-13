# TJAC Ementario de Jurisprudencia

## Identidade

- Autoridade: Tribunal de Justica do Estado do Acre (`TJAC`).
- Ramo: Justica Estadual (`branch=state`).
- Grau e instancia: segundo grau (`degree=second`, `instance=second`).
- Colecao: `TJAC_EMENTARIO` (superficie `CJSG`).
- Tipo documental: ementa de acordao (`acordao_ementa`).
- Fonte oficial: pagina institucional do TJAC e volume PDF oficial.
- Provider: `tjac_ementario_jurisprudencia`.

## Contrato observado

A pagina institucional aponta o volume corrente e o provider segue somente a
URL HTTPS oficial do host `www.tjac.jus.br`:

`GET /wp-content/uploads/2026/07/Ementario_TJAC_Vol_XXX_2026.pdf`

O PDF e uma publicacao editorial dos julgados do Tribunal Pleno Jurisdicional,
Tribunal Pleno Administrativo e Conselho da Justica Estadual. O adapter valida
magic bytes, MIME observado, tamanho de 8 MB, no maximo 300 paginas e host final
antes de extrair texto. Nenhuma rota e adivinhada e nenhum desafio de acesso e
contornado.

## Dados canonicos

O parser preserva `authority`, `branch`, `degree`, `instance`, `collection`,
`document_type`, numero CNJ, classe quando legivel, relator, data de julgamento,
ementa em `summary`/`full_text`, URL do volume, `raw` e `SourceTrace`. A origem
de cada decisao e `tjac_ementario_pdf`. Campos nao publicados permanecem
ausentes; texto corrompido nao e inventado.

## Busca e limites

O volume e carregado uma vez por busca e filtrado localmente por texto, frase,
numero e termos excluidos. A resposta usa `pagination_mode=local_pdf_window`,
`total_known=false` e `is_complete=false`: o numero observado e apenas o numero
de registros que satisfazem o termo no volume corrente. O provider nao declara
que o volume representa o acervo integral do TJAC e nao cria indice persistente.

Filtros suportados: `text`, `exact_phrase`, `number`, `without_words`, `degree`,
`instance`, `branch`, `authority`, `collection` e `page`. Classe, relator,
orgao, datas, partes e `fetch_details` sao explicitamente `unsupported`.

## Documentos

O volume disponibiliza ementas, nao o voto integral separado de cada decisao.
`get_document` e `get_decisions` devolvem o texto da ementa observada na mesma
sessao, com `document_type=acordao_ementa`; nao ha OCR de paginas imagem-only.
PDF invalido, MIME incorreto, tamanho excedido, redirecionamento para host nao
oficial e falha TLS produzem erro explicito.

## Estados e evidencia live

O smoke bounded de 2026-09-08 usou o termo `constitucional` e confirmou HTTP
200, PDF oficial de 593570 bytes e 7 registros textuais de segundo grau. A
evidencia redigida esta em
`docs/provider-discovery/tjac-ementario-live-20260908.json`.

Estados possiveis: `success_with_results`, `authoritative_empty`,
`unconfirmed_empty`, `timeout`, `access_blocked`, `rate_limited`,
`transport_error`, `schema_invalid`, `partial` e `cancelled`. Ausencia de termo
no volume nao e ausencia nacional. 403, CAPTCHA, WAF, 429, timeout, TLS ou PDF
inesperado nunca viram lista vazia.

## Fixtures e promocao

Fixtures: `tests/fixtures/tjac_ementario_success.txt`,
`tjac_ementario_empty.txt` e `tjac_ementario_schema_invalid.txt`.
Testes: `tests/test_tjac_ementario_jurisprudencia.py`.

Desde 2026-09-08, o download do volume usa o transporte compartilhado
`SharedHttpClient`, com allowlist do host oficial, limite de bytes, pacing e
classificacao explicita de timeout, bloqueio e erro de transporte. O escopo
editorial e a semantica de total desconhecido permanecem inalterados.

O provider atende os gates tecnicos para uma fonte parcial e esta habilitado na
federacao como `default_federation=true`, sem alegacao de completude. A decisao
de promocao e tecnica e automatica; ela nao substitui revisao juridica de uso ou
qualquer autorizacao de publicacao.

## MCP e diagnostico

MCP e Studio podem expor a mesma janela bounded. A interface deve mostrar
`total_unknown`, `is_complete=false`, filtros locais, latencia, URL oficial e
limitacoes do volume. O diagnostico deve distinguir fonte vazia de fonte
indisponivel.

## Proximos passos

1. Revalidar o volume corrente em baixa frequencia e atualizar o hash da fonte.
2. Adicionar fixture de drift se a estrutura PDF mudar.
3. Avaliar apenas rotas oficiais caso o TJAC publique busca textual ou PDFs
   individuais.
4. Manter o provider parcial ate existir total pesquisavel e inteiro teor.

## Uso responsavel

Usar somente a publicacao oficial, com uma chamada bounded por busca, rate limit
compartilhado e sem armazenamento de corpus. Nao contornar CAPTCHA, WAF,
Turnstile, rate limit, login ou controles de acesso.
