# Tarefas de implementação

Referência: `specs/changes/0002-provider-discovery/spec.md`

## Fundação

- [x] T1 Criar modelos serializáveis de política, request, response e
  evidência.
- [x] T2 Criar validação de URL, allowlist, limites e redaction.
- [x] T3 Criar cliente HTTP bounded com redirects auditados.
- [x] T4 Reutilizar a análise de rota existente para classificação.

## Descoberta

- [x] T5 Extrair links, formulários, scripts e endpoints JSON.
- [x] T6 Criar adaptador Playwright opcional para document/XHR/fetch.
- [x] T7 Criar candidatos de campos e seletores com confiança explícita.
- [x] T8 Implementar cache/replay offline por hash.

## SDD e operação

- [x] T9 Gerar relatório JSON e artefatos SDD.
- [x] T10 Criar CLI local bounded e ferramenta MCP.
- [x] T11 Criar fixtures offline e testes de falhas.
- [x] T12 Atualizar documentação de uso e threat model.
- [x] T13 Executar ruff, mypy, pytest e `validate_sdd.py` (gates locais
  executados em 2026-09-02; suíte NanoJuris: 1096 passed, 12 skipped).

## Gate de aceite

- [x] T14 Revisão do operador dos artefatos e da política de execução,
  registrada em `docs/operations/provider-promotion-approvals-20260905.json`;
  a decisão cobre apenas fontes públicas no runtime local/federado.
- [x] T15 Nenhum provider é derivado automaticamente: cada promoção efetiva
  foi registrada em SDD próprio (por exemplo, 0041 e 0067) e no manifesto
  técnico; fontes sem gates permanecem opt-in ou bloqueadas.
