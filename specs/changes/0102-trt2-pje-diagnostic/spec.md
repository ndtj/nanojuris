# SDD 0102 - TRT2 PJe jurisprudencia diagnostico

Status: `verified`  
Owner: Provider Engineering  
Data: `2026-09-10`

## Objetivo

Implementar o adapter seguro para a superficie publica de jurisprudencia PJe
do TRT da 2a Regiao, incluindo o catalogo de opcoes/filtros e a classificacao
explicita do desafio que impede a entrega automatizada de decisoes.

## Requisitos

- **REQ-001** - consultar `GET /juris-backend/api/opcoes` sem persistir segredos
  ou material de desafio;
- **REQ-002** - consultar `POST /juris-backend/api/filtros` como catalogo
  diagnostico, sem trata-lo como busca de decisoes;
- **REQ-003** - transportar `POST /juris-backend/api/documentos` com limite de
  bytes, timeout e allowlist HTTPS;
- **REQ-004** - classificar `tokenDesafio`, `imagem` e `audio` como
  `AccessControlRequiredError`, nunca como vazio;
- **REQ-005** - quando uma resposta futura publica documentos, normalizar
  `authority=TRT2`, `branch=labor`, `degree=second`, `instance=second` e
  `collection=JURISPRUDENCIA`;
- **REQ-006** - manter runtime apenas opt-in e fora da federacao padrao ate que
  resultado, paginacao, documento e fixtures live sejam comprovados.

## Fora de escopo

Resolver CAPTCHA, gerar ou reutilizar token, automatizar desafio humano,
contornar WAF, usar credenciais/cookies, afirmar cobertura do corpus ou
promover a busca federada.

## Critérios de aceite

- **AC-001** — opções e filtros públicos são consultados sem expor o segredo
  `recaptchaSecretKey`.
- **AC-002** — a tentativa de documentos preserva o payload de segundo grau e
  classifica desafio como controle de acesso, nunca como vazio.
- **AC-003** — HTTP 403/429, timeout, TLS e schema inválido permanecem estados
  explícitos.
- **AC-004** — o provider é opt-in e não altera o roteamento federado padrão.
- **AC-005** — qualquer promoção futura exige resposta pública com documentos,
  paginação, contrato de detalhe e fixtures live; a ausência atual mantém o
  provider como candidato.
