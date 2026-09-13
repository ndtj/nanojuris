# Pesquisa e referências — busca live inteligente

Mudança: `specs/changes/0077-live-intelligent-federated-search/spec.md`
Data da revisão: `2026-09-07`
Responsável: Search Architecture

## Pergunta de pesquisa

Como melhorar a relevância jurídica do top 10 em uma federação de fontes com
scores, campos, latências e disponibilidade heterogêneos, sem manter corpus
indexado e sem inferência neural por consulta?

## Evidência interna observada

| Evidência | Achado | Impacto |
| --- | --- | --- |
| `NanoJurisClient._rank_and_deduplicate` | score atual é contagem simples de tokens em poucos campos | substituir por ranker jurídico comparável |
| `mergeBatchResults` da plataforma | lotes são concatenados e deduplicados sem reranking global | ordenar todo o conjunto a cada onda |
| contrato da API web | máximo de 12 fontes por chamada | usar até 12 no modo adaptativo e lotes no modo all |
| configuração atual | somente três fontes recomendadas | criar seleção adaptativa sem remover seleção manual |
| live: `responsabilidade civil administrativa` | resultado genérico de responsabilidade civil apareceu no topo | exigir cobertura de conceitos e penalizar termo isolado |
| live: `acórdãos sobre divórcio` | quatro resultados fortes seguidos por itens fracos | separar comando documental do tema e aplicar limiar/razões |

As chamadas bounded observadas em 2026-09-07 usaram as três fontes recomendadas
e concluíram em aproximadamente 2,4–2,8 segundos. Elas servem como diagnóstico,
não como benchmark estatístico.

## Fontes primárias e técnicas

| Fonte | Achado verificável | Aplicabilidade | Confiança |
| --- | --- | --- | --- |
| [BEIR](https://arxiv.org/abs/2104.08663) | BM25 é baseline robusto; reranking neural melhora média com custo superior | fundamenta baseline lexical CPU-only | alta |
| [Legal Case Retrieval Survey](https://aclanthology.org/2024.acl-long.350/) | recuperação jurídica exige avaliação específica de casos e relevância | fundamenta benchmark jurídico próprio | alta |
| [Legal Elements for Case Retrieval](https://aclanthology.org/2024.findings-acl.139/) | elementos jurídicos melhoram a correspondência entre casos | fundamenta sinais de classe, tema, órgão e tipo | alta |
| [Query-driven Relevant Paragraph Extraction](https://aclanthology.org/2024.lrec-main.1177/) | trechos relevantes à consulta são mais úteis que texto integral indiscriminado | fundamenta destaque de trechos e truncamento seguro | alta |
| [OpenSearch RRF](https://docs.opensearch.org/latest/vector-search/ai-search/hybrid-search/rrf/) | RRF combina posições sem comparar magnitudes heterogêneas | fundamenta uso fraco do rank nativo | alta |

## Síntese técnica

1. Não é correto comparar scores nativos dos tribunais.
2. O rank nativo ainda contém sinal útil e pode entrar por posição, com peso
   pequeno e auditável.
3. A principal melhoria de baixo custo vem de interpretação da consulta,
   ponderação por campo, cobertura/proximidade e consistência jurídica.
4. O algoritmo deve ranquear apenas a janela de candidatos live; portanto a
   avaliação deve distinguir precisão do top 10 de recall nacional.
5. Pesos só devem mudar por benchmark versionado, nunca por impressão visual.

## Alternativas rejeitadas

- Índice próprio: rejeitado por decisão do produto e custo operacional.
- Reranking LLM/embedding: rejeitado por custo e requisito de determinismo.
- Concatenar fontes: rejeitado porque ordem de lote vira falso sinal de
  relevância.
- Ordenar por data: rejeitado como default; recência não equivale a relevância.
- Quota rígida por tribunal: rejeitada porque desloca resultado superior.
- Usar apenas RRF: insuficiente quando um resultado fraco ocupa posição alta em
  uma única fonte; RRF será apenas um sinal do ranker.

## Limitações

- Não foi produzido ainda um conjunto de julgamentos humanos em português.
- Latência de providers varia externamente e não pode ser garantida pela lib.
- Sinônimos jurídicos precisam de curadoria conservadora para evitar expansão
  semântica indevida.
- O modo all pode exceder uma única invocação e continuará sendo progressivo.
