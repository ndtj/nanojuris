# 0061 - Rechecagem live TJSP/CJSG

Status: verified
Owner: Provider Research, QA e Security

## Intencao

Revalidar o fluxo público CJSG do TJSP em uma chamada bounded, distinguindo
controle de acesso de pagina vazia ou resultado válido.

## Requisitos

- REQ-001: chamar apenas o POST público já contratado, sem credenciais;
- REQ-002: classificar sinais de captcha/login como `blocked_access`;
- REQ-003: não persistir corpo, cookies, tokens ou payload completo;
- REQ-004: manter `runtime_unchanged` e não converter bloqueio em vazio;
- REQ-005: atualizar dossiê, contrato e catálogos em paridade;
- REQ-006: não alterar produção, deploy ou publicação.

## Critérios de aceite

- AC-001: artefato registra os sinais de acesso observados;
- AC-002: teste offline impede resultados positivos na evidência bloqueada;
- AC-003: catálogo e workpack refletem a fotografia mais recente;
- AC-004: suíte e gates locais passam;
- AC-005: revisão humana permanece obrigatória.

## Fora de escopo

Bypass de CAPTCHA/WAF/login, captura de sessão, retry em escala, alteração de
endpoint/parser e promoção para gold.
