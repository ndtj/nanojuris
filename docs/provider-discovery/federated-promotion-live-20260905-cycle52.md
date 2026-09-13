# Federated promotion live smoke — cycle 52

Executado em `2026-09-05` pelo utilitário
`tools/run_federated_promotion_smoke.py`. A consulta pública bounded usou
`responsabilidade`, página 1, tamanho 1 e no máximo uma página por fonte.

- **22/22 fontes promovidas chamadas**;
- **22/22 janelas parseáveis**;
- **0 registros inválidos** e **0 erros**;
- totais desconhecidos permaneceram `None` quando a fonte não os comprovou;
- `collection_complete=false` é intencional: uma única página não comprova
  completude;
- nenhum corpo de resposta, token, cookie ou cabeçalho foi persistido.

O manifesto de promoção habilitou tecnicamente 22 fontes no rollout local.
Fontes `opt_in` e bloqueadas não foram chamadas nesta rodada. O TJMS/CJSG foi
incluído após a validação específica do ciclo 51; seu detalhe pode retornar
PDF sem camada de texto, estado que permanece explícito no diagnóstico.

Evidência estruturada: `federated-promotion-live-20260905-cycle52.json`.
