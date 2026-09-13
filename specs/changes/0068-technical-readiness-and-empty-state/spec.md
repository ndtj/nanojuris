# 0068 — prontidão técnica e estados vazios

Status: `verified`

## Intenção

Evitar que uma resposta sem registros seja tratada como disponibilidade quando
o provider não comprovou que a janela remota foi esgotada. Permitir promoção
local dos providers que passam todos os gates técnicos quando o operador
registrar essa decisão, sem alterar produção.

## Requisitos

- REQ-001: distinguir `empty` confirmado de `empty_unconfirmed`.
- REQ-002: health, validação e federação devem preservar essa distinção.
- REQ-003: `empty_unconfirmed` não pode ser considerado operacional ou aprovado.
- REQ-004: a promoção deve exigir contrato, live, fixtures, qualidade e acesso
  público; a decisão operacional não pode liberar fonte bloqueada.
- REQ-005: bloqueios de acesso, transporte, TLS, timeout e schema drift devem
  permanecer observáveis.
- REQ-006: providers que não exibem contador remoto devem marcar o total como
  desconhecido, inclusive quando retornam registros, e nunca inferir total zero.
- REQ-007: a matriz de superfícies deve consumir o manifesto técnico gerado,
  reconciliando a decisão de operador sem promover superfícies sem contrato.
- REQ-008: memória de seletores adaptativos não pode reintroduzir registros de
  uma página anterior em uma resposta explicitamente vazia.
- REQ-009: o parser TJSP/CJSG deve expor total, completude e estados de acesso
  e extração no mesmo contrato das demais fontes.
- REQ-010: o parser TJSP/CJPG também deve impedir relocação de linhas antigas
  em uma resposta vazia e manter `total_known` coerente quando não há contador.
- REQ-011: o parser TJTO deve aplicar a mesma semântica de total desconhecido e
  nunca reutilizar cards adaptativos quando a página declarar vazio explícito.
- REQ-012: a matriz não deve marcar uma superfície como federada apenas pela
  capacidade declarada; o modo `enabled` do manifesto técnico é obrigatório.

## Critérios de aceite

- AC-001: página sem resultados e sem prova de completude gera
  `empty_unconfirmed`.
- AC-002: página explicitamente vazia continua gerando `empty`.
- AC-003: o manifesto promove somente fontes tecnicamente prontas aceitas pelo
  operador, sem modificar runtime por efeito colateral.
- AC-004: testes offline, smoke live bounded e gates estáticos passam.
- AC-005: TJPI/JusPI e TJPR preservam `total_known=False` quando o contador
  remoto não está presente, com regressão coberta por fixtures.
- AC-006: o registro de superfícies marca como `operator_approved` apenas as
  superfícies de providers explicitamente aprovados ou tecnicamente prontos
  pelo manifesto, preservando `pending_human_review` nos demais casos.
- AC-007: uma consulta vazia do TJPI continua `is_explicit_empty=True` mesmo
  após uma página de sucesso ter alimentado a memória adaptativa.
- AC-008: TJSP/CJSG retorna `total_known`, `is_complete`, `access_status` e
  `extraction_status` para páginas com resultados, vazias e sem contador.
- AC-009: TJSP/CJPG permanece explicitamente vazio após uma página de sucesso
  ter populado a memória adaptativa e marca contador ausente como desconhecido.
- AC-010: TJTO preserva `total_known=False` sem contador e uma página vazia
  continua sem resultados mesmo quando a memória adaptativa possui um card
  anterior.
- AC-011: superfícies de providers `opt_in`, `blocked` ou sem decisão no
  manifesto permanecem `not_enabled`, ainda que declarem `unified_search`.

## Fora de escopo

Deploy, publicação, bypass de controles de acesso e alteração de dados em
produção.
