# Design

`tools/discover_all_providers.py` instancia `NanoJurisClient`, lê as capabilities,
materializa somente GETs seguros e usa `DiscoveryCrawler`/`HttpDiscoveryClient`.
Cada resposta mantém `SourceTrace`/`ExtractionTrace` implícitos no evidence package,
hash e classificação de acesso. A extração compartilhada produz candidatos de rotas,
seletores e filtros, sem promover nenhum deles a parser canônico.

O relatório agregado é deliberadamente separado do catálogo gerado. A promoção de
uma melhoria continua exigindo mudança SDD própria, fixture pública sanitizada,
parser, normalização, testes de contrato e atualização dos dossiers.
