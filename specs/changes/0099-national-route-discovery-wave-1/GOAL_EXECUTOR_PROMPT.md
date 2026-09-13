# Prompt da meta de busca federal

Você executa o SDD 0099 na raiz `repos/nanojuris`. Trabalhe somente em
TRF1, TRF2 e TRF4, em lotes de até três fontes. Leia `AGENTS.md`, a
constituição, o SDD 0098, este pacote e os dossiês dos providers antes de
chamar qualquer rota.

Faça descoberta oficial e chamadas live bounded de baixa frequência. Não use
credenciais, não resolva CAPTCHA/Turnstile, não contorne WAF, não repita
tokens/cookies, não use rotação de IP, stealth, fuzzing de endpoints privados,
TLS inseguro ou deploy. HTTP 403/429, desafio, timeout, TLS ou schema inválido
é bloqueio explícito, não vazio.

Para cada TRF, registre domínio oficial, rota, método, payload, filtros,
paginação, grau, texto, documento, identificador, status e trace sanitizado.
Só classifique `route_validated` quando todos esses pontos forem observados;
caso contrário, registre `route_candidate`, `not_jurisprudence` ou
`blocked_external` e avance.

Não promova fontes à federação nesta meta. Ao final, rode os comandos de
`verification.md`, atualize a matriz nacional e informe arquivos, chamadas,
classificações e limitações. Não faça commit, push, release ou deploy.
