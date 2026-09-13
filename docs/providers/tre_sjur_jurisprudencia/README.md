# tre_sjur_jurisprudencia

## Identidade

- Fonte oficial: SJUR/TREs, mantido pelo Tribunal Superior Eleitoral.
- Categoria: `electoral_jurisprudence`.
- Escopo: uma autoridade regional por consulta, informada explicitamente como
  `TRE-XX` ou `TREXX`.
- Entrada oficial: `https://jurisprudencia-tres.tse.jus.br/`.
- API observada: `https://sjur-pesquisa-api.tse.jus.br/{tre}/sjur-pesquisa-backend/rest/public/pesquisa/simples`.
- A família irmã `tre_sjur_first_degree` aceita somente rótulos explícitos de
  sentença/primeiro grau e permanece opt-in; ela nunca mistura registros com
  este binding de segundo grau.

## Contrato executável

O binding de família (`TreSjurJurisprudenciaFamilyProvider`) delega para o
adapter específico da UF. A busca exige `JurisprudenceQuery.authority`; não há
escopo agregado implícito. O payload público usa `termoPesquisa` como DSL JSON,
`pagina`, `tamanho` e `tribunais`.

O parser aceita somente rótulos de decisão explicitamente compatíveis com a
superfície regional (acórdão, decisão monocrática, resolução ou equivalente).
Sentenças e rótulos desconhecidos são rejeitados, nunca presumidos como
segundo grau. Os campos canônicos preservam autoridade, ramo eleitoral, grau,
instância, coleção SJUR, classe, número, relator, datas, ementa, decisão,
identificador e `SourceTrace`.

## Limitações e estado

- O binding de família está disponível no runtime para seleção explícita de
  `authority=TRE-XX`, mas continua **opt-in** e não participa da federação
  padrão. Os 27 adapters por UF permanecem diagnósticos.
- A rota retornou uma janela textual pública para 26 TREs no inventário
  bounded de 2026-09-09; TRE-RR retornou total zero para o termo sondado.
- A requisição de página 2 repetiu a janela da página 1 no TRE-SP. Por isso o
  adapter rejeita páginas remotas não comprovadas e marca `total_known=false`.
- Alguns identificadores declarados com PDF retornaram corpo de erro em vez de
  PDF válido. O fluxo de documentos preserva essa falha como schema/conteúdo
  inválido e não como documento vazio.
- Não são usados cookies, tokens, CAPTCHA, proxies ou qualquer bypass.

## Promoção

O provider só poderá entrar na busca federada quando cada UF comprovar contrato
de paginação, fixtures de sucesso/vazio/erro, detalhe ou inteiro teor válido,
qualidade canônica e smoke federado. Até lá, use a família ou o adapter
específico apenas para diagnóstico explícito.

## Dimensões de saúde (2026-09-12)

O catálogo separa deliberadamente três dimensões que antes ficavam implícitas
em `live_status`:

- `availability=valid_partial`: as rotas públicas das 27 UFs responderam e
  foram parseadas em sondagem bounded;
- `completeness=bounded_partition`: uma janela mensal explícita pode ser
  validada quando o total declarado coincide com os registros retornados;
- `pagination=unverified`: a rota geral repetiu a mesma janela ao trocar
  `pagina`, portanto não há ainda paginação remota confiável.

O `live_status=partial` permanece intencionalmente conservador e impede a
promoção automática. Essas dimensões tornam a disponibilidade utilizável para
diagnóstico sem declarar que o acervo inteiro foi coletado.

Para um lote nacional explícito, use `search_authorities(query, authorities)`
com as UFs escolhidas. A operação é serial, limitada a 27 autoridades, exige a
lista no chamador e devolve `authority_status` por UF; ela não habilita escopo
agregado implícito nem a federação padrão.

## Evidências e testes

- `docs/provider-discovery/tre-sjur-route-inventory-live-20260909.json`
- `docs/provider-discovery/tre-sjur-gold-live-20260909.json`
- `docs/provider-discovery/tre-sp-sjur-pagination-live-20260909.json`
- `docs/provider-discovery/tre-ac-mg-sjur-pagination-live-20260911.json`
- `docs/provider-discovery/tre-sjur-first-degree-live-20260911.json`
- `docs/provider-discovery/tre-sjur-second-degree-type-filter-live-20260912.json` — filtro oficial de tipos de segundo grau sondado serialmente em todas as 27 UFs; 24 janelas filtradas válidas, TRE-SC vazio autoritativo e 2 respostas excedendo o limite de corpo.
- `docs/provider-discovery/tre-sp-sjur-live-20260910.json` — sondagem bounded
  atual com três registros de segundo grau e um PDF oficial extraído com sucesso.
- `tests/test_tre_sjur_jurisprudencia.py`
- `docs/provider-discovery/tre-sp-sjur-structured-filters-live-20260912.json`
## Filtro remoto de segundo grau (2026-09-12)

O binding de segundo grau envia, além do tribunal, o filtro oficial
`descricaoTipoDecisao.keyword` com `Acórdão`, `Decisão monocrática`, `Resolução`
e `Decisão sem resolução`. O parser ainda valida localmente os rótulos para
impedir que schema drift ou conteúdo misto seja promovido como segundo grau.
Na sondagem bounded serial das 27 UFs, 24 retornaram janelas filtradas válidas,
TRE-SC retornou vazio autoritativo e TRE-GO/TRE-PB excederam o limite de corpo;
esses últimos permanecem indisponíveis para essa execução, não vazios.

Uma segunda sonda com `document_type=acordao` e limite de transporte de 16 MB
recuperou uma janela válida de TRE-GO e TRE-PB (5.444.253 e 4.188.662 bytes).
As duas UFs continuam com `total_known=false` e `is_complete=false`, pois a
paginação remota ainda não foi comprovada. Evidência:
`docs/provider-discovery/tre-sjur-large-window-live-20260912.json`.
- `docs/provider-discovery/tre-sjur-pagination-recheck-20260912.json` — a sonda
  serial comparou `pagina=0` e `pagina=1` no TRE-SP; a fonte devolveu a mesma
  janela de 1.000 registros (total informado 2.119), portanto o total segue
  desconhecido e `page > 1` continua rejeitado pelo adapter.

## Refinamentos estruturados da SPA (2026-09-12)

O frontend oficial tambem comprovou os seguintes controles, agora expostos de
forma opcional em `JurisprudenceQuery` e traduzidos para o DSL remoto somente
no binding TRE:

| Campo canonico | Campo remoto | Semantica |
|---|---|---|
| `election_year` | `anoEleicao` | `terms` numerico |
| `observations` | campos de observacao oficiais | `query_string` |
| `tags` | `etiquetas.etiqueta.keyword` | `terms` |
| `municipality` | `nomeMunicipio.keyword` | `terms` |
| `publication_source` | `publicacoes.siglaFontePublicacao.keyword` | `terms` |
| `publication_number` | `publicacoes.numeroPublicacao` | `terms` |
| `publication_volume` | `publicacoes.numeroVolume` | `terms` |
| `uf` | `siglaUF.keyword` | `terms` |

Listas sao separadas por virgula. Anos nao numericos ou fora de 1800-2200 sao
rejeitados antes da requisicao. TSE e providers nao-TRE nao declaram esses
campos como suportados; um filtro explicito nessas superficies gera erro, nunca
uma busca silenciosamente incompleta. A descoberta dos nomes dos campos foi
feita no bundle SPA oficial; nenhum codigo de terceiro ou tecnica de bypass foi
utilizado.
