# TJMS CJPG (jurisprudência de primeiro grau)

Status técnico: `implemented`, `live_validated`, `federation_enabled`.

O provider usa a consulta pública de julgados de primeiro grau do e-SAJ do
Tribunal de Justiça de Mato Grosso do Sul. A rota observada é
`https://esaj.tjms.jus.br/cjpg/`, com busca em `GET /cjpg/pesquisar.do` e
paginação mantida pela sessão pública do e-SAJ. O formulário retorna HTML com
linhas `tr.fundocinza1`, metadados e o texto da decisão inline.

O binding reaproveita somente o parser independente e endurecido da família
e-SAJ; autoridade, URL, IDs e `SourceTrace` permanecem específicos do TJMS.
Todo registro aceito é marcado `branch=state`, `degree=first`,
`instance=first` e `collection=CJPG`. Consulta processual e CJSG não são
misturados.

Filtros comprovados: texto, número CNJ, data de disponibilização (mapeada como
`updated_*`) e ordenação da fonte. Classe, assunto, vara e magistrado ficam
preservados em `raw` até que um contrato de filtro específico seja validado.
Erros HTTP, CAPTCHA, WAF, timeout e mudança de layout são outcomes explícitos;
nenhum é convertido em vazio.

Evidência bounded: `docs/provider-discovery/tjms-cjpg-live-20260907.json`.
Fixtures sanitizadas e parser: `tests/fixtures/tjms_cjpg_success.html` e
`tests/test_tjms_cjpg.py`. O texto integral é inline; não há endpoint de
detalhe independente observado.

Rechecagem de transporte em 2026-09-09: a política compartilhada foi rebindada
ao host oficial `esaj.tjms.jus.br`, corrigindo a rejeição local causada pelo
host TJSP herdado. A chamada bounded respondeu HTTP 200 com inteiro teor
inline. Evidência: `docs/provider-discovery/tjms-cjpg-transport-detail-live-20260909.json`.

## Identidade

Autoridade: TJMS; ramo estadual; primeiro grau; coleção CJPG.

## Contrato

Sessão pública e-SAJ, `GET /cjpg/pesquisar.do`, HTML de resultados e janela de
dez registros por página.

## Dados

CNJ, classe, assunto, magistrado, vara, comarca, datas, texto integral e todos
os campos originais são preservados em `raw`.

## Estados

`SourceTrace` registra status HTTP, URL final, bytes e hash. Vazio autoritativo,
bloqueio, timeout, rate limit e mudança de schema são estados distintos.

## Fixtures

`tests/fixtures/tjms_cjpg_success.html` cobre uma linha sanitizada;
`tests/fixtures/tjms_cjpg_empty.html`,
`tests/fixtures/tjms_cjpg_access_control.html` e
`tests/fixtures/tjms_cjpg_schema_drift.html` cobrem vazio autoritativo, controle de acesso e
mudança de layout.

## MCP

O provider pode ser selecionado explicitamente via `source="tjms_cjpg"`, com
trace e completude expostos ao consumidor.

## Próximos passos

Validar segunda página e filtros de classe, assunto, vara e magistrado em novos
replays bounded, sem alterar o rollout quando a fonte estiver indisponível.
