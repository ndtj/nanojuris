# Verificação

## Resultados

Planejamento criado; nenhum TJ foi declarado concluído por este pacote.

## Rechecagem oficial TJRJ/TJSC — 2026-09-07

- `docs/provider-discovery/state-first-degree-eproc-recheck-20260907.json`
  confirma que as rotas eproc públicas de TJRJ e TJSC retornaram registros de
  segundo grau quando consultadas sem credenciais; a tentativa explícita de
  `degree=first` foi rejeitada por identidade incompatível.
- `docs/provider-discovery/tjrj-ejuris-origin-options-live-20260907.json`
  confirma que o formulário oficial EJURIS expõe origens de segunda instância
  (incluindo valor `1`) e não oferece uma opção observável de primeiro grau.
- Portanto, essas evidências fortalecem o contrato CJSG, mas não fecham o gate
  de CJPG. As tarefas de rota, parser, documento e promoção continuam abertas
  até existir uma superfície oficial de primeiro grau reproduzível.

## Limite de primeiro grau eproc - 2026-09-08

- `docs/provider-discovery/state-eproc-first-degree-boundary-live-20260908.json`
  registra uma nova consulta publica limitada para `responsabilidade civil`,
  `degree=first`, `instance=first`, pagina 1 e um registro solicitado.
- TJRJ e TJSC responderam HTTP 200, mas os cards retornados nao provaram
  primeiro grau. O contrato compartilhado rejeitou os registros com
  `ParserContractChangedError: results outside requested degree=first`.
- A rejeicao foi preservada como erro de contrato, nao como lista vazia. Nao
  houve credencial, solver, reutilizacao de sessao ou contorno de controle.
- A inspecao do payload confirmou que o valor de origem observado para essas
  instalacoes nao oferece uma rota publica distinta de primeiro grau; nao se
  deve repetir a mesma sondagem. TJRJ e TJSC permanecem CJSG validos e CJPG
  pendentes ate uma superficie oficial reproduzivel.

## Limite de disponibilidade TJBA — 2026-09-09

- `docs/provider-discovery/tjba-cjpg-route-live-20260909.json` registra o
  probe GET bounded da rota oficial `www2.tjba.jus.br/jurisprudencianet`.
- A fonte respondeu HTTP 503 sem texto decisório. Isso é
  `source_unavailable`, não vazio autoritativo e não contrato de primeiro grau.
- Não houve POST, credencial, token, CAPTCHA, sessão autenticada ou tentativa
  de contornar controle. TJBA/CJPG permanece pendente de rota oficial
  reproduzível; T003–T006 continuam abertas.

## Rastreabilidade

AC-001 → T001–T003; AC-002 → T003–T004; AC-003 → T003–T005; AC-004 → T006.
