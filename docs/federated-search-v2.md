# Fundacao da busca federada v2

`nanojuris.federated` e uma camada opt-in para planejar uma consulta antes de
chamar providers. Ela nao faz rede e nao substitui `NanoJurisClient`; portanto
nao altera o comportamento legado.

## Intencao e plano

`SearchIntent` representa texto, filtros, fontes e ordenacao sem assumir o
vocabulário de uma fonte. `plan_federated_query` gera um
`ProviderQueryPlan` deterministico por provider:

- `native` e `translated` podem entrar no payload do provider;
- `local_postfilter` fica separado para aplicacao local;
- `validated_scope` é validado pelo adapter e registrado na transformação, sem
  ser incluído no payload remoto;
- `unsupported` e `unverified` sao omitidos e aparecem em
  `omitted_filters`;
- transformacoes e filtros aplicados ficam inspecionaveis em `to_dict()`.

O planner generico nao inventa aliases. Um adapter so deve enviar um nome
traduzido quando sua propria evidencia declarar o alias.

## Cursor

`FederatedCursor` codifica versao, fingerprint da intencao e posicao por fonte
em base64url. O cursor e rejeitado quando esta malformado, tem versao
desconhecida ou nao possui fingerprint SHA-256 valido. A camada de transporte
deve ainda associar o cursor a sessao/tenant quando isso for necessario; o
cursor nao e mecanismo de autenticacao.

## Merge determinístico

`merge_federated_pages` é uma operação opt-in e sem efeitos de rede. Ela recebe
páginas já coletadas, deduplica somente quando a identidade 0037 é exatamente a
mesma, preserva registros sem identidade como distintos e expõe
`raw_result_count`, `duplicate_count`, páginas por fonte e `source_outcomes`.
Ordenações aceitas são `published_desc`, `published_asc`, `updated_desc`,
`updated_asc` e `source_id`; relevância nativa nunca é comparada entre fontes.
Um limite de resultados ou uma fonte parcial/bloqueada mantém a página global
como incompleta com motivo explícito. A API legada e o cliente não são alterados
automaticamente; a integração deve ser adotada por facade em ciclo próprio.

Providers com login, CAPTCHA, WAF, robots ou contrato instável continuam
bloqueados e não são promovidos por este planner/merge.
