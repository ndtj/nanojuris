# 0032 — pipeline seguro de inteiro teor

Status: verified
Owner: Provider/Data Engineering e Security

## Intenção

Tratar documento e inteiro teor como cadeia própria, auditável e opcional, sem
misturar metadado de busca com download de conteúdo.

## Requisitos

- REQ-001: busca retorna referência documental, não baixa conteúdo por padrão.
- REQ-002: download exige capability, opt-in, URL allowlisted e limites.
- REQ-003: documento preserva content type, tamanho, hash, retrieved_at e trace.
- REQ-004: PDF, HTML, texto e formatos legados têm parsers separados.
- REQ-005: conteúdo excessivo, criptografado, corrompido ou inesperado é
  quarentenado.
- REQ-006: vínculo decisão-documento deve ser determinístico.
- REQ-007: OCR permanece dependência opcional, opera somente sobre documento
  público obtido legitimamente, nunca resolve CAPTCHA, e sua incerteza é explícita.
- REQ-008: fixtures minimizam conteúdo e dados pessoais.

## Critérios de aceite

- AC-001: nenhum download ocorre silenciosamente em search.
- AC-002: hash e trace permitem reproduzir a origem.
- AC-003: formatos inválidos e limites são testados.
- AC-004: documentos não alteram a identidade da decisão sem evidência.
- AC-005: segurança e licença são revisadas por fonte.
