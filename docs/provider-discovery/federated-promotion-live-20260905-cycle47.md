# Federated promotion live smoke — cycle 47

Executado em `2026-09-05` pelo utilitário
`tools/run_federated_promotion_smoke.py`. A consulta pública bounded usou
`responsabilidade`, página 1, tamanho 1 e no máximo uma página por fonte.

- **19/19 fontes promovidas chamadas**;
- **19/19 janelas parseáveis**;
- **0 registros inválidos** e **0 erros**;
- totais desconhecidos permaneceram `None` quando a fonte não os comprovou;
- `collection_complete=false` é intencional: uma única página não comprova
  completude;
- nenhum corpo de resposta, token, cookie ou cabeçalho foi persistido.

O manifesto de promoção habilitou tecnicamente 19 fontes no rollout local.
Fontes `opt_in` e bloqueadas não foram chamadas nesta rodada.

Evidência estruturada: `federated-promotion-live-20260905-cycle47.json`.
