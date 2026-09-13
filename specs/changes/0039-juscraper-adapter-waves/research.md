# Pesquisa — ondas Juscraper

## Snapshot de entrada

O intake foi corrigido para o repositório `jtrecenti/juscraper`, commit
`604c1dd70d6f313011cc1079790febe6c71807e2`, versão `0.3.0`, licença MIT.
O inventário estático atual está em
`docs/provider-discovery/juscraper-intake-20260901.json`. Ele confirma 25
tribunais estaduais, mas não constitui prova de que suas rotas estão
disponíveis hoje.
O cruzamento completo de todos os 25 TJ e quatro TRF está em
`docs/provider-discovery/juscraper-court-inventory-20260901.*`; sua classificação
é deliberadamente separada de qualquer promoção de adapter.

## Ganhos observados

- API TJES com múltiplos cores e primeiro grau;
- APIs de jurisprudência textual TJRN e TJRO ainda candidatas na NanoJuris;
- detalhe de ementa TJTO corrige cards sem conteúdo da listagem;
- ampla suíte de fixtures para comparação de parsers estaduais;
- CJPG em TJES/TJSP/TJTO amplia collections decisórias sem usar processo.

## Limitações observadas

- software upstream está em estágio Alpha;
- registry, docs e árvore runtime divergem;
- modelos DataFrame e dependências não combinam com o núcleo NanoJuris;
- TJMG usa OCR de CAPTCHA e TJAP encontra Turnstile;
- TJRJ depende de comportamento de CAPTCHA que não será presumido legítimo;
- saúde das rotas não é provada pela suíte offline.

Chamadas públicas bounded de 2026-09-01 confirmaram dados reais nas superfícies
TJES (`GET /consulta-jurisprudencia/api/search`) e TJRN
(`POST /api/pesquisar`); os metadados estão em
`docs/provider-discovery/juscraper-live-smoke-20260901.*`. Nenhum adapter foi
copiado ou registrado nesta rodada. As superfícies seguem `candidate_live_valid_data`
até cada tribunal ter contrato completo, fixture, parser canônico, identidade,
teste negativo e revisão de reuso independentes.
