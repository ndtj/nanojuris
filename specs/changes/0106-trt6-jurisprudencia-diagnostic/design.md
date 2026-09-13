# Design

O provider usa o `SharedHttpClient` com allowlist separada para
`pje.trt6.jus.br` e `apps.trt6.jus.br`, limite de resposta de 2 MB, sem retry e
com o intervalo operacional global configurado. O payload PJe reproduz apenas a
forma pública documentada pelo SPA; o campo `token` permanece vazio e a
resposta de validação do reCAPTCHA interrompe a busca com estado de acesso
controlado.

O formulário legado é somente lido por `GET`; sua submissão não é realizada
sem uma resposta de desafio fornecida pelo usuário. Assim, o adapter fornece
diagnóstico e uma trilha de evidência sem mascarar indisponibilidade como
`authoritative_empty`.
