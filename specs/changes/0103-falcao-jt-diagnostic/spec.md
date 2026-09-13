# SDD 0103 - Falcao JT diagnostico

Status: `verified`
Owner: Provider Engineering
Data: `2026-09-10`

## Objetivo

Adicionar um adapter opt-in para sondar o repositorio oficial nacional Falcao
da Justica do Trabalho sem inventar um contrato de resultados enquanto a borda
CloudFront estiver intermitente ou retornar somente o shell Angular.

## Requisitos

- **REQ-001** — executar somente GET HTTPS bounded na origem oficial.
- **REQ-002** — classificar HTTP 403/CloudFront como controle de acesso, nunca
  como resultado vazio.
- **REQ-003** — classificar shell sem API como mudanca/ausencia de contrato.
- **REQ-004** — manter provider opt-in, sem federacao ou parser de documentos.
- **REQ-005** — permitir busca autorizada somente com token OIDC Bearer
  fornecido pelo chamador em sessão oficial, sem login, persistência, replay ou
  bypass.

## Critérios de aceite

- **AC-001** — fixture CloudFront gera `AccessControlRequiredError`.
- **AC-002** — fixture de shell gera `ParserContractChangedError`.
- **AC-003** — capabilities declaram paginacao, filtros e inteiro teor como
  desconhecidos/não suportados até existir resposta oficial reproduzivel.
- **AC-004** — a rota pública não usa cookie, token, proxy, sessão ou bypass;
  a rota autorizada aceita somente o token OIDC fornecido pelo chamador na
  mesma chamada.
- **AC-005** — `search_authorized` reutiliza o parser do contrato, redige o
  token de `raw`/trace e mantém o provider fora da federação até evidência live
  autorizada reproduzível.

## Fora de escopo

Descobrir endpoints ocultos, reutilizar material de navegador, resolver
CloudFront/CAPTCHA/WAF, criar corpus persistente ou promover a federação.
