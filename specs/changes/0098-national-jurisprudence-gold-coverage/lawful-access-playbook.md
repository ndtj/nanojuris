# Playbook de acesso público legítimo

## Regra absoluta

O NanoJuris só consulta conteúdo que uma pessoa anônima poderia obter pela
jornada pública normal, uma API/exportação oficialmente documentada ou uma
autorização formal do mantenedor. Não existe “zona de sombra” autorizada.

## Técnicas permitidas

| Técnica | Limite operacional | Evidência |
| --- | --- | --- |
| GET/POST/HEAD público | rota e método publicados ou observados na UI pública | URL, método, data, hash |
| Navegador padrão | mesma jornada de usuário anônimo, sem stealth | trace redigido |
| Cookies/CSRF | somente sessão corrente, sem persistência ou replay | escopo/expiração |
| Redirect oficial | host final allowlistado | cadeia de URLs |
| Paginação publicada | cursor/offset e limites da fonte | páginas e sobreposição |
| Retry transitório | apenas rede, timeout elegível ou 5xx definido | tentativas e motivo |
| `Retry-After` | respeitar atraso e concorrência | timestamps |
| ETag/Last-Modified | somente URL pública | cabeçalhos e 304/200 |
| Exportação oficial | PDF, HTML, CSV, JSON, XML, RSS, sitemap, ZIP ou dataset | MIME, tamanho, hash |
| Portal equivalente | mesmo tribunal e mesmo escopo textual comprovado | vínculo e grau |
| Desafio mediado por humano | humano conclui no navegador; agente lê resultado público | confirmação sem token |
| Proxy institucional fixo | somente conectividade/observabilidade, sem ocultar origem | configuração e finalidade |
| Suporte/allowlist | ticket formal com escopo | número e resposta |

## Técnicas proibidas

- resolver CAPTCHA/Turnstile por OCR, visão, serviço externo, token ou automação;
- burlar WAF, bot management, fingerprint, JavaScript challenge ou login;
- reutilizar cookie, CSRF, token, URL assinada ou cabeçalho de outra sessão;
- rotacionar IP/proxy, falsificar User-Agent ou usar stealth;
- desabilitar TLS, aceitar certificado inválido ou fazer downgrade;
- fuzzing, brute force, bundle mining ou descoberta de endpoint privado;
- repetir após 403/429/desafio sem nova autorização;
- usar credenciais pessoais ou gravar segredos em fixtures/logs;
- alterar robots, termos, limites ou políticas da fonte;
- chamar consulta processual em lugar de jurisprudência.

## Fluxo de decisão

1. Identificar fonte oficial, coleção e grau.
2. Escolher API/exportação antes de HTML.
3. Fazer chamada única, bounded, com timeout, bytes e baixa frequência.
4. Seguir redirects allowlistados e paginação documentada.
5. Classificar antes de parsear: `success_with_results`,
   `authoritative_empty`, `unconfirmed_empty`, `access_blocked`,
   `rate_limited`, `timeout`, `transport_error`, `schema_invalid`, `partial`
   ou `cancelled`.
6. Se houver desafio passivo e a navegação pública continuar sem token especial,
   registrar `challenge_passive` e prosseguir somente pela mesma jornada.
7. Se o desafio for requisito para obter dados, parar em `access_blocked`.
8. Procurar alternativa oficial ou solicitar allowlist/fixture ao mantenedor.
9. Encerrar o provider localmente se a alternativa não existir.

## Caso: CAPTCHA na primeira tela, próxima página parece acessível

Um link visível não é autorização para chamar endpoint oculto. A segunda página
só pode ser usada se o navegador público normal a alcançar sem extrair, copiar ou
reutilizar token de desafio. Caso contrário, registrar bloqueio e não insistir.

## Registro mínimo

```json
{
  "provider": "...",
  "authority": "TJXX",
  "surface": "CJSG",
  "url": "https://oficial.example/rota",
  "method": "GET",
  "observed_at": "2026-09-08T00:00:00Z",
  "classification": "success_with_results",
  "challenge": "none|passive|required|unknown",
  "redirect_chain": [],
  "bytes": 0,
  "content_type": "application/json",
  "page": 1,
  "rate_limit": {"retry_after_seconds": null, "delay_applied_seconds": 0},
  "evidence_id": "provider-live-...",
  "raw_body_persisted": false
}
```

Esse evento deve ser redigido, sem PII desnecessária, tokens, cookies ou corpo
integral quando um hash/fixture basta.

