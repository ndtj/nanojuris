# 0085 — certificação contínua

Status: `proposed`

Operar a cobertura com freshness, smoke, drift, shadow, rollback e promoção
local automática, mantendo deploy fora do programa.

- **AC-001:** evidência expirada reabre somente os gates afetados.
- **AC-002:** schema drift e queda de completude geram alerta e bloqueiam promoção.
- **AC-003:** smoke periódico não grava conteúdo pessoal ou tokens.
- **AC-004:** rollback de parser é reversível e testado.
- **AC-005:** cada smoke federado preserva, sem corpos de resposta, as fontes
  pesquisadas, puladas, com avisos e com falhas em um envelope redigido.
