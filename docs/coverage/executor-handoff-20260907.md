# Handoff técnico — execução local NanoJuris (2026-09-07)

Este arquivo é o ponto de entrada para outro modelo continuar a execução sem
repetir diagnóstico nem assumir cobertura que não foi comprovada. A árvore
continua sem commit, push, publicação, deploy ou alteração de produção.

## Já implementado localmente

- Busca live determinística v1: `search_intent.py`, `adaptive_search.py`,
  `relevance.py`, outcomes explícitos e deduplicação conservadora.
- API aditiva: `mode` (`adaptive`, `selected`, `all`, `legacy`) e
  `ranking_version` (`legal-live-v1`, `legacy`) na biblioteca, plataforma e
  Function.
- Projeção web allowlisted com razões, estados de fonte, chips de intenção,
  merge global, ondas 3/4/rest para listas selecionadas e congelamento após
  interação com ação de aplicação da nova ordem.
- Cache de transporte com namespace `TransportRequest.cache_version`, TTL,
  limite de bytes e `stale-if-error` explícito; não é índice pesquisável.
- Gate estático sem IA/vetor: `python tools/audit_search_no_ai.py --json`.
- Benchmark e guia: `docs/benchmarks/live-ranking-v1.*` e medição local em
  `docs/benchmarks/live-ranking-performance-20260907.json`.
- Telemetria opcional HMAC em `src/nanojuris/search_telemetry.py`, sem texto de
  consulta, cookies, headers ou inteiro teor.
- Programa nacional e técnicas de acesso legítimo: SDD 0078 e filhos 0079–
  0085, incluindo `legitimate-techniques.md`, `access-policy.md` e o playbook
  `docs/coverage/public-access-boundary-playbook-20260908.md`. CAPTCHA/WAF/
  Turnstile/login/TLS e rate limit continuam estados explícitos; não há bypass.

## Comandos de verificação

Na biblioteca:

```powershell
$env:PYTHONPATH='src'
python -m pytest -q tests/test_search_intent.py tests/test_adaptive_search.py tests/test_relevance.py tests/test_search_many_ranking.py tests/test_search_outcomes.py tests/test_federated_equivalence.py tests/test_transport_runtime.py tests/test_search_no_ai.py tests/test_search_telemetry.py tests/test_live_ranking_benchmark.py tests/test_live_ranking_performance.py
python tools/audit_search_no_ai.py --json
python tools/benchmark_live_ranking.py --rounds 25 --candidates 240
python -m ruff check .
python -m ruff format --check .
python -m mypy src
python -m compileall -q src tools tests
python -m pytest -q
```

Na plataforma:

```powershell
python -m pytest -q
python -m ruff check src tests
python -m ruff format --check src tests
python -m mypy src
node --check src/nanojuris_platform/web/app.js
```

## Pendências honestas

- SDD 0077: T04 (baseline formal), T62 (rótulos humanos, calibração e
  holdout) e T64 (suíte final + smokes bounded + fechamento dos gates).
- SDD 0078: 26 tarefas de cobertura nacional e acesso legítimo permanecem
  planejadas; fontes externas bloqueadas não podem ser promovidas localmente.
- SDDs 0079–0085: workpacks de reconciliação, runtime público, CJPG, famílias
  trabalhista/eleitoral, federal/superior/militar, inteiro teor e certificação
  contínua ainda requerem execução por lotes.
- 0069 T07 permanece bloqueado por dependências externas. Não converter
  bloqueio, timeout, 403, 429, TLS ou schema inválido em vazio.
- Publicação, OCI, Terraform, secrets, IAM e produção continuam fora do
  escopo autorizado.

## Próxima ação segura

1. Rodar a suíte completa da biblioteca e da plataforma.
2. Gerar baseline/ledger/matriz com os comandos de `0078`.
3. Fechar T04 e registrar o resultado no `0077/verification.md`.
4. Adicionar julgamentos humanos ao benchmark sem inserir texto pessoal ou
   conteúdo não autorizado; só então medir T62/holdout.
5. Executar os workpacks 0079–0085 em lotes pequenos, mantendo fontes
   bloqueadas em `access_blocked`/`blocked_recheck`.
6. Antes de qualquer release, revisar divergências e obter autorização humana
   separada para publicação/deploy.
