# Descoberta de providers

O NanoJuris possui uma camada de descoberta separada dos providers oficiais.
Ela observa fontes públicas, registra evidências reproduzíveis e gera rascunhos
SDD para revisão.

## Execução HTTP bounded

```bash
python tools/provider_discovery.py \
  --url https://example.org/jurisprudencia \
  --domain example.org \
  --max-pages 20 \
  --output .tmp/provider-discovery
```

O comando gera `evidence.json` e os drafts `research.md`, `clarify.md`,
`spec.md`, `design.md`, `tasks.md`, `verification.md`, `traceability.md` e
`threat-model.md`.

## Navegação dinâmica opcional

Quando o portal público depende de JavaScript, a execução pode usar o adapter
Playwright:

```bash
python tools/provider_discovery.py \
  --url https://example.org/jurisprudencia \
  --domain example.org \
  --browser \
  --output .tmp/provider-discovery-browser
```

O modo dinâmico observa documentos e chamadas `xhr`/`fetch`, mantendo método,
URL, payload redigido, headers, status, bytes e hash.

## Interpretação

Uma execução de descoberta produz hipóteses e evidências. Ela não registra
provider, não edita catálogo e não substitui fixtures ou testes offline. Rotas,
campos, paginação, ordenação, identidade e texto integral precisam ser
confirmados no contrato do provider antes da implementação.

O replay de `evidence.json` reprocessa a análise localmente, sem nova consulta:

```python
from nanojuris.discovery.replay import replay_analysis

result = replay_analysis(".tmp/provider-discovery/evidence.json")
```

Também é possível usar a mesma capacidade pelo CLI principal:

```bash
nanojuris descobrir-provider https://example.org/jurisprudencia \
  --dominio example.org \
  --saida .tmp/provider-discovery
```

Para repetir uma investigação sem nova consulta, use um cache local:

```bash
nanojuris descobrir-provider https://example.org/jurisprudencia \
  --dominio example.org \
  --cache-dir .tmp/provider-cache \
  --saida .tmp/provider-replay
```

Agentes conectados ao MCP podem chamar `discover_provider` e receber as métricas
da rodada e o diretório de artefatos produzido.

## Auditoria offline do catálogo

Para revisar candidates já mapeados sem consultar a internet, use:

```bash
python tools/audit_provider_discovery_offline.py
```

O comando cruza o catálogo, dossiers, contratos, módulos, testes e fixtures.
Quando há fixture local, executa a extração de rotas e a sugestão de seletores
somente sobre os bytes versionados. O resultado fica em
`docs/provider-discovery/offline-audit.md` e `.json`.

`no_local_fixture` significa falta de evidência offline; não significa resultado
vazio nem autoriza a criação automática de um provider.

## Matriz do contrato unificado

Para auditar se os providers realmente oferecem os mesmos filtros e o mesmo
perfil de dados, gere a matriz offline:

```bash
python tools/audit_unified_contract.py
```

Para repetir o discovery live aprofundado antes da auditoria:

```bash
python tools/discover_all_providers.py --live --include-catalog-candidates \
  --max-pages 5 --max-depth 2 --timeout 8 --delay 0.25
```

Os artefatos ficam em
`docs/provider-discovery/unified-contract-matrix.json` e
`docs/provider-discovery/unified-contract-matrix.md`. A matriz separa decisão,
precedente, conteúdo curado e documento de apoio; também evidencia filtros não
declarados, paginação/completude desconhecidas e o snapshot live mais recente.

O fechamento de TODOs é controlado pelo ledger
`docs/provider-discovery/provider-closure-ledger.md` e seu JSON. Cada item fica
como evidência local, bloqueio externo, candidate pendente de adapter ou exige
nova evidência; nenhum item é removido silenciosamente.

```bash
python tools/build_provider_closure_ledger.py
```

A rodada live bounded mais recente de todos os providers esta em
[`all-provider-sweep-20260902-cycle24.json`](provider-discovery/all-provider-sweep-20260902-cycle24.json).

## Descoberta nacional de primeiro grau

Para mapear rotas públicas de sentenças/CJPG nos 27 TJs sem inferir cobertura,
execute a sondagem bounded:

```bash
python tools/discover_first_degree_routes.py --probe-candidates
```

O resultado fica em
[`first-degree-route-inventory-20260906.json`](provider-discovery/first-degree-route-inventory-20260906.json)
e no respectivo Markdown. O comando consulta apenas páginas oficiais, registra
metadados e hashes (nunca corpos), e classifica cada rota como processual,
candidata a jurisprudência ou contextual. Rotas candidatas ainda exigem
contrato, fixture, chamada live, qualidade e gate de federação próprios.
Ela observou 50 providers, 146 rotas declaradas e 2.394 observacoes de rotas;
os oito candidates tambem foram sondados em
[`catalog-candidates-sweep-20260902-cycle25.md`](provider-discovery/catalog-candidates-sweep-20260902-cycle25.md)
e no JSON correspondente. Dez fontes exibiram sinais de controle de acesso.
Observacao de rota nao equivale a retorno de jurisprudencia e estados de
robots, acesso, vazio e resposta valida continuam sendo diagnosticos, nao
promocoes. O sweep anterior permanece como evidencia historica.

Os contratos de dados publicos exercitados na mesma janela estao em
[`public-contract-live-20260902-cycle21.md`](provider-discovery/public-contract-live-20260902-cycle21.md).
Foram nove cenarios validos e dois bloqueios de acesso (STJ/SCON e TJSP/CJSG),
sem converter bloqueios em resultados vazios.

A rechecagem bounded de paginaÃ§Ã£o do TJRN (duas paginas, 20 registros e total
53.366) estÃ¡ em
[`tjrn-jurisprudencia-pagination-live-20260902-cycle22.md`](provider-discovery/tjrn-jurisprudencia-pagination-live-20260902-cycle22.md).
Ela confirma apenas a janela page=1/page=2 e mantÃ©m o provider como opt-in.

O ciclo 3 rechecóu as rotas alternativas oficiais do candidato TRF3 e registrou
timeouts de transporte sem os converter em resultados vazios:
[`trf3-live-recheck-20260901-cycle3.md`](provider-discovery/trf3-live-recheck-20260901-cycle3.md).

## Rechecagem de bindings de grau

A rechecagem bounded dos bindings de grau CJPG/CJSG está em
[`degree-bindings-live-20260902-cycle26.md`](provider-discovery/degree-bindings-live-20260902-cycle26.md).
TJES/CJPG, TJES/CJSG e TJSP/CJPG retornaram registros jurídicos reais com
HTTP 200; TJSP/CJSG permaneceu bloqueado por CAPTCHA/WAF/login e não foi
convertido em resultado vazio. O artefato registra apenas metadados e hashes,
sem persistir corpos de resposta.

## Coleta longa e retomável

Depois que o contrato e os fixtures forem aprovados, a coleta pode ser executada
por lotes, sem manter todo o resultado em memória:

```bash
nanojuris coletar "responsabilidade civil" \
  --fonte tjgo_projudi_jurisprudencia \
  --limite 100 \
  --max-paginas 100 \
  --max-registros 10000 \
  --store .tmp/tjgo.db \
  --checkpoint .tmp/tjgo.checkpoint.json
```

O checkpoint v2 é validado contra a fonte, a intenção da consulta e o contrato
declarado do provider. Ele guarda `run_id`, contadores, tentativas e hashes
estruturais das páginas (sem persistir conteúdo bruto), é gravado com `fsync` e
replace atômico e retoma na próxima página. Checkpoints legados v1 são
recusados para retomada até que a coleta seja reiniciada explicitamente com
`resume=False`. Falhas de provider, canonicalização ou acesso ficam no
relatório; uma página vazia não é confundida com bloqueio ou inexistência de
dados. O relatório também expõe freshness por coleta (`observed_at`), sem
inferir uma data de atualização do tribunal. O mesmo fluxo está disponível no
cliente Python e no MCP.

O cache de discovery não é limpo automaticamente. Quando houver política local
de retenção, use `DiscoveryCache.cleanup(max_age_seconds=..., max_bytes=...)`;
ela atua apenas nos JSON diretos do diretório configurado, remove os mais
antigos primeiro e devolve contadores/erros para auditoria. O limite é opt-in e
não apaga artefatos fora desse diretório.
