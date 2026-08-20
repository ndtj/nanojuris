# Design da mudança

Referência: `specs/changes/0002-provider-discovery/spec.md`

## Decisão arquitetural

Adicionar um pacote `nanojuris.discovery` com coleta HTTP nativa, análise de
respostas, geração de candidatos e replay. O navegador será um adaptador
opcional. A descoberta não será importada pelos providers em runtime.

## Componentes e fluxo

```text
seed + allowlist
      |
      v
DiscoveryPolicy -> HttpDiscoveryClient -> DiscoveryEvidence
      |                    |                    |
      |                    +--> RouteCandidate |
      |                    +--> SelectorCandidate
      |                                         |
      +--> BrowserDiscoveryClient (optional) -->+
                                                    |
                                                    v
                                           SDD draft + replay artifact
                                                    |
                                             human review gate
                                                    |
                                      provider implementation and tests
```

## Interfaces e contratos

- API: `DiscoveryPolicy`, `DiscoveryRequest`, `DiscoveryEvidence` e
  `DiscoveryRun` dataclasses serializáveis.
- CLI: `tools/provider_discovery.py` para uma execução local bounded.
- Browser: Playwright opcional, apenas navegação pública e captura de
  document/XHR/fetch.
- Store: JSON versionado, com corpos separados e hash referenciado.
- Provider: nenhum acoplamento automático; saída é material SDD.

## Dados e migração

Nenhuma migração de dados existente. O pacote é novo e não altera catálogo,
fixtures ou providers. A persistência inicial é filesystem local fornecido pelo
operador; uma store durável é mudança posterior.

## Segurança e privacidade

- validação de esquema `http`/`https`;
- rejeição de credenciais embutidas e destinos privados;
- allowlist de domínio e validação de cada redirect;
- redaction de token, cookie, authorization, password e session;
- limite de bytes e quantidade de respostas;
- nenhum segredo em relatório;
- corpos brutos opcionais e minimizados;
- browser sem cookies injetados, proxy, CDP ou automação de desafio.

## Operação

- Health/readiness: dependência HTTP sempre; Playwright somente sob demanda.
- Timeout/retry: timeout bounded; sem retry automático de bloqueio.
- Métricas: páginas, respostas, bytes, bloqueios, erros, candidatos e duração.
- Logs: JSON opcional, sem payloads secretos.
- Rollback: remover o pacote novo; nenhum provider existente é alterado.

## ADRs relacionados

- `ADR-0002`: descoberta separada do runtime de providers.
- `ADR-0003`: navegador opcional e evidência como saída primária.
