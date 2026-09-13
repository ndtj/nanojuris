# 0059 - Rechecagem live STF Jurisprudencia

Status: verified
Owner: Provider Research, QA e Security

## Intencao

Registrar uma tentativa publica bounded no endpoint JSON do STF, mantendo a
distincao entre falha TLS, desafio de acesso e resposta JSON valida.

## Requisitos

- REQ-001: usar somente o POST publico ja contratado, sem credenciais;
- REQ-002: manter `verify_ssl=true` e timeout explicito;
- REQ-003: classificar falha de cadeia TLS como `blocked_transport`;
- REQ-004: nao persistir corpo, payload completo, cookies ou tokens;
- REQ-005: atualizar dossie, contrato e catalogos em paridade;
- REQ-006: preservar `runtime_unchanged` e nao converter falha em vazio;
- REQ-007: nao alterar producao, deploy ou publicacao.

## Criterios de aceite

- AC-001: artefato registra `SourceUnavailableError`/`SSLError` sem HTTP;
- AC-002: teste offline impede total ou resultados positivos na evidencia;
- AC-003: catalogo e workpack refletem o estado live mais recente;
- AC-004: suite e gates locais passam;
- AC-005: revisao humana continua obrigatoria.

## Fora de escopo

Desabilitar TLS no runtime, bypass de WAF/CAPTCHA, retry em escala, captura de
sessao, mudança de endpoint, alteração de parser e promoção para gold.
