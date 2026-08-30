# Tasks

- [x] **T01** Registrar o contrato JSON observado no dossiê canônico e na
  pesquisa de rotas (concluído em 0023/route-research; sincronizado neste
  ciclo).
- [ ] **T02** Revisar as condições públicas de reuso/redistribuição do acervo e
  registrar a conclusão. Bloqueia toda a implementação abaixo.
- [ ] **T03** Capturar fixtures live sanitizadas: sucesso `pje2g`, vazio, erro
  de parâmetro, paginação `page=1`/`page=2`, e core `legado`.
- [ ] **T04** Confirmar `per_page` máximo, ordenação estável e comportamento de
  rate limit; fixar constantes do adapter.
- [ ] **T05** Implementar o request JSON com seleção de core e classificação de
  erro (`REQ-002`, `REQ-005`, `REQ-006`).
- [ ] **T06** Implementar o parser canônico e a conversão de paginação
  (`REQ-003`, `REQ-004`).
- [ ] **T07** Declarar rota, cores, formatos e limite no catálogo/capability e
  atualizar os dossiês (`REQ-007`).
- [ ] **T08** Adicionar os testes de contrato (AC-001..AC-007) e executar
  suíte focada, lint e validação SDD sem rede.
- [ ] **T09** Marcar o provider como `candidate_adapter_p1` → adapter ativo no
  registro e no `provider-catalog.full.json` regenerado.
