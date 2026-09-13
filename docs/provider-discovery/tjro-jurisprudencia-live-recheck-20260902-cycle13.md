# TJRO jurisprudência — rechecagem live bounded (ciclo 13)

Em 2026-09-02 foi feita uma única chamada pública, sem credenciais e sem
contornar CAPTCHA/WAF, para `POST /search/varios_parametros/` com
`from=0`, `size=1` e `fields.query=responsabilidade`.

Resultado observado:

- HTTP **200**, `application/json`;
- `hits.total.value=676011` e um hit retornado;
- primeiro hit com `_id`, grau `1` e sistema `PJEPG`;
- corpo com 93.148 bytes, SHA-256
  `92be2fa33ad1f1373e68664fcaaf2d8fbf627e90db8141ecb97a8b715fd13040`;
- latência observada: 1.674,95 ms.

O corpo não foi persistido. A evidência machine-readable está em
`tjro-jurisprudencia-live-recheck-20260902-cycle13.json`. Isso confirma a
listagem e o offset já documentados; não promove o provider nem fecha a rota
de detalhe, o limite remoto de `size` ou a federação padrão.
