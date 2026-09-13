# Design — TJMSP diagnóstico

O adapter usa `SharedHttpClient` com allowlist do host oficial, limite de 2 MB,
timeout, rate limit e zero retries. A resposta 403 é preservada como controle
de acesso. Se a página pública voltar a responder sem bloqueio, o shell ainda
exige contrato de resultados antes de qualquer parser ou promoção.
