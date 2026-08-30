# Tarefas

- [x] **T01** Isolar canonicalizacao invalida no fluxo federado (REQ-001).
- [x] **T02** Sanitizar mensagens de erro e adicionar regressoes (REQ-002).
- [x] **T03** Definir e testar a metrica `record_count` (REQ-003).
- [x] **T04** Atualizar rastreabilidade de fixtures e relatorio (REQ-004).
- [x] **T05** Executar gates e revisao final (AC-005).
- [x] **T06** Manter uma entrada de completude para providers cujo future excedeu
  o timeout global, sem mascarar a falha como fonte nao observada (REQ-002,
  AC-001/AC-002).
- [x] **T07** Repetir a classificacao sanitizada de falhas e timeouts em
  `source_completeness`, mantendo-a alinhada a `errors` para consumidores que
  nao processam o array global (REQ-002, AC-001/AC-002).
