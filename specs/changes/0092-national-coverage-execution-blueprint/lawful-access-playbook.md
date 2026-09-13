# Playbook de acesso público lícito

Este playbook existe para evitar que outro modelo pare na primeira resposta
403, mas também para impedir bypass. As ações são ordenadas do menor ao maior
envolvimento externo.

## Sequência permitida

1. **Entrada oficial:** usar o link de jurisprudência publicado pelo tribunal;
   não adivinhar endpoint privado.
2. **Metadados públicos:** ler HTML, `robots.txt`, sitemap, RSS, `config.json`
   e documentação entregue ao navegador.
3. **Fluxo normal:** seguir redirects, cookies e CSRF da sessão própria; usar o
   método e payload observados no frontend público.
4. **Paginação publicada:** respeitar cursor/página, limite e ordenação exibidos.
5. **Condições transitórias:** uma nova tentativa bounded somente para timeout ou
   erro transitório previsto, com backoff e teto de chamadas.
6. **Condicionamento:** se aparecer CAPTCHA/Turnstile/WAF/login, registrar o
   desafio e procurar rota oficial alternativa, export, API ou contato.
7. **Apoio institucional:** solicitar API, export, allowlist, frequência e
   termos por canal oficial; registrar a resposta como decisão humana.
8. **Parada:** sem alternativa pública, marcar `blocked_external` e avançar.

## CAPTCHA em uma etapa e página seguinte

O fato de uma URL posterior responder quando aberta isoladamente não autoriza
usar a página de desafio como ponte. O executor deve separar os casos:

| Situação observada | Ação permitida | Estado da busca |
| --- | --- | --- |
| A rota seguinte está publicada no link oficial, aceita uma requisição anônima limpa e entrega o contrato esperado | chamar uma única vez com limite; registrar URL, host e prova de que não depende do desafio | `success_with_results` ou `authoritative_empty` |
| A rota seguinte só funciona com cookie/CSRF emitido depois do desafio | não automatizar nem transportar o desafio; solicitar fluxo mediado/allowlist ao tribunal | `access_blocked` |
| A rota seguinte funciona na mesma sessão manual, mas a API exige token assinado ou cabeçalho não publicado | não persistir/reproduzir token; documentar a dependência | `challenge_enforced` |
| A página seguinte é um export/API oficial claramente vinculado no próprio portal | usar o export/API com o mesmo limite e contrato, sem reaproveitar token de desafio | `success_with_results` ou `source_unavailable` |

Uma sessão manual pode confirmar visualmente que o tribunal oferece uma rota,
mas o token, cookie de desafio e URL assinada não entram em fixtures, cache,
logs ou código. O provedor permanece fora da federação enquanto a rota pública
reproduzível não for comprovada.

## Técnicas avançadas permitidas

Estas técnicas melhoram confiabilidade sem esconder a origem ou contornar
controle de acesso:

- observar somente requisições feitas pelo frontend público durante uma sessão
  anônima normal;
- seguir redirects para hosts oficiais allowlisted e rejeitar saltos externos;
- usar `ETag`, `Last-Modified`, `Retry-After` e `Cache-Control` quando publicados;
- respeitar cursores, limites, ordenação e intervalos de data declarados pelo
  portal;
- aplicar backoff cooperativo apenas em timeout, reset e 5xx transitórios;
- solicitar formalmente API, CSV, XML, JSON, RSS, sitemap, dataset, allowlist
  ou ambiente de homologação;
- manter egress institucional fixo previamente autorizado, sem rotação para
  evasão;
- redigir corpos e identificadores sensíveis, guardando apenas hashes,
  metadados e fixtures sanitizadas.

Nenhuma dessas técnicas transforma um endpoint privado em público. Se o
contrato não puder ser reproduzido por uma requisição normal e limitada, a
classificação correta continua sendo bloqueio externo.

## Nunca fazer

- solver, OCR ou automação de CAPTCHA/Turnstile;
- alterar fingerprint, stealth, spoofing, replay ou injeção de tokens;
- alternar IP/proxy para escapar de limite ou WAF;
- downgrade TLS, desabilitar verificação ou usar endpoint privado;
- bombardear uma fonte para “provar” que funciona;
- transformar HTML de desafio, timeout ou 403 em `[]`;
- usar dados restritos de magistrados/servidores sem autorização.

## Classificação padrão

| Observação | Estado |
| --- | --- |
| resultados + identidade + texto válidos | `success_with_results` |
| resposta oficial declara zero | `authoritative_empty` |
| página normal sem prova de total | `unconfirmed_empty` |
| CAPTCHA, Turnstile, WAF, login, 403 | `access_blocked` |
| 429 ou cabeçalho de limite | `rate_limited` |
| timeout/TLS/reset | `timeout` ou `transport_error` |
| JSON/HTML incompatível | `schema_invalid` |
| fonte fora do ar/rota removida | `source_unavailable` |

Toda classificação deve apontar para um evidence ID redigido.
