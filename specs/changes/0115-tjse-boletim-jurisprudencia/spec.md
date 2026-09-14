# TJSE Boletim Jurídico — superfície pública de segundo grau

Status: verified

## Objetivo

Adicionar uma superfície independente para as ementas do Boletim Jurídico do
TJSE. A rota é pública, não exige sessão autenticada nem desafio no fluxo
observado, e publica material das câmaras, seção especializada e tribunal
pleno. O adapter não substitui a pesquisa judicial protegida por Turnstile.

## Requisitos

- REQ-001: aceitar somente consultas com termo, número ou frase e escopo de
  segundo grau estadual.
- REQ-002: descobrir edições por `pesquisar.wsp` e obter uma seção por
  `principal.wsp`, preservando o HTML bruto em `SourceTrace`/`raw`.
- REQ-003: extrair ementa, classe, processo, acórdão, relator, data da edição e
  URL pública do acórdão como `JurisprudenceResult` canônico.
- REQ-004: expor falhas HTTP, timeout, rate limit e schema inválido como erro
  explícito; nunca convertê-las em vazio.
- REQ-005: limitar cada chamada a uma edição/seção e no máximo 100 resultados
  locais; declarar total entre edições como desconhecido.

## Critérios de aceitação

- AC-001: fixture de pesquisa e principal gera resultado com
  `authority=TJSE`, `branch=state`, `degree=second`, `instance=second` e
  `collection=CJSG`.
- AC-002: fixture sem registros é marcado como vazio explícito; HTML inválido
  gera `ParserContractChangedError`.
- AC-003: filtros de escopo incompatíveis geram `QueryRejectedError`.
- AC-004: chamada live bounded retorna pelo menos uma ementa da seção pública
  ou registra bloqueio/indisponibilidade sem promoção automática.
