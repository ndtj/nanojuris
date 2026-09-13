# Benchmark do ranking live v1

Este benchmark mede apenas a ordenação determinística da busca live. Ele não é
um corpus e não substitui a disponibilidade dos tribunais. A versão inicial
contém oito consultas sanitizadas e deliberadamente não contém texto de
decisões.

## Julgamento

1. Separe desenvolvimento e holdout antes de calibrar pesos.
2. Para cada consulta, monte o pool do ranking legado, do `legal-live-v1` e
   das variantes nativas disponíveis.
3. Mostre ao julgador apenas a consulta, o ID canônico, metadados mínimos e o
   trecho público permitido; o algoritmo e o score ficam ocultos.
4. Atribua 0–3: irrelevante; relacionado mas não responde; relevante;
   altamente relevante.
5. Use dois julgadores independentes. Diferença de dois pontos exige terceiro
   julgamento.
6. Calibre somente no split `development`; congele pesos e meça `holdout` uma
   vez para o gate de release.

## Métricas

`tools/evaluate_live_ranking.py` calcula nDCG@10, precisão@5, MRR@10 e a taxa
de irrelevantes no top 5. Sem julgamentos, o comando retorna `pending_labels` e
não inventa uma métrica.

## Critério

O ranking só pode substituir o legado após melhoria relativa de 25% em nDCG@10,
redução de 50% de irrelevantes no top 5, no máximo 10% de irrelevantes no top 5,
100% de acerto na posição 1 para identificador exato e p95 local abaixo de
150 ms para 240 candidatos. Esses números são gates de avaliação, não uma
afirmação de que já foram atingidos.
