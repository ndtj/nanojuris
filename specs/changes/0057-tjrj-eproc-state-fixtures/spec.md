# 0057 - Estados de resposta TJRJ/eproc

Status: verified
Owner: Provider Engineering, Data Quality, QA e Security

## Intencao

Cobrir explicitamente os estados de busca publica vazia e de desafio de acesso
do TJRJ/eproc. O parser deve aceitar uma pagina publica sem cards como vazio
legitimo e levantar erro de acesso para CAPTCHA/WAF, sem mascarar a diferenca.

## Requisitos

- REQ-001: versionar fixture HTML de busca publica sem resultados;
- REQ-002: versionar fixture HTML de desafio sem cards;
- REQ-003: exercitar `parse_eproc_jurisprudencia_results` com identidade TJRJ;
- REQ-004: garantir que desafio levante `AccessControlRequiredError`;
- REQ-005: atualizar dossie, contrato e catalogo de fixtures;
- REQ-006: nao alterar endpoint, parser compartilhado, promocao ou producao.

## Criterios de aceite

- AC-001: pagina vazia retorna lista vazia somente quando contem formulario de
  pesquisa publico;
- AC-002: pagina de desafio nao retorna lista vazia e gera erro de acesso;
- AC-003: fixtures nao contem cookies, tokens, nomes reais ou credenciais;
- AC-004: testes, auditorias e gates passam;
- AC-005: nenhum deploy, push ou chamada live e realizado neste ciclo.

## Fora de escopo

Bypass de CAPTCHA/WAF, captura de resposta live, mudanca de status de acesso,
inteiro teor e paginacao remota.
