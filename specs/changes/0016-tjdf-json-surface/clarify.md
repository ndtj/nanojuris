# Clarify

- **Q1**: a API JSON deve substituir o fluxo HTML imediatamente? **Não**. Ela
  permanece opt-in até uma comparação controlada de cobertura e campos.
- **Q2**: a nova rota cria um provider separado? **Não**. A rota pertence ao
  adapter `tjdf_juris`, que preserva a identidade única da fonte.
- **Q3**: `possuiInteiroTeor=true` garante texto integral? **Não**. O texto só é
  preenchido quando o campo de conteúdo está presente e não indica
  indisponibilidade; o valor bruto permanece em `raw`.
