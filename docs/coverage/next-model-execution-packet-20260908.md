# Pacote de execução para o próximo modelo — NanoJuris

Versão: `2026-09-08`  
Escopo: continuidade local da cobertura nacional, qualidade de providers e
busca federada. Este pacote não autoriza commit, push, tag, publicação, deploy,
Terraform, OCI, IAM, secrets ou alteração de produção.

## Entrada rápida

Leia primeiro:

1. `AGENTS.md`;
2. `specs/constitution.md` e `specs/README.md`;
3. `docs/coverage/README.md` e `docs/coverage/source-of-truth.md`;
4. `specs/changes/0091-national-coverage-gold-handoff/`;
5. `specs/changes/0092-national-coverage-execution-blueprint/`;
6. `specs/changes/0078-national-coverage-lawful-access/`;
7. `docs/coverage/public-access-boundary-playbook-20260908.md`;
8. os artefatos de cada provider antes de alterá-lo.

Os inventários gerados são a autoridade para contagens. Regenere-os antes de
tomar decisões; os números abaixo são apenas o snapshot desta preparação.

## Snapshot verificado

| Indicador | Estado | Fonte |
|---|---:|---|
| Providers catalogados | 73 | `docs/registry/provider-catalog.full.json` |
| Providers em runtime | 68 | catálogo, `summary.implemented_sources` |
| Fontes na federação declarada | 50 | catálogo, `summary.unified_search_sources` |
| Fixtures de runtime completas | 68/68 | `docs/coverage/fixture-completeness-20260908.json` |
| Superfícies nacionais | 151 (125 obrigatórias) | `docs/coverage/surface-state-registry-20260902.json` |
| CJPG comprovado | 8/27 | `docs/topology/degree-coverage-matrix-20260901.json` |
| CJSG comprovado | 25/27 | mesma matriz |
| Workpacks estaduais completos | 25/27 | `docs/coverage/state-appellate-program-20260905.json` |
| Tarefas abertas | 60 (0 locais, 44 externas, 16 humanas) | `docs/coverage/open-task-audit-current.json` |
| Tarefas locais executáveis | 0 | auditoria de tarefas |

O estado nacional continua **25/27** para segundo grau estadual. Bloqueios
externos e decisões humanas não são convertidos em resultado vazio nem em
conclusão automática.

### Último lote local: TJAL ESMAL Banco de Sentenças

O provider `tjal_esmal_banco_sentencas` foi implementado para a coleção curada
de primeiro grau do ESMAL. A chamada pública bounded retornou 17 linhas com PDF
oficial (`HTTP 200`, `application/pdf`); a paginação e o termo inexistente foram
classificados como `total_unknown`, pois a página não fornece total autoritativo.
O PDF foi validado por MIME e assinatura, sem persistir corpo judicial. O
provider permanece `opt_in_only` até a decisão humana de promoção e retenção.

- SDD: `specs/changes/0096-tjal-esmal-banco-sentencas/`;
- evidência: `docs/provider-discovery/tjal-esmal-banco-sentencas-live-20260908.json`;
- contrato: `docs/source-contracts/tjal_esmal_banco_sentencas.md`;
- testes focados: `8 passed`;
- fixtures: `tests/fixtures/tjal_esmal_*.html` e `tjal_esmal_invalid.pdf`.

## Lote concluído nesta preparação

### TJMG/EJEF - Boletim de Jurisprudência

Provider: `tjmg_ejef_boletim_jurisprudencia`  
SDD: `specs/changes/0097-tjmg-ejef-boletim-jurisprudencia/`  
Evidência: `docs/provider-discovery/tjmg-ejef-boletim-live-20260908.json`  
Smoke federado: `docs/provider-discovery/tjmg-ejef-boletim-federated-live-20260908.json`

A API pública DSpace da coleção oficial EJEF respondeu HTTP 200 para uma
consulta bounded, com total conhecido 2 e dois boletins retornados. O parser
aceita tanto itens com resumo quanto boletins cujo texto jurídico está nos
assuntos e no PDF oficial; nenhum item é promovido como processo individual.
O documento original foi validado por MIME, tamanho e hash. A fonte entrou na
federação como coleção curada de segundo grau, com as limitações preservadas.

- testes focados: `7 passed`;
- fixtures: `tests/fixtures/tjmg_ejef_boletim_search.json`, `tjmg_ejef_boletim_empty.json` e `tjmg_ejef_boletim_invalid.json`;
- bypass: não utilizado;
- revisão humana pendente apenas para política de retenção/atualização.

### TRT2 — ementário oficial

Provider: `trt2_ementario_jurisprudencia`  
SDD: `specs/changes/0088-trt2-ementario-jurisprudencia/`  
Evidência: `docs/provider-discovery/trt2-ementario-live-20260908.json`

Rechecagem pública bounded (sem bypass) confirmou:

- coleção Tribunal Pleno: uma decisão de segundo grau, ementa extensa e PDF
  oficial público;
- coleção Corregedoria: uma decisão de segundo grau e ementa;
- `authority=TRT2`, `branch=labor`, `degree=second`, `instance=second`;
- total retornado pela janela estático e não autoritativo (`total_known=false`);
- PDF de exemplo com MIME `application/pdf`, 489171 bytes e hash registrado;
- o PDF pode ser imagem-only; não foi executado OCR de desafio nem OCR
  automático nesta etapa.

Decisão técnica: o provider passou a `supports_unified_search=true` e
`opt_in_unified_search=false`, entrando na federação padrão **somente como
fonte parcial**. `is_complete=false`, `total_unknown` e a limitação do
ementário permanecem explícitos. O ementário não substitui busca PJe nem prova
acervo exaustivo.

Arquivos funcionais/documentais do lote:

- `src/nanojuris/providers/trt2_ementario_jurisprudencia.py`;
- `tests/test_trt2_ementario_jurisprudencia.py`;
- `tests/fixtures/trt2_ementario_index.html`;
- `tests/fixtures/trt2_ementario_topic.html`;
- `tests/fixtures/trt2_ementario_topic_no_pdf.html`;
- `docs/providers/trt2_ementario_jurisprudencia/README.md`;
- `docs/source-contracts/trt2_ementario_jurisprudencia.md`;
- `specs/changes/0088-trt2-ementario-jurisprudencia/`.

### TJAC — ementario oficial

Provider: `tjac_ementario_jurisprudencia`  
SDD: `specs/changes/0094-tjac-ementario-jurisprudencia/`  
Evidencia: `docs/provider-discovery/tjac-ementario-live-20260908.json`

O volume PDF oficial do TJAC respondeu HTTP 200 com `application/pdf` e
593570 bytes. A chamada bounded com `degree=second`, `instance=second` e o
termo `constitucional` retornou 7 ementas; o parser recompõe registros cujo
cabecalho e ementa aparecem em paginas consecutivas. A superficie e
`TJAC/state/second/second/TJAC_EMENTARIO`.

Decisao tecnica: habilitar na federacao como fonte parcial, com
`total_known=false`, `is_complete=false` e sem alegacao de acervo integral. O
volume publica ementas, nao votos integrais separados, e nao foi criado indice
persistente.

Arquivos funcionais/documentais do lote:

- `src/nanojuris/providers/tjac_ementario_jurisprudencia.py`;
- `tests/test_tjac_ementario_jurisprudencia.py` e fixtures TJAC;
- `docs/providers/tjac_ementario_jurisprudencia/README.md`;
- `docs/source-contracts/tjac_ementario_jurisprudencia.md`;
- `specs/changes/0094-tjac-ementario-jurisprudencia/`.

### Reconciliacao de evidencia — TJRJ Banco de Sentencas

O artefato `docs/provider-discovery/tjrj-banco-sentencas-live-20260908.json`
foi normalizado com `source_id`, superficie `cjpg`, estado `partial`,
`access_status=public` e `extraction_status=partial`. O indice PDF oficial
respondeu HTTP 200, mas o primeiro documento observado respondeu HTTP 503.
O catalogo agora registra `live_status=partial` e removeu a divergencia de
evidencia; a colecao continua curada, opt-in e fora da cobertura CJPG integral.
Os dossies canonico/legacy do provider passaram a conter contrato, dados,
estados, fixtures, MCP e proximos passos completos, em paridade byte a byte.

### Rechecagem tecnica da busca

O ranker CPU-only foi medido novamente com 1.000 rodadas e 240 candidatos:
mediana 15,625 ms, p95 46,875 ms, maximo 78,125 ms, zero chamadas de rede.
O artefato e `docs/benchmarks/live-ranking-performance-20260908-rerun.json`.
T62 continua aberto apenas para rotulos humanos, calibracao no development e
validacao do holdout; nenhuma metrica juridica foi inventada.

## Gates executados no fechamento

- teste focado TRT2: `5 passed`;
- suíte de documentação/coverage/fixtures/baseline: `35 passed`;
- Ruff e formatação dos arquivos do lote: aprovados;
- mypy do adapter: aprovado;
- `validate_sdd.py`: aprovado;
- auditoria de artefatos e gates 0091: aprovadas, com TODOs apenas reportados;
- catálogos, ledger, matriz, workpacks e manifesto regenerados.

O próximo modelo deve rodar a suíte completa antes de qualquer novo lote.

### Fronteira eproc de primeiro grau

A evidencia `docs/provider-discovery/state-eproc-first-degree-boundary-live-20260908.json`
registra a sondagem bounded de TJRJ e TJSC com `degree=first`. As duas rotas
responderam HTTP 200, mas o contrato rejeitou registros de grau incompativel;
nao ha nova prova CJPG. A origem publica observada nao oferece rota distinta de
primeiro grau para essas instalacoes, portanto nao se deve repetir a mesma
consulta. O estado correto continua CJSG valido e CJPG pendente.

## Fechamento deste ciclo

Depois da reconciliacao TJRJ e da regeneracao dos artefatos dependentes, a
suite completa terminou com **1593 passed, 26 skipped** após a inclusão do provider TJMG/EJEF. Os skips sao testes
live opt-in e a dependencia opcional `lxml`; nao representam falha convertida
em vazio. Ruff, formatacao, mypy, compileall, `validate_sdd.py`,
`validate_executor_packet.py` e os audits 0091 passaram. A auditoria final
continua registrando **60 tarefas abertas**, todas classificadas como
`external_source` (44) ou `human_review` (16); tarefas locais executaveis:
**0**.

Estado nacional apos a rodada: **73 providers catalogados, 68 em runtime,
50 fontes declaradas na federacao, 8/27 CJPG, 25/27 CJSG e 25/27 workpacks
estaduais completos**. O TJRJ Banco de Sentencas agora aparece como live
`partial`, nao como `not_checked`, sem alterar a contagem de cobertura integral.

## Ordem de continuação

1. Rodar os comandos de baseline abaixo e confirmar que a worktree continua
   sem divergência catálogo/runtime.
2. Executar `python -m pytest -q` e todos os gates de qualidade.
3. Fechar somente providers com evidência pública reproduzível, priorizando os
   candidatos que ainda tenham uma rota oficial real: `tjse_jurisprudencia`,
   `trt2_pje_jurisprudencia` e superfícies CJPG ainda não cobertas.
4. Manter `tjap_tucujuris`, `tjma_jurisconsult`, TJSP/CJSG, TJCE/TJPE e toda
   fonte com CAPTCHA/WAF/SSO como bloqueio explícito quando o desafio for
   imposto.
5. Promover automaticamente apenas quando os oito gates da superfície forem
   verdadeiros: fonte oficial, contrato, adapter, fixtures, filtros/paginação,
   chamada live, qualidade/documento e smoke federado.
6. Atualizar inventários apenas ao final de cada lote de um a três providers.

## Comandos de baseline e fechamento

```powershell
Set-Location C:\Users\admin\Desktop\Nanojuris\repos\nanojuris
$env:PYTHONPATH = 'src'
python tools/audit_open_tasks.py
python tools/audit_provider_docs.py --write
python tools/build_provider_coverage.py --write
python tools/build_provider_quality.py --write
python tools/build_provider_capability_ledger.py --write
python tools/build_fixture_completeness.py --write
python tools/build_degree_coverage.py
python tools/build_surface_state_registry.py
python tools/build_state_appellate_program.py --write
python tools/build_promotion_manifest.py --write
python tools/build_surface_workpacks.py --write
python tools/build_0091_baseline.py --write
python tools/audit_0091_local_gates.py --write
python tools/audit_0091_artifacts.py --write
python tools/validate_executor_packet.py
python tools/validate_sdd.py
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
python -m mypy src
python -m compileall -q src tools tests
git diff --check
```

## Fronteira de acesso

São permitidos apenas API, export, feed, PDF/HTML/JSON/XML e navegação pública
normal publicados pela autoridade; cookies/CSRF efêmeros da sessão corrente;
redirects para hosts oficiais; retry transitório cooperativo; `ETag`/cache
efêmero; egress fixo aprovado; ou allowlist/suporte formal do tribunal.

Não usar solver/OCR de CAPTCHA, stealth, spoofing de fingerprint, rotação de
IP/proxy/User-Agent, replay de cookies/tokens, fuzzing de endpoint privado,
desativação de TLS, bypass de login, exaustão de rate limit ou enumeração
agressiva. CAPTCHA, Turnstile, WAF, 403, 429, timeout, TLS e schema inesperado
são estados de acesso explícitos.

## Condição de parada honesta

Só declarar cobertura nacional concluída se o programa indicar:

```text
summary.authorities == 27
summary.complete_8_of_8 == 27
summary.incomplete == 0
summary.coverage_claim == "27/27"
open_tasks == 0
```

Caso contrário, entregue a tabela objetiva de bloqueios externos e decisões
humanas, com URL, data/método bounded, classificação, evidência redigida,
alternativa oficial e ação necessária. Não fazer commit, push, publicação ou
deploy.
