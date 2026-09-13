# Verification — SDD 0109

## Resultados

- Testes focados: `tests/test_tre_sjur_jurisprudencia.py` e contratos de
  catálogo/documentação aprovados após regeneração.
- A família aparece no runtime e permanece `supports_unified_search=false`;
  nenhum rollout federado padrão foi alterado.
- A cobertura gerada mantém 27 autoridades eleitorais como diagnóstico, sem
  afirmar completude de paginação ou de acervo.

## Evidência

- Família oficial: `src/nanojuris/providers/tse_sjur_jurisprudencia.py`.
- Registro runtime: `src/nanojuris/client.py`.
- Registry: `docs/registry/providers.json`.
- Contrato e limites: `docs/providers/tre_sjur_jurisprudencia/README.md` e
  `docs/source-contracts/tre_sjur_jurisprudencia.md`.

## Gates técnicos

- `tests/test_tre_sjur_jurisprudencia.py` confirma binding de família e
  adapters por UF opt-in.
- `python tools/build_provider_coverage.py --write` confirma lifecycle e
  runtime binding separados.
- Smoke bounded de 2026-09-10 em `TRE-SP` retornou um registro textual
  publico de segundo grau (`access_status=public`, `extraction_status=complete`,
  `total_known=false`) sem persistir corpo bruto:
  `docs/provider-discovery/tre-sp-sjur-runtime-live-20260910.json`.
- A matriz nacional passou a vincular as 27 linhas `TRE-XX/SJUR` ao binding da
  família, em `contract_pending`, reduzindo falsos bloqueios sem promover a
  federação: `docs/coverage/national-coverage-gap-map-20260908.json`.
- `python tools/validate_sdd.py` aprovado.
- Os demais gates estáticos devem ser executados no fechamento do lote.

## Limitações mantidas

A consulta de página 2 continua rejeitada porque a fonte repetiu a janela da
página 1 na evidência live. O provider não é incluído na federação padrão e
não afirma total exaustivo ou inteiro teor para todo registro.

## Rastreabilidade

| Critério | Implementação/teste | Evidência |
|---|---|---|
| AC-001/AC-002 | `NanoJurisClient` e testes de autoridade | `tests/test_tre_sjur_jurisprudencia.py` |
| AC-003/AC-004 | transporte compartilhado e estados de página | `src/nanojuris/providers/tse_sjur_jurisprudencia.py` |
| AC-005 | capability opt-in e roteamento padrão | `src/nanojuris/client.py` |
| AC-006 | gates locais e suíte focada | comandos registrados no handoff do lote |

## Atualização 2026-09-12

- O filtro remoto oficial de segundo grau (`Acórdão`, `Decisão monocrática`,
  `Resolução`, `Decisão sem resolução`) foi validado serialmente nas 27 UFs;
  24 retornaram janelas filtradas válidas, TRE-SC retornou vazio autoritativo e
  TRE-GO/TRE-PB excederam o limite de corpo sem persistência de resposta:
  `docs/provider-discovery/tre-sjur-second-degree-type-filter-live-20260912.json`.
- `document_type` agora é traduzido para os rótulos oficiais (`acordao`,
  `decisao`, `resolucao` e `sentenca` no binding de primeiro grau); consultas
  incompatíveis com o grau são rejeitadas e não geram requisição ambígua.
- O classificador local aceita somente rótulos de segundo grau observados no
  contrato remoto; categorias não comprovadas, como `Consulta` e `Instrucao`,
  permanecem desconhecidas e não são promovidas por heurística.
- A sondagem de primeiro grau de 2026-09-12 agora é consumida pelo gerador de
  cobertura: `tre_sjur_first_degree` aparece com `live_status=valid`, escopo
  `SJUR/TRE/first/decision_type_filter` e retorno bounded observado, mas segue
  `lifecycle=candidate`, `unified_search=false` e sem promoção. Assim, a matriz
  não perde a evidência live nem confunde uma janela de uma UF com cobertura
  completa dos 27 TREs.
- A extensão de 2026-09-12 compila os controles estruturados observados na SPA
  oficial: `anoEleicao`, observações, etiquetas, município, fonte/número/volume
  de publicação e UF. Eles são filtros canônicos opcionais e aparecem como
  `native` somente em `TreSjur*`; TSE e demais providers rejeitam explicitamente
  esses campos quando não possuem contrato. O ano aceita somente listas
  numéricas no intervalo 1800–2200. Cobertura de paginação, total exaustivo e
  federação continuam inalterados.
- The `NanoJurisClient` facade now accepts the eight canonical structured
  filters and Portuguese aliases, forwards them into `JurisprudenceQuery`, and
  canonicalizes aliases for adaptive planning. The focused regression test
  `test_client_forwards_tre_structured_filters_and_portuguese_aliases` proves
  that the fields are not dropped or silently sent to an undeclared provider.
- A bounded live call through the same facade with Portuguese aliases returned
  HTTP 200 and one public TRE-SP result; the applied canonical fields are
  recorded without persisting response content in
  `docs/provider-discovery/tre-sp-client-filter-forwarding-live-20260912.json`.
- A nova sonda direta do mesmo contrato variou `pagina=0/1` e `tamanho=1` no
  TRE-SP. Ambas as respostas HTTP 200 retornaram 1.000 registros, total 7.057
  e a mesma sequência de IDs (hash
  `5515a1c83370e2fae5683f39d2b85345c5677a6813eae1c8651762d52ec8632a`), sem
  persistir corpo. A evidência está em
  `docs/provider-discovery/tre-sjur-pagination-parameter-recheck-live-20260912.json`;
  a rejeição de páginas maiores que 1 permanece correta.
- O gate documental foi validado para um acórdão público observado no TRE-SP:
  HTTP 200, `application/pdf`, 161.960 bytes, assinatura `%PDF-` e hash
  `1282651e11ac65b806541a475d909cda5e99f3a120977192e0da3a988e113891`.
  O corpo não foi persistido; somente os metadados redigidos estão em
  `docs/provider-discovery/tre-sp-sjur-document-live-20260912.json`. O
  catálogo enriquece a família com `full_text_status=valid`, mas não altera o
  bloqueio de federação causado pela paginação não comprovada.

### Coleta temporal particionada — 2026-09-12

- A sonda oficial TRE-SP para `direito`/`acordao` no intervalo
  `2025-01-01..2025-01-31` retornou HTTP 200, `totalRegistros=15` e 15 itens.
  A evidência redigida está em
  `docs/provider-discovery/tre-sp-sjur-date-partition-live-20260912.json`.
- O método opt-in `search_partitioned` divide somente intervalos explícitos em
  meses não sobrepostos, limita a 36 partições, solicita a janela oficial de
  1.000 itens e marca uma partição como completa apenas quando o total declarado
  coincide com os itens retornados sem atingir esse limite. IDs são deduplicados
  e o trace registra todas as faixas consultadas.
- A paginação remota geral continua não comprovada; a família permanece opt-in
  e fora da federação padrão. Nenhum bloqueio foi contornado e nenhum corpo de
  resposta foi persistido.
- Verificação: `tests/test_tre_sjur_jurisprudencia.py` (34 passed),
  `tests/test_provider_coverage.py`, Ruff, mypy, compileall, `validate_sdd` e
  suíte completa (`1806 passed, 26 skipped`).
- Uma segunda execução bounded cobriu doze partições mensais de
  `2020-01-01..2020-12-31`: 203 registros retornados, `total_known=true` e
  `complete=true`, sem persistir corpos. A evidência redigida está em
  `docs/provider-discovery/tre-sp-sjur-date-partition-year-live-20260912.json`.
- A mesma sonda mensal, serializada, foi executada em todas as 27 autoridades
  TRE para janeiro de 2025: 27/27 retornaram HTTP 200 e cada total coincidiu
  com os registros devolvidos (3–68 por UF). O resultado agregado está em
  `docs/provider-discovery/tre-sjur-date-partition-uf-sweep-live-20260912.json`;
  isso valida a família em uma janela bounded, não o acervo histórico nem a
  paginação geral.
- O dispatcher `TreSjurJurisprudenciaFamilyProvider` agora expõe o mesmo método
  `search_partitioned`, exige a autoridade TRE explicitamente e normaliza o
  `source`/`SourceTrace` para a família sem perder os IDs qualificados por UF.
- A sonda é reproduzível por `python tools/probe_tre_sjur_date_partition.py`;
  seus parâmetros controlam intervalo, tipo, timeout e intervalo serial, e o
  arquivo gerado contém apenas metadados redigidos.
- A superfície de primeiro grau retornou vazio autoritativo bounded para as 27
  UFs em janeiro de 2025 (`document_type=sentenca`), registrado em
  `docs/provider-discovery/tre-sjur-first-degree-date-partition-uf-sweep-live-20260912.json`.
  Isso não significa ausência histórica. Em TRE-MG, a janela 2022–2024 em 36
  partições retornou 3/3 registros completos, com evidência em
  `docs/provider-discovery/tre-mg-first-degree-date-partition-live-20260912.json`.

### Reconciliação de instâncias por UF — 2026-09-12

- O catálogo passou a declarar `runtime_expansion` para
  `tre_sjur_jurisprudencia` e `tre_sjur_first_degree`, com padrão
  `tre_<uf>_sjur_*`, fábrica compartilhada e as 27 autoridades TRE.
- As instâncias continuam bindings operacionais de diagnóstico; não são
  contadas como 54 providers independentes e `federation_default=false` é
  explícito até que cada UF feche paginação, documentos e fixtures.
- A reconciliação confirmou 84 IDs canônicos no catálogo, 79 providers no
  runtime padrão e 138 bindings quando o modo candidato é solicitado. O teste
  `test_tre_family_runtime_instances_are_explicitly_reconciled` cobre a
  correspondência e evita divergência futura entre runtime e inventário.
- Gates executados após a alteração: `validate_sdd`, Ruff, formatação, mypy,
  `compileall`, auditoria offline e suíte completa (`1804 passed, 26 skipped`).
