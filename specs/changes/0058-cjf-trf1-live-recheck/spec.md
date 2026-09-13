# 0058 - Rechecagem live CJF/TRF1

Status: verified
Owner: Provider Research, QA e Security

## Intencao

Registrar a disponibilidade observada da superficie publica TRF1 do CJF em uma
rodada bounded, distinguindo pagina de desafio de resultados e preservando o
contrato runtime sem promocao baseada em uma unica fotografia.

## Requisitos

- REQ-001: executar somente GET publico, sem credenciais e com timeout explicito;
- REQ-002: classificar CAPTCHA/reCAPTCHA como `blocked_access`;
- REQ-003: persistir apenas metadados, hash, marcadores e limites, nunca o corpo;
- REQ-004: nao enviar POST especulativo quando a pagina inicial estiver bloqueada;
- REQ-005: atualizar dossie, contrato e catalogos em paridade;
- REQ-006: manter `runtime_unchanged` e nao converter bloqueio em lista vazia;
- REQ-007: nao alterar producao, deploy ou publicacao.

## Criterios de aceite

- AC-001: o artefato JSON registra HTTP 200 e a classificacao `blocked_access`;
- AC-002: o artefato nao contem corpo HTML, cookies, ViewState ou credenciais;
- AC-003: teste offline impede que a evidencia seja interpretada como resultado;
- AC-004: gates locais e auditorias geradas passam;
- AC-005: revisao humana permanece explicita antes de qualquer mudanca de tier.

## Fora de escopo

Bypass de CAPTCHA/WAF, captura de sessao autenticada, retry em escala, alteracao
de endpoint, implementacao da superficie unificada e promocao do provider.
