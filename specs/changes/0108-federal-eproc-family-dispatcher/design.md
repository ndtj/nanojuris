# Design — dispatcher ePROC federal

`FederalEprocJurisprudenciaFamilyProvider` é uma camada fina sobre os
adapters `TnuEprocJurisprudenciaProvider`, `Trf2EprocJurisprudenciaProvider`,
`Trf4EprocJurisprudenciaProvider` e `Trf6EprocJurisprudenciaProvider`.

O método `search` exige autoridade explícita e seleciona uma instância filha
por um mapa imutável de aliases. O filho continua responsável pelo endpoint,
payload, paginação, normalização, limites de bytes, retry, circuit breaker e
classificação de erro. A família não faz fan-out, não soma totais e não
converte falha de uma autoridade em vazio de outra.

`get_decisions` e `get_document` usam prefixos de identificador emitidos pelos
adapters filhos. Um prefixo desconhecido é rejeitado, evitando que um ID seja
enviado ao tribunal errado. `get_parameters` descreve o mapa de autoridades e
`get_capabilities` declara explicitamente o caráter opt-in e a ausência de
federação padrão.

O cliente registra a família no runtime normal, mas o dispatcher exige
`authority` explícita e declara `supports_unified_search=False`. Assim, a
família pode ser usada de forma opt-in por autoridade sem virar uma fonte
agregada nem promover qualquer superfície sem contrato e live check
específicos. Os estados de acesso e completude continuam sendo os do adapter
filho e são preservados nos traces.
