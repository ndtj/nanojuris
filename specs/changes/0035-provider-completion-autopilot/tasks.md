# Tarefas

- [x] T01 — executar auditorias offline de catálogo, docs, fixtures e contratos.
- [x] T02 — definir máquina de estados e política de retomada.
- [x] T03 — implementar gerador de baseline, fila, estado e work packs.
- [x] T04 — gerar e revisar estruturalmente um work pack por entrada atual do catálogo.
- [x] T05 — testar preservação de estado e cobertura.
- [x] T06 — reconciliar fila com 0006, 0007, 0008 e 0009.
- [x] T07 — iniciar fundação 0027, 0028 e 0031 (contratos, runtime
  compartilhado e scorecards presentes e validados localmente).
- [x] T08 — processar providers por prioridade com workpacks/SDDs individuais;
  os 11 tecnicamente elegíveis foram promovidos, e os demais ficaram em
  opt-in, candidate ou blocked com motivo e `resume_when` explícitos.
- [x] T09 — encerrar ou classificar todos os bloqueios (ledger regenerado em
  2026-09-02; bloqueios externos e candidates pendentes separados, sem false
  empty).
- [x] T10 — executar gates integrados; o operador aceitou o escopo técnico
  local/federado, mantendo publicação, deploy e redistribuição fora do escopo.
- [x] T11 — remover contagens rígidas e adicionar fingerprint de revalidação.
- [x] T12 — separar saúde operacional, andamento e disposição terminal.
- [x] T13 — integrar unidades de cobertura 0036 e superfícies candidatas 0039 à fila (topologia e oito candidates reconciliados nos workpacks de 2026-09-02).
- [x] T14 — migrar estados terminais v1 para revisão no schema v2.
- [x] T15 — implementar classificador bounded de disposições com retomada e
  saúde operacional derivadas do manifesto técnico.
- [x] T16 — aplicar disposições a todas as entradas, preservar evidência e
  regenerar work packs sem tarefas WP não processadas.
- [x] T17 — adicionar testes de classificação, idempotência, bloqueios e
  completude cardinalidade do estado.

Dependência: T01 -> T02 -> T03 -> T04 -> T05 -> T06 -> T11 -> T12 -> T14 -> T13 -> T07 -> T08 -> T09 -> T10.
