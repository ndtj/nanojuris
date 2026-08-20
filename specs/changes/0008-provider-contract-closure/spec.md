# Spec — fechamento profissional de contratos de providers

ID: `0008-provider-contract-closure`
Status: `in_progress`
Owner: `NanoJuris engineering`
Data: `2026-08-20`

## Objetivo

Levar todos os providers runtime e candidates documentais ao maior estado de maturidade comprovável, encerrando TODOs com implementação/evidência ou convertendo impedimentos externos em diagnósticos formais e rastreáveis.

## Requisitos funcionais

- RF-001: inventariar cada TODO atual por source, causa raiz, evidência e estado de fechamento.
- RF-002: reutilizar contratos, fixtures, parsers e testes locais existentes antes de abrir trabalho duplicado.
- RF-003: fechar filtros, paginação, completude, identidade, texto integral e estados de erro quando houver evidência suficiente.
- RF-004: produzir fixtures de sucesso, vazio e erro para cada adapter promovido.
- RF-005: diferenciar `closed`, `implemented_with_local_evidence`, `blocked_external`, `candidate_pending_adapter` e `needs_new_evidence`.
- RF-006: não executar POST especulativo nem contornar robots, CAPTCHA, WAF, login, rate limit ou segredo.
- RF-007: atualizar dossiês, contratos, cobertura, matriz unificada e SDD após cada lote.
- RF-008: zerar apenas TODOs realmente fechados; impedimentos devem permanecer visíveis com causa e critério de retomada.

## Critérios de aceitação

- AC-001: cada TODO do sweep possui estado, evidência e responsável lógico.
- AC-002: nenhum TODO é removido por silenciamento ou por transformar bloqueio em vazio.
- AC-003: cada provider runtime tem contrato canônico, estados e testes proporcionais à superfície disponível.
- AC-004: candidates sem adapter permanecem explicitamente pendentes até contrato e fixtures aprovados.
- AC-005: filtros observados não são promovidos sem correspondência no parser/query e teste.
- AC-006: o discovery profundo é repetido após os lotes e seus números ficam versionados.
- AC-007: suite, SDD, compilação, auditoria de docs e cobertura passam.
- AC-008: o ciclo só é marcado como concluído quando não houver TODO sem estado justificável.

## Não objetivos

- Prometer acesso a fonte controlada ou indisponível.
- Enviar payloads POST inventados para “provar” uma rota.
- Criar adapters para candidates sem contrato e fixtures públicos suficientes.
