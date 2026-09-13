# 0031 — avaliação executável de qualidade de providers

Status: verified
Owner: Data Quality e QA

## Intenção

Transformar maturidade em evidência reproduzível de contrato, dados e operação,
sem usar quantidade de providers como sinônimo de qualidade.

## Requisitos

- REQ-001: scorecard mede autoridade, contrato, identidade, texto, datas,
  provenance, paginação, completude, erros, fixtures e documentação.
- REQ-002: golden sets cobrem sucesso, vazio, parcial, inválido, timeout,
  bloqueio, rate limit e schema drift.
- REQ-003: invariantes detectam colisão, duplicidade, data inválida, HTML cru,
  URL insegura e campo obrigatório ausente.
- REQ-004: score e tier devem apontar evidência e data; nenhum número é manual
  sem justificativa.
- REQ-005: regressão crítica bloqueia promoção.
- REQ-006: qualidade do dado e saúde live são dimensões separadas.

## Critérios de aceite

- AC-001: scorecard é gerado para todos os providers runtime.
- AC-002: providers gold/premium não possuem lacuna crítica não aceita.
- AC-003: golden set é sanitizado e determinístico.
- AC-004: mutation/schema-drift tests provam falha explícita.
- AC-005: relatórios são consumíveis por CI e humanos.
