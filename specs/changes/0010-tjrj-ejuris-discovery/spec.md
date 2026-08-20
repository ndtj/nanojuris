# Spec — descoberta TJRJ eJURIS

ID: `0010-tjrj-ejuris-discovery`
Status: `in_progress`
Owner: `NanoJuris engineering`
Data: `2026-08-20`

## Objetivo

Catalogar o eJURIS legado como candidato independente do eproc, preservando a
fronteira NanoJuris/NanoJud e sem promover busca que não possui contrato público
reproduzível.

## Requisitos

- RF-001: registrar `tjrj_ejuris` como candidato no registry.
- RF-002: manter dossiê canônico e cópia de compatibilidade com rotas,
  evidência, estados e limites.
- RF-003: excluir o candidato da busca unificada e do runtime.
- RF-004: classificar reCAPTCHA e contrato ausente como diagnóstico explícito,
  nunca como resultado vazio.
- RF-005: manter CPOPg processual fora do NanoJuris.

## Critérios de aceitação

- AC-001: o catálogo gerado contém `tjrj_ejuris` com lifecycle `candidate`.
- AC-002: o dossiê canônico e a cópia legada possuem paridade.
- AC-003: não existe módulo runtime, fixture decisória ou entrada de busca
  unificada para o candidato.
- AC-004: auditoria documental, coverage e validação SDD passam.
