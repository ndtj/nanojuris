# Pesquisa — discovery de todos os providers

## Objetivo

Produzir uma fotografia reproduzível de todos os providers registrados em runtime,
comparando declarações de capabilities com rotas, filtros, formatos, estados de
acesso e sinais de conteúdo observados em endpoints públicos.

## Decisões

- O escopo é limitado aos providers registrados e às URLs declaradas em runtime.
- A coleta é bounded por fonte, domínio, profundidade, bytes, timeout e intervalo.
- Apenas GET declarado ou link GET observado é reproduzido automaticamente.
- POST, payloads de pesquisa e rotas com placeholders não são adivinhados.
- CAPTCHA, WAF, login, rate limit, TLS e timeout são resultados técnicos explícitos.

## Critério de evidência

Uma declaração só pode ser promovida para contrato operacional quando houver
resposta reproduzível, hash, content-type, status, rota/método, filtros observados
ou justificativa de ausência, e teste offline correspondente.
