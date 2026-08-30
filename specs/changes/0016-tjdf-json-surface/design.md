# Design

O adapter `tjdf_juris` recebe uma opção explícita (`use_api=True` ou
`NanoJurisConfig.tjdf_juris_api_enabled=True`) para consultar
`POST /api/v1/pesquisa`. O payload usa apenas campos documentados, converte a
  página pública 1-based para a página remota 0-based e mapeia o envelope
`hits`/`registros` para `SearchPage` e `JurisprudenceResult`.

O parser normaliza datas para ISO, mantém campos desconhecidos e agregações no
payload bruto, valida identidade (`uuid` ou `identificador`) e diferencia erro
de contrato, rejeição de consulta, indisponibilidade e limite de taxa. O fluxo
HTML legado permanece como default para evitar mudança silenciosa de cobertura.
