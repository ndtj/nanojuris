# Threat model

- **Entrada:** HTML fornecido pela fonte publica; tratado como texto, nunca
  executado.
- **Risco de injecao:** nenhum HTML e renderizado pelo parser; o consumidor
  recebe texto normalizado e o original apenas em `raw`.
- **Risco de segredo:** fixtures nao contem cookies, tokens ou credenciais.
- **Risco de classificacao:** fallback nao altera `core`, grau ou tribunal e nao
  pode promover uma resposta de erro para resultado.
