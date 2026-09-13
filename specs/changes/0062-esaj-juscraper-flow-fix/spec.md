# 0062 - Alinhar fluxo eSAJ ao contrato do Juscraper

Status: verified
Owner: Provider Engineering, QA e Security

## Intenção

Corrigir o fluxo de busca CJSG dos adaptadores eSAJ do NanoJuris para
reproduzir o contrato público observado no Juscraper: submissão do formulário
por `POST /resultadoCompleta.do`, seguida de leitura da primeira página por
`GET /trocaDePagina.do` e paginação posterior na mesma sessão HTTP.

## Requisitos

- REQ-001: o `POST /resultadoCompleta.do` deve apenas estabelecer a busca e a sessão;
- REQ-002: toda busca deve executar o `GET` da página 1 antes de interpretar resultados;
- REQ-003: buscas de páginas posteriores devem manter a sessão e buscar a página 1 e a página solicitada;
- REQ-004: o TJSP deve propagar `conversationId` observado na página 1 para páginas posteriores;
- REQ-005: bloqueios, CAPTCHA, login, TLS, timeout e mudança de contrato nunca podem virar lista vazia;
- REQ-006: a interface pública dos providers e a separação CJPG/CJSG devem permanecer compatíveis;
- REQ-007: nenhum corpo live, cookie, token ou credencial deve ser persistido;
- REQ-008: a mudança não autoriza deploy, publicação ou bypass de controles externos.

## Critérios de aceite

- AC-001: testes verificam `POST -> GET página 1` para todos os providers eSAJ compartilhados;
- AC-002: testes verificam `POST -> GET página 1 -> GET página N` para paginação;
- AC-003: teste TJSP verifica propagação de `conversationId` sem expor o valor em logs públicos;
- AC-004: fixtures distinguem confirmação do POST, sucesso, vazio e bloqueio;
- AC-005: documentação canônica e compatibilidade são atualizadas e geradas;
- AC-006: suíte e gates locais passam;
- AC-007: rechecagem live bounded registra explicitamente sucesso ou bloqueio real.

## Fora de escopo

Resolver CAPTCHA/WAF/login, alterar políticas de robots, desabilitar TLS,
implementar Playwright automatizado ou promover novos providers para a busca
federada padrão.
