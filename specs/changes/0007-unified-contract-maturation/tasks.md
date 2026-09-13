# Tasks

- T001 [x] Auditar a facade, routing, capabilities e modelos canônicos.
- T002 [x] Gerar matriz offline de filtros, perfis, paginação, completude e texto integral.
- T003 [x] Cruzar a matriz com os snapshots live e all-provider discovery existentes.
- T004 [x] Classificar formalmente filtros por provider como native/translated/local_postfilter/unsupported/unverified.
- T005 [x] Promover filtros observados somente após fixtures, parser e testes por
  provider; filtros sem prova permanecem `unverified`/`unsupported`.
- T006 [x] Fechar contratos de paginação e completude dos providers com
  `unknown`; todos os providers catalogados agora declaram um contrato de
  completude explícito. Isso não transforma janela observada em completude
  nacional.
- T007 [x] Fechar a evidência de texto integral e identidade estável onde há
  resposta reproduzível; superfícies sem documento ou com acesso controlado
  ficam com a limitação explícita no contrato.
- T008 [x] Amadurecer os candidates sem adapter com estado, evidência e gate
  objetivo; nenhum candidato é promovido sem contrato público reproduzível.
- T009 [x] Executar gates locais e novo smoke live bounded após cada lote de providers.
- T010 [x] Atualizar dossiês, contratos compatíveis, catálogo gerado e verificação final.
