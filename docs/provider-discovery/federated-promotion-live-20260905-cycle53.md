# Federated promotion live smoke — cycle 53

Executado em `2026-09-05` por `tools/run_federated_promotion_smoke.py` com a
consulta pública bounded `responsabilidade`, página 1, tamanho 1 e limite de
uma página por fonte.

- **25/25 fontes promovidas chamadas**;
- **25/25 janelas parseáveis**;
- **0 registros inválidos** e **0 erros**;
- os dez totais que a fonte não comprovou permaneceram `None`;
- `collection_complete=false` é intencional: uma janela não prova completude;
- nenhum corpo, token, cookie ou cabeçalho foi persistido.

O manifesto técnico local habilita 25 fontes. Os três novos bindings e-SAJ
(TJAC, TJAL e TJAM) fornecem busca textual; seus detalhes com CAPTCHA aparecem
como `AccessControlRequiredError` no ciclo 51 e não são contornados.

Evidência estruturada: `federated-promotion-live-20260905-cycle53.json`.
