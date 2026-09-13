# Design — operação contínua

Canários bounded terão frequência por risco/família. Métricas incluem latência,
bytes, páginas, status, completude e schema fingerprint. Shadow mode compara
versões; promoção exige manifesto técnico; rollback troca parser/contrato sem
alterar produção.

