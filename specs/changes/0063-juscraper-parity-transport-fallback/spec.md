# 0063 - Paridade segura de transporte para TJCE, TJPE, TJTO e TJSP

Status: verified
Owner: Provider Engineering, QA e Security

## Intenção

Alinhar os adaptadores locais aos contratos públicos reproduzíveis observados
no Juscraper, sem tratar bloqueios externos como resultados vazios e sem
contornar controles de acesso. O escopo cobre a negociação TLS legada do
TJCE, o fluxo JSF/RichFaces público do TJPE como fallback explícito, e
retentativas limitadas para respostas transitórias nos adaptadores TJTO/TJSP.

## Requisitos

- REQ-001: a sessão do TJCE pode negociar apenas o nível TLS mínimo exigido
  pela fonte, mantendo verificação de certificado habilitada;
- REQ-002: o TJPE deve preservar a API REST atual e oferecer o fluxo público
  JSF/RichFaces em modo opt-in ou `auto` somente para falhas de transporte;
- REQ-003: o fluxo JSF do TJPE deve manter JSESSIONID/ViewState em memória,
  extrair IDs dinâmicos de submissão/paginação e mapear os campos canônicos;
- REQ-004: retentativas são bounded, respeitam `Retry-After`/backoff e nunca
  transformam 401/403/CAPTCHA/WAF em zero resultados;
- REQ-005: respostas HTML/JSON são preservadas em `raw` e `SourceTrace`, com
  endpoint efetivamente utilizado e motivo de fallback;
- REQ-006: contratos públicos, identificadores e separação CJPG/CJSG atuais
  permanecem compatíveis;
- REQ-007: fixtures são sintéticas/sanitizadas; nenhum cookie, token, corpo
  live ou credencial é persistido;
- REQ-008: não há bypass de CAPTCHA, WAF, login, robots, rate limit ou TLS
  inseguro, nem deploy/publicação neste pacote.

## Critérios de aceite

- AC-001: teste do TJCE confirma montagem do adaptador TLS e `verify=True`;
- AC-002: testes TJPE cobrem GET de consulta, POST com ViewState, escolha de
  tipo, paginação AJAX, parser, vazio, mudança de schema e bloqueio;
- AC-003: testes TJTO/TJSP cobrem retentativa limitada de 429/5xx e preservam
  a classificação final;
- AC-004: a suíte, Ruff, mypy, compilação, `validate_sdd.py` e diff-check passam;
- AC-005: documentação canônica, matriz e catálogo gerados são atualizados;
- AC-006: chamada live pública bounded registra sucesso ou bloqueio real sem
  persistir conteúdo sensível.

## Fora de escopo

Automação de navegador, resolução de CAPTCHA, rotação de IP, desativação de
verificação TLS, autenticação, alteração de produção e substituição do
contrato REST do TJPE.
