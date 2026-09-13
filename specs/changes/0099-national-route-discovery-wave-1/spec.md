# Especificação — descoberta federal bounded

Status: `proposed`

## Objetivo

Para cada autoridade `TRF1`, `TRF2` e `TRF4`, identificar uma superfície
oficial pública que retorne jurisprudência textual de segundo grau e registrar
um contrato suficiente para o próximo lote de adapters.

## Requisitos

- **REQ-001** — a origem deve ser domínio oficial do tribunal ou órgão federal
  responsável pela jurisprudência;
- **REQ-002** — o método, rota, payload, headers públicos, paginação e limites
  devem ser reproduzíveis sem credenciais;
- **REQ-003** — a resposta deve provar `branch=federal` e `degree=second`;
- **REQ-004** — cada registro deve conter texto jurídico (ementa, decisão ou
  inteiro teor), identificador estável e trace de origem;
- **REQ-005** — filtros suportados, ignorados e traduzidos devem ser anotados;
- **REQ-006** — uma falha 403, CAPTCHA, WAF, Turnstile, timeout, TLS, 429 ou
  schema inesperado deve receber estado explícito e encerrar a tentativa;
- **REQ-007** — nenhuma fonte será promovida à federação nesta meta;
- **REQ-008** — toda conclusão terá fixture/evidência redigida ou classificação
  de bloqueio externo.

## Critérios de aceite

Uma fonte é `route_validated` somente com HTTP válido, conteúdo textual,
identidade de segundo grau, rota de detalhe ou documento observável e trace
sanitizado. `route_candidate` exige nova validação. `blocked_external` não é
falha do parser e não pode ser convertido em lista vazia.

## Critérios de aceite

- **AC-001** — cada TRF possui rota, método e classificação registrada;
- **AC-002** — nenhum bloqueio externo é representado como resultado vazio;
- **AC-003** — cada `route_validated` possui evidência e fixture sanitizada;
- **AC-004** — a matriz nacional é atualizada sem habilitar rollout padrão.
