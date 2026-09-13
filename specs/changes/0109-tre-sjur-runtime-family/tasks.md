# Tasks — SDD 0109

- [x] T001 adicionar a família ao registro padrão do `NanoJurisClient`.
- [x] T002 manter os 27 adapters por UF no modo candidato explícito.
- [x] T003 atualizar registry e documentação canônica/legada.
- [x] T004 atualizar testes de runtime e de não-federalização.
- [x] T005 validar que a autoridade continua obrigatória e que páginas não
  comprovadas são rejeitadas.
- [x] T006 regenerar catálogos, ledgers e workpacks.
- [x] T007 executar gates focados e suíte completa.

- [x] T008 validar filtro remoto oficial de tipo de decisão de segundo grau em
  janela bounded serial nas 27 UFs.
- [x] T009 traduzir `document_type` canônico para rótulos oficiais e rejeitar
  combinações incompatíveis com o grau selecionado.
- [x] T010 reconciliar a sondagem multi-UF de primeiro grau no ledger de live,
  preservando `candidate`/opt-in e sem transformar a evidência em federação.
- [x] T011 traduzir os refinamentos estruturados comprovados na SPA oficial
  (`election_year`, `observations`, `tags`, `municipality`, `publication_source`,
  `publication_number`, `publication_volume` e `uf`) para o DSL remoto, com
  rejeição explícita de valores numéricos inválidos.
- [x] T012 expor esses filtros como `native` somente no binding TRE e cobrir
  a compilação, capacidades e rastreabilidade em testes.
- [x] T013 propagate the structured TRE filters through `NanoJurisClient`,
  federated routing and Portuguese API/Studio aliases without sending them to
  providers that do not declare support.
- [x] T014 registrar no catálogo a expansão determinística das duas superfícies
  TRE em 27 instâncias por UF, sem duplicar providers canônicos nem habilitar
  a federação padrão.
- [x] T015 repetir a sonda oficial variando `pagina` e `tamanho`, comparar
  sequências de IDs sem persistir corpos e manter a decisão de paginação não
  comprovada quando a fonte repete a mesma janela.
- [x] T016 validar o download PDF de um acórdão TRE-SP observado, incluindo
  MIME, assinatura `%PDF-`, tamanho e hash, sem persistir o corpo no repositório.
- [x] T017 implementar coleta opt-in por partições mensais de data quando o
  intervalo explícito permanecer abaixo da janela remota; deduplicar registros,
  preservar o trace das partições e manter a federação padrão desabilitada.
- [x] T018 expor a coleta particionada no dispatcher da família, exigindo
  `authority` explícita e preservando o envelope de fonte/trace da família.
- [x] T019 revalidar a partição temporal de segundo grau serialmente nas 27
  autoridades TRE e registrar somente metadados redigidos.
- [x] T020 revalidar a superfície de primeiro grau com vazio bounded nas 27
  UFs e uma janela histórica não vazia em TRE-MG, sem promover a família.
