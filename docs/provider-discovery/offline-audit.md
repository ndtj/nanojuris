# Auditoria offline de descoberta de providers

Gerado em `2026-09-13T04:19:09+00:00`. Modo: **offline-only**; rede utilizada: **não**.

## Resultado executivo

- Entradas no catálogo: **85**.
- Candidates sem adapter local: **0**.
- Adapters diagnósticos opt-in (sem promoção): **5**.
- Entradas de família: **0**.
- Candidates sem fixture local: **0**.
- Análises de fixtures executadas: **17**.
- Providers runtime auditados: **80**; com fixture versionada: **80**.
- Providers runtime somente com payload inline: **0**; sem evidência de fixture: **0**.

A ausência de fixture local não é tratada como `empty`: é uma lacuna de evidência. O catálogo e os status live foram apenas lidos; não foram revalidados contra a internet.

## Candidates mapeados com promoção pendente

| Provider | Score | Dossiê | Contrato | Fixture local | Teste local | Bloqueadores | Próxima ação |
| --- | ---: | :---: | :---: | :---: | :---: | --- | --- |

## Adapters diagnosticos opt-in

Estes modulos possuem testes e fixtures locais, mas permanecem fora do runtime padrao ate que acesso e contrato live sejam comprovados.
- `tjmsp_jurisprudencia`: lifecycle catalogado como candidato; fixtures=1, testes=1.
- `trt2_pje_jurisprudencia`: lifecycle catalogado como candidato; fixtures=4, testes=1.
- `falcao_jt`: lifecycle catalogado como candidato; fixtures=4, testes=1.
- `tjse_jurisprudencia`: lifecycle catalogado como candidato; fixtures=3, testes=2.
- `tjap_tucujuris`: lifecycle catalogado como candidato; fixtures=2, testes=2.

## Evidência dos providers runtime

A auditoria separa fixture versionada de payload embutido no teste. Payload inline não é promovido automaticamente a fixture: ele deve ser extraído somente quando o conteúdo já estiver versionado e sanitizado.

### Somente payload inline

- Nenhum provider runtime identificado.

### Sem fixture nem payload inline

- Nenhum provider runtime identificado.

## Execução prática sobre evidência local

A camada de discovery foi executada sobre referências de fixture encontradas nos dossiers. Adapters diagnósticos podem ter fixtures e testes, mas continuam fora da federação enquanto o contrato live ou o acesso público não forem comprovados.


## Decisão de promoção

Nenhum candidate foi promovido automaticamente. O próximo passo de cada candidate é obter uma evidência pública reproduzível e adicioná-la como fixture/HAR sanitizado, depois fechar o contrato e implementar em mudança SDD separada.

## Próxima ordem de trabalho

1. Escolher um candidate com contrato mais detalhado no dossier e obter fixture pública revisável.
2. Reexecutar este relatório para confirmar a presença da evidência local.
3. Criar parser e provider somente após fixture de sucesso, vazio/erro e detalhe quando disponível.
4. Atualizar catálogo gerado somente pelos geradores oficiais.

Relatório JSON correspondente: `docs/provider-discovery/offline-audit.json`.
