# Threat model

## Ativos

Cookies de sessão pública, identificadores de decisões, metadados de
proveniência e conteúdo jurídico retornado por fonte oficial.

## Ameaças

- interpretar confirmação do POST como conteúdo e produzir resultados vazios;
- perder sessão ou `conversationId` e atribuir falha ao parser;
- transformar CAPTCHA/WAF/login em zero resultados;
- registrar corpo, cookie ou token em fixture/log;
- aumentar frequência de chamadas ao repetir a primeira página.

## Mitigações

- fluxo explícito POST/GET com uma chamada bounded extra;
- sessão única por busca e `conversationId` somente em memória;
- diagnóstico de acesso antes do parser;
- artefatos sem corpo e testes sanitizados;
- respeito ao rate limit e nenhuma automação de bypass.
