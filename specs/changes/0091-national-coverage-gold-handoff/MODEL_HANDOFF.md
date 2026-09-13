# Handoff executavel para o proximo modelo

Snapshot: `2026-09-08`. Este arquivo e a porta de entrada operacional do SDD
0091. Ele complementa `GOAT_EXECUTOR_PROMPT.md`, `spec.md`, `design.md`,
`tasks.md` e `verification.md`; os inventarios gerados sao a fonte dos numeros.

## Estado local regenerado

| Indicador | Valor | Fonte |
|---|---:|---|
| Fontes catalogadas | 71 | `docs/registry/provider-catalog.full.json` |
| Providers em runtime | 66 | catalogo/runtime reconciliados |
| Fontes unificadas | 49 | resumo do catalogo |
| Superficies mapeadas/obrigatorias | 150 / 125 | `docs/coverage/surface-state-registry-20260902.json` |
| CJPG comprovados | 7/27 | `docs/topology/degree-coverage-matrix-20260901.json` |
| CJSG comprovados | 25/27 | mesma matriz |
| Fixtures de runtime | 66/66 | `docs/coverage/fixture-completeness-20260908.json` |
| Workpacks com oito gates | 61/150 | `surface-workpacks/manifest.json` |
| Tarefas abertas no escopo do handoff | 43 (35 externas, 8 humanas) | `docs/coverage/executor-packet-20260907.json` |
| Tarefas abertas no repositório | 57 (44 externas, 13 humanas) | `docs/coverage/open-task-audit-current.json` |

Validacao local final: **1578 testes aprovados, 26 skips**; Ruff, formatacao,
mypy, compilacao, SDD e os 10 gates locais passaram. Os skips sao smokes live
opt-in ou dependencia opcional; nao sao falhas locais.

Esses numeros nao significam 27/27, disponibilidade permanente ou aprovacao
juridica. Regenere tudo antes de iniciar qualquer lote.

## Leitura e ordem de execucao

1. Leia `AGENTS.md`, `specs/constitution.md`, `specs/README.md`,
   `docs/coverage/README.md` e todos os arquivos deste pacote.
2. Leia os SDDs 0070, 0077, 0078, 0080, 0081, 0082, 0083, 0084, 0089 e 0090.
3. Leia catalogo, capability ledger, surface registry, document inventory,
   quality, open-task audit e a referencia Juscraper.
4. Escolha 1--3 superfices em `provider-batch-plan.json`, obedecendo a ordem de
   descoberta do `AGENTS.md`.
5. Para cada uma, confirme fonte, grau, metodo, payload, filtros, paginacao,
   ordenacao, limites, erros, campos canonicos, documentos e provenance.
6. Faça uma chamada publica bounded; so confirme novamente se a primeira for
   semanticamente valida. Gere fixture sanitizada e teste focado.
7. Rode smoke federado opt-in, regenere inventarios e registre a decisao.

## Evidencias live recentes

- `stm-live-20260908-cycle70.json`: busca, pagina e detalhe validos.
- `trf4-live-20260908-cycle71.json`: busca, pagina e detalhe validos.
- `trf5-live-20260908-cycle72.json`: busca, pagina e detalhe validos.
- `eproc-detail-live-20260908-cycle73.json`: tres detalhes validos.
- `stj-live-20260908-cycle74.json`: STJ informativo e dados abertos validos;
  SCON explicitamente `access_blocked`.
- `eproc-detail-live-20260908-cycle75.json`: TNU, TRF2 e TRF6 com
  `degree=second`, `instance=second` e detalhe HTML valido.
- `tjrj-banco-sentencas-live-20260908.json`: indice PDF 200; documento
  individual `source_unavailable`.
- `tjba-cjpg-banco-sentencas-live-20260907.json`: formulario CJPG 200, POST
  exige CAPTCHA; estado `blocked_access`.
- `tjpa-banco-sentencas-live-20260907.json`: Banco de Sentencas restrito a
  magistrados; nao e superficie publica reproduzivel.
- `first-degree-secondary-probes-live-20260907.json`: TJRS DNS, TJAC/TJPR
  curatoriais/contextuais; nenhum foi contado como CJPG.
- `trf3-exact-process-live-20260908.json`: rechecagem por CNJ exato terminou
  em timeout de transporte de 20 segundos; o provider continua opt-in e o
  resultado não foi classificado como vazio.

## Limite de acesso legitimo

Permitido: API/export/feed/dataset/documento oficial; jornada anonima normal de
HTTP ou navegador; cookies/CSRF efemeros da sessao corrente; redirects oficiais
allowlisted; paginacao publicada; Retry-After, retry transitivo cooperativo,
ETag/Last-Modified; egress fixo aprovado; allowlist ou rota de homologacao
fornecida pelo tribunal; desafio mediado manualmente sem persistir token.

Proibido: solver ou OCR de CAPTCHA/Turnstile; stealth/fingerprint spoofing;
rotacao de IP/proxy; replay de cookies, CSRF, tokens ou URLs assinadas; fuzzing
de endpoints privados; bypass de login; downgrade de TLS; exaustao de rate
limit; alteracao de termos/robots. Nao existe zona de sombra operacional.
CAPTCHA, WAF, 403, 429, login, timeout, TLS e schema inesperado sao estados
explicitos, nunca `authoritative_empty`.

## Gates de promocao

So habilite uma superficie na federacao quando todos forem verdadeiros:

```text
runtime=true
degree_contract=valid
fixtures=complete
live_status=valid
quality_gate=passed
access_status=public
federation_status=enabled
promotion_decision=automatic_technical_approval
```

`implemented`, `live_validated`, `quality_passed`, `federation_enabled` e
`legal_status` sao dimensoes independentes. Nao declare 27/27 por existencia de
adapter.

## Fechamento do lote

```powershell
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
python tools/audit_0091_local_gates.py --write
python tools/audit_0091_artifacts.py --write
python tools/build_0091_baseline.py --write
python tools/validate_sdd.py
python -m pytest -q
python -m ruff check .
python -m ruff format --check .
python -m mypy src
python -m compileall -q src tools tests
git diff --check
```

## Parada honesta e limite de release

Se restarem apenas fontes bloqueadas externamente ou decisoes humanas, registre
tribunal, URL, data/metodo, classificacao, evidencia, alternativa oficial e
acao necessaria; isso e uma parada legitima, nao conclusao. Nao repetir chamadas
contra bloqueio estavel.

Nao fazer commit, push, tag, publicacao, deploy, Terraform apply, alteracao OCI,
secrets/IAM ou mudanca de producao neste handoff.
