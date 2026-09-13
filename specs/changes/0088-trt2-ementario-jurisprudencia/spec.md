# 0088 — TRT2 ementário público de jurisprudência

Status: `in_progress`

## Objetivo

Disponibilizar uma superfície oficial, estática e bounded de ementas de
acórdãos do TRT2, separada da busca PJe protegida por desafio. O provider deve
ser útil para descoberta e leitura, sem declarar cobertura completa do acervo.

## Critérios de aceitação

- **AC-001:** cada registro aceito tem `authority=TRT2`, `branch=labor`,
  `degree=second`, `instance=second` e `collection=TRT2_EMENTARIO`.
- **AC-002:** somente links observados nos índices oficiais são seguidos.
- **AC-003:** a consulta é bounded a 32 tópicos e declara total desconhecido.
- **AC-004:** PDF, MIME, host, tamanho, hash e trace são preservados quando
  houver documento.
- **AC-005:** filtros não suportados permanecem explicitamente rejeitados ou
  marcados como `unsupported`.
- **AC-006:** 403, 429, timeout, CloudFront e schema drift não são vazio.
- **AC-007:** a federação padrão pode usar o provider somente como fonte parcial
  explicitamente incompleta, com `total_known=false` e limites bounded.
- **AC-008:** nenhum CAPTCHA, WAF, token, cookie importado ou bypass é usado.

## Fora de escopo

Busca PJe completa, consulta processual, enumeração agressiva de arquivos,
OCR, acesso autenticado e afirmação de cobertura nacional do TRT2.
