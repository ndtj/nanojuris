# Design

`SearchPage.is_explicit_empty` é a única prova aceita para um vazio completo.
`ProviderOutcome`, `validate_provider`, `check_provider` e o agregador federado
propagam `empty_unconfirmed` quando a fonte não informa total confiável nem
completude.

O manifesto de promoção lê uma decisão operacional explícita. Essa decisão
substitui apenas o gate humano local; nunca substitui os gates técnicos nem
transforma `blocked_*`, TLS, timeout ou indisponibilidade em sucesso. O
manifesto é artefato de decisão e não altera o registro de providers sozinho.
