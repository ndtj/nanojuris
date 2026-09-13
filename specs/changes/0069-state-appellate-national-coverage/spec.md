# 0069 - Cobertura nacional de segundo grau dos TJs

Status: `in_progress`

## Intencao

Transformar a meta de segundo grau dos 27 tribunais estaduais em um programa
executavel e mensuravel. Cada tribunal possui uma superficie independente;
existencia de provider generico, resposta HTTP 200 ou modulo no Juscraper nao
equivale a cobertura comprovada.

## Requisitos

- REQ-001: o programa deve conter exatamente os 27 TJs/TJDFT do catalogo
  canonico, uma vez cada, para `degree=second` e `collection=CJSG`.
- REQ-002: cada superficie deve expor provider, estado, capacidade de consulta,
  evidencias e proxima acao, inclusive quando bloqueada ou sem adapter.
- REQ-003: toda superficie deve possuir tarefas para pesquisa oficial,
  contrato, implementacao, fixtures, paginacao/filtros, chamada live bounded,
  qualidade e federacao.
- REQ-004: tarefas satisfeitas devem ser derivadas de evidencia da matriz;
  tarefas futuras nao podem ser marcadas concluidas por inferencia.
- REQ-005: CAPTCHA, WAF, login, TLS, timeout e bloqueio de transporte nunca
  podem ser classificados como vazio.
- REQ-006: o Juscraper e fonte de pesquisa de rotas e semantica, nao prova de
  disponibilidade atual nem autorizacao para copiar implementacao.
- REQ-007: o artefato deve ser regeneravel por comando local e validado por
  teste automatizado, sem contagens manuais.
- REQ-008: promocao federada exige contrato especifico de segundo grau,
  fixture, live valido, qualidade e decisao tecnica do operador.

## Criterios de aceite

- AC-001: o gerador falha quando falta ou sobra tribunal, existe duplicidade ou
  uma linha nao representa segundo grau/CJSG.
- AC-002: JSON e Markdown apresentam as mesmas 27 superficies e seus gates.
- AC-003: fontes bloqueadas permanecem com acao `blocked_recheck`; fontes sem
  provider permanecem `adapter_discovery`.
- AC-004: cada linha possui oito tarefas estaveis e rastreaveis.
- AC-005: a suite de testes e o validador SDD passam.
- AC-006: 27/27 so pode ser declarado quando todas as linhas forem consultaveis
  com contrato e evidencia live especificos.

## Fora de escopo

Consulta processual, copia de codigo de terceiros, bypass de controles,
coleta em massa, publicacao, deploy e mudancas de producao.
