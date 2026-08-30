# Threat model

Riscos principais: aceitar HTML/payload alterado como válido, misturar campos
de providers, transformar bloqueio em vazio ou registrar dados pessoais em
fixtures. Mitigações: fixtures mínimas, validação de schema, traces, limites de
payload, classificação explícita e revisão de diffs.
