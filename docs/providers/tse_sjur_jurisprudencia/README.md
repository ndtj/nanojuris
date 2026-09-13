# TSE SJUR — jurisprudência textual

Status: `implemented`, `live_validated` para consulta exata, runtime opt-in e
fora da federação padrão.

## Identidade

Autoridade: TSE. Ramo: eleitoral. Instância: superior. Coleção: SJUR.
Esta entrada não cobre automaticamente os TREs.

## Contrato observado

Fonte oficial: [Portal de jurisprudência do TSE](https://jurisprudencia.tse.jus.br).
O adapter usa apenas:

```text
POST https://sjur-pesquisa-api.tse.jus.br/tse/sjur-pesquisa-backend/rest/public/pesquisa/simples
```

O campo `termoPesquisa` é uma string JSON com DSL `bool`; o filtro de tribunal
é fixado em `TSE`. Texto, expressão exata e identificador são traduzidos; os
demais filtros permanecem explicitamente não suportados.

## Estados e dados canônicos

O parser preserva código da decisão, processo CNJ quando disponível, classe,
tipo, relator, data de julgamento, publicação, ementa, decisão e `raw`. Os
registros aceitos são marcados `authority=TSE`, `branch=electoral`,
`degree=superior`, `instance=superior` e `collection=SJUR`.

## Dados

O contrato atual entrega JSON com HTML embutido em `textoEmenta` e
`textoDecisao`. O parser conserva o objeto bruto e converte os fragmentos para
texto visível; campos ausentes permanecem ausentes, nunca são inferidos.

## Limitações e promoção

O smoke de 2026-09-09 comprovou uma consulta exata (HTTP 200, um registro),
mas uma consulta textual posterior ignorou `pagina`/`tamanho` e devolveu 132
registros. A paginação remota foi validada como não suportada (janela única).
A rota oficial
`https://sjur-servicos.tse.jus.br/sjur-servicos/rest/download/pdf/<codigoDecisao>`
foi localizada no bundle público e validada para o registro observado 504401;
o adapter só aceita IDs observados na sessão. Por isso o provider foi
promovido tecnicamente para runtime opt-in: é instanciado pelo cliente padrão
para uso explícito, mas permanece fora da federação padrão
(`supports_unified_search=false`); T009 registra a decisão de não promover ao
rollout federado até que a paginação remota seja provada.

Não são usados tokens, CAPTCHA solving, proxy, sessão autenticada ou qualquer
tentativa de contornar controle de acesso. 401/403/429, timeout e schema drift
permanecem estados explícitos.

## Fixtures e evidência

- `tests/fixtures/tse_sjur_success.json`
- `tests/fixtures/tse_sjur_empty.json`
- `tests/fixtures/tse_sjur_schema_drift.json`
- `tests/test_tse_sjur_jurisprudencia.py`
- `docs/provider-discovery/tse-sjur-search-live-20260909.json`
- `docs/provider-discovery/tse-sjur-empty-live-20260909.json`
- `docs/provider-discovery/tse-sjur-pagination-live-20260909.json`
- `docs/provider-discovery/tse-sjur-document-live-20260909.json`

## TREs em modo opt-in

O mesmo contrato oficial possui rotas por UF no frontend
`https://jurisprudencia-tres.tse.jus.br/`. A classe
`TreSjurJurisprudenciaProvider` reutiliza o transporte e restringe a DSL a
uma autoridade `TRE-XX`. Os 27 nomes ficam disponíveis somente quando
`include_candidate_providers=True`; não são entradas federadas nem substituem
o dossiê agregado `justica_eleitoral_sjur`.

O inventário bounded de 2026-09-09 observou texto em 26 TREs e vazio
autoritativo para TRE-RR no termo testado. Cada UF ainda precisa fechar
paginação, fixtures, MIME/documento e smoke antes de ser registrada como
provider no catálogo. Sentenças e rótulos desconhecidos são rejeitados pelo
adapter, não classificados automaticamente como segundo grau.
No TRE-SP, o probe de duas páginas devolveu a mesma janela de dez IDs e
`totalRegistros=10` em ambas; a API não comprovou paginação remota.

Os adapters `tre_*_sjur_jurisprudencia` rejeitam `page > 1` como consulta nao
suportada. O probe bounded do TRE-SP registrou a mesma janela para as paginas
1 e 2, portanto repetir a resposta nao e tratado como segunda pagina nem como
completude.

## MCP e Studio

As interfaces podem exibir o provider como fonte runtime opt-in. A federação
padrão não o roteia porque a fonte oferece
uma resposta única e não suporta paginação remota segura.

## Próximos passos

Validar, em baixa frequência e sem contornar controles, se `pagina` e `tamanho`
produzem janelas distintas; adicionar fixture de segunda página; só então
reavaliar o gate técnico.
