# 0029 — intake de providers e evidências do Juscraper

Status: verified
Owner: Architecture, Provider Engineering e Security

## Intenção

Criar um processo auditável para aproveitar código MIT, rotas, parsers e
fixtures do Juscraper sem copiar dependências, bugs ou semânticas incompatíveis.

O repositório de referência desta mudança é `jtrecenti/juscraper`. O intake
atual está registrado em
`docs/provider-discovery/juscraper-intake-20260901.json`; um checkout de outro
projeto com nome semelhante não é evidência válida para esta mudança.

## Requisitos

- REQ-001: fixar commit upstream, licença, arquivos considerados e data.
- REQ-002: inventariar por superfície (`cjsg`, `cjpg`, detalhe, documento ou
  processo), e classificar cada item como algoritmo, fixture, evidência,
  hardening, bloqueio, rejeição ou fora de escopo.
- REQ-003: produzir diff de campos, filtros, paginação, erros e identidade.
- REQ-004: preservar copyright e licença em cópia substancial.
- REQ-005: não importar pandas, browser cookies, auth ou agregadores
  processuais para o núcleo.
- REQ-006: exigir teste de equivalência antes de promover qualquer adaptação.
- REQ-007: registrar divergência documental do upstream sem inferir saúde live.
- REQ-008: separar primeiro grau, segundo grau e detalhe mesmo quando usam o
  mesmo parser ou endpoint.
- REQ-009: proibir adaptação de qualquer fluxo que dependa de resolver ou
  ignorar CAPTCHA, Turnstile, login ou outro controle de acesso.
- REQ-010: comparar upstream com a implementação NanoJuris atual antes de
  substituir rota, parser ou modelo.
- REQ-011: novas collections devem receber source ID planejado e pacote próprio
  antes de entrar no catálogo runtime.
- REQ-012: revisar delta de árvore, rotas, schemas, fixtures e licença no início
  de cada coverage epoch, sem atualização automática de runtime.
- REQ-013: o cruzamento deve ser derivado do runtime e do catálogo live atuais;
  equivalentes promovidos, bloqueados ou removidos não podem permanecer com
  classificação histórica obsoleta.
- REQ-014: equivalência deve ser registrada por superfície. Consulta processual
  (`cpopg`/`cposg`) nunca pode ser satisfeita por um provider jurisprudencial e
  uma superfície bloqueada nunca pode ser classificada como coberta.

## Critérios de aceite

- AC-001: ledger cobre todas as classes runtime e todas as superfícies públicas
  observadas no snapshot, sem usar o registry/documentação divergente como
  fonte única.
- AC-002: os 25 CJSG, 3 CJPG e 1 detalhe de ementa estão cruzados com o catálogo
  NanoJuris.
- AC-003: candidatos de ganho real possuem pacote próprio ou decisão defer.
- AC-004: itens fora do escopo permanecem fora da NanoJuris.
- AC-005: licença e atribuição passam por revisão.
- AC-006: TJRJ, TJMG e TJAP possuem decisão explícita de acesso e não são
  promovidos por evidência de bypass.
- AC-007: TJES, TJRN, TJRO e TJTO detail possuem ordem e gate no pacote 0039.
- AC-008: TJMA/TJSE ausentes no snapshot e a collection de turma recursal TJES
  possuem classificação explícita, sem inferência por ausência.
- AC-009: TJES, TJRN e TJRO refletem seus providers runtime atuais; TJES e TJSP
  preservam bindings independentes para CJPG/CJSG e TJSP bloqueado não conta
  como cobertura completa.
