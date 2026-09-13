# Verificação — convergência ouro

Referência: `specs/changes/0070-provider-capability-gold-convergence/spec.md`
Status: `verified_local; release_approval_pending`

## Current verification snapshot - 2026-09-07

The local implementation and quality gates are verified against the current
worktree. The generated evaluator reports 64 catalog entries, 58 runtime
providers, 47 strict `provider_gold` providers and 5 providers without a recent
live check. The remaining gaps are explicit operational or external-source
states; they are not treated as empty results. TJAP/TJMA filter declarations
now classify every common filter as native, translated, validated-scope or
explicitly unsupported; no runtime provider remains blocked by an unverified
filter declaration.

- Full suite: 1,420 passed, 26 skipped.
- Ruff, format check, mypy, compileall, SDD validation and diff check: passed.
- Release compatibility: 64/64 providers passed.
- Local release rehearsal: passed (sdist, wheel, twine check and size budgets).
- No commit, push, publication or deploy was performed.

The release gate remains pending only for external access/legal review and the
human approval required before publication. This is not evidence of missing
local implementation.

## Execucao adicional

### Fechamento offline de workpacks — 2026-09-06

`tools/complete_provider_workpacks.py --write` atribuiu uma disposiÃ§Ã£o
terminal a todas as 60 fontes: 38 `accepted_with_limitations` e 22
`deferred_with_review`. As fontes adiadas conservam explicitamente a razÃ£o e
a condiÃ§Ã£o de retomada; nenhuma foi convertida em resultado vazio.

- Onda 0: ledger e workpacks regenerados para 60 providers; o denominador e
  reconciliado automaticamente e estados desconhecidos permanecem explicitos.
- Onda 1: contratos canonicos, planos federados de filtros, fingerprints e
  comparacao diferencial foram implementados sem quebrar interfaces legadas.
- A auditoria de contratos agora incorpora `filter_semantics` explícito dos
  adapters, distinguindo `translated`/`local_postfilter` de fallback legado;
  o ledger foi regenerado com estados terminais explícitos; a lacuna de filtros
  permanece auditável por provider e não há semântica implícita.
- Hardening eproc: consultas com `degree`/`instance` sao traduzidas para o
  filtro oficial `selOrigem[]`; resultados sem grau identificavel ou fora do
  grau solicitado geram erro de contrato, nunca falso vazio.
- Smoke live bounded: TJRN (1), TJRO/TJGO (4), TJPI (2) e o lote CJSG
  (4/4 buscas) passaram; três detalhes foram corretamente classificados como
  controle de acesso e bloqueios/vazios continuam separados.
- Suite NanoJuris: 1.260 testes passaram e 23 foram pulados por opt-in/live ou
  dependencia opcional. Ruff, format, mypy, compileall, SDD e diff check
  passaram.
- Federated promotion smoke: 38/38 fontes habilitadas foram consultadas; a
  execucao atual nao teve erro operacional, mas nove fontes mantiveram total
  desconhecido e a coleta global permaneceu incompleta (nenhuma foi convertida
  em vazio).
- Eproc estadual smoke: TJRJ/TJSC 2/2 buscas de segundo grau válidas, com
  `degree`/`instance` explícitos e corpos não persistidos.
- Eproc detail smoke: TJRJ/TJSC 2/2 rotas públicas de inteiro teor retornaram
  texto; somente hashes, MIME, tamanho e status foram persistidos.
- TJRO recebeu pós-filtros canônicos bounded para grau, instância, coleção,
  tipo, datas e vocabulário textual; TJGO passou a declarar e testar as
  traduções oficiais de `Id_Instancia`, tipo e intervalo de datas.
- TJPI passou a declarar explicitamente filtros nativos/traduzidos e filtros
  não oferecidos pelo portal, mantendo a restrição pública à coleção CJSG.
- A família e-SAJ/CJSG passou a validar escopo de segundo grau, ramo,
  autoridade e coleção antes da requisição; zero-resultados explicitamente
  declarados agora carregam `total_known=true` e o `SearchPage` preserva o
  plano de filtros aplicados.
- O contrato de filtros agora possui o estado `validated_scope`: dimensões
  fixas do provider (autoridade, ramo, grau, instância e coleção) são
  validadas pelo adapter sem serem fingidas como parâmetros remotos. Isso
  reduz omissões silenciosas na federação e torna a transformação auditável.
- O piloto eproc passou a expor no `SearchPage` os filtros nativos,
  traduzidos e pós-filtrados; TRF4 agora declara explicitamente o contrato
  compartilhado e os campos não suportados.
- O pipeline documental agora valida MIME por cabeçalho e magic bytes, registra
  hash/tamanho/método, conta páginas PDF quando possível e classifica PDF sem
  páginas como formato estruturalmente inválido, sem confundir com vazio real.
- A regressão de paridade Juscraper confirma que todas as 26 superfícies
  upstream cobertas possuem binding registrado no runtime NanoJuris; candidatos
  sem equivalente continuam fora da promoção.
- SDK, CLI, MCP e Studio agora expÃµem o mesmo conjunto de refinamentos do
  contrato canÃ´nico; o MCP canÃ´nico preserva o envelope de pÃ¡gina e a
  federaÃ§Ã£o publica `source_filters_applied` por fonte.
- O avaliador de cinco eixos permanece conservador: 3 providers `provider_gold`
  no snapshot atual; os demais continuam pendentes por filtros, campos,
  documentos ou evidência live.

- Studio: o payload agora expÃµe `filter_intersection` e `filter_union` para
  as fontes padrÃ£o, reconhece semÃ¢nticas v2 aplicÃ¡veis como filtros de UI e
  publica `filter_application` como alias contratual de
  `source_filters_applied`.
- O Workbench agora renderiza a cobertura de filtros ao lado do seletor de
  fontes, com alternÃ¢ncia explÃ­cita entre filtros comuns e uniÃ£o; TypeScript e
  build Vite foram executados com bundle reproduzÃ­vel.

## Ambiente

- Data: 2026-09-06
- Escopo: execução local com chamadas live bounded; sem alteração de runtime
- Worktree: alterações anteriores preservadas

## Comandos executados

```text
Leitura de AGENTS.md, specs/constitution.md e specs/README.md
Inspeção dos SDDs 0007, 0026, 0031, 0032, 0038 e 0069
Leitura programática de provider-catalog.full.json
Leitura programática de provider-quality.json
Leitura programática de unified-contract-matrix.json
Leitura programática de document-capability-inventory.json
Leitura programática de all-provider-sweep.json
python tools/validate_sdd.py
git diff --check
```

## Execução da Onda 0

`python tools/build_provider_capability_ledger.py --write` gerou o ledger
determinístico com 60 providers (52 runtime, 7 candidatos e 1 família).
Os testes focados do ledger, workpacks e auditoria de contrato passaram: 11.
Filtros não verificados, estados live não válidos e capacidades documentais
desconhecidas permanecem explícitos; nenhum provider foi promovido.

## Execução da Onda 1

Foram adicionados os contratos tipados de evidência, campo, documento e
aliases canônicos. O comparador diferencial offline de páginas e filtros foi
incluído, e `FederatedSearchPage` agora preserva os planos por fonte com
filtros nativos, traduzidos, locais e omitidos. As interfaces legadas foram
mantidas e os testes focados passaram.

## Resultados

| Gate | Resultado | Evidência |
| --- | --- | --- |
| Linha de base | `passed` | 60 catalogadas, 52 runtime, 38 federadas |
| Divergência de ouro | `passed` | 14 maturity gold versus 32 quality gold |
| Lacuna de filtros | `passed` | 100% das declarações comuns possuem estado terminal explícito |
| Lacuna documental | `passed` | 18 runtime sem full text declarado |
| Arquitetura | `passed` | ledger, discovery em oito passes e cinco eixos ouro |
| Decomposição | `passed` | ondas 0–9 e T01–T42 |
| SDD estrutural | `passed` | `python tools/validate_sdd.py` |
| Cobertura do board | `passed` | 60/60 IDs do catálogo, sem ausentes ou extras |
| Rastreabilidade | `passed` | 24 requisitos e 15 critérios presentes na matriz |
| Higiene do diff | `passed` | `git diff --check -- specs/changes/0070-provider-capability-gold-convergence` |
| Implementação | `pending` | fora da fase atual de planejamento |

## Rastreabilidade

T01–T04 fecham a fase de planejamento. REQ-001 a REQ-024 estão ligados a
AC-001 a AC-015 e às tarefas de implementação em `traceability.md`.

## Divergências e riscos residuais

- Os artefatos de discovery possuem datas diferentes; a Onda 0 deve reconciliar
  freshness antes de produzir prioridades definitivas.
- `gold` legado não equivale a `provider_gold` até a nova avaliação.
- Não é possível prometer inteiro teor em fonte que comprovadamente não o
  publica; o estado terminal deve permanecer explícito.

## Decisão

- [x] Planejamento pronto para revisão e execução local.
- [ ] Implementação concluída.
- [ ] Aprovado para release.

## Correção de paridade TJRR — 2026-09-06

- O adapter passou a enviar o formulário JSF/PrimeFaces completo na busca e
  paginação (ViewState, defaults, flags AJAX e cabeçalhos de navegador).
- O resultado canônico agora explicita `degree=second`, `instance=second`,
  `branch=state`, `authority=TJRR` e `collection=CJSG`.
- Filtros de relator e órgão julgador são traduzidos para os valores do
  formulário; escopos incompatíveis são rejeitados.
- Smoke live bounded confirmou a segunda página com IDs distintos; detalhe
  sem bytes continua classificado como indisponível.
- O agregador de evidência aceita `observed_at` ou `generated_at`, evitando
  perder o frescor de smokes dedicados.

## Fechamento dos pilotos de familia - 2026-09-06

Os pilotos T16-T22 foram verificados localmente, sem promover novos
providers: eSAJ (`tjac_cjsg`/`tjsp_cjpg`), eproc (`trf4_eproc_jurisprudencia`),
PJe (`tjpb_pje_jurisprudencia`), GraphQL/BFF/REST (`tjba_graphql`,
`tjpa_jurisprudencia_bff`, `tjmt_jurisprudencia_api`), Projudi/JSF/Solr
(`tjgo_projudi_jurisprudencia`, `tjpe_jurisprudencia`, `tjrr_juris`,
`tjrs_solr`), dataset (`tcu_jurisprudencia`) e componentes compartilhados.
Os testes de contrato, parser, paginacao, filtros, redaction e federacao
passaram; a certificacao individual permanece nas tarefas T23-T32.

## Execução de qualidade federada

### T40 — bloqueio explícito de gaps de capacidade

O avaliador agora expõe `unverified_filters`, `unverified_fields` e
`provider_gold_blocked_reasons` por provider, além das contagens agregadas
`blocked_by_unverified_filters` e `blocked_by_unverified_fields`. A promoção
continua possível apenas quando essas listas estão vazias. Na execução mais
recente de 2026-09-06, os 35 providers `provider_gold` e os demais providers
tinham declarações de filtro terminais; nenhum permaneceu bloqueado por filtro
`unverified`. Gaps de acesso, documentos, operação e promoção continuam
separados e auditáveis para as ondas T23–T32.

## Revisão AC-001—AC-015 — 2026-09-06

| Critério | Estado | Evidência/limitação |
|---|---|---|
| AC-001 | passed | ledger/workpack gerado para 60/60 fontes |
| AC-002 | passed | IDs reconciliados entre catálogo, runtime, discovery e live |
| AC-003 | passed | nenhum dos 3 `provider_gold` possui filtro `unverified` |
| AC-004 | passed | todas as declarações de filtros possuem estado terminal explícito |
| AC-005 | partial | campos não classificados permanecem em providers não ouro |
| AC-006 | partial | estados documentais ainda incompletos em fontes candidatas |
| AC-007 | partial | detalhe/documento depende de disponibilidade de cada fonte |
| AC-008 | passed | filtros ausentes são explicitamente omitidos/unsupported |
| AC-009 | passed | pilotos e validadores cobrem paginação, vazio, total e ordenação |
| AC-010 | passed | envelope federado expõe `filter_application` por fonte |
| AC-011 | passed | avaliador separa os cinco eixos e bloqueia ouro inválido |
| AC-012 | passed | candidatos/família fora do runtime funcional, com workpack |
| AC-013 | passed | novos providers entram no denominador automaticamente |
| AC-014 | passed | suíte 1.279 pass, 24 skips opt-in, Ruff, format, mypy, compileall e SDD verdes |
| AC-015 | passed | relatório separa filtros, dados, documentos, operação e federação |

Esta revisão fecha T42 como auditoria; não declara conclusão do programa. As
linhas `partial` permanecem abertas nas tarefas T23–T32 e nos workpacks 0069.

- A validação federada agora possui `validate_federated_page`, verificando
  ordenação estável, deduplicação de identidades, limites e coerência de
  completude sem mutar resultados.
- Foi executado shadow mode bounded com
  `python tools/run_federated_shadow.py --text responsabilidade --page-size 1`.
  O envelope redigido está em
  `docs/provider-discovery/federated-shadow-20260906.json`; a execução mais
  recente comparou janelas de 47 e 46 registros, com 45 identidades
  coincidentes (overlap 0,9375). A alteração de conjunto foi registrada como
  `stable_identity_set_changed` e `result_count_changed`, sem corpos, cookies
  ou tokens persistidos e sem habilitar rollout.

## QA documental bounded - 2026-09-06

## Paridade TJRJ eJURIS - 2026-09-06

Foi implementado um adapter NanoJuris independente para o fluxo WebForms/XHR
observado no Juscraper. A chamada publica bounded retornou HTTP 200, total
45.643 e texto de segundo grau. Fixtures e testes cobrem sucesso, vazio
autoritativo, schema drift, pagina dois, escopo e acesso controlado. Os gates
tecnicos foram satisfeitos e `tjrj_ejuris` foi promovido ao runtime e a
federacao padrao; a matriz nacional continua creditando CJSG pelo binding
eproc, sem duplicar a superficie complementar.

Suite apos esta alteracao: **1.288 pass, 25 skips**. Nenhum commit, push,
deploy ou alteracao de producao foi executado.

- T28 revalidou as 34 rotas runtime declaradas com inteiro teor em sete lotes:
  19 verificacoes completas, 13 parciais e 2 falhas de transporte/acesso.
- T29 cobriu os 17 providers `link_only`/`unknown` selecionados pelo inventario:
  6 completos, 2 parciais, 2 vazios explicitos e 7 falhas classificadas; nenhum
  bloqueio, CAPTCHA, SSL, 403/405 ou fonte indisponivel foi convertido em vazio.
- O `tjpr_jurisprudencia` passou a expor `get_document` por URL HTTPS explicita,
  usando o pipeline compartilhado de MIME, tamanho, hash e `SourceTrace`.
  A capacidade declarada mudou para `document_link`; IDs opacos sao aceitos
  somente quando vieram da busca atual e foram associados ao slug oficial
  observado (IDs arbitrarios continuam rejeitados).

## Extração PDF CJSG compartilhada - 2026-09-06

- `extract_cjsg_document_text_bytes` deixou de tratar PDFs como placeholders e
  passou a delegar ao extrator PDF comum, preservando bytes, status, avisos e
  transformações; PDF escaneado continua explicitamente dependente de OCR opt-in.
- Smoke bounded do `tjms_cjsg` confirmou o efeito em fonte pública: PDF de
  475.946 bytes, `application/pdf`, inteiro teor extraído com 41.313 caracteres,
  sem falhas de documento.
- Smoke bounded do `tjpr_jurisprudencia` confirmou detalhe HTML publico de
  51.731 bytes e 14.242 caracteres, resolvido pelo ID retornado na propria
  busca, sem reconstrução de slug.
- Smoke bounded do `tce_pr_viajuris` confirmou URL oficial do ViaJuris, PDF de
  430.453 bytes e 9.544 caracteres extraídos; o ID da linha CSV foi resolvido
  somente pelo mapa observado durante a busca.
- Smoke bounded do `cnj_jurisprudencia` confirmou PDF oficial de 430.737 bytes
  e 36.087 caracteres extraídos; IDs de resultados agora resolvem apenas URLs
  oficiais observadas no catálogo atual.

### Revalidação final do ciclo — 2026-09-06

- `run_cjsg_live_smoke.py --page-size 1`: 4/4 buscas CJSG retornaram dados;
  1 detalhe foi extraído e 3 permaneceram `access_control_required`, sem
  conversão para vazio.
- `run_federated_promotion_smoke.py --page-size 1`: 38 fontes habilitadas
  consultadas; 38 responderam, 0 registros inválidos e 1 erro explícito
  (`tst_jurisprudencia` HTTP 400). A completude permaneceu falsa por totais
  desconhecidos em 17 fontes, como previsto pelo contrato.
- Suíte completa após CNJ/TCE-PR/TJPR/STF: 1.279 testes passaram e 24 foram
  pulados por dependências opcionais ou live opt-in.
- Gates finais: Ruff, formatação, mypy, compileall, validação SDD e
  `git diff --check` aprovados.
- Reexecução focada de workpacks, avaliador ouro, QA documental e os quatro
  providers com fetcher compartilhado: 45 testes passaram.
- `stf_juris` também passou a resolver URLs de inteiro teor observadas pela
  API através do fetcher compartilhado, com allowlist de `portal.stf.jus.br`;
  o teste offline cobre HTML público e mantém WAF/403 como bloqueio explícito.

### Convergência de filtros — ciclo local atual

- TJBA GraphQL agora traduz `all_words`, `any_words` e `without_words` para a
  expressão booleana oficial de `assunto`, sem descartar filtros.
- TJMT traduz número, frase exata e combinações de palavras para o termo de
  busca da API pública.
- TJDFT, TJES CJSG/CJPG, TJSP CJPG, TJPR, TJRR, TJRS e TJRN distinguem
  explicitamente escopo validado, filtros traduzidos e campos não suportados.

O ledger gerado registra 60 providers, 52 em runtime, 1.820 declarações
terminais e zero declarações `unverified`. As capacidades continuam separadas
por semântica: filtros nativos/traduzidos são distinguíveis de pós-filtros
locais, escopo validado e recursos não oferecidos pela fonte; isso não promove
providers bloqueados nem altera o rollout federado.

As declarações foram fechadas também para fontes contextuais, catálogos,
informativos e endpoints bloqueados. Nesses casos, os filtros não expostos pela
fonte permanecem explicitamente `unsupported`, enquanto
autoridade/ramo/coleção/documento só são `validated_scope` quando fixados pelo
contrato do provider.

As rechecagens live bounded deste ciclo passaram para TJBA/CJSG (3 cenários),
TJES/CJSG (1 cenário) e TJRN (1 cenário). O TJMT respondeu HTTP 200 público
com uma página de tamanho 1, total reportado e texto extraído; os metadados
foram preservados no `SourceTrace`.

Uma chamada adicional do TJBA usando somente `all_words`, `any_words` e
`without_words` também respondeu HTTP 200 com resultado público. A validação
de entrada foi ajustada para aceitar esses filtros quando não há `text` ou
`exact_phrase` explícitos.

O smoke federado bounded mais recente (`--text "responsabilidade civil"
--page-size 1`) consultou 38 fontes, sem erros e sem registros inválidos. Foram
retornados 46 registros deduplicados; 18 fontes informaram total desconhecido,
por isso a coleção foi corretamente marcada como incompleta.

### Fechamento de semântica de filtros e rechecagem live — 2026-09-06

- As dez superfícies restantes sem mapa explícito de filtros receberam
  declarações conservadoras no runtime: CJF, CNJ, Justiça Eleitoral SJUR, STJ
  Dados Abertos, TCE-PR, TCE-SP, TCU, TJMA JurisConsult, TJPE e TRE-SP. O
  ledger resultante tem `unverified_filter_declarations=0`; recursos não
  expostos permanecem `unsupported` e não são anunciados pela federação.
- A suíte completa terminou com 1.280 testes aprovados e 24 skips esperados;
  Ruff, formatação, mypy, compileall, SDD e diff check também passaram.
- Rechecagem pública do STJ CKAN passou (catálogo e plano de sincronização sem
  download). O endpoint público do TST respondeu HTTP 400 sem corpo durante a
  chamada bounded; isso foi mantido como indisponibilidade externa, não como
  vazio, e o provider não foi promovido.
- O avaliador de qualidade foi regenerado após a atualização do catálogo:
  60 providers, 52 runtime, 51 `engineering_gold`, 38 `provider_gold`, 10 sem
  live recente e zero bloqueios por filtro ou campo não verificado.

### Extensão T30 — TCE-SP

- O provider `tce_sp_jurisprudencia` agora resolve URLs de boletins observadas
  na busca ou catálogo por `get_document`, usando `fetch_document_reference`
  com allowlist, MIME, limite, hash e `SourceTrace`.
- O parser rejeita links de navegação sem número de edição, evitando que a
  página inicial seja classificada como boletim.
- Evidência pública bounded: `docs/provider-discovery/tce-sp-document-live-20260906.json`.
- Testes: `tests/test_tce_sp_jurisprudencia.py` — 7 passed.

### Extensão T30 — STJ Informativo

- O provider `stj_informativo` recupera a URL CNOT pública observada mesmo
  quando o portal a entrega como texto sem âncora HTML.
- `get_document` usa somente CNOT no host oficial; o link do acórdão SCON
  permanece separado e não é baixado como fallback.
- Evidência bounded: `docs/provider-discovery/stj-informativo-cnot-live-20260906.json`.
- Testes: `tests/test_stj_informativo.py` — 17 passed.
