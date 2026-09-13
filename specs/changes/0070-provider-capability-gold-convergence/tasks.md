# Tarefas — convergência ouro

Referência: `specs/changes/0070-provider-capability-gold-convergence/spec.md`

## Planejamento

- [x] **T01** — auditar catálogo, scorecard, matriz de filtros, inventário
  documental e sweep disponíveis.
- [x] **T02** — definir semântica de ouro relativa às capacidades oficiais.
- [x] **T03** — definir arquitetura do ledger, discovery, implementação e
  certificação.
- [x] **T04** — decompor providers por papel e família técnica.

## Onda 0 — verdade única

- [x] **T05** — criar schema versionado do capability ledger.
- [x] **T06** — implementar gerador que reconcilia todas as fontes atuais.
- [x] **T07** — gerar workpack incremental por provider.
- [x] **T08** — separar métricas legadas dos cinco eixos ouro.
- [x] **T09** — adicionar testes de cardinalidade, conflitos, freshness e IDs.

## Onda 1 — contratos comuns

- [x] **T10** — implementar modelos de evidência, filtro, campo e documento.
- [x] **T11** — criar registro canônico de filtros, aliases, tipos e enums.
- [x] **T12** — implementar captura redigida e fingerprints.
- [x] **T13** — implementar comparador diferencial de filtros/páginas.
- [x] **T14** — implementar inventário e classificação de campos.
- [x] **T15** — expor aplicação de filtros no envelope federado.

## Onda 2 — pilotos

- [x] **T16** — fechar pilotos eSAJ.
- [x] **T17** — fechar piloto eproc.
- [x] **T18** — fechar piloto PJe.
- [x] **T19** — fechar pilotos GraphQL/BFF/REST.
- [x] **T20** — fechar pilotos Projudi/JSF/Solr.
- [x] **T21** — fechar piloto de dataset.
- [x] **T22** — consolidar componentes compartilhados sem apagar overlays.

## Ondas 3–6 — providers

- [x] **T23** — certificar os 33 providers textuais primários. O avaliador
  atual registra 37 superfícies primárias (incluindo as 33 previstas), todas
  com `engineering_gold=true`, `provider_gold=true`, contrato, dados,
  documentos, live e federação válidos; relatório:
  `docs/quality/provider-gold-evaluation.json`.
- [x] **T24** — certificar as fontes especializadas e de precedentes. Cada
  fonte recebeu avaliação por eixo e disposição técnica; bloqueios permanecem
  fora do ouro operacional sem serem confundidos com vazio.
- [x] **T25** — certificar curadoria, administração e datasets. Contratos,
  capacidades documentais, filtros e estados live foram reconciliados; fontes
  sem federação conservam disposição terminal explícita.
- [x] **T26** — pesquisar e dispor os sete candidates e a família eproc. Os
  workpacks, inventário Juscraper e evidências bounded foram gerados; adapters
  diagnósticos existem quando seguros e os demais permanecem pendentes sem
  promoção prematura.
- [x] **T27** — reconciliar categorias/roles incorretos antes da promoção.
  TJMG foi restrito à superfície CJSG (a rota do espelho de acórdão não é
  CJPG) e TJRN deixou de ser associado a CJPG sem prova de primeiro grau;
  ambos permanecem separados de `federation_enabled` quando há bloqueio ou
  contrato incompleto.

## Onda 7 — documentos

- [x] **T28** — revalidar todas as rotas inline/detail já declaradas.
- [x] **T29** — descobrir detalhe/documento nos providers link-only/unknown.
- [x] **T30** — implementar referências, fetchers e parsers faltantes. Foram
  fechados os fetchers públicos identificados (TCE-SP e STJ Informativo) e o
  parser bounded de cargas ZIP do STJ Dados Abertos. Surfaces sem rota pública
  de documento permanecem explicitamente bloqueadas ou fora de escopo.
- [x] **T31** — implementar OCR opcional, isolado e mensurável.
- [x] **T32** — provar estados `not_offered_by_source` restantes. LIAME/TJRO
  agora declara esse estado para a superfície de precedentes qualificados;
  TJMA declara `access_blocked` por CAPTCHA; STJ Dados Abertos declara
  `inline_summary` para o campo `decisao`. Nenhum desses estados é tratado
  como vazio ou inteiro teor integral.

## Onda 8 — interfaces e federação

- [x] **T33** — alinhar SDK, CLI, MCP e Studio.
- [x] **T34** — implementar UI de interseção/união de filtros.
- [x] **T35** — validar pós-filtros, completude, ordenação e deduplicação.
- [x] **T36** — executar shadow mode antes de habilitação padrão.

## Onda 9 — certificação

- [x] **T37** — implementar avaliador dos cinco eixos ouro.
- [x] **T38** — incorporar freshness e invalidação incremental.
- [x] **T39** — executar suíte completa e smokes bounded por provider.
- [x] **T40** — impedir `unverified` e campos não classificados de chegarem a
  `provider_gold` (os gaps permanecem visíveis para orientar o fechamento).
- [x] **T41** — regenerar todos os artefatos e emitir relatório final.
- [x] **T42** — revisar contra AC-001 a AC-015, sem commit, push ou deploy.

## Dependências

```text
T01-T04
  -> T05-T09
  -> T10-T15
  -> T16-T22
  -> T23-T27
  -> T28-T32
  -> T33-T36
  -> T37-T42
```

Providers podem avançar em paralelo dentro de uma onda, mas nenhum pode pular
seu workpack, evidências, fixtures ou gates.

## Critério de parada

O programa só termina quando cada fonte possuir estado terminal para filtros,
campos e documentos, e todos os providers rotulados `provider_gold` passarem
os cinco eixos sem evidência expirada. Bloqueios externos são terminais para a
pesquisa local, mas não são classificados como operação saudável.
