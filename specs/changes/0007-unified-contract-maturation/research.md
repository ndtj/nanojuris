# Research — maturação do contrato unificado

Data: `2026-08-20`

## Evidências locais

- O runtime registra 44 providers; 41 declaram `supports_unified_search=true`.
- O envelope é comum (`SearchPage` e `JurisprudenceResult`), mas os canônicos declarados são heterogêneos: `CanonicalDecision`, `CanonicalPrecedent` e `CanonicalDocument`.
- Os perfis semânticos não são equivalentes: decisões textuais, precedentes qualificados, jurisprudência curada e documentos de apoio.
- A matriz local encontrou 21 filtros declarados no conjunto, mas a cobertura por provider varia fortemente; filtros de parte, advogado, OAB e identificadores especializados não são uniformes.
- A paginação declarada varia entre `page`, `offset`, `local_window` e `unknown`.
- A completude varia entre contratos com total/janela explícitos, janelas observadas e `unknown`.
- O smoke live versionado usa a consulta `direito`, `page_size=1`; o snapshot atual registra 33/44 providers com dados válidos.
- O discovery all-provider registra rotas e campos observados, mas observação não é promoção automática de filtro ou contrato.

## Hipótese de trabalho

A facade unificada está adequada como ponto de entrada, mas ainda não como promessa de equivalência semântica. A próxima camada deve explicitar a capacidade por filtro e por perfil de dado, preservar a heterogeneidade na resposta e bloquear afirmações de completude que a fonte não comprova.

## Decisões de segurança e escopo

- A auditoria é offline e consome apenas declarações e artefatos locais.
- O smoke live permanece bounded e diagnóstico; desafios de acesso, WAF, CAPTCHA, login, TLS e timeout continuam estados explícitos.
- Nenhum filtro observado será promovido sem contrato, fixture, parser e teste correspondentes.
