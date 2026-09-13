# Pesquisa — avaliação de qualidade

Status: in_progress

## Evidência atual

O scorecard normativo define autoridade, contrato, identidade, conteúdo,
temporalidade, provenance, parser, completude, operação e documentação. O
catálogo já contém maturity_tier, mas o cálculo ainda precisa ser plenamente
reproduzível.

## Decisão orientada

Combinar score ponderado com gates críticos. Pontuação alta nunca compensa false
empty, identidade instável, ausência de provenance ou fonte não oficial.

## Lacunas

- schema do relatório;
- golden comparator comum;
- tolerância de drift por campo;
- processo humano de promoção e rebaixamento.
