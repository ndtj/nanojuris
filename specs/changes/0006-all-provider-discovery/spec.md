# Spec — discovery e maturação de todos os providers

ID: `0006-all-provider-discovery`
Status: `in_progress`
Owner: `NanoJuris engineering`
Data: `2026-08-20`

## Requisitos funcionais

- RF-001: enumerar todos os providers runtime e candidates documentais do catálogo, distinguindo adapter implementado de fonte ainda não promovida.
- RF-002: registrar rotas declaradas e rotas observadas com método, URL, origem e confiança.
- RF-003: registrar filtros declarados e campos observados, incluindo tipo, label, opções e required.
- RF-004: registrar status HTTP, content-type, hash, bytes, tempo, redirecionamentos e trace.
- RF-005: distinguir sucesso, vazio, query inválida, bloqueio, login, rate limit, timeout e indisponibilidade.
- RF-006: não executar POST sem contrato/payload aprovado e não alterar provider automaticamente.
- RF-007: gerar relatório comparativo e fila de TODO por lacuna de contrato, fixture, parser ou teste.
- RF-008: permitir reexecução bounded e replay local sem depender da rede.

## Critérios de aceite

- AC-001: todos os providers runtime aparecem no relatório bounded.
- AC-002: cada observação preserva estado de acesso distinto de vazio real.
- AC-003: rotas declaradas e observadas são comparáveis por provider.
- AC-004: filtros declarados e campos observados são registrados com evidência.
- AC-005: nenhum POST é submetido sem contrato e fixture aprovados.
- AC-006: o relatório gera TODO rastreável para cada lacuna material.
- AC-007: replay e testes locais não dependem da rede.
- AC-008: gates locais e live bounded são executados e registrados.

- Todos os providers runtime e candidates documentais do catálogo aparecem no relatório ou têm erro por-fonte explícito.
- Nenhum estado de acesso controlado é classificado como resultado vazio.
- O relatório contém declared/observed routes e filters por provider.
- O sweep e os parsers têm testes locais; os resultados live são artefatos versionáveis.
- Documentação, source contracts, catalog e SDD são regenerados pelos comandos oficiais.
