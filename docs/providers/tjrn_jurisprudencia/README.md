# TJRN - Pesquisa de Jurisprudencia

Status: `implemented`, `live_validated`, `federation_enabled`; binding CJSG
explícito comprovado em 2026-09-06.

## Identidade da fonte

Tribunal de Justica do Estado do Rio Grande do Norte. Portal oficial:
`https://jurisprudencia.tjrn.jus.br/`. Categoria: jurisprudencia estadual
unificada, com registros PJe e legado SAJ.

## Contrato

O provider usa `POST /api/pesquisar` com `jurisprudencia.ementa`, numero de
processo opcional, `page` e contexto `usuario` vazio. O tamanho remoto e
limitado a 10. O parser mapeia processo, tipo de decisao, classe, assunto,
relator, orgao julgador, datas, ementa, inteiro teor, sistema e grau. Filtros
nao comprovados permanecem explicitamente unsupported.

## Dados Retornados

O endpoint e uma superficie textual unificada. Grau, instancia, origem PJe/SAJ,
tipo documental e valores nativos sao preservados em campos canonicos e em
`raw`. A revalidação bounded de 2026-09-06 observou duas páginas exclusivamente
com `degree=second`/`instance=second`; por isso o binding CJSG foi promovido na
matriz. A superfície CJPG permanece não comprovada.

## Estados e diagnostico

Uma chamada live limitada em 2026-09-05 retornou HTTP 200, registros reais,
total declarado, inteiro teor e identificadores estaveis. A segunda pagina
retornou identificadores distintos. HTTP 401/403, 429, falhas de transporte,
JSON invalido e schema drift produzem estados explicitos, nunca lista vazia.

## Fixtures

Fixtures sanitizadas e testes cobrem sucesso, vazio, erro, schema drift,
pagina e promocao:

- `tests/fixtures/tjrn_jurisprudencia_success.json`
- `tests/fixtures/tjrn_jurisprudencia_empty.json`
- `tests/fixtures/tjrn_jurisprudencia_invalid.json`
- `tests/fixtures/tjrn_jurisprudencia_schema_drift.json`
- `tests/test_tjrn_jurisprudencia.py`

## MCP

O provider pode ser exposto por MCP com rastros e limites preservados. A
federacao padrao usa o mesmo adapter e nao oculta bloqueios ou filtros
ignorados.

## Proximos passos

Manter smoke live bounded, observar mudancas de schema e ampliar filtros somente
apos evidencia publica reproduzivel. O provider nao e automaticamente atribuido
a uma superficie CJPG/CJSG.

## Promocao

TJRN esta habilitado na busca federada padrao porque runtime, contrato, fixtures,
qualidade e evidencia live passaram o gate tecnico. O artefato
`docs/operations/provider-promotion-approvals-20260905.json` autoriza operacao
local/federada, sem autorizar deploy ou redistribuicao.

## Evidencia live

- `docs/provider-discovery/tjrn-jurisprudencia-live-20260905-cycle27.json`
- `docs/provider-discovery/tjrn-jurisprudencia-live-20260905-cycle28.json`
- `docs/provider-discovery/tjrn-jurisprudencia-pagination-live-20260905-cycle31.json`
- `docs/provider-discovery/tjrn-cjsg-live-20260906.json`
- `docs/provider-discovery/tjrn-first-degree-probe-live-20260907.json`

## Fontes oficiais

- https://jurisprudencia.tjrn.jus.br/
- https://glaucialima.com/2019/11/18/nova-versao-do-sistema-de-consulta-de-jurisprudencia-esta-a-disposicao-dos-usuarios/
