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
- [ ] T13 Executar ruff, mypy, pytest e `validate_sdd.py`.

## Gate de aceite

- [ ] T14 Revisão humana dos artefatos e da política de execução.
- [ ] T15 Aprovar eventual provider derivado em mudança separada.
