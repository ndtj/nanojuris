# 0030 - TJSP SAJ public control-session initialization

Status: `verified`

## Intent

Permitir que `tjsp_cjsg` reproduza a inicializacao e a continuacao publica de
sessao usadas pelo SAJ/TJSP, sem transformar uma tela de controle em uma busca
bem-sucedida.

## Scope

- chamar `POST /captchaControleAcesso.do` na mesma sessao quando houver UUID no
  formulario;
- reutilizar somente o `uuidCaptcha` retornado pela fonte;
- manter CAPTCHA, login, token fabricado, credenciais e cookies persistentes fora
  do escopo;
- atualizar exemplo, testes, contratos e evidencias.

## Requirements

- REQ-001: o provider deve manter GET, inicializacao e POST na mesma sessao.
- REQ-002: UUID retornado pela fonte deve substituir o UUID inicial no payload.
- REQ-003: resposta de controle sem JSON/UUID nao pode virar resultado falso.
- REQ-004: CAPTCHA, login e sessao ausente continuam estados observaveis.
- REQ-005: documentacao e testes devem descrever a nova sequencia.

## Acceptance criteria

- AC-001: testes offline comprovam a ordem GET -> controle -> busca.
- AC-002: busca live bounded com `dano moral` retorna resultados publicos pela
  continuacao `trocaDePagina.do`, ou erro de controle explicito quando a
  resposta final permanece bloqueada.
- AC-003: pytest direcionado, lint, type-check e validacao SDD passam.
