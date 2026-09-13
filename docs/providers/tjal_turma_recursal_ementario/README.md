# TJAL Turmas Recursais - ementario oficial

## Escopo

`tjal_turma_recursal_ementario` le, sob demanda e em memoria, uma janela de
ementas publicada pelo Tribunal de Justica de Alagoas para as Turmas Recursais.
E uma colecao recursal (`degree=recursal`, `instance=turma_recursal`) e nao e
contabilizada como CJPG ou CJSG.

Fonte oficial: [indice de jurisprudencia dos Juizados](https://aceco.tjal.jus.br/?pag=juizados_jurisprudencias).
O volume padrao e [`Ementas-3.pdf`](https://aceco.tjal.jus.br/juizados/relatorios/Ementas-3.pdf).

## Contrato operacional

- Metodo: `GET` HTTPS; somente o host oficial `aceco.tjal.jus.br` e aceito.
- Uma requisicao por busca, respeitando o intervalo comum de transporte.
- PDF limitado a 8 MB e 700 paginas; resposta invalida ou sem texto gera erro,
  nunca resultado vazio.
- Paginacao e uma janela local; a fonte nao informa total autoritativo nem
  acervo integral.
- Texto, frase, numero e exclusoes sao pos-filtrados localmente. Grau,
  instancia, ramo, autoridade e colecao sao validacoes de escopo.
- Classe, orgao, relator e datas nao sao declarados suportados sem prova da
  fonte.
- O conteudo e ementa extraida; nao ha promessa de voto integral e PDFs
  image-only nao recebem OCR automatico.

## Identidade

Registros preservam `authority=TJAL`, `branch=state`, `degree=recursal`,
`instance=turma_recursal`, `collection=TJAL_TURMAS_RECURSAIS`, tipo de decisao,
numero quando encontrado, ementa, relator/origem, URL oficial, `SourceTrace` e
estados de acesso/extracao.

## Federacao

O provider e runtime e `opt_in_unified_search=true`, mas nao participa da
federacao padrao. Deve ser selecionado explicitamente em consultas recursais e
nao substitui jurisprudencia geral de primeiro ou segundo grau. Ausencia de
termo no volume e `total_unknown`, nao ausencia no tribunal.

Evidencia live: `docs/provider-discovery/tjal-turma-recursal-live-20260908.json`.

## Fixtures

- `tests/fixtures/tjal_turma_recursal_success.txt`
- `tests/fixtures/tjal_turma_recursal_empty.txt`
- `tests/fixtures/tjal_turma_recursal_invalid.pdf`
- `tests/fixtures/provider_contracts.json` com `success`, `empty` e `non_success`.

## Dados

O parser preserva numero, tipo, ementa, relator, origem, URL do volume, `raw`,
`SourceTrace`, `access_status` e `extraction_status`. Campos nao publicados
permanecem ausentes, sem preenchimento especulativo.

## Comportamento

Sucesso e `success_with_results`; volume sem texto e `schema_invalid`; HTTP
403/429, timeout, TLS e redirect nao permitido geram estados proprios. Busca
sem correspondencia na janela continua `unconfirmed_empty`/`total_unknown`.

## Uso Via MCP

O contrato pode ser consultado pelas ferramentas de fontes e contratos. Mantenha
`degree=recursal` ou `collection=TJAL_TURMAS_RECURSAIS` para evitar mistura.

## Proximos passos

Revisao humana deve decidir se a fonte permanece opt-in e como novos volumes
serao atualizados. Nenhuma dessas decisoes e necessaria para o adapter local.

O download do volume usa `SharedHttpClient` com allowlist de
`aceco.tjal.jus.br`, limite de 8 MB, timeout, rate limit e circuito. O corpo é
validado como PDF antes da extração; respostas de acesso, transporte, MIME ou
tamanho permanecem explícitas e nunca são tratadas como ausência de ementas.
