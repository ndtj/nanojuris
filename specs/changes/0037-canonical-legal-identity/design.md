# Design — identidade jurídica

## Grafo mínimo

    CaseIdentity
      -> DecisionIdentity (0..n)
          -> PublicationIdentity (0..n)
          -> DocumentIdentity (0..n)
          -> DecisionVersion (1..n)

`PrecedentIdentity` referencia decisões paradigma sem herdar sua identidade.

## Estratégia

1. usar ID nativo estável quando o contrato provar estabilidade;
2. compor namespace com authority/collection/grau/tipo;
3. usar fingerprint canônico versionado apenas como fallback ou sinal;
4. preservar candidatos a match antes de qualquer merge;
5. exigir política por categoria e provider.

## Deduplicação

O engine produz `distinct`, `candidate_match` ou `same_record`. Não realiza
merge destrutivo. O record escolhido mantém aliases, provenances, razões e
versões. Mudança do algoritmo reprocessa matches sem alterar IDs anteriores
silenciosamente.

## Datas

Julgamento, publicação, disponibilização, atualização da fonte e coleta são
campos distintos, com valor bruto preservado e timezone/precisão explícitos.
