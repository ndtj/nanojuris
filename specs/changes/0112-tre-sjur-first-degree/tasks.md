# Tarefas — SDD 0112

- [x] **T001** registrar contrato, limites e separação de grau.
- [x] **T002** implementar provider e dispatcher de primeiro grau reutilizando
  transporte/parser compartilhados.
- [x] **T003** adicionar bindings candidatos por UF no cliente.
- [x] **T004** criar fixtures e testes de classificação, escopo, vazio e
  janela duplicada.
- [x] **T005** registrar evidência live bounded do TRE-MG com rótulo explícito
  `Sentença`, sem persistir corpos de resposta.
- [ ] **T006 [E]** validar paginação remota por UF na fonte oficial.
- [ ] **T007 [E]** validar detalhe/PDF e retenção permitida por UF.
- [ ] **T008 [H]** revisar promoção técnica/legal antes de qualquer federação.
- [x] **T009** criar ferramenta bounded de inventário multi-UF sem persistir
  corpos de resposta.
- [x] **T010** executar uma janela pública por cada TRE, classificando tipos de
  decisão e estados de acesso sem promover bindings.
- [x] **T011** registrar a evidência agregada, promover o dispatcher para
  runtime opt-in e manter a federação padrão condicionada a
  paginação/documento por UF.
- [x] **T012** validate the official remote decision-type filter in a bounded
  serial sweep of all 27 UFs, record sanitized evidence, and apply it only to
  the first-degree binding while retaining local classification as a defense.
- [x] **T013** alinhar o limite de bytes da sonda multi-UF ao transporte do
  provider (16 MB), evitando classificar janelas públicas maiores como
  indisponíveis sem antes tentar o parsing bounded.
