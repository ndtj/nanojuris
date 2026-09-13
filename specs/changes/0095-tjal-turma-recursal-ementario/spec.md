# 0095 — TJAL Turmas Recursais

Status: `in_progress`  
Escopo: provider local/federado opt-in para ementas oficiais das Turmas
Recursais do Tribunal de Justiça de Alagoas.

## Requisitos

- **REQ-001:** consultar somente hosts oficiais `aceco.tjal.jus.br`.
- **REQ-002:** preservar `authority=TJAL`, `branch=state`, `degree=recursal`,
  `instance=turma_recursal` e `collection=TJAL_TURMAS_RECURSAIS`.
- **REQ-003:** oferecer busca textual local sobre uma janela PDF bounded, sem
  criar índice persistente ou alegar total remoto.
- **REQ-004:** preservar número do processo, origem, relator, tipo de decisão,
  ementa, volume, página e URL da fonte quando extraíveis.
- **REQ-005:** rejeitar filtros de primeiro/segundo grau e qualquer autoridade
  diferente de TJAL.
- **REQ-006:** classificar HTTP 403/429, timeout, TLS, PDF inválido, PDF sem
  texto e redirect fora da allowlist como estados de erro, nunca como vazio.
- **REQ-007:** limitar tamanho, páginas e frequência; não executar OCR em
  imagem ou desafio.
- **REQ-008:** declarar `total_unknown` e `is_complete=false`, pois os PDFs
  são volumes históricos selecionados e não acervo integral.
- **REQ-009:** fornecer fixtures de sucesso, vazio, PDF inválido e erro externo,
  além de teste de escopo recursal.

## Fora de escopo

- CJPG, CJSG ou consulta processual;
- scraping de e-SAJ ou rotas privadas;
- OCR de páginas image-only;
- download automático de todos os volumes históricos;
- publicação, deploy ou alteração de produção.

## Critérios de aceite

- **AC-001:** chamada bounded ao índice oficial retorna links allowlisted.
- **AC-002:** ao menos um volume textual é parseado em registros recursais.
- **AC-003:** volume image-only gera `document_unavailable`, não vazio.
- **AC-004:** filtros textuais e número funcionam localmente.
- **AC-005:** contrato e fixtures passam nos gates do repositório.
- **AC-006:** provider permanece separado de CJPG/CJSG e não altera as métricas
  dessas coleções.
