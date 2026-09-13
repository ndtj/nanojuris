# 0060 - Rechecagem live TJPE Jurisprudencia

Status: verified
Owner: Provider Research, QA e Security

## Intencao

Revalidar de forma publica e bounded a rota REST do TJPE, distinguindo falha de
certificado TLS de respostas vazias, acesso controlado e JSON valido.

## Requisitos

- REQ-001: chamar apenas `GET /api/v1/jurisprudencias`, sem credenciais;
- REQ-002: manter `verify_ssl=true` e timeout explicito;
- REQ-003: classificar erro de certificado como `blocked_transport`;
- REQ-004: nao persistir corpo, cookies, tokens ou payload completo;
- REQ-005: atualizar dossie, contrato e catalogos em paridade;
- REQ-006: manter `runtime_unchanged` e nao converter falha em vazio;
- REQ-007: nao alterar producao, deploy ou publicacao.

## Criterios de aceite

- AC-001: artefato registra `SourceUnavailableError`/`SSLCertVerificationError` sem HTTP;
- AC-002: teste offline impede total ou resultados positivos na evidencia;
- AC-003: catalogo e workpack refletem a fotografia mais recente;
- AC-004: suite e gates locais passam;
- AC-005: revisao humana permanece explicita.

## Fora de escopo

Desabilitar TLS no runtime, bypass de WAF/CAPTCHA, retry em escala, mudanca de
endpoint, alteracao de parser e promocao para gold.
