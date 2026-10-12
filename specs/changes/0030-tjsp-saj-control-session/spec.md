# 0030 - TJSP SAJ public control-session initialization

Status: `in_progress`

## Intent

Permitir que `tjsp_cjsg` reproduza a inicializacao publica de sessao usada pelo
SAJ/TJSP e, assim, aceite buscas que atualmente funcionam no script standalone.

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
- AC-002: busca live bounded com `dano moral` retorna resultados ou erro de
  controle explicito, nunca zero resultados enganoso.
- AC-003: pytest direcionado, lint, type-check e validacao SDD passam.
