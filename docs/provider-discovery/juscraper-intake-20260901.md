# Intake estático do Juscraper — 2026-09-01

Este registro audita o repositório correto (`jtrecenti/juscraper`) a partir de
uma árvore local fixada. Não executa código upstream, não copia arquivos, não
faz chamadas live e não altera o catálogo runtime.

## Proveniência

- Repositório: https://github.com/jtrecenti/juscraper
- Commit: `604c1dd70d6f313011cc1079790febe6c71807e2` (2026-08-10T15:06:55-03:00)
- Versão: `0.3.0`
- Licença: `MIT`
- SHA-256 de `LICENSE`: `268966cc8228411db2775fbacf3d91b1a15bcdd99a713892e905b3a541b83c59`

## Superfícies encontradas

O projeto declara 25 pacotes de tribunais
estaduais brasileiros e 4 pacotes TRF. A superfície
jurisprudencial útil para este intake é de 25 `cjsg`, três `cjpg` (TJES, TJSP e
TJTO) e um detalhe `tjto.cjsg_ementa`. `cpopg`/`cposg` são consultas
processuais e os agregadores (`comunica_cnj, datajud, jusbr, pdpj`) ficam
fora do runtime textual da NanoJuris.

## Decisão

Todas as superfícies upstream são `candidate`, não `implemented`: código e
fixtures ainda precisam de adaptação independente, contrato NanoJuris,
identidade jurídica, testes negativos e evidência live limitada por fonte.
Nenhum provider novo foi registrado ou promovido nesta auditoria.

A matriz detalhada por tribunal (25 TJ + 4 TRF), incluindo equivalentes runtime,
lacunas e superfícies processuais fora de escopo, está em
`juscraper-court-inventory-20260901.json` e `.md`.

O sweep live dos providers NanoJuris permanece separado em
`all-provider-sweep-20260901.json`. Evidência estática do Juscraper não prova
que uma rota de tribunal esteja disponível agora.
