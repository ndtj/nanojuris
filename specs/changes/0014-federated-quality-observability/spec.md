# Qualidade federada e observabilidade

Status: `verified`

## Intenção

Fechar os próximos achados da auditoria local: isolamento de itens inválidos
em buscas federadas, mensagens de erro seguras e métricas de persistência
semânticas.

## Requisitos

- **REQ-001**: um registro inválido não pode descartar registros válidos da
  mesma página federada.
- **REQ-002**: erros retornados ao consumidor devem ser limitados e não conter
  segredos, PII desnecessária ou payload jurídico integral.
- **REQ-003**: `record_count` deve ter definição documentada e testes que
  diferenciem entradas recebidas de registros persistidos/deduplicados.
- **REQ-004**: rastreabilidade de fixtures deve ser automatizada sem inventar
  rotas ou dados.

## Aceite

- **AC-001**: lote federado misto preserva válidos e reporta inválidos.
- **AC-002**: sanitização de erros é determinística e compatível.
- **AC-003**: métrica documentada e coberta por teste.
- **AC-004**: inventário de fixtures atualizado e auditável.
- **AC-005**: suíte, lint, compilação e SDD passam.

## Fora de escopo

Não inclui chamadas live, bypass de controles, promoção de candidatos ou
alterações de catálogo sem evidência.
