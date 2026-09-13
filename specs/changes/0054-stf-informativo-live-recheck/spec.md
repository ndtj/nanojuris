# 0054 - Rechecagem live do STF Informativo

Status: verified
Owner: Provider Research, QA e Security

## Intencao

Registrar a disponibilidade observada da planilha XLSX oficial do Informativo
STF em uma rodada publica bounded, sem converter falha de transporte ou acesso
em resultado vazio e sem alterar o provider runtime.

## Requisitos

- REQ-001: executar somente GET publico, sem credenciais e com timeout explicito;
- REQ-002: distinguir `blocked_transport` de `blocked_access` e de XLSX valido;
- REQ-003: persistir apenas metadados, hash e limites, nunca o corpo live;
- REQ-004: manter `verify_ssl=True` como padrao do provider;
- REQ-005: atualizar dossie e contrato sobre a fotografia operacional;
- REQ-006: nao promover, remover ou reclassificar o provider por uma unica
  rodada de ambiente.

## Criterios de aceite

- AC-001: artefato JSON registra as duas tentativas e classificacoes;
- AC-002: nenhum HTTP 403/SSL e apresentado como lista vazia;
- AC-003: teste local valida ausencia de corpo e credenciais;
- AC-004: gates e auditorias passam sem alteracao de producao.

## Fora de escopo

Retry em escala, bypass de WAF/TLS, captura de cookies, persistencia do XLSX,
mudanca de endpoints e alteracao da categoria runtime.
