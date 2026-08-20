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

O checkpoint é validado contra a fonte e a consulta, é gravado atomicamente e
retoma na próxima página. Falhas de provider, canonicalização ou acesso ficam
no relatório; uma página vazia não é confundida com bloqueio ou inexistência de
dados. O mesmo fluxo está disponível no cliente Python e no MCP.
