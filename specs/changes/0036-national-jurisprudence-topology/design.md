# Design — topologia nacional

## Entidades

- `Branch`: ramo ou dimensão administrativa;
- `Authority`: órgão responsável;
- `Collection`: conjunto jurídico publicado, com grau e tipo;
- `Surface`: contrato técnico observado durante um intervalo;
- `ProviderBinding`: implementação NanoJuris que consome a superfície;
- `CoverageEvidence`: fixture, contrato, live snapshot e período;
- `CoverageClaim`: métrica derivada com numerador, denominador e data.

## Identidade

IDs são estáveis e não dependem do hostname. Uma troca de portal cria nova
surface e encerra a validade da anterior; não cria nova autoridade ou collection.

## Projeções

O mesmo arquivo fonte gera matriz nacional, backlog por ramo, cobertura pública
e validação dos source IDs. Estados operacionais live vêm de 0033 e nunca
reescrevem a existência institucional da collection.

## Épocas de cobertura

Cada rodada fecha uma `coverage_epoch` identificada pela versão da topologia e
data de corte. Novos tribunais, collections ou evidências abrem outra época;
eles não tornam impossível concluir a rodada anterior nem reescrevem seu
histórico.

## Gate

Nenhum claim “nacional”, “completo” ou “100%” é publicado sem projeção desta
topologia e sem explicitar a dimensão medida.
