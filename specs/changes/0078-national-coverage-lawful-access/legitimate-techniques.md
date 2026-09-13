# Técnicas legítimas para acesso a fontes públicas

Este documento é um guia operacional para ampliar a cobertura sem contornar
controles de segurança. Ele não autoriza exploração, autenticação indevida ou
uso de dados fora dos termos da fonte. Em caso de dúvida, a execução para e o
estado da superfície permanece explícito.

## Técnicas permitidas

1. **Descoberta pelo fluxo público:** abrir a página oficial, seguir a
   navegação normal, preencher uma consulta pequena e registrar somente a
   requisição necessária para reproduzi-la.
2. **Sessão efêmera:** aceitar cookies e tokens CSRF emitidos pela própria
   sessão; mantê-los apenas em memória e nunca gravá-los em fixtures, logs ou
   artefatos.
3. **JavaScript público:** executar o JavaScript entregue ao navegador em
   Chromium padrão, sem stealth, alteração de fingerprint ou automação
   disfarçada.
4. **Transporte observado:** reproduzir XHR, `fetch`, GraphQL ou BFF que a UI
   pública dispara, com o mesmo método, payload mínimo e cabeçalhos públicos.
5. **Redirect oficial:** seguir redirects somente quando o host final pertence
   à allowlist oficial da autoridade; registrar a cadeia e interromper diante de
   host inesperado.
6. **Compatibilidade de transporte:** tentar HTTP/1.1 quando uma fonte pública
   apresentar incompatibilidade de HTTP/2, mantendo verificação TLS e sem
   reduzir a validação de certificados.
7. **Resiliência conservadora:** usar timeout bounded, retry apenas para erro
   transitório documentado, backoff com jitter, cache efêmero e rate limit por
   fonte. Um retry não pode ser usado para insistir em 403, 429, CAPTCHA ou WAF.
8. **Rotas oficiais equivalentes:** verificar API, exportação, catálogo, feed,
   portal de jurisprudência, ementário ou download que a própria autoridade
   publica. A rota alternativa precisa provar o mesmo grau e tipo documental.
9. **Paginação autorizada:** usar apenas o cursor/página fornecido pela fonte,
   em poucas páginas, detectando repetição e sem enumerar parâmetros ocultos.
10. **Detalhe documental:** seguir o link oficial retornado pela decisão,
    validar host, MIME, magic bytes, tamanho, hash e conteúdo antes de extrair.

## CAPTCHA, WAF, Turnstile e páginas intermediárias

Um widget presente não é, sozinho, prova de bloqueio. O executor pode verificar
uma vez, pelo fluxo normal, se a consulta pública prossegue sem token humano e
entrega jurisprudência válida. Se o servidor exigir solução, token, interação
humana ou sessão autenticada, classificar `challenge_enforced`/`access_blocked`,
preservar a evidência redigida e avançar. Não é permitido solver, OCR do
desafio, interceptação/reutilização de token, cookie importado, stealth,
rotação de IP/proxy ou tentativa repetida contra a mesma proteção.

## Decision tree operacional

```text
rota oficial pública?
  não -> source_unavailable ou legal_pending
  sim -> consulta mínima bounded
          resposta jurisprudencial válida?
            sim -> validar grau, identidade, paginação e documento
            não -> erro externo, schema_invalid ou challenge_enforced
                      nunca authoritative_empty sem prova de vazio
```

## Evidência mínima por tentativa

- autoridade, superfície e URL de entrada;
- data/hora, método e payload sanitizado;
- status HTTP, host final, MIME e tamanho;
- classificação (`success_with_results`, `authoritative_empty`,
  `challenge_enforced`, `access_blocked`, `timeout`, `rate_limited`,
  `schema_invalid` ou `source_unavailable`);
- identificador, grau, coleção, resumo/inteiro teor e trace quando houver;
- fixture redigida e comando reproduzível;
- alternativa oficial avaliada e motivo para não utilizá-la.

## Critério de parada

Ao primeiro bloqueio estável, cessar novas tentativas equivalentes. A superfície
fica visível no diagnóstico, não entra na federação padrão e só pode ser
reavaliada após mudança observável da fonte ou autorização humana documentada.
