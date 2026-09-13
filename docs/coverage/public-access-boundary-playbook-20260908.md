# NanoJuris — playbook de acesso público legítimo

Versão: `2026-09-08`  
Escopo: descoberta e coleta bounded de jurisprudência em fontes oficiais  
Relacionados: SDD 0078, SDD 0080, SDD 0089 e SDD 0090

Este documento é o limite operacional para qualquer provider novo ou revalidado.
Ele permite aproveitar todas as superfícies públicas que uma fonte oferece sem
transformar um bloqueio de acesso em resultado vazio e sem tentar contornar
controles de segurança.

## Regra principal

Só é permitido usar uma superfície que possa ser acessada por uma navegação
pública normal, por uma API/exportação oficialmente documentada ou por uma
autorização explícita do mantenedor da fonte. A existência de uma rota no HTML,
JavaScript ou em um projeto de terceiros não prova autorização nem contrato.

Não existe uma “zona cinzenta” operacional neste projeto: quando a próxima
ação depender de evasão, solver ou credencial privilegiada, o estado é
`access_blocked` e a evidência é encerrada.

## Técnicas permitidas

| Técnica | Condição de uso | Evidência mínima |
|---|---|---|
| GET/POST/HEAD público | método e URL fazem parte da página, documentação ou exportação oficial | URL, método, data e fingerprint |
| Navegador padrão | somente a mesma jornada que um usuário anônimo faria | trace redigido e classificação da navegação |
| Cookies/CSRF de sessão | obtidos durante a jornada corrente; nunca persistidos ou reutilizados para atravessar desafio | escopo da sessão e expiração |
| Redirect oficial | seguir apenas destinos allowlistados e coerentes com a fonte | cadeia de URLs e host final |
| Paginação | usar parâmetros, cursores e limites publicados pela fonte | duas páginas quando possível e teste de sobreposição |
| Rate limit cooperativo | baixa frequência, concorrência limitada, respeito a `Retry-After` | timestamps, atraso aplicado e status |
| Retry transitório | somente timeout/rede/5xx elegíveis pelo transporte compartilhado | política, tentativa e motivo |
| ETag/Last-Modified | requisição condicional na mesma URL pública | cabeçalhos redigidos e resultado 304/200 |
| Exportação oficial | PDF, HTML, CSV, JSON, XML, RSS, sitemap, dataset ou ZIP oferecido pela fonte | URL de download, MIME, hash e tamanho |
| Superfície oficial alternativa | portal, API, exportação ou catálogo do próprio tribunal com o mesmo escopo textual | vínculo entre as superfícies e prova de grau |
| Desafio interativo mediado pelo usuário | humano conclui o desafio no navegador; o sistema só lê a página pública resultante | confirmação humana, sem token/cookie gravado |
| Proxy institucional | apenas egress aprovado para conectividade/observabilidade; não pode ocultar origem, rotacionar IP ou evitar limite | configuração fixa e finalidade |
| Suporte/allowlist | solicitação formal de rota, limite, fixture ou ambiente de homologação | ticket, resposta e escopo autorizado |

As técnicas acima não concedem acesso a conteúdo autenticado, restrito ou
privado. Também não autorizam aumentar frequência, paralelismo ou tamanho de
resposta além do que a fonte publica.

## Técnicas proibidas

Não implementar, recomendar ou experimentar:

- resolver CAPTCHA, Turnstile ou desafio equivalente por OCR, visão, serviço de
  terceiros, token pré-resolvido ou intervenção automatizada;
- contornar WAF, bot-management, fingerprint, JavaScript challenge ou login;
- reutilizar cookies, CSRF, tokens, URLs assinadas ou headers de outra sessão;
- rotacionar IP/proxy, falsificar User-Agent/fingerprint ou usar stealth para
  parecer um navegador diferente;
- desabilitar verificação TLS, aceitar certificado inválido ou fazer downgrade
  criptográfico;
- descobrir endpoints privados por fuzzing, brute force, bundle mining ou
  chamadas que a UI pública não realiza;
- repetir chamadas após 403, 429, CAPTCHA ou bloqueio sem uma nova autorização;
- usar credenciais pessoais, contas compartilhadas ou armazenamento de segredo
  em fixtures, logs ou repositório;
- alterar robots, termos, limites, controles de origem ou políticas da fonte;
- classificar HTML de bloqueio, timeout, schema inválido ou resposta vazia não
  autoritativa como `authoritative_empty`.

## Fluxo de decisão

1. Identificar a fonte oficial, a coleção e o grau pretendido.
2. Escolher a superfície pública documentada de menor custo (API/exportação
   antes de scraping HTML).
3. Fazer uma única chamada bounded, com timeout, limite de bytes e frequência
   conservadora.
4. Seguir somente redirects allowlistados e a paginação publicada.
5. Classificar a resposta antes de parsear:
   `success_with_results`, `authoritative_empty`, `unconfirmed_empty`,
   `access_blocked`, `rate_limited`, `timeout`, `transport_error`,
   `schema_invalid`, `partial` ou `cancelled`.
6. Se surgir um desafio passivo e a navegação normal continuar, registrar
   `challenge_passive` e prosseguir apenas pela jornada pública observada.
7. Se o desafio for exigido para obter a página, parar com `access_blocked`.
   Não chamar a próxima página por endpoint oculto nem tentar extrair o token.
8. Procurar uma alternativa oficial: exportação, dataset, RSS/sitemap, portal
   equivalente, contato técnico ou ambiente de homologação.
9. Se não houver alternativa autorizada, emitir evidência terminal e avançar
   para o próximo provider.

## Caso comum: CAPTCHA na primeira página, mas a segunda parece disponível

Isso não é autorização implícita. Verifique se a segunda página é alcançável
pela própria navegação pública, sem reproduzir token, cookie ou URL de uma sessão
desafiada. Se for, registre a jornada normal e o contrato observado. Se não for,
o provider permanece bloqueado; a existência de um link, parâmetro ou endpoint
no código do portal não muda a classificação.

## Registro obrigatório

Cada tentativa deve produzir um evento redigido com:

```json
{
  "provider": "...",
  "authority": "...",
  "surface": "...",
  "url": "https://...",
  "method": "GET",
  "observed_at": "2026-09-08T00:00:00Z",
  "http_status": 200,
  "classification": "success_with_results",
  "challenge": "none|passive|required|unknown",
  "redirect_chain": ["https://..."],
  "bytes": 1234,
  "content_type": "application/json",
  "page": 1,
  "rate_limit": {"retry_after_seconds": null, "delay_applied_seconds": 0},
  "evidence_id": "...",
  "raw_body_persisted": false
}
```

Não armazenar corpo bruto com dados pessoais quando um hash, fixture sanitizada
ou screenshot redigida for suficiente. O `SourceTrace` deve indicar o que veio
da fonte e o que foi transformado localmente.

## Critério de promoção

Uma superfície só pode ser promovida quando, além dos gates do SDD 0078/0080,
possuir contrato de grau/coleção, fixture de sucesso e vazio, fixture de
bloqueio ou schema inválido quando aplicável, paginação comprovada, chamada live
bounded e classificação de acesso pública. “HTTP 200” isolado não é suficiente.

Bloqueios externos, termos pendentes ou ausência de rota pública são estados
terminais para a execução local, não falhas a serem mascaradas.

## Orientação para o próximo modelo

- Leia SDD 0078 e 0080 antes de qualquer provider.
- Reutilize o transporte compartilhado e os classificadores existentes.
- Não repita chamadas contra a mesma proteção; use a evidência registrada.
- Trabalhe em lotes de um a três tribunais e regenere os inventários ao final.
- Atualize o pacote de execução 0089 e o ledger, sem alterar produção.
- Mantenha separados `live_validated`, `federation_enabled`, `legal_status` e
  `document_capability`.
- Se uma ação exigir autorização humana, gere uma solicitação em
  `docs/coverage/external-action-requests-20260907.md` e siga para outra fonte.

Este playbook complementa os SDDs existentes; não substitui termos de uso,
contratos do tribunal ou revisão humana.
