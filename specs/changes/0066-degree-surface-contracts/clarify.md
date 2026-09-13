# Clarify - 0066

- O portal unificado do TJRN pode misturar PJe e SAJ; a origem permanece em
  `source_origin` e nao e convertida em uma colecao CJPG/CJSG.
- O TJRO publica graus distintos no mesmo indice; o sufixo PJEPG/PJESG e o
  campo numerico `grau_jurisdicao` sao evidencias por registro, nao contrato de
  filtro para toda a fonte.
- TJTO e TJGO aceitam parametros de instancia, mas um card sem grau explicito
  nao permite inferencia segura; o parser mantem `unknown`/`None`.
