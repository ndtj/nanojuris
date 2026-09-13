# Design - Falcao JT diagnostico

O adapter usa `SharedHttpClient` com allowlist de `jurisprudencia.jt.jus.br`,
limite de 2 MB, timeout configurado e sem retry adicional. A única operação é
uma sondagem GET da raiz. A resposta é inspecionada apenas para distinguir
bloqueio de distribuição, shell público e resposta sem contrato.

O provider fica registrado somente em `include_candidate_providers=True`.
Não há `SearchPage` sintético: qualquer ausência de contrato resulta em erro
explícito para impedir falso vazio.

## Caminho autorizado

`search_authorized` reutiliza o mesmo endpoint, parser e normalização, mas
recebe um Bearer OIDC de curta validade do chamador que já concluiu a
autenticação oficial. O header é montado apenas em memória; o token não é
armazenado, renovado, repetido em traces ou usado para contornar controles. A
rota continua opt-in e não habilita federação sem resposta live autorizada,
fixtures e qualidade comprovadas.
