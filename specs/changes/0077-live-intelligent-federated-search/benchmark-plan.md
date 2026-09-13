# Benchmark de relevância jurídica live

## Estrutura do dataset

Arquivo versionado JSONL, sem conteúdo sigiloso:

```json
{"query_id":"Q001","query":"acórdãos sobre divórcio","intent":{"document_type":"acordao"},"split":"development","notes":"linguagem natural"}
```

Julgamentos separados:

```json
{"query_id":"Q001","result_id":"public-id","grade":3,"judge":"J1","reason_codes":["topic_exact","document_type_exact"]}
```

`judge` é pseudônimo de função, não identidade. Não copiar inteiro teor para o
dataset; referenciar ID e fonte públicos.

## Composição mínima

- 60 queries development e 30 holdout.
- Ao menos 10 por tipo: tema, linguagem natural, identificador, filtro
  estrutural, ambiguidade e consulta negativa/sem resultado.
- Representar civil, família, consumidor, administrativo, penal, processual,
  constitucional, tributário, trabalhista e eleitoral quando as fontes
  selecionadas forem aplicáveis.
- Não permitir que mais de 20% das queries venham do mesmo padrão sintático.

## Pool

Por query, unir os top 20 do legacy, legal-live-v1 e ranks nativos de cada
fonte. Deduplicar por identidade, randomizar apresentação e ocultar algoritmo,
rank e score do julgador.

## Guia 0–3

- 3: responde diretamente ao tema/intenção e respeita filtros.
- 2: materialmente relevante, mas parcial ou menos específico.
- 1: apenas relacionado; não responde à necessidade principal.
- 0: irrelevante, conflitante ou correspondência lexical acidental.

Conflito explícito de grau/tipo solicitado limita nota a 0. Documento sem texto
suficiente para avaliar recebe `unjudgeable`, não 0, e é medido separadamente.

## Métricas

- principal: nDCG@10;
- Precision@5, MRR@10, irrelevante@5;
- success@1 para identificadores;
- precisão de grau/tipo;
- cobertura julgável e taxa de zero;
- tempo até primeira onda e consolidação;
- CPU p50/p95 do ranker e memória máxima.

## Calibração

1. Congelar holdout antes de alterar pesos.
2. Medir baseline legacy.
3. Ajustar uma família de sinais por vez no development.
4. Registrar cada configuração e métrica.
5. Selecionar uma única configuração antes do holdout.
6. Executar holdout uma vez; falha não autoriza recalibrar no holdout.

## Gates

- nDCG@10: +25% relativo.
- irrelevante@5: -50% relativo e <= 10% absoluto.
- identifier success@1: 100%.
- grau/tipo explícito: 100% de precisão.
- 240 candidatos: <150 ms p95 em 100 repetições, após 10 warmups.

O relatório deve publicar baseline, novo valor, intervalo por bootstrap e número
de queries julgáveis. Não usar frases como “nível Google” como claim mensurado.
