# Clarificações

## C1 — O que significa “sistema completo”?

Nesta fase significa núcleo de coleta, parsing, normalização, proveniência,
persistência e providers com contrato reproduzível. Uma fonte sem evidência
local não pode ser considerada implementada só porque possui uma URL documentada.

## C2 — Como migrar os providers existentes?

A migração será incremental. Cada provider mantém seu contrato e fixtures; o
novo parser entra primeiro por adapters testados e só depois substitui helpers
locais quando o comportamento for equivalente ou melhor.

## C3 — Como operar por horas?

O runner terá limites configuráveis, checkpoint serializável, cache, métricas e
retomada explícita. Uma execução longa não será um loop sem supervisão nem uma
permissão para ignorar falhas de acesso.
